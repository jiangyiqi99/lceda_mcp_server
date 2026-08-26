# LCEDA / EasyEDA Official API Reference — Schematic Subset

Authoritative starting point: <https://prodocs.lceda.cn/cn/api/reference/>

This reference also incorporates the user-provided EasyEDA API Skill's schematic-specific details. The live MCP tool schema remains the authority for what Codex can actually invoke.

## Coordinate and document model

**Critical:** schematic coordinates use `0.01 inch = 10mil = 0.254mm` per unit. PCB coordinates use a different unit. Mixing the two moves schematic objects by about a factor of ten.

Before mutations, verify the active project/document is a schematic through whatever read capability the MCP exposes. Do not call schematic operations against an unknown/PCB document state.

## Access model

LCEDA extension runtime provides a root `eda` object. Typical class mappings are:
- `SCH_Document` → `eda.sch_Document`
- `SCH_PrimitiveComponent` → `eda.sch_PrimitiveComponent`
- `SCH_PrimitiveWire` → `eda.sch_PrimitiveWire`
- `SCH_PrimitiveText` → `eda.sch_PrimitiveText`
- `SCH_Drc` → `eda.sch_Drc`
- `SCH_Netlist` → `eda.sch_Netlist`

Do not assume the MCP server exposes these as 1:1 tool names.

## Components and pin geometry

`eda.sch_PrimitiveComponent`
- `create(component, x, y, subPartName?, rotation?, mirror?, addIntoBom?, addIntoPcb?)`
- `get(...)`, `getAll()`, `getAllPrimitiveId()`
- `getAllPinsByPrimitiveId(primitiveId)`
- `modify(primitiveId, {x?, y?, rotation?, mirror?, ...})`
- `delete(...)`
- `createNetFlag(identification, net, x, y, rotation?, mirror?)`
- `createNetPort(direction, net, x, y, rotation?, mirror?)`, where direction is `IN | OUT | BI`

For sheet-placement decisions, read actual pin `x`, `y`, and `rotation` values after each component move. Associated component-pin geometry is largely read-only; reposition the component rather than trying to mutate pin coordinates.

Use orthogonal component rotations `0/90/180/270°` for normal schematic cleanup. Keep `mirror=false` unless the specific symbol genuinely becomes more readable and unambiguous when mirrored.

## Wires

`eda.sch_PrimitiveWire`
- `create(line, net?, color?, lineWidth?, lineType?)`
- `get(...)`, `getAll()`, `modify(...)`, `delete(...)`

`line` is a continuous polyline represented by coordinate groups. Finished schematic routing should use Manhattan segments.

### Explicit-net side effect — critical

When `create(...)` is called **without** `net`, LCEDA can infer the network from contacted primitives and fail when multiple incompatible networks are touched.

When a **specified net** is supplied, touching primitives that do not themselves have an **explicit** network identity (for example via a label/port) may **follow** the specified net. If a contacted primitive already explicitly names a conflicting net, creation fails.

Therefore:
1. read both endpoint pins/net identities first;
2. never provide `net` merely as a convenience or repair tactic;
3. use only the intended known net;
4. re-read the created wire's `line` and `net`;
5. run topology/DRC verification after a batch.

## Labels, ports, flags

The documented component API explicitly exposes NetFlag and NetPort creation. A dedicated same-sheet Net Label creation API must not be assumed from that fact. Bind `CREATE_NET_LABEL`, `MODIFY_NET_LABEL`, and `READ_NET_LABELS` only when the live MCP schemas expose the corresponding write and verification paths. After creating or modifying a label, re-read its primitive id, net identity, position, and side/orientation when available, then verify the resulting Netlist/DRC. If the capabilities are absent, preserve readable wires instead of misusing a port or plain text as an electrical label.

## Text and boundaries

`eda.sch_PrimitiveText.create(...)` supports rotation and formatting. Prefer horizontal text; avoid rotated labels unless necessary.

`eda.sch_PrimitiveRectangle.create(...)` exists, but ordinary grouping should use whitespace/headings. Rectangles are for real engineering boundaries such as isolation, safety, or variants.

## DRC and Netlist

`eda.sch_Drc.check(strict, userInterface, includeVerboseError)` supports strict checking and verbose results.

`eda.sch_Netlist.getNetlist(type)` exists but is documented as deprecated in favor of manufacture-data Netlist export in newer API material. Use whichever Netlist capability is actually exposed by the live MCP; do not invent enum values.

## Stability warning

Many schematic primitive mutation/automation APIs are BETA. Every mutation path must include `read → mutate → re-read → verify`. Whole-sheet auto-layout/auto-routing is proposal-only, never correctness evidence.
