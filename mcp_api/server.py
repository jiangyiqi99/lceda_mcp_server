"""Factory for the stateless MCP tool surface."""

from __future__ import annotations

from typing import Any

from broker.registry import ProjectRegistry
from broker.router import RequestRouter
from broker.events import EventBuffer
from mcp_api.tools import register_tools


def create_mcp_server(
    registry: ProjectRegistry,
    router: RequestRouter,
    events: EventBuffer | None = None,
) -> Any:
    # MCP SDK v2 renamed FastMCP to MCPServer. Supporting both keeps the service
    # usable with the stable 1.x SDK while allowing a no-code migration to 2.x.
    try:
        from mcp.server.mcpserver import MCPServer

        server = MCPServer(name="JLCEDA AI Agent")
    except ImportError:
        from mcp.server.fastmcp import FastMCP

        server = FastMCP(
            "JLCEDA AI Agent",
            stateless_http=True,
            json_response=True,
        )

    register_tools(server, registry, router, events or EventBuffer())
    return server
