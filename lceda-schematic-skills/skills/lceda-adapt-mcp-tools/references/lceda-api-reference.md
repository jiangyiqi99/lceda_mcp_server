# LCEDA Pro Official API Reference — Schematic Subset

Authoritative starting point: <https://prodocs.lceda.cn/cn/api/reference/>

## Access model

LCEDA extension runtime provides a root `eda` object. Class instances use a lowercased three-letter prefix, e.g.:

- `SCH_Document` → `eda.sch_Document`
- `SCH_PrimitiveComponent` → `eda.sch_PrimitiveComponent`
- `SCH_PrimitiveWire` → `eda.sch_PrimitiveWire`
- `SCH_PrimitiveText` → `eda.sch_PrimitiveText`
- `SCH_Drc` → `eda.sch_Drc`
- `SCH_Netlist` → `eda.sch_Netlist`
- `LIB_Device` → `eda.lib_Device`
- `LIB_Symbol` → `eda.lib_Symbol`

Do not assume the MCP Server exposes these as 1:1 MCP tool names.

## Document

`eda.sch_Document`
- `getPrimitiveAtPoint(x, y)`
- `getPrimitivesInRegion(left, right, top, bottom)`
- `navigateToCoordinates(x, y)`
- `navigateToRegion(left, right, top, bottom)`
- `save()`
- `autoLayout(props?)` — BETA; proposal only
- `autoRouting(props?)` — BETA; proposal only

## Components

`eda.sch_PrimitiveComponent`
- `create(component, x, y, subPartName?, rotation?, mirror?, addIntoBom?, addIntoPcb?)`
- `get(...)`, `getAll()`, `getAllPrimitiveId()`
- `getAllPinsByPrimitiveId(...)`
- `modify(primitiveId, property)` where properties include position/rotation/mirror and component metadata
- `delete(...)`
- `createNetFlag(identification, net, x, y, rotation?, mirror?)`
- `createNetPort(direction, net, x, y, rotation?, mirror?)`

Library identifiers must come from actual search/inspection results; never fabricate them.

## Wires

`eda.sch_PrimitiveWire`
- `create(line, net?, color?, lineWidth?, lineType?)`
- `get(...)`, `getAll()`, `modify(...)`, `delete(...)`

`line` is composed of connected coordinate segments. Official examples reject diagonal segments; treat schematic wiring as Manhattan geometry.

## Text and boundaries

`eda.sch_PrimitiveText.create(x, y, content, rotation?, textColor?, fontName?, fontSize?, bold?, italic?, underLine?, alignMode?)`

Text rotations are orthogonal. Prefer 0° unless layout convention genuinely requires otherwise.

`eda.sch_PrimitiveRectangle.create(...)` exists, but ordinary functional grouping should prefer whitespace + headings. Rectangles are for meaningful boundaries such as isolation, safety, or variants.

## DRC and Netlist

`eda.sch_Drc.check(strict, userInterface, includeVerboseError)`
- current schematic mode is strict;
- verbose mode returns detailed error information.

`eda.sch_Netlist.getNetlist(type)` obtains the current schematic Netlist. Use the MCP/live schema or current official enum to choose a valid type; never invent one.

## Export

`eda.sch_ManufactureData.getExportDocumentFile(...)` can export the current schematic document when available. If the MCP transport does not expose it, do not claim a PDF/render review was performed.

## Stability warning

Many schematic primitive mutation and automation APIs are documented as BETA. Every mutation path must therefore include post-read verification and, for cleanup, topology comparison.
