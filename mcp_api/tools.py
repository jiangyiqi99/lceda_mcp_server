"""Register MCP tools that forward every operation to the in-memory broker."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from broker.registry import ProjectRegistry
from broker.router import RequestRouter
from broker.events import EventBuffer

EdaScope = Literal["project", "library", "panel", "schematic", "pcb", "system"]


def _defined(**values: Any) -> dict[str, Any]:
    """Drop omitted optional arguments before forwarding them to the extension."""
    return {key: value for key, value in values.items() if value is not None}


def register_tools(
    server: Any,
    registry: ProjectRegistry,
    router: RequestRouter,
    events: EventBuffer,
) -> None:
    """Attach stateless tools to an MCP server instance.

    The closures only hold references to the broker. All project and connection
    state remains owned by the broker registry/router.
    """

    @server.tool(name="list_projects")
    async def list_projects() -> dict[str, Any]:
        """List JLCEDA projects that currently have a live extension connection."""
        return {"projects": await registry.list_projects()}

    @server.tool(name="project.get_info")
    async def project_get_info(project_id: str) -> Any:
        """Return current JLCEDA project metadata and the active document."""
        return await router.request(project_id, "project.get_info")

    @server.tool(name="eda.call")
    async def eda_call(
        project_id: str,
        scope: EdaScope,
        api: str,
        method: str,
        args: list[Any] | None = None,
        confirm_mutation: bool = False,
    ) -> Any:
        """Call a JSON-safe JLCEDA API not yet represented by a dedicated tool.

        ``api`` is a public namespace such as ``sch_PrimitiveText`` and
        ``method`` is a method such as ``getAll``. File/Blob APIs and callback
        listeners require dedicated transports and are rejected. Methods that
        may change EDA state require ``confirm_mutation=true``. File arguments
        can use ``{"$file_base64": "...", "name": "x", "type": "..."}``.
        """
        capability = scope if scope in {"schematic", "pcb"} else None
        return await router.request(
            project_id,
            "eda.call",
            {
                "scope": scope,
                "api": api,
                "method": method,
                "args": args or [],
                "confirm_mutation": confirm_mutation,
            },
            capability=capability,
        )

    @server.tool(name="eda.call_primitive")
    async def eda_call_primitive(
        project_id: str,
        scope: Literal["schematic", "pcb"],
        primitive_id: str,
        calls: list[dict[str, Any]],
        transaction: bool = False,
        confirm_mutation: bool = False,
    ) -> Any:
        """Call methods on a schematic/PCB primitive instance.

        Each call is ``{"method": "getState_X", "args": []}``. With
        ``transaction=true``, the Extension calls ``toAsync()``, applies all
        setters, then commits once with ``done()``. Mutations require explicit
        confirmation.
        """
        return await router.request(
            project_id,
            "eda.call_primitive",
            {
                "scope": scope,
                "primitive_id": primitive_id,
                "calls": calls,
                "transaction": transaction,
                "confirm_mutation": confirm_mutation,
            },
            capability=scope,
        )

    @server.tool(name="eda.list_apis")
    async def eda_list_apis(
        project_id: str,
        scope: EdaScope,
    ) -> Any:
        """List public JLCEDA API namespaces available in the connected EDA runtime."""
        capability = scope if scope in {"schematic", "pcb"} else None
        return await router.request(
            project_id,
            "eda.list_apis",
            {"scope": scope},
            capability=capability,
        )

    @server.tool(name="eda.describe_api")
    async def eda_describe_api(
        project_id: str,
        scope: EdaScope,
        api: str,
    ) -> Any:
        """List runtime methods with official overload signatures and callability flags."""
        capability = scope if scope in {"schematic", "pcb"} else None
        return await router.request(
            project_id,
            "eda.describe_api",
            {"scope": scope, "api": api},
            capability=capability,
        )

    @server.tool(name="eda.describe_type")
    async def eda_describe_type(project_id: str, name: str) -> Any:
        """Return official enum, interface, or type-alias declarations by name."""
        return await router.request(
            project_id,
            "eda.describe_type",
            {"name": name},
        )

    @server.tool(name="eda.export_file")
    async def eda_export_file(
        project_id: str,
        scope: EdaScope,
        api: str,
        method: str,
        args: list[Any] | None = None,
        filename: str | None = None,
    ) -> Any:
        """Run a JLCEDA File-returning API and return a temporary download URL."""
        capability = scope if scope in {"schematic", "pcb"} else None
        return await router.request(
            project_id,
            "eda.export_file",
            {
                "scope": scope,
                "api": api,
                "method": method,
                "args": args or [],
                "filename": filename,
            },
            capability=capability,
        )

    @server.tool(name="eda.export_primitive_file")
    async def eda_export_primitive_file(
        project_id: str,
        scope: Literal["schematic", "pcb"],
        primitive_id: str,
        method: str,
        args: list[Any] | None = None,
        filename: str | None = None,
    ) -> Any:
        """Export File/Blob data returned by a primitive instance method."""
        return await router.request(
            project_id,
            "eda.export_primitive_file",
            {
                "scope": scope,
                "primitive_id": primitive_id,
                "method": method,
                "args": args or [],
                "filename": filename,
            },
            capability=scope,
        )

    @server.tool(name="eda.poll_events")
    async def eda_poll_events(
        project_id: str,
        after_sequence: Annotated[int, Field(ge=0)] = 0,
        limit: Annotated[int, Field(ge=1, le=500)] = 100,
        timeout_seconds: Annotated[float, Field(ge=0, le=30)] = 0,
    ) -> Any:
        """Read buffered EDA subscription events after a sequence number."""
        return await events.poll(project_id, after_sequence, limit, timeout_seconds)

    @server.tool(name="eda.subscribe")
    async def eda_subscribe(
        project_id: str,
        scope: EdaScope,
        api: str,
        method: str,
        subscription_id: str,
        args: list[Any],
        unsubscribe_method: str | None = None,
        unsubscribe_args: list[Any] | None = None,
    ) -> Any:
        """Subscribe to an EDA callback/listener API.

        Put ``__EDA_EVENT_CALLBACK__`` in ``args`` where the API expects its
        callback. Events can then be read with ``eda.poll_events``. Listener,
        MessageBus-task, Timer and Window cancellation are inferred. For other
        APIs, specify an unsubscribe method and use
        ``__EDA_SUBSCRIPTION_ID__``/``__EDA_SUBSCRIPTION_RESULT__`` markers in
        its arguments.
        """
        capability = scope if scope in {"schematic", "pcb"} else None
        return await router.request(
            project_id,
            "eda.subscribe",
            {
                "scope": scope,
                "api": api,
                "method": method,
                "subscription_id": subscription_id,
                "args": args,
                "unsubscribe_method": unsubscribe_method,
                "unsubscribe_args": unsubscribe_args or [],
            },
            capability=capability,
        )

    @server.tool(name="eda.unsubscribe")
    async def eda_unsubscribe(project_id: str, subscription_id: str) -> Any:
        """Remove a previously registered EDA event subscription."""
        return await router.request(
            project_id,
            "eda.unsubscribe",
            {"subscription_id": subscription_id},
        )

    @server.tool(name="schematic.get_info")
    async def schematic_get_info(project_id: str) -> Any:
        """Return components, pins, nets, and wires from a project's active schematic."""
        return await router.request(
            project_id, "schematic.get_info", capability="schematic"
        )

    @server.tool(name="schematic.get_primitives_bbox")
    async def schematic_get_primitives_bbox(
        project_id: str, primitive_ids: list[str]
    ) -> Any:
        """Return the exact bounding box of schematic primitives."""
        return await router.request(
            project_id,
            "schematic.get_primitives_bbox",
            {"primitive_ids": primitive_ids},
            capability="schematic",
        )

    @server.tool(name="schematic.get_netlist")
    async def schematic_get_netlist(
        project_id: str, format: str = "Protel2"
    ) -> Any:
        """Export the active schematic netlist as text in a JLCEDA format."""
        return await router.request(
            project_id,
            "schematic.get_netlist",
            {"format": format},
            capability="schematic",
        )

    @server.tool(name="component.search")
    async def component_search(
        project_id: str,
        query: str,
        page: Annotated[int, Field(ge=1)] = 1,
        page_size: Annotated[int, Field(ge=1, le=100)] = 20,
    ) -> Any:
        """Search JLCEDA libraries and return structured candidates for AI selection.

        This tool never changes the schematic. Continue with the next page while
        ``has_more`` is true, then pass the chosen candidate UUIDs to
        ``schematic.place_component``.
        """
        return await router.request(
            project_id,
            "component.search",
            {"query": query, "page": page, "page_size": page_size},
            capability="schematic",
        )

    @server.tool(name="schematic.place_component")
    async def schematic_place_component(
        project_id: str,
        library_uuid: str,
        device_uuid: str,
        reference: str,
        x: float,
        y: float,
        sub_part_name: str | None = None,
        rotation: float = 0,
        mirror: bool = False,
        add_into_bom: bool = True,
        add_into_pcb: bool = True,
    ) -> Any:
        """Place one exact AI-selected library candidate on the active schematic."""
        return await router.request(
            project_id,
            "schematic.place_component",
            {
                "library_uuid": library_uuid,
                "device_uuid": device_uuid,
                "reference": reference,
                "x": x,
                "y": y,
                "sub_part_name": sub_part_name,
                "rotation": rotation,
                "mirror": mirror,
                "add_into_bom": add_into_bom,
                "add_into_pcb": add_into_pcb,
            },
            capability="schematic",
        )

    @server.tool(name="schematic.modify_component")
    async def schematic_modify_component(
        project_id: str,
        reference: str,
        x: float | None = None,
        y: float | None = None,
        rotation: float | None = None,
        mirror: bool | None = None,
        new_reference: str | None = None,
        name: str | None = None,
        unique_id: str | None = None,
        manufacturer: str | None = None,
        manufacturer_id: str | None = None,
        supplier: str | None = None,
        supplier_id: str | None = None,
        other_property: dict[str, str | int | float | bool] | None = None,
        add_into_bom: bool | None = None,
        add_into_pcb: bool | None = None,
    ) -> Any:
        """Modify position, identity, display, and BOM/PCB state of a component."""
        return await router.request(
            project_id,
            "schematic.modify_component",
            _defined(
                reference=reference,
                x=x,
                y=y,
                rotation=rotation,
                mirror=mirror,
                new_reference=new_reference,
                name=name,
                unique_id=unique_id,
                manufacturer=manufacturer,
                manufacturer_id=manufacturer_id,
                supplier=supplier,
                supplier_id=supplier_id,
                other_property=other_property,
                add_into_bom=add_into_bom,
                add_into_pcb=add_into_pcb,
            ),
            capability="schematic",
        )

    @server.tool(name="schematic.delete_components")
    async def schematic_delete_components(
        project_id: str,
        references: list[str] | None = None,
        primitive_ids: list[str] | None = None,
    ) -> Any:
        """Delete exact schematic components by reference and/or primitive ID."""
        return await router.request(
            project_id,
            "schematic.delete_components",
            _defined(references=references, primitive_ids=primitive_ids),
            capability="schematic",
        )

    @server.tool(name="schematic.delete_wires")
    async def schematic_delete_wires(
        project_id: str,
        primitive_ids: list[str] | None = None,
        nets: list[str] | None = None,
    ) -> Any:
        """Delete exact schematic wires by primitive ID and/or net name."""
        return await router.request(
            project_id,
            "schematic.delete_wires",
            _defined(primitive_ids=primitive_ids, nets=nets),
            capability="schematic",
        )

    @server.tool(name="schematic.modify_wire")
    async def schematic_modify_wire(
        project_id: str,
        primitive_id: str,
        points: list[list[float]] | None = None,
        net: str | None = None,
        color: str | None = None,
        line_width: float | None = None,
        line_type: Annotated[int | None, Field(ge=0, le=3)] = None,
        allow_crossings: bool = False,
    ) -> Any:
        """Modify an existing schematic wire with orthogonal/crossing checks."""
        return await router.request(
            project_id,
            "schematic.modify_wire",
            _defined(
                primitive_id=primitive_id,
                points=points,
                net=net,
                color=color,
                line_width=line_width,
                line_type=line_type,
                allow_crossings=allow_crossings,
            ),
            capability="schematic",
        )

    @server.tool(name="schematic.modify_pin")
    async def schematic_modify_pin(
        project_id: str,
        primitive_id: str,
        x: float | None = None,
        y: float | None = None,
        rotation: float | None = None,
        pin_number: str | None = None,
        pin_name: str | None = None,
        pin_length: float | None = None,
        pin_color: str | None = None,
        pin_shape: Literal["None", "Inverted", "Clock", "Inverted Clock"] | None = None,
        pin_type: Literal[
            "IN", "OUT", "BI", "Passive", "Open Collector", "Open Emitter",
            "Power", "Ground", "HIZ", "Terminator", "Undefined",
        ] | None = None,
        no_connected: bool | None = None,
        other_property: dict[str, str | int | float | bool] | None = None,
    ) -> Any:
        """Modify a standalone pin in the active symbol editor.

        JLCEDA does not support modifying pins on placed component instances.
        Their derived left/right/top/bottom side remains available from
        ``schematic.get_info``.
        """
        return await router.request(
            project_id,
            "schematic.modify_pin",
            _defined(
                primitive_id=primitive_id,
                x=x,
                y=y,
                rotation=rotation,
                pin_number=pin_number,
                pin_name=pin_name,
                pin_length=pin_length,
                pin_color=pin_color,
                pin_shape=pin_shape,
                pin_type=pin_type,
                no_connected=no_connected,
                other_property=other_property,
            ),
            capability="schematic",
        )

    @server.tool(name="schematic.clear")
    async def schematic_clear(
        project_id: str,
        include_wires: bool = True,
        include_components: bool = True,
    ) -> Any:
        """Clear placed schematic wires/components while preserving the sheet frame."""
        return await router.request(
            project_id,
            "schematic.clear",
            {
                "include_wires": include_wires,
                "include_components": include_components,
            },
            capability="schematic",
        )

    @server.tool(name="schematic.create_net_flag")
    async def schematic_create_net_flag(
        project_id: str,
        kind: Literal["Power", "Ground", "AnalogGround", "ProtectGround"],
        net: str,
        x: float,
        y: float,
        rotation: float = 0,
        mirror: bool = False,
    ) -> Any:
        """Create a named power or ground network flag."""
        return await router.request(
            project_id,
            "schematic.create_net_flag",
            {
                "kind": kind,
                "net": net,
                "x": x,
                "y": y,
                "rotation": rotation,
                "mirror": mirror,
            },
            capability="schematic",
        )

    @server.tool(name="schematic.create_net_port")
    async def schematic_create_net_port(
        project_id: str,
        net: str,
        x: float,
        y: float,
        direction: Literal["IN", "OUT", "BI"] = "BI",
        rotation: float = 0,
        mirror: bool = False,
    ) -> Any:
        """Create a named schematic network port."""
        return await router.request(
            project_id,
            "schematic.create_net_port",
            {
                "direction": direction,
                "net": net,
                "x": x,
                "y": y,
                "rotation": rotation,
                "mirror": mirror,
            },
            capability="schematic",
        )

    @server.tool(name="schematic.create_net_label")
    async def schematic_create_net_label(
        project_id: str,
        net: str,
        x: float,
        y: float,
        side: Literal["left", "right", "top", "bottom"] | None = None,
        rotation: float | None = None,
        align_mode: Annotated[int | None, Field(ge=1, le=9)] = None,
    ) -> Any:
        """Create a named net label with an explicit anchor side/orientation."""
        return await router.request(
            project_id,
            "schematic.create_net_label",
            _defined(
                net=net,
                x=x,
                y=y,
                side=side,
                rotation=rotation,
                align_mode=align_mode,
            ),
            capability="schematic",
        )

    @server.tool(name="schematic.modify_net_marker")
    async def schematic_modify_net_marker(
        project_id: str,
        primitive_id: str,
        net: str | None = None,
        x: float | None = None,
        y: float | None = None,
        side: Literal["left", "right", "top", "bottom"] | None = None,
        rotation: float | None = None,
        mirror: bool | None = None,
    ) -> Any:
        """Modify a net port/flag position, side, rotation, mirror, or net name."""
        return await router.request(
            project_id,
            "schematic.modify_net_marker",
            _defined(
                primitive_id=primitive_id,
                net=net,
                x=x,
                y=y,
                side=side,
                rotation=rotation,
                mirror=mirror,
            ),
            capability="schematic",
        )

    @server.tool(name="schematic.modify_net_label")
    async def schematic_modify_net_label(
        project_id: str,
        primitive_id: str,
        net: str | None = None,
        x: float | None = None,
        y: float | None = None,
        side: Literal["left", "right", "top", "bottom"] | None = None,
        rotation: float | None = None,
        align_mode: Annotated[int | None, Field(ge=1, le=9)] = None,
        color: str | None = None,
        font_name: str | None = None,
        font_size: float | None = None,
        bold: bool | None = None,
        italic: bool | None = None,
        under_line: bool | None = None,
        fill_color: str | None = None,
        key_visible: bool | None = None,
        value_visible: bool | None = None,
    ) -> Any:
        """Modify a network label's name, position, side, rotation, alignment, and style."""
        return await router.request(
            project_id,
            "schematic.modify_net_label",
            _defined(
                primitive_id=primitive_id,
                net=net,
                x=x,
                y=y,
                side=side,
                rotation=rotation,
                align_mode=align_mode,
                color=color,
                font_name=font_name,
                font_size=font_size,
                bold=bold,
                italic=italic,
                under_line=under_line,
                fill_color=fill_color,
                key_visible=key_visible,
                value_visible=value_visible,
            ),
            capability="schematic",
        )

    @server.tool(name="schematic.connect_net")
    async def schematic_connect_net(
        project_id: str,
        net: str,
        pins: list[str],
        style: Literal[
            "port",
            "power",
            "ground",
            "analog_ground",
            "protect_ground",
            "label",
        ] = "port",
        side: Literal["auto", "left", "right", "top", "bottom"] = "auto",
        direction: Literal["IN", "OUT", "BI"] = "BI",
    ) -> Any:
        """Join multiple pins by placing same-name ports/flags directly on them.

        Prefer this for long-distance connections because it cannot short crossing
        wires. Pin addresses use forms such as ``U1.34``.
        """
        return await router.request(
            project_id,
            "schematic.connect_net",
            {
                "net": net,
                "pins": pins,
                "style": style,
                "side": side,
                "direction": direction,
            },
            capability="schematic",
        )

    @server.tool(name="schematic.create_wire")
    async def schematic_create_wire(
        project_id: str,
        points: list[list[float]],
        net: str = "",
        allow_crossings: bool = False,
    ) -> Any:
        """Create an explicit orthogonal wire path with crossing checks enabled."""
        return await router.request(
            project_id,
            "schematic.create_wire",
            {"points": points, "net": net, "allow_crossings": allow_crossings},
            capability="schematic",
        )

    @server.tool(name="schematic.add_component")
    async def schematic_add_component(
        project_id: str, component: dict[str, Any]
    ) -> Any:
        """Convenience tool that searches and places the first matching component."""
        return await router.request(
            project_id,
            "schematic.add_component",
            {"component": component},
            capability="schematic",
        )

    @server.tool(name="schematic.connect")
    async def schematic_connect(
        project_id: str,
        from_pin: str,
        to_pin: str,
        net: str | None = None,
        waypoints: list[list[float]] | None = None,
        allow_crossings: bool = False,
    ) -> Any:
        """Connect two pins with an orthogonal path and reject net crossings."""
        return await router.request(
            project_id,
            "schematic.connect",
            _defined(
                **{
                    "from": from_pin,
                    "to": to_pin,
                    "net": net,
                    "waypoints": waypoints,
                    "allow_crossings": allow_crossings,
                }
            ),
            capability="schematic",
        )

    @server.tool(name="schematic.auto_layout")
    async def schematic_auto_layout(
        project_id: str,
        primitive_ids: list[str] | None = None,
        netlist: dict[str, Any] | None = None,
        device_types: dict[str, str] | None = None,
    ) -> Any:
        """Run JLCEDA automatic schematic layout on the active sheet."""
        return await router.request(
            project_id,
            "schematic.auto_layout",
            _defined(
                primitive_ids=primitive_ids,
                netlist=netlist,
                device_types=device_types,
            ),
            capability="schematic",
        )

    @server.tool(name="schematic.auto_route")
    async def schematic_auto_route(
        project_id: str,
        primitive_ids: list[str] | None = None,
        netlist: dict[str, Any] | None = None,
        device_types: dict[str, str] | None = None,
    ) -> Any:
        """Run JLCEDA automatic schematic routing on the active sheet."""
        return await router.request(
            project_id,
            "schematic.auto_route",
            _defined(
                primitive_ids=primitive_ids,
                netlist=netlist,
                device_types=device_types,
            ),
            capability="schematic",
        )

    @server.tool(name="schematic.run_drc")
    async def schematic_run_drc(project_id: str) -> Any:
        """Run detailed schematic design-rule checking."""
        return await router.request(
            project_id, "schematic.run_drc", capability="drc"
        )

    @server.tool(name="pcb.get_info")
    async def pcb_get_info(project_id: str) -> Any:
        """Return components, pads, tracks, vias, and layers from the active PCB."""
        return await router.request(project_id, "pcb.get_info", capability="pcb")

    @server.tool(name="pcb.get_primitives_bbox")
    async def pcb_get_primitives_bbox(
        project_id: str, primitive_ids: list[str]
    ) -> Any:
        """Return the exact bounding box of PCB primitives."""
        return await router.request(
            project_id,
            "pcb.get_primitives_bbox",
            {"primitive_ids": primitive_ids},
            capability="pcb",
        )

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

    @server.tool(name="pcb.modify_component")
    async def pcb_modify_component(
        project_id: str,
        reference: str,
        layer: int | None = None,
        x: float | None = None,
        y: float | None = None,
        rotation: float | None = None,
        locked: bool | None = None,
        add_into_bom: bool | None = None,
        new_reference: str | None = None,
        name: str | None = None,
        unique_id: str | None = None,
        manufacturer: str | None = None,
        manufacturer_id: str | None = None,
        supplier: str | None = None,
        supplier_id: str | None = None,
        other_property: dict[str, Any] | None = None,
    ) -> Any:
        """Modify PCB component placement, layer, lock, reference, or name."""
        return await router.request(
            project_id,
            "pcb.modify_component",
            _defined(
                reference=reference,
                layer=layer,
                x=x,
                y=y,
                rotation=rotation,
                locked=locked,
                add_into_bom=add_into_bom,
                new_reference=new_reference,
                name=name,
                unique_id=unique_id,
                manufacturer=manufacturer,
                manufacturer_id=manufacturer_id,
                supplier=supplier,
                supplier_id=supplier_id,
                other_property=other_property,
            ),
            capability="pcb",
        )

    @server.tool(name="pcb.delete_components")
    async def pcb_delete_components(
        project_id: str,
        references: list[str] | None = None,
        primitive_ids: list[str] | None = None,
    ) -> Any:
        """Delete exact PCB components by reference and/or primitive ID."""
        return await router.request(
            project_id,
            "pcb.delete_components",
            _defined(references=references, primitive_ids=primitive_ids),
            capability="pcb",
        )

    @server.tool(name="pcb.create_track")
    async def pcb_create_track(
        project_id: str,
        layer: int,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        net: str = "",
        width: float = 10,
        locked: bool = False,
    ) -> Any:
        """Create one straight PCB track segment."""
        return await router.request(
            project_id,
            "pcb.create_track",
            {
                "net": net,
                "layer": layer,
                "start_x": start_x,
                "start_y": start_y,
                "end_x": end_x,
                "end_y": end_y,
                "width": width,
                "locked": locked,
            },
            capability="pcb",
        )

    @server.tool(name="pcb.modify_track")
    async def pcb_modify_track(
        project_id: str,
        primitive_id: str,
        net: str | None = None,
        layer: int | None = None,
        start_x: float | None = None,
        start_y: float | None = None,
        end_x: float | None = None,
        end_y: float | None = None,
        width: float | None = None,
        locked: bool | None = None,
    ) -> Any:
        """Modify a PCB line primitive's net, geometry, width, layer, or lock."""
        return await router.request(
            project_id,
            "pcb.modify_track",
            _defined(
                primitive_id=primitive_id,
                net=net,
                layer=layer,
                start_x=start_x,
                start_y=start_y,
                end_x=end_x,
                end_y=end_y,
                width=width,
                locked=locked,
            ),
            capability="pcb",
        )

    @server.tool(name="pcb.create_board_outline")
    async def pcb_create_board_outline(
        project_id: str,
        points: list[list[float]],
        close: bool = True,
        width: float = 10,
    ) -> Any:
        """Create a PCB board outline from ordered vertices."""
        return await router.request(
            project_id,
            "pcb.create_board_outline",
            {"points": points, "close": close, "width": width},
            capability="pcb",
        )

    @server.tool(name="pcb.create_via")
    async def pcb_create_via(
        project_id: str,
        net: str,
        x: float,
        y: float,
        hole_diameter: float,
        diameter: float,
        via_type: Annotated[int, Field(ge=0, le=2)] = 0,
        locked: bool = False,
        design_rule_blind_via_name: str | None = None,
        solder_mask_expansion: dict[str, Any] | None = None,
    ) -> Any:
        """Create a PCB via with explicit geometry and net."""
        return await router.request(
            project_id,
            "pcb.create_via",
            {
                "net": net,
                "x": x,
                "y": y,
                "hole_diameter": hole_diameter,
                "diameter": diameter,
                "via_type": via_type,
                "locked": locked,
                "design_rule_blind_via_name": design_rule_blind_via_name,
                "solder_mask_expansion": solder_mask_expansion,
            },
            capability="pcb",
        )

    @server.tool(name="pcb.modify_via")
    async def pcb_modify_via(
        project_id: str,
        primitive_id: str,
        net: str | None = None,
        x: float | None = None,
        y: float | None = None,
        hole_diameter: float | None = None,
        diameter: float | None = None,
        via_type: Annotated[int | None, Field(ge=0, le=2)] = None,
        locked: bool | None = None,
        design_rule_blind_via_name: str | None = None,
        solder_mask_expansion: dict[str, Any] | None = None,
    ) -> Any:
        """Modify a PCB via's net, position, geometry, type, or lock."""
        return await router.request(
            project_id,
            "pcb.modify_via",
            _defined(
                primitive_id=primitive_id,
                net=net,
                x=x,
                y=y,
                hole_diameter=hole_diameter,
                diameter=diameter,
                via_type=via_type,
                locked=locked,
                design_rule_blind_via_name=design_rule_blind_via_name,
                solder_mask_expansion=solder_mask_expansion,
            ),
            capability="pcb",
        )

    @server.tool(name="pcb.delete_routing_primitives")
    async def pcb_delete_routing_primitives(
        project_id: str,
        line_ids: list[str] | None = None,
        arc_ids: list[str] | None = None,
        polyline_ids: list[str] | None = None,
        via_ids: list[str] | None = None,
    ) -> Any:
        """Delete exact PCB tracks, arcs, polylines, and vias by primitive ID."""
        return await router.request(
            project_id,
            "pcb.delete_routing_primitives",
            _defined(
                line_ids=line_ids,
                arc_ids=arc_ids,
                polyline_ids=polyline_ids,
                via_ids=via_ids,
            ),
            capability="pcb",
        )

    @server.tool(name="pcb.clear_routing")
    async def pcb_clear_routing(
        project_id: str,
        type: Literal["all", "net", "connection"] = "all",
    ) -> Any:
        """Clear all routing or the currently selected net/connection."""
        return await router.request(
            project_id,
            "pcb.clear_routing",
            {"type": type},
            capability="pcb",
        )

    @server.tool(name="pcb.route_net")
    async def pcb_route_net(
        project_id: str,
        net: str,
        strategy: Literal["completion", "fast"] = "completion",
        corner_style: Literal[45, 90] = 45,
        existing_primitive_mode: Literal["keep", "remove"] = "keep",
        layers: list[int] | None = None,
    ) -> Any:
        """Run JLCEDA auto-routing for one named PCB net."""
        return await router.request(
            project_id,
            "pcb.route_net",
            _defined(
                net=net,
                strategy=strategy,
                corner_style=corner_style,
                existing_primitive_mode=existing_primitive_mode,
                layers=layers,
            ),
            capability="pcb",
        )

    @server.tool(name="pcb.auto_route")
    async def pcb_auto_route(
        project_id: str,
        nets: list[str] | None = None,
        ignore_nets: list[str] | None = None,
        strategy: Literal["completion", "fast"] = "completion",
        corner_style: Literal[45, 90] = 45,
        existing_primitive_mode: Literal["keep", "remove"] = "keep",
        layers: list[int] | None = None,
    ) -> Any:
        """Auto-route all or selected PCB nets, optionally excluding named nets."""
        return await router.request(
            project_id,
            "pcb.auto_route",
            _defined(
                nets=nets,
                ignore_nets=ignore_nets,
                strategy=strategy,
                corner_style=corner_style,
                existing_primitive_mode=existing_primitive_mode,
                layers=layers,
            ),
            capability="pcb",
        )

    @server.tool(name="pcb.auto_layout")
    async def pcb_auto_layout(project_id: str) -> Any:
        """Run JLCEDA automatic PCB component layout."""
        return await router.request(
            project_id, "pcb.auto_layout", capability="pcb"
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
