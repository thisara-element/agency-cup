"""Starter detective: Google ADK + NVIDIA model + the game's MCP tools.

    uv run python starters/agent_adk.py            # dry run: investigates, does NOT submit
    uv run python starters/agent_adk.py --submit   # the real thing: may call submit_report

There is no tool code in this file. McpToolset connects to the game's MCP server,
asks which tools exist, and gives them to the agent. The Runner gives you one
event per step, so this script prints every tool call as it happens.
ADK talks to NVIDIA (or OpenAI) through LiteLLM, using the same polite client as the other starters.
"""

import asyncio
import json
import sys

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.run_config import RunConfig
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.genai import types

from starters.agent_openai_sdk import DRY_RUN_NOTE, INSTRUCTIONS
from agency_kit.case_mcp import mcp_headers, mcp_url
from agency_kit.nvidia_client import make_client

load_dotenv()


def make_model() -> LiteLlm:
    """Wrap the rate-limited NVIDIA (or OpenAI) client so ADK can use it."""
    client, model_name = make_client()
    return LiteLlm(model=f"openai/{model_name}", client=client, api_key=client.api_key, api_base=str(client.base_url))


def _short(reply: dict) -> str:
    """Turn one MCP tool answer into a short line: its cost, then the start of the content."""
    data = reply.get("structuredContent") or {}
    if not data:
        text = next((c.get("text", "") for c in reply.get("content") or [] if isinstance(c, dict)), "")
        try:
            data = json.loads(text)
        except ValueError:
            return text[:150] or str(reply)[:150]
    data = data.get("result", data) if isinstance(data.get("result"), dict) else data
    rest = {k: v for k, v in data.items() if k not in ("ok", "cost", "budget_left")}
    return f"cost {data.get('cost', 0)} · {str(data.get('error') or rest)[:130]}"


async def run_detective(instructions: str = INSTRUCTIONS, submit: bool = False, max_llm_calls: int = 60) -> str:
    """Run the detective once, print each step, and return its final answer.

    submit=False is a dry run: the submit_report tool is hidden from the agent. Budget points are still spent.
    """
    game = McpToolset(connection_params=StreamableHTTPConnectionParams(url=mcp_url(), headers=mcp_headers(), timeout=30),
                      tool_filter=lambda tool, _context=None: submit or tool.name != "submit_report")
    detective = LlmAgent(name="detective", model=make_model(), instruction=instructions, tools=[game])
    runner = InMemoryRunner(agent=detective, app_name="agency_cup")
    session = await runner.session_service.create_session(app_name="agency_cup", user_id="team")
    task = "Solve Case #002. Start with case_brief." + ("" if submit else DRY_RUN_NOTE)

    answer, n = "", 0
    try:
        async for event in runner.run_async(user_id="team", session_id=session.id,
                                            run_config=RunConfig(max_llm_calls=max_llm_calls),
                                            new_message=types.Content(role="user", parts=[types.Part(text=task)])):
            for part in (event.content.parts if event.content and event.content.parts else []):
                if part.function_call:
                    n += 1
                    print(f"🔧 {n}. {part.function_call.name}({dict(part.function_call.args or {})})")
                elif part.function_response:
                    print(f"     ↳ {_short(part.function_response.response or {})}")
                elif part.text and event.is_final_response():
                    answer += part.text
    finally:
        await game.close()  # close the MCP connection
    print(f"\n🔎 Tool calls: {n}")
    return answer


if __name__ == "__main__":
    final = asyncio.run(run_detective(submit="--submit" in sys.argv))
    print("\n=== Detective's final answer ===\n")
    print(final)
