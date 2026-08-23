from __future__ import annotations

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
        "project.get_info",
        "schematic.get_netlist",
        "schematic.modify_component",
        "schematic.delete_components",
        "schematic.delete_wires",
        "schematic.modify_wire",
        "schematic.set_pin_no_connect",
        "schematic.clear",
        "schematic.create_net_flag",
        "schematic.create_net_port",
        "schematic.create_net_label",
        "schematic.connect_net",
        "schematic.create_wire",
        "schematic.auto_layout",
        "schematic.auto_route",
        "schematic.run_drc",
        "pcb.modify_component",
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

    clear = tools["schematic.clear"].parameters
    assert clear["properties"]["include_wires"]["default"] is True
    assert clear["properties"]["include_components"]["default"] is True

    via = tools["pcb.create_via"].parameters
    assert via["properties"]["via_type"]["minimum"] == 0
    assert via["properties"]["via_type"]["maximum"] == 2
