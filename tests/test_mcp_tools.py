from __future__ import annotations

import re
from pathlib import Path

import pytest

from broker.registry import ProjectRegistry
from broker.router import RequestRouter
from mcp_api.server import create_mcp_server


def test_component_selection_tools_have_safe_schemas() -> None:
    registry = ProjectRegistry()
    server = create_mcp_server(registry, RequestRouter(registry))
    tools = {tool.name: tool for tool in server._tool_manager.list_tools()}

    search_schema = tools["component.search"].parameters
    assert search_schema["required"] == ["project_id", "query"]
    assert search_schema["properties"]["page"]["minimum"] == 1
    assert search_schema["properties"]["page_size"]["maximum"] == 100

    place_schema = tools["schematic.place_component"].parameters
    assert set(place_schema["required"]) == {
        "project_id",
        "library_uuid",
        "device_uuid",
        "reference",
        "x",
        "y",
    }


def test_extended_eda_tools_are_registered_with_guarded_schemas() -> None:
    registry = ProjectRegistry()
    server = create_mcp_server(registry, RequestRouter(registry))
    tools = {tool.name: tool for tool in server._tool_manager.list_tools()}

    expected = {
        "eda.call",
        "eda.call_primitive",
        "eda.describe_api",
        "eda.describe_type",
        "eda.export_file",
        "eda.export_primitive_file",
        "eda.list_apis",
        "eda.poll_events",
        "eda.subscribe",
        "eda.unsubscribe",
        "project.get_info",
        "schematic.get_netlist",
        "schematic.get_primitives_bbox",
        "schematic.modify_component",
        "schematic.delete_components",
        "schematic.delete_wires",
        "schematic.modify_wire",
        "schematic.modify_pin",
        "schematic.clear",
        "schematic.create_net_flag",
        "schematic.create_net_port",
        "schematic.create_net_label",
        "schematic.modify_net_label",
        "schematic.connect_net",
        "schematic.create_wire",
        "schematic.auto_layout",
        "schematic.auto_route",
        "schematic.run_drc",
        "pcb.modify_component",
        "pcb.get_primitives_bbox",
        "pcb.delete_components",
        "pcb.create_track",
        "pcb.modify_track",
        "pcb.create_board_outline",
        "pcb.create_via",
        "pcb.modify_via",
        "pcb.delete_routing_primitives",
        "pcb.clear_routing",
        "pcb.auto_route",
        "pcb.auto_layout",
    }
    assert expected <= tools.keys()

    raw_scope = tools["eda.call"].parameters["properties"]["scope"]["enum"]
    assert set(raw_scope) == {
        "project", "library", "panel", "schematic", "pcb", "system"
    }

    primitive_call = tools["eda.call_primitive"].parameters
    assert primitive_call["required"] == [
        "project_id", "scope", "primitive_id", "calls"
    ]

    connect_net = tools["schematic.connect_net"].parameters
    assert connect_net["required"] == ["project_id", "net", "pins"]
    assert set(connect_net["properties"]["style"]["enum"]) == {
        "port",
        "power",
        "ground",
        "analog_ground",
        "protect_ground",
        "label",
    }

    create_wire = tools["schematic.create_wire"].parameters
    assert create_wire["required"] == ["project_id", "points"]
    assert create_wire["properties"]["allow_crossings"]["default"] is False

    modify_pin = tools["schematic.modify_pin"].parameters
    assert modify_pin["required"] == ["project_id", "primitive_id"]

    clear = tools["schematic.clear"].parameters
    assert clear["properties"]["include_wires"]["default"] is True
    assert clear["properties"]["include_components"]["default"] is True

    via = tools["pcb.create_via"].parameters
    assert via["properties"]["via_type"]["minimum"] == 0
    assert via["properties"]["via_type"]["maximum"] == 2


@pytest.mark.asyncio
async def test_server_prompt_recommends_the_companion_schematic_skill() -> None:
    registry = ProjectRegistry()
    server = create_mcp_server(registry, RequestRouter(registry))

    prompts = {prompt.name: prompt for prompt in await server.list_prompts()}
    result = await server.get_prompt(
        "lceda-schematic-workflow",
        {"task": "Clean up the power page"},
    )
    text = result.messages[0].content.text

    assert "lceda-schematic-workflow" in prompts
    assert "lceda-draw-readable-schematic" in server.instructions
    assert "lceda-draw-readable-schematic" in text
    assert "Clean up the power page" in text


def test_every_extension_handler_has_an_mcp_tool() -> None:
    registry = ProjectRegistry()
    server = create_mcp_server(registry, RequestRouter(registry))
    tool_names = {tool.name for tool in server._tool_manager.list_tools()}
    handler_source = (
        Path(__file__).resolve().parents[2]
        / "lceda_mcp_extension"
        / "src"
        / "commands"
        / "index.ts"
    ).read_text(encoding="utf-8")
    handler_names = set(
        re.findall(r"^\s*'([^']+)'\s*:", handler_source, flags=re.MULTILINE)
    )
    assert handler_names <= tool_names
