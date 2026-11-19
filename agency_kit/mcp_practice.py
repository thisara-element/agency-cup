"""An MCP tool server for a practice case: build the tools ONCE, plug them into any framework.

    python -m agency_kit.mcp_practice coffee     # Case #000 tools over stdio
    python -m agency_kit.mcp_practice cake       # Case #001 tools over stdio

The notebooks start this as a subprocess. The Agency Cup itself already has an MCP server at <game>/mcp.
"""

import sys

from fastmcp import FastMCP

from agency_kit.practice_cases import CAKE_TOOLS, COFFEE_TOOLS

which = sys.argv[1] if len(sys.argv) > 1 else "cake"
mcp = FastMCP(f"case-{which}")
for fn in {"coffee": COFFEE_TOOLS, "cake": CAKE_TOOLS}[which]:
    mcp.tool(fn)  # the docstring and type hints become the MCP tool's description and schema

if __name__ == "__main__":
    mcp.run(show_banner=False)  # stdio: never print to stdout here, it carries the protocol
