"""Starter detective: OpenAI Agents SDK + NVIDIA model + the game's MCP tools.

    uv run python starters/agent_openai_sdk.py            # dry run: investigates, does NOT submit
    uv run python starters/agent_openai_sdk.py --submit   # the real thing: may call submit_report

There is no tool code in this file. The agent connects to the game's MCP server,
asks which tools exist, and uses them.

This is a starting point, not a winner. The instructions below are bare on purpose:
how the agent should investigate is for your team to work out. That is the challenge.
"""

import asyncio
import json
import os
import sys

from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from agents.mcp import MCPServerStreamableHttp, create_static_tool_filter
from dotenv import load_dotenv

from agency_kit.case_mcp import mcp_headers, mcp_url
from agency_kit.nvidia_client import make_client

# ✏️ Bare on purpose. Your team's strategy goes here (or pass your own text to run_detective).
INSTRUCTIONS = """You are a detective agent working Case #002: The Phantom Leak.
Read case_brief first. Use your tools to investigate.
When you are confident, call submit_report once. Then summarise your reasoning.
"""

DRY_RUN_NOTE = """
This is a DRY RUN: you cannot submit. End with the report you WOULD submit:
culprit, accomplice, channel, time_window, motive and the evidence IDs."""


async def run_detective(instructions: str = INSTRUCTIONS, submit: bool = False, max_turns: int | None = None):
    """Run the detective once and return the result (result.final_output is its answer).

    submit=False is a dry run: the submit_report tool is hidden from the agent, so you
    can test without using one of your 3 submissions. Budget points are still spent.
    """
    load_dotenv()
    set_tracing_disabled(True)  # tracing uploads to OpenAI; turn it off when you use NVIDIA keys
    client, model_name = make_client()
    model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)
    hidden = [] if submit else ["submit_report"]

    async with MCPServerStreamableHttp(params={"url": mcp_url(), "headers": mcp_headers(), "timeout": 30},
                                       client_session_timeout_seconds=60, cache_tools_list=True,
                                       tool_filter=create_static_tool_filter(blocked_tool_names=hidden)) as case_tools:
        detective = Agent(name="Detective", instructions=instructions, model=model, mcp_servers=[case_tools])
        task = "Solve Case #002. Start with case_brief." + ("" if submit else DRY_RUN_NOTE)
        return await Runner.run(detective, task, max_turns=max_turns or int(os.environ.get("MAX_TURNS", "60")))


def _short(output) -> str:
    """Turn one tool answer into a short line: its cost, then the start of the content."""
    text = output.get("text", "") if isinstance(output, dict) else str(output)
    try:
        data = json.loads(text)
    except ValueError:
        return text[:150]
    if not isinstance(data, dict):
        return text[:150]
    if not data.get("ok", True):
        return f"ERROR: {data.get('error')}"
    rest = {k: v for k, v in data.items() if k not in ("ok", "cost", "budget_left")}
    return f"cost {data.get('cost', 0)} · {json.dumps(rest, ensure_ascii=False)[:130]}"


def show_steps(result) -> None:
    """Print every tool the agent called, with its inputs and the start of each answer."""
    answers = {item.raw_item.get("call_id"): item.output for item in result.new_items
               if item.type == "tool_call_output_item" and isinstance(item.raw_item, dict)}
    n = 0
    for item in result.new_items:
        if item.type != "tool_call_item":
            continue
        n += 1
        raw = item.raw_item
        print(f"🔧 {n}. {getattr(raw, 'name', '?')}({getattr(raw, 'arguments', '')})")
        if getattr(raw, "call_id", None) in answers:
            print(f"     ↳ {_short(answers[raw.call_id])}")
    print(f"\n🔎 Tool calls: {n} · Model calls: {len(result.raw_responses)}")


if __name__ == "__main__":
    result = asyncio.run(run_detective(submit="--submit" in sys.argv))
    show_steps(result)
    print("\n=== Detective's final answer ===\n")
    print(result.final_output)
