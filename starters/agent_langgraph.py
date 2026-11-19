"""Starter detective: a LangGraph agent + NVIDIA model + the game's MCP tools.

    uv run python starters/agent_langgraph.py            # dry run: investigates, does NOT submit
    uv run python starters/agent_langgraph.py --submit   # the real thing: may call submit_report

There is no tool code in this file. MultiServerMCPClient connects to the game's
MCP server, asks which tools exist, and turns each one into a LangChain tool.
build_graph() draws the agent as a LangGraph flowchart: think ⇄ act.
"""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from starters.agent_openai_sdk import DRY_RUN_NOTE, INSTRUCTIONS, _short
from agency_kit.case_mcp import mcp_headers, mcp_url
from agency_kit.nvidia_client import DEFAULT_NVIDIA_MODEL, NVIDIA_BASE_URL, RateLimitedTransport

load_dotenv()


def make_model() -> ChatOpenAI:
    http = httpx.AsyncClient(transport=RateLimitedTransport(), timeout=120)
    if os.environ.get("PROVIDER", "nvidia").lower() == "openai":
        return ChatOpenAI(model=os.environ.get("MODEL", "gpt-5.4-mini"), http_async_client=http, max_retries=0)
    return ChatOpenAI(model=os.environ.get("MODEL", DEFAULT_NVIDIA_MODEL), base_url=NVIDIA_BASE_URL,
                      api_key=os.environ["NVIDIA_API_KEY"], http_async_client=http, max_retries=0)


def build_graph(model: ChatOpenAI, tools: list, instructions: str):
    """The agent as a LangGraph flowchart: think (the model) ⇄ act (the tools), until no more tool calls."""
    llm = model.bind_tools(tools)

    async def think(state: MessagesState):
        return {"messages": [await llm.ainvoke([SystemMessage(instructions), *state["messages"]])]}

    def next_step(state: MessagesState):
        return "act" if state["messages"][-1].tool_calls else END

    graph = StateGraph(MessagesState)
    graph.add_node("think", think)
    graph.add_node("act", ToolNode(tools))
    graph.add_edge(START, "think")
    graph.add_conditional_edges("think", next_step, ["act", END])
    graph.add_edge("act", "think")
    return graph.compile()


async def run_detective(instructions: str = INSTRUCTIONS, submit: bool = False):
    """Run the detective once. submit=False is a dry run: the agent does not get the submit_report tool."""
    game = MultiServerMCPClient({"agency_cup": {"transport": "streamable_http", "url": mcp_url(),
                                                "headers": mcp_headers()}})
    tools = [t for t in await game.get_tools() if submit or t.name != "submit_report"]  # the server lists its tools
    print(f"🔌 MCP tools from the game: {', '.join(t.name for t in tools)}\n")

    task = "Solve Case #002. Start with case_brief." + ("" if submit else DRY_RUN_NOTE)
    agent = build_graph(make_model(), tools, instructions)
    return await agent.ainvoke({"messages": [HumanMessage(task)]}, {"recursion_limit": 120})


def show_steps(result) -> None:
    """Print every tool the agent called, with its inputs and the start of each answer."""
    answers = {m.tool_call_id: m.text for m in result["messages"] if m.type == "tool"}
    n = 0
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", None) or []:
            n += 1
            print(f"🔧 {n}. {call['name']}({call['args']})")
            if call["id"] in answers:
                print(f"     ↳ {_short(answers[call['id']])}")
    print(f"\n🔎 Tool calls: {n}")


if __name__ == "__main__":
    result = asyncio.run(run_detective(submit="--submit" in sys.argv))
    show_steps(result)
    print("\n=== Detective's final answer ===\n")
    print(result["messages"][-1].text)
