"""Shared set-up for the starter notebooks: one model, four frameworks.

Every notebook imports this first (`from agency_kit import kit`). It reads the repo's .env, then gives each framework the SAME model:
    openai_sdk_model()   OpenAI Agents SDK
    crewai_llm()         CrewAI
    langchain_model()    LangChain / LangGraph
    adk_model()          Google ADK
PROVIDER=nvidia (default) uses build.nvidia.com; PROVIDER=openai uses an OpenAI key instead.
All four send their model calls through ONE shared speed limit (RPM, default 20 a minute), so the
free NVIDIA tier's ~40 requests a minute is never exceeded, whichever sections you run.

`traced` wraps a plain tool function so it prints every call. Because all four frameworks call the
very same Python functions, you see the same trace whichever framework you run.
For tools that live on an MCP server (Case #002) there is no function to wrap, so each framework gets its own
small helper that prints the same lines: sdk_steps(), crewai_steps(), langchain_steps() and adk_step.
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import os
import random
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # the AgencyCup folder

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
logging.getLogger("crewai.llms.base_llm").setLevel(logging.ERROR)  # quiet "approximate token count" warnings

MCP_SERVER_LOG = Path(tempfile.gettempdir()) / "agency_kit_mcp_server.log"


def _give_notebook_stderr_a_file() -> None:
    """Windows + Jupyter: let MCP start a tool server as a subprocess (stdio).

    MCP hands the notebook's stderr to the subprocess, and Windows needs a real file for that. A Jupyter
    kernel on Windows has none, so every stdio MCP cell stopped with `UnsupportedOperation: fileno`.
    We give it MCP_SERVER_LOG. What the tool server prints on stderr then goes to that file.
    On macOS and Linux the notebook's stderr already has a real file, so nothing changes there."""
    err = sys.stderr
    try:
        err.fileno()
    except (AttributeError, OSError, ValueError):  # io.UnsupportedOperation is both an OSError and a ValueError
        if type(err).__module__.startswith("ipykernel"):
            err._original_stdstream_copy = os.open(MCP_SERVER_LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND)


_give_notebook_stderr_a_file()

import httpx  # noqa: E402
from agency_kit.nvidia_client import DEFAULT_NVIDIA_MODEL, NVIDIA_BASE_URL  # noqa: E402

PROVIDER = os.environ.get("PROVIDER", "nvidia").lower()
MODEL = os.environ.get("MODEL", DEFAULT_NVIDIA_MODEL if PROVIDER == "nvidia" else "gpt-5.4-mini")
CONTEXT_WINDOW = int(os.environ.get("CONTEXT_WINDOW", "128000"))  # tokens; check your model's card


def _nvidia_key() -> str:
    key = os.environ.get("NVIDIA_API_KEY", "")
    if PROVIDER == "nvidia" and not key:
        raise SystemExit("Put NVIDIA_API_KEY=nvapi-... in AgencyCup/.env (free key at build.nvidia.com)")
    return key


def describe() -> None:
    where = "NVIDIA API (build.nvidia.com)" if PROVIDER == "nvidia" else "OpenAI API"
    print(f"🧠 Model: {MODEL}  via {where}")


# ---------------------------------------------------------------- one shared speed limit
# The free NVIDIA tier allows about 40 requests a minute per key. All four frameworks send their model calls
# through the same gate below, so even running every section back to back stays under that limit.
RPM = int(os.environ.get("RPM", "20"))  # NVIDIA said 429 at 30 a minute in our tests
RETRY_STATUS = {429, 500, 502, 503, 504}


class _Gate:
    """Hands out one request slot every 60/RPM seconds, shared by every thread and event loop."""

    def __init__(self, rpm: int):
        self.interval, self.next_slot, self.lock = 60.0 / rpm, 0.0, threading.Lock()

    def reserve(self) -> float:
        with self.lock:
            now = time.monotonic()
            wait = self.next_slot - now
            self.next_slot = max(now, self.next_slot) + self.interval
        return max(0.0, wait)


GATE = _Gate(RPM)


def _backoff(response: httpx.Response, attempt: int) -> float:
    try:
        return float(response.headers.get("retry-after", ""))
    except ValueError:
        return min(30.0, 2.0 ** attempt) + random.random()


def _say_retry(status: int, delay: float, attempt: int) -> None:
    print(f"[model] {status}: waiting {delay:.0f} s, then retry {attempt + 1}/6", flush=True)


class PacedTransport(httpx.BaseTransport):
    """Sync HTTP: wait for a slot, retry 429/5xx with backoff. (CrewAI and LiteLLM use sync calls.)"""

    def __init__(self):
        self.inner = httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        for attempt in range(7):
            time.sleep(GATE.reserve())
            response = self.inner.handle_request(request)
            if response.status_code not in RETRY_STATUS or attempt == 6:
                return response
            response.close()
            delay = _backoff(response, attempt)
            _say_retry(response.status_code, delay, attempt)
            time.sleep(delay)
        raise RuntimeError("unreachable")


class AsyncPacedTransport(httpx.AsyncBaseTransport):
    """Async HTTP: the same gate and retries, without blocking the event loop."""

    def __init__(self):
        self.inner = httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        for attempt in range(7):
            await asyncio.sleep(GATE.reserve())
            response = await self.inner.handle_async_request(request)
            if response.status_code not in RETRY_STATUS or attempt == 6:
                return response
            await response.aclose()
            delay = _backoff(response, attempt)
            _say_retry(response.status_code, delay, attempt)
            await asyncio.sleep(delay)
        raise RuntimeError("unreachable")


def _sync_http() -> httpx.Client:
    return httpx.Client(transport=PacedTransport(), timeout=httpx.Timeout(120, connect=15))


def _async_http() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=AsyncPacedTransport(), timeout=httpx.Timeout(120, connect=15))


def _api() -> dict:
    """base_url and api_key for an OpenAI-compatible client."""
    if PROVIDER == "openai":
        return {"api_key": os.environ.get("OPENAI_API_KEY")}
    return {"base_url": NVIDIA_BASE_URL, "api_key": _nvidia_key()}


# ---------------------------------------------------------------- one model, four frameworks
def openai_sdk_model():
    """OpenAI Agents SDK: any OpenAI-compatible API through OpenAIChatCompletionsModel."""
    from agents import OpenAIChatCompletionsModel, set_tracing_disabled
    from openai import AsyncOpenAI

    set_tracing_disabled(True)  # tracing uploads to OpenAI; off when you use an NVIDIA key
    client = AsyncOpenAI(**_api(), http_client=_async_http(), max_retries=2)
    return OpenAIChatCompletionsModel(model=MODEL, openai_client=client)


def langchain_model():
    """LangChain / LangGraph: ChatOpenAI pointed at NVIDIA, through the shared gate."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=MODEL, **_api(), http_client=_sync_http(), http_async_client=_async_http(),
                      max_retries=2)  # the gate handles 429/5xx; this retries dropped connections


def crewai_llm():
    """CrewAI: 'openai/<model>' + base_url = any OpenAI-compatible API."""
    from crewai import LLM
    from openai import AsyncOpenAI, OpenAI

    # Tell CrewAI the real context size: for unknown models it assumes 8,192 tokens, cuts the
    # investigation short, and the next agent may then invent facts.
    if PROVIDER == "openai":
        llm = LLM(model=MODEL, context_window_size=CONTEXT_WINDOW)
    else:
        llm = LLM(model=f"openai/{MODEL}", base_url=NVIDIA_BASE_URL, api_key=_nvidia_key(), temperature=0.2,
                  context_window_size=CONTEXT_WINDOW)
    # CrewAI builds its own OpenAI clients. Swap in clients that go through the shared gate.
    llm._client = OpenAI(**_api(), http_client=_sync_http(), max_retries=2)
    llm._async_client = AsyncOpenAI(**_api(), http_client=_async_http(), max_retries=2)
    return llm


def crewai_embedder():
    """CrewAI memory: it finds old notes by MEANING, so it needs an embedding model (text in, numbers out)."""
    if PROVIDER == "openai":
        return {"provider": "openai", "config": {"model_name": os.environ.get("EMBED_MODEL", "text-embedding-3-small")}}
    return {"provider": "openai", "config": {"api_key": _nvidia_key(), "api_base": NVIDIA_BASE_URL,
                                             "model_name": os.environ.get("EMBED_MODEL", "nvidia/nemotron-3-embed-1b")}}


def adk_model():
    """Google ADK uses Gemini by default. LiteLlm lets it use any other model, NVIDIA's included."""
    import litellm
    from google.adk.models.lite_llm import LiteLlm

    litellm.suppress_debug_info = True
    litellm.client_session, litellm.aclient_session = _sync_http(), _async_http()  # LiteLLM's calls use the gate too
    if PROVIDER == "openai":
        return LiteLlm(model=f"openai/{MODEL}", num_retries=2)
    return LiteLlm(model=f"openai/{MODEL}", api_base=NVIDIA_BASE_URL, api_key=_nvidia_key(), num_retries=2)


# ---------------------------------------------------------------- see every tool call
def traced(fn):
    """Print each call of a tool and a short view of its result. Keeps the name, docstring and types."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        shown = ", ".join([repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()])
        text = str(result).replace("\n", " ")
        # One write for both lines, so tools that run at the same time (a team of agents) do not mix their lines.
        print(f"🔧 {fn.__name__}({shown})\n     ↳ {text[:150]}{'…' if len(text) > 150 else ''}\n", end="", flush=True)
        return result

    return wrapper


# ---------------------------------------------------------------- see every tool call (MCP tools)
# With MCP there is no Python function to wrap: the tools live on the server. Each framework has its own
# place to watch a tool call, so there is one small helper per framework. All four print the same two lines.
def show_step(name: str, args, result) -> None:
    """Print one tool call and the start of its answer: the same two lines `traced` prints."""
    shown = ", ".join(f"{k}={v!r}" for k, v in args.items()) if isinstance(args, dict) else str(args or "")
    text = _answer_text(result).replace("\n", " ")
    print(f"🔧 {name}({shown})\n     ↳ {text[:150]}{'…' if len(text) > 150 else ''}\n", end="", flush=True)


def _answer_text(result) -> str:
    """The text of a tool answer, whichever shape the framework hands over."""
    if isinstance(result, dict):
        blocks = result.get("content")
        if isinstance(blocks, list):
            texts = [b.get("text", "") for b in blocks if isinstance(b, dict)]
            if any(texts):
                return " ".join(texts)
        if isinstance(result.get("text"), str):
            return result["text"]
        return json.dumps(result.get("structuredContent") or result, ensure_ascii=False, default=str)
    text = getattr(result, "text", None)  # a LangChain ToolMessage
    return str(text) if isinstance(text, str) else str(result)


def sdk_steps():
    """OpenAI Agents SDK: `Runner.run(agent, task, hooks=kit.sdk_steps())` prints every tool call."""
    from agents import RunHooks

    class Steps(RunHooks):
        async def on_tool_end(self, context, agent, tool, result):
            args = getattr(context, "tool_arguments", "") or ""
            try:
                args = json.loads(args)
            except (TypeError, ValueError):
                pass
            show_step(tool.name, args, result)

    return Steps()


def langchain_steps():
    """LangGraph: `graph.ainvoke(..., {"callbacks": [kit.langchain_steps()]})` prints every tool call."""
    from langchain_core.callbacks import AsyncCallbackHandler

    class Steps(AsyncCallbackHandler):
        def __init__(self):
            self.calls = {}

        async def on_tool_start(self, serialized, input_str, *, run_id, inputs=None, **kwargs):
            self.calls[run_id] = ((serialized or {}).get("name", "tool"), inputs if inputs is not None else input_str)

        async def on_tool_end(self, output, *, run_id, **kwargs):
            name, args = self.calls.pop(run_id, ("tool", ""))
            show_step(name, args, output)

        async def on_tool_error(self, error, *, run_id, **kwargs):
            name, args = self.calls.pop(run_id, ("tool", ""))
            show_step(name, args, f"ERROR: {error}")

    return Steps()


def adk_step(tool, args, tool_context, tool_response):
    """Google ADK: `LlmAgent(..., after_tool_callback=kit.adk_step)` prints every tool call."""
    show_step(tool.name, args, tool_response)


def crewai_steps() -> None:
    """CrewAI: call `kit.crewai_steps()` once before kickoff. It listens for CrewAI's tool events."""
    global _crewai_listening
    if _crewai_listening:
        return
    from crewai.events import crewai_event_bus
    from crewai.events.types.tool_usage_events import ToolUsageErrorEvent, ToolUsageFinishedEvent

    def short(name: str) -> str:  # CrewAI puts the server's address in front: agency_thisara_me_mcp_search
        return str(name).split("_mcp_", 1)[-1]

    @crewai_event_bus.on(ToolUsageFinishedEvent)
    def _finished(source, event):
        show_step(short(event.tool_name), event.tool_args, event.output)

    @crewai_event_bus.on(ToolUsageErrorEvent)
    def _failed(source, event):
        show_step(short(event.tool_name), event.tool_args, f"ERROR: {event.error}")

    _crewai_listening = True


_crewai_listening = False


def crewai_tools(functions):
    """CrewAI wants its own tool objects: wrap plain functions with crewai.tools.tool."""
    from crewai.tools import tool

    return [tool(f.__name__)(f) for f in functions]


async def run_adk(agent, prompt: str) -> str:
    """Run an ADK agent once and return its final answer: the InMemoryRunner lines from Case #000, section 4."""
    from google.adk.runners import InMemoryRunner

    events = await InMemoryRunner(agent=agent, app_name="agency_cup").run_debug(prompt, quiet=True)
    for event in reversed(events):
        parts = [p for p in (event.content.parts if event.content else []) or [] if p.text and not p.thought]
        if parts:
            return "\n".join(p.text for p in parts)
    return "(no final answer)"


def ask_human(question: str) -> bool:
    """A human check. In Jupyter it waits for you to type; when run headless it says so and approves."""
    try:
        answer = input(f"👤 {question} (yes/no): ")
    except Exception:  # no keyboard, e.g. nbconvert --execute
        print(f"👤 {question} (yes/no): yes   ← no keyboard here, so this demo approves")
        return True
    return answer.strip().lower() in {"y", "yes"}
