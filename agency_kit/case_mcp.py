"""Talk to the game's MCP server by hand, the same way your agent does.

    from agency_kit.case_mcp import list_tools, call_tool
    await list_tools()                               # ask the server which tools exist
    await call_tool("search", query="deck")          # call one tool

MCP (Model Context Protocol) is a standard way to give tools to an agent.
The game is an MCP server. Your agent is an MCP client. The agent does not need
any code for the tools: it connects, asks "which tools do you have?", and the
server answers with each tool's name, description and inputs.

The game's MCP server is at https://agency.thisara.me/mcp (AGENCY_CUP_URL + /mcp).
The three starter agents and the Case #002 notebook use mcp_url() and mcp_headers() from this file.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from agency_kit.case_client import game_url

load_dotenv()


def mcp_url() -> str:
    """The address of the game's MCP server: https://agency.thisara.me/mcp, unless .env says another game."""
    return game_url() + "/mcp"


def mcp_headers() -> dict[str, str]:
    """Your team key. The MCP server uses it to know which team is calling."""
    key = os.environ.get("TEAM_KEY")
    if not key:
        raise SystemExit("Set TEAM_KEY in your .env (you get it when you register your team).")
    return {"Authorization": f"Bearer {key}"}


@asynccontextmanager
async def connect():
    """Open one MCP session with the game: `async with connect() as session: ...`"""
    async with httpx.AsyncClient(headers=mcp_headers(), timeout=30) as http:
        async with streamable_http_client(mcp_url(), http_client=http) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()  # the MCP handshake
                yield session


async def list_tools() -> list[dict]:
    """Ask the MCP server which tools it has. This is what every agent does first."""
    async with connect() as session:
        found = await session.list_tools()
    return [{"name": t.name, "description": " ".join((t.description or "").split()),
             "inputs": list((t.inputSchema or {}).get("properties", {}))} for t in found.tools]


async def call_tool(name: str, **args) -> dict:
    """Call one game tool through MCP. Returns the answer as a dict; check answer["ok"]."""
    for attempt in range(6):
        async with connect() as session:
            result = await session.call_tool(name, args)
        text = next((c.text for c in result.content if getattr(c, "type", "") == "text"), "")
        try:
            data = json.loads(text)
        except ValueError:
            return {"ok": False, "error": text[:300] or "The server sent an empty answer."}
        wait = re.search(r"Retry after (\d+)", str(data.get("error", "")))
        if not wait:
            return data
        print(f"[game] Your team is over 60 calls a minute: waiting {wait.group(1)} s")
        await asyncio.sleep(int(wait.group(1)))
    return {"ok": False, "error": "Gave up after several retries."}
