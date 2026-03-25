"""ControlMCP MCP server entrypoint.

This module now acts as a thin MCP bootstrap layer. Tool definitions live in the
application registry, and execution is routed through the dispatcher so the
control plane can evolve independently from protocol wiring.
"""

from __future__ import annotations

import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from control_mcp.app.dispatcher import dispatch_tool
from control_mcp.app.tool_registry import TOOLS

server = Server("control-mcp")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    result = dispatch_tool(name, arguments or {})
    return [TextContent(type="text", text=result)]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run() -> None:
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        sys.exit(0)
