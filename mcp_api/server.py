"""Factory for the stateless MCP tool surface."""

from __future__ import annotations

from typing import Any

from broker.registry import ProjectRegistry
from broker.router import RequestRouter
from broker.events import EventBuffer
from mcp_api.tools import register_tools


SERVER_INSTRUCTIONS = """Use these tools to inspect and edit live LCEDA projects.
For schematic creation, cleanup, routing, or review, pair this server with the
`lceda-draw-readable-schematic` Agent Skill when it is installed. That skill
provides the planning, topology-preservation, incremental-edit, and review
workflow; the MCP server provides the live LCEDA reads and mutations. Always
inspect current tool schemas and project state before writing.
"""


def register_prompts(server: Any) -> None:
    @server.prompt(
        name="lceda-schematic-workflow",
        description="Start an LCEDA schematic task with the companion Agent Skills and live MCP tools.",
    )
    def lceda_schematic_workflow(task: str = "Improve the active schematic") -> str:
        return f"""Use the `lceda-draw-readable-schematic` Agent Skill together with this
JLCEDA AI Agent MCP server. Load only the companion LCEDA skills needed for the
task, inspect the active project and schematic before mutation, work in small
verified batches, and finish with Netlist/DRC and readability checks when those
capabilities are available.

Task: {task}
"""


def create_mcp_server(
    registry: ProjectRegistry,
    router: RequestRouter,
    events: EventBuffer | None = None,
) -> Any:
    # MCP SDK v2 renamed FastMCP to MCPServer. Supporting both keeps the service
    # usable with the stable 1.x SDK while allowing a no-code migration to 2.x.
    try:
        from mcp.server.mcpserver import MCPServer

        server = MCPServer(name="JLCEDA AI Agent", instructions=SERVER_INSTRUCTIONS)
    except ImportError:
        from mcp.server.fastmcp import FastMCP

        server = FastMCP(
            "JLCEDA AI Agent",
            instructions=SERVER_INSTRUCTIONS,
            stateless_http=True,
            json_response=True,
        )

    register_tools(server, registry, router, events or EventBuffer())
    register_prompts(server)
    return server
