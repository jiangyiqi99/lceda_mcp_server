# Source Notes and Design Rationale

## LCEDA Pro official API capabilities used by this pack

The official API exposes schematic document operations, components, component pins, wires, text, rectangles, DRC, Netlist, manufacture/export data, and library search. Extension APIs are accessed through the root `eda` object; class instances use the first three letters of the class prefix in lowercase, e.g. `SCH_Document` → `eda.sch_Document`.

Important capabilities for this Skill Pack:

- `eda.sch_Document`: read regions/points, save, BETA auto-layout/auto-routing.
- `eda.sch_PrimitiveComponent`: create/get/getAll/modify/delete, get pins, create net flags and net ports.
- `eda.sch_PrimitiveWire`: create/get/getAll/modify/delete. Wire geometry is represented as connected horizontal/vertical segments.
- `eda.sch_PrimitiveText`: create/get/getAll/modify/delete; rotations are orthogonal.
- `eda.sch_PrimitiveRectangle`: optional visual/safety/variant boundaries.
- `eda.sch_Drc.check(...)`: strict DRC with optional verbose results.
- `eda.sch_Netlist.getNetlist(...)`: capture electrical topology.
- `eda.lib_Device` / `eda.lib_Symbol`: search and inspect library objects.
- `eda.sch_ManufactureData.getExportDocumentFile(...)`: export document when exposed by the MCP transport.

Many mutation/automation methods are marked BETA by LCEDA documentation. The skills therefore wrap them in read → mutate → re-read → verify cycles.

## Visual sources distilled into rules

Altium and TU Delft converge on the same visual grammar used here:
- signal flow usually left → right;
- positive power above, ground below;
- keep related components together;
- use spacing and alignment to create hierarchy;
- minimize crossings and unnecessary wire tracing;
- use meaningful net names and hierarchy;
- schematic symbols should express circuit logic, not mimic package pin order.

The user-provided guide adds a particularly useful operational distinction: **Wire expresses local relationship; Label expresses identity**. It also emphasizes placement-before-wiring, repeated-channel visual symmetry, sparse annotations with design intent, one named theme per page, and a final visual cleanup pass.

## Why MCP names are not hard-coded

`lceda_mcp_extension` and `lceda_mcp_server` are the intended transport, but the skills bind to semantic capabilities rather than specific third-party tool names. The server's live schemas are the authority. This prevents tool-name drift from silently breaking the workflow or encouraging the agent to hallucinate calls.
