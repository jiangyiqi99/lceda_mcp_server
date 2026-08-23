"""Register MCP tools that forward every operation to the in-memory broker."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from broker.registry import ProjectRegistry
from broker.router import RequestRouter


def register_tools(server: Any, registry: ProjectRegistry, router: RequestRouter) -> None:
    """Attach stateless tools to an MCP server instance.

    The closures only hold references to the broker. All project and connection
    state remains owned by the broker registry/router.
    """

    @server.tool(name="list_projects")
    async def list_projects() -> dict[str, Any]:
        """List JLCEDA projects that currently have a live extension connection."""
        return {"projects": await registry.list_projects()}

    @server.tool(name="schematic.get_info")
    async def schematic_get_info(project_id: str) -> Any:
        """Return components, pins, nets, and wires from a project's active schematic."""
        return await router.request(
            project_id, "schematic.get_info", capability="schematic"
        )

    @server.tool(name="schematic.add_component")
    async def schematic_add_component(
        project_id: str, component: dict[str, Any]
    ) -> Any:
        """Search and place a library component on the active schematic."""
        return await router.request(
            project_id,
            "schematic.add_component",
            {"component": component},
            capability="schematic",
        )

    @server.tool(name="schematic.connect")
    async def schematic_connect(
        project_id: str,
        from_: Annotated[str, Field(alias="from")],
        to: str,
    ) -> Any:
        """Connect two schematic pins such as U1.1 and C1.1 with a wire."""
        return await router.request(
            project_id,
            "schematic.connect",
            {"from": from_, "to": to},
            capability="schematic",
        )

    @server.tool(name="pcb.get_info")
    async def pcb_get_info(project_id: str) -> Any:
        """Return components, pads, tracks, vias, and layers from the active PCB."""
        return await router.request(project_id, "pcb.get_info", capability="pcb")

    @server.tool(name="pcb.place_component")
    async def pcb_place_component(
        project_id: str, reference: str, x: float, y: float
    ) -> Any:
        """Move an existing PCB component to the given EDA canvas coordinates."""
        return await router.request(
            project_id,
            "pcb.place_component",
            {"reference": reference, "x": x, "y": y},
            capability="pcb",
        )

    @server.tool(name="pcb.route_net")
    async def pcb_route_net(project_id: str, net: str, strategy: str = "completion") -> Any:
        """Run JLCEDA auto-routing for one named PCB net."""
        return await router.request(
            project_id,
            "pcb.route_net",
            {"net": net, "strategy": strategy},
            capability="pcb",
        )

    @server.tool(name="pcb.run_drc")
    async def pcb_run_drc(project_id: str) -> Any:
        """Run detailed PCB design-rule checking and return errors and warnings."""
        return await router.request(project_id, "pcb.run_drc", capability="drc")

    @server.tool(name="capture.schematic")
    async def capture_schematic(project_id: str, mode: str = "fit") -> Any:
        """Capture the active schematic and return a temporary HTTP image URL."""
        return await router.request(
            project_id,
            "capture.schematic",
            {"mode": mode},
            capability="capture",
        )

    @server.tool(name="capture.pcb")
    async def capture_pcb(project_id: str, mode: str = "fit") -> Any:
        """Capture the active PCB and return a temporary HTTP image URL."""
        return await router.request(
            project_id,
            "capture.pcb",
            {"mode": mode},
            capability="capture",
        )

    @server.tool(name="capture.region")
    async def capture_region(project_id: str, region: dict[str, float]) -> Any:
        """Capture a specified EDA canvas region and return a temporary HTTP image URL."""
        return await router.request(
            project_id,
            "capture.region",
            {"region": region},
            capability="capture",
        )
