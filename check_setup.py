"""Check that your laptop is ready for the Agency Cup.

    uv run python check_setup.py

It checks Python, your .env, the game website, your team key, the game's MCP server and your model key.
It never prints your keys.
"""

from __future__ import annotations

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv

try:
    import agency_kit  # noqa: F401  (switches the output to UTF-8, so the ✅ lines also work on Windows)
except ImportError:
    pass  # not run with uv: the check below says so


def _say(ok: bool, text: str, fix: str = "") -> bool:
    print(("✅ " if ok else "❌ ") + text + (f"\n     → {fix}" if fix and not ok else ""))
    return ok


def check_setup() -> bool:
    """Check Python, the .env values, the game website and the team key. Returns True when all pass."""
    load_dotenv(override=True)
    good = _say(sys.version_info >= (3, 12), f"Python {sys.version_info.major}.{sys.version_info.minor}",
                "Run this with uv: uv run python check_setup.py")

    url = os.environ.get("AGENCY_CUP_URL", "").rstrip("/")
    key = os.environ.get("TEAM_KEY", "")
    good &= _say(bool(url), "AGENCY_CUP_URL is set", "Copy .env.example to .env and fill it in.")
    good &= _say(key.startswith("ac_") and key != "ac_your_team_key", "TEAM_KEY is set",
                 "Register your team on the game website, then paste the key (ac_...) into .env.")
    if os.environ.get("PROVIDER", "nvidia").lower() == "openai":
        good &= _say(bool(os.environ.get("OPENAI_API_KEY")), "OPENAI_API_KEY is set (PROVIDER=openai)")
    else:
        nv = os.environ.get("NVIDIA_API_KEY", "")
        good &= _say(nv.startswith("nvapi-") and nv != "nvapi-your-key", "NVIDIA_API_KEY is set",
                     "Get a free key at https://build.nvidia.com and paste it (nvapi-...) into .env.")
    if not url:
        return False

    try:
        health = httpx.get(f"{url}/api/health", timeout=15)
        reachable = _say(health.status_code == 200, f"The game website answers: {url}",
                         f"It replied {health.status_code}. Check AGENCY_CUP_URL with the organisers.")
    except httpx.HTTPError as e:
        reachable = _say(False, f"The game website answers: {url}", f"No connection ({type(e).__name__}). Check the URL and your network.")
    good &= reachable
    if not reachable or not key:
        return False

    me = httpx.get(f"{url}/api/me", headers={"Authorization": f"Bearer {key}"}, timeout=15)
    if not _say(me.status_code == 200, "Your team key works", "The game did not accept TEAM_KEY. Copy it again, with no spaces."):
        return False
    info = me.json()
    print(f"     Team: {info['team']}")
    good &= _say(info["round_status"] == "open", f"A round is open: {info['round'] or 'none'}",
                 f"Round status is '{info['round_status']}'. You can call tools only while a round is open.")
    return bool(good)


async def check_mcp() -> bool:
    """Connect to the game's MCP server and ask for its tools. Returns True when it answers."""
    from agency_kit.case_mcp import list_tools, mcp_url

    load_dotenv(override=True)
    try:
        tools = await list_tools()
        return _say(bool(tools), f"The MCP server answers: {len(tools)} tools at {mcp_url()}")
    except BaseException as e:  # noqa: BLE001 - connection problems arrive wrapped in exception groups
        while isinstance(e, BaseExceptionGroup) and e.exceptions:
            e = e.exceptions[0]
        return _say(False, f"The MCP server answers: {mcp_url()}",
                    f"{type(e).__name__}: {str(e)[:160]}. Check AGENCY_CUP_URL and TEAM_KEY.")


async def check_model() -> bool:
    """Send one tiny request to your model. Returns True when it answers."""
    from agency_kit.nvidia_client import make_client

    load_dotenv(override=True)
    try:
        client, model = make_client()
    except SystemExit as e:  # the model key is missing
        return _say(False, "Your model answers", str(e))
    try:
        reply = await client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": "Reply with exactly: ready"}])
        return _say(True, f"Your model answers: {model} said {reply.choices[0].message.content!r}")
    except Exception as e:  # noqa: BLE001 - show any API problem as a hint
        return _say(False, f"Your model answers: {model}", f"{type(e).__name__}: {str(e)[:160]}")


if __name__ == "__main__":
    ready = check_setup()
    ready = asyncio.run(check_mcp()) and ready
    ready = asyncio.run(check_model()) and ready
    print("\n🎉 You are ready. Open start_here.ipynb." if ready else "\nFix the ❌ lines above, then run this again.")
    sys.exit(0 if ready else 1)
