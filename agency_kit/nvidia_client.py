"""A polite model client for the NVIDIA API (free tier: about 40 requests per minute per key).

- Spaces calls out to 32 requests per minute (headroom under ~40).
- Runs at most 3 model calls at the same time.
- On 429 or 5xx: waits (honouring Retry-After, else 1 s, 2 s, 4 s... up to 30 s, plus jitter) and retries.
- On 401/403: prints a clear hint (wrong key, or credits used up).

Works with any framework that accepts an OpenAI client or an httpx client:
    client, model = make_client()            # AsyncOpenAI + model name
    ChatOpenAI(..., http_async_client=httpx.AsyncClient(transport=RateLimitedTransport()))

Set PROVIDER=openai to test locally with an OpenAI key instead of NVIDIA.
"""

from __future__ import annotations

import asyncio
import os
import random
import time

import httpx
from openai import AsyncOpenAI

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"  # tested Nov 2026: live, reliable tool calls
RETRY_STATUS = {429, 500, 502, 503, 504}


class RateLimitedTransport(httpx.AsyncBaseTransport):
    def __init__(self, rpm: int = 32, max_parallel: int = 3, max_retries: int = 6):
        self.inner = httpx.AsyncHTTPTransport()
        self.interval = 60.0 / rpm
        self.next_slot = 0.0
        self.max_parallel = max_parallel
        self.max_retries = max_retries
        self._lock: asyncio.Lock | None = None
        self._sem: asyncio.Semaphore | None = None

    async def _wait_turn(self) -> None:
        self._lock = self._lock or asyncio.Lock()
        async with self._lock:
            now = time.monotonic()
            wait = self.next_slot - now
            self.next_slot = max(now, self.next_slot) + self.interval
        if wait > 0:
            await asyncio.sleep(wait)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self._sem = self._sem or asyncio.Semaphore(self.max_parallel)
        async with self._sem:
            for attempt in range(self.max_retries + 1):
                await self._wait_turn()
                response = await self.inner.handle_async_request(request)
                if response.status_code in (401, 403):
                    print("[model] The API said 401/403: check your API key, and your NVIDIA credits at build.nvidia.com.")
                    return response
                if response.status_code not in RETRY_STATUS or attempt == self.max_retries:
                    return response
                retry_after = response.headers.get("retry-after", "")
                await response.aclose()
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = min(30.0, 2.0 ** attempt) + random.random()
                print(f"[model] {response.status_code}: waiting {delay:.1f} s, then retry {attempt + 1}/{self.max_retries}")
                await asyncio.sleep(delay)
        raise RuntimeError("unreachable")

    async def aclose(self) -> None:
        await self.inner.aclose()


def make_client() -> tuple[AsyncOpenAI, str]:
    """Return (client, model name) for PROVIDER=nvidia (default) or PROVIDER=openai."""
    provider = os.environ.get("PROVIDER", "nvidia").lower()
    http = httpx.AsyncClient(transport=RateLimitedTransport(), timeout=httpx.Timeout(120, connect=15))
    if provider == "openai":
        return AsyncOpenAI(http_client=http, max_retries=0), os.environ.get("MODEL", "gpt-5.4-mini")
    key = os.environ.get("NVIDIA_API_KEY")
    if not key:
        raise SystemExit("Set NVIDIA_API_KEY (from build.nvidia.com) in your .env")
    client = AsyncOpenAI(base_url=NVIDIA_BASE_URL, api_key=key, http_client=http, max_retries=0)
    return client, os.environ.get("MODEL", DEFAULT_NVIDIA_MODEL)
