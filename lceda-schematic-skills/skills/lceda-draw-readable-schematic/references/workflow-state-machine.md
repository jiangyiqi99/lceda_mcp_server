# End-to-End Workflow State Machine

```text
DISCOVER_TOOLS
   ↓
VERIFY_SCH_DOCUMENT
   ↓
READ_TARGET + PIN_GEOMETRY
   ↓
CLASSIFY_TASK
   ├─ cleanup → SNAPSHOT_TOPOLOGY → ORIENT → ALIGN/SPACE → ROUTE/LABEL
   └─ new/edit → PLAN_LANES → ORIENT → PLACE_ALL → ROUTE/LABEL
                                      ↓
                              SUPPORT/INTERFACES
                                      ↓
                                  DOCUMENT
                                      ↓
                               GEOMETRY_LINT
                                      ↓
                              NETLIST/DRC REVIEW
                               ↙ fail      pass ↘
                            REPAIR             SAVE/DONE
```

## DISCOVER_TOOLS
Exit: live MCP schema is mapped to semantic reads/writes. No invented calls.

## VERIFY_SCH_DOCUMENT
Exit: target is an active schematic, not an assumed PCB/unknown document. Coordinate domain is known: schematic uses 10mil per unit.

## READ_TARGET + PIN_GEOMETRY
Read relevant component anchors, `rotation/mirror`, actual component pin coordinates, wires, labels/ports, and nets.

## PLAN_LANES
Exit: page theme, boundary sides, main-chain anchor order, support lanes, repeated-channel families, and abstraction choices are known.

## ORIENT
Exit: directional components have been evaluated against `0/90/180/270°` candidates from actual pin geometry. Wrong-facing connectors/passives/support branches are removed before routing.

## PLACE_ALL / ALIGN/SPACE
Exit: anchors follow grid/lanes, main-path X is monotonic where appropriate, repeated ΔX/ΔY is stable, and pin-escape room exists.

## ROUTE/LABEL
Exit:
- no diagonal wire segments;
- 0–2 bends is normal;
- 3 bends is a warning;
- local 4+ bend routes are rejected;
- Wire/Label/Port/NetFlag selection follows semantic scope;
- crossings/four-way junctions are minimized.

## GEOMETRY_LINT
Count/check orientation, orthogonality, bends, backtracking, crossings, junctions, alignment outliers, repeated-channel drift, and label economy. Failure returns to the earliest causal state, usually ORIENT or PLACE, not merely ROUTE.

## NETLIST/DRC REVIEW
Geometry-only cleanup requires topology equivalence and no DRC regression. New electrical design is checked against requested connectivity/specification.

## Transaction rule

`read → compute exact geometry → mutate small batch → re-read → geometry lint → topology/DRC verify`

## Automation rule

Whole-sheet autoLayout/autoRouting is not a workflow state. It may only propose disposable candidate geometry whose result is independently re-read and verified.
