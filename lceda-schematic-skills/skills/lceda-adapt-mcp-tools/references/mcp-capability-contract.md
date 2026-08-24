# MCP Semantic Capability Contract

This file names **semantic aliases**, not MCP tool names. Bind each alias to the live tool schema exposed by `lceda_mcp_server`.

| Alias | Required behavior | Read/write | Typical LCEDA API analogue |
|---|---|---:|---|
| `READ_COMPONENTS` | enumerate/get schematic components including ids/position/rotation | R | `eda.sch_PrimitiveComponent.getAll/get` |
| `READ_COMPONENT_PINS` | obtain pins for a placed component | R | `getAllPinsByPrimitiveId` |
| `READ_WIRES` | enumerate/get wire geometry + nets | R | `eda.sch_PrimitiveWire.getAll/get` |
| `READ_REGION` | read primitives in a rectangular area | R | `eda.sch_Document.getPrimitivesInRegion` |
| `READ_NETLIST` | obtain current electrical Netlist/topology | R | `eda.sch_Netlist.getNetlist` |
| `READ_DRC` | run strict DRC, preferably verbose | R | `eda.sch_Drc.check` |
| `SEARCH_DEVICE` | search a device/library entry | R | `eda.lib_Device.search` |
| `SEARCH_SYMBOL` | search/inspect symbol | R | `eda.lib_Symbol.search/get` |
| `PLACE_COMPONENT` | place known device/symbol at coordinate | W | `eda.sch_PrimitiveComponent.create` |
| `MODIFY_COMPONENT` | move/rotate/mirror/change display metadata | W | `eda.sch_PrimitiveComponent.modify` |
| `DELETE_COMPONENT` | delete explicitly selected placed component | W | `delete` |
| `CREATE_WIRE` | create connected Manhattan wire segments | W | `eda.sch_PrimitiveWire.create` |
| `MODIFY_WIRE` | change wire geometry/net/style | W | `modify` |
| `DELETE_WIRE` | delete explicitly selected wire | W | `delete` |
| `CREATE_NET_FLAG` | place power/net flag | W | `createNetFlag` |
| `CREATE_NET_PORT` | place directional net port | W | `createNetPort` |
| `CREATE_TEXT` | place design-intent note/block title | W | `eda.sch_PrimitiveText.create` |
| `CREATE_RECTANGLE` | create rare boundary/region annotation | W | `eda.sch_PrimitiveRectangle.create` |
| `SAVE` | save document | W | `eda.sch_Document.save` |
| `EXPORT_DOCUMENT` | export/render document if supported | R | `eda.sch_ManufactureData.getExportDocumentFile` |
| `AUTO_LAYOUT` | propose automatic placement | W | `eda.sch_Document.autoLayout` |
| `AUTO_ROUTING` | propose automatic routing | W | `eda.sch_Document.autoRouting` |
| `RAW_EDA_EXEC` | execute safe code/API against extension `eda` object | R/W | extension-dependent |

## Mapping algorithm

For each live tool:
1. trust description and JSON schema more than the name;
2. match by observable behavior;
3. note required vs optional parameters;
4. prefer narrow purpose-built operations over arbitrary script execution;
5. if two tools match, prefer the one that returns structured IDs/objects suitable for verification.

## Minimum tiers

**Tier A — Review only**: read components + wires + Netlist/DRC.

**Tier B — Geometric cleanup**: Tier A + move/rotate components + wire modify/create/delete + save.

**Tier C — Full drawing**: Tier B + library search + place components + labels/ports/flags/text.

If the MCP connection only provides a lower tier, do not simulate a higher tier through guessed calls.
