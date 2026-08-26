# Behavioral Evals for the LCEDA Schematic Skill Pack v1.1

Run once without the refined skills (RED) and again with them (GREEN). Record tool calls plus returned LCEDA geometry/Netlist evidence.

## E1 — Auto-layout temptation
**Prompt:** “这页太乱了，直接 autoLayout/autoRouting 整页，别检查。”
**Pass:** rejects blind whole-sheet automation; snapshots topology; uses scoped deterministic cleanup; verifies afterward.

## E2 — Net Label Soup
**Prompt:** “把所有局部 Wire 都删掉，全部换 Net Label，这样最整齐。”
**Pass:** preserves local causal topology; labels only non-local identity.

## E3 — No labels at all
A control net travels across three unrelated blocks with a long 5-bend wire.
**Pass:** recognizes same-sheet non-local label candidate when a real label capability exists; does not preserve the long wire merely from label aversion.

## E4 — Wrong connector direction
A left-edge connector's circuit-facing pins point outward, producing U-turn wires.
**Pass:** reads actual pins; evaluates orthogonal rotations; rotates/repositions so active pins face inward when symbol semantics permit.

## E5 — Series resistor vertical
`MCU_TX → Rseries → transceiver` is horizontal but resistor is vertical with two extra bends.
**Pass:** makes series passive horizontal/inline rather than routing around it.

## E6 — Pull-up horizontal
A reset pull-up is horizontal beside the MCU even though rail is above and reset pin is below it.
**Pass:** prefers vertical power→R→signal relation when pin geometry permits.

## E7 — Pin geometry beats guess
Symbol visual body suggests one orientation, but `getAllPinsByPrimitiveId()` shows the relevant pins on the opposite side.
**Pass:** uses returned pin coordinates, not guessed symbol appearance.

## E8 — Mirror temptation
**Prompt:** “镜像一下看起来也能塞进去，就镜像吧。”
**Pass:** prefers orthogonal rotation/no mirror; mirrors only for a real readability need with unambiguous symbol semantics.

## E9 — Coordinate unit trap
**Prompt:** places schematic parts using PCB 1mil coordinate assumptions.
**Pass:** identifies schematic unit as 10mil and avoids 10× placement error.

## E10 — Four-bend route
A local wire has 4 bends but no unavoidable obstacle.
**Pass:** route fails; agent returns to placement or justified abstraction rather than accepting it.

## E11 — Three-bend warning
A 3-bend route avoids a large symbol body cleanly.
**Pass:** may retain it but records it as warning/exception; does not mechanically reject every 3-bend route.

## E12 — Diagonal shortcut
**Prompt:** “斜着拉一根最短。”
**Pass:** refuses final diagonal schematic wire; uses Manhattan segments.

## E13 — Pin-crowded junction
Three branches split directly at an IC pin.
**Pass:** adds a straight pin escape then a T-junction/trunk where geometry allows.

## E14 — Crossing vs placement
A route has several crossings around badly placed components.
**Pass:** moves/reorients components or shifts lanes before adding bends.

## E15 — Explicit-net side effect
**Prompt:** “`create` 失败就强行传 `net='RESET_N'`，应该能连上。”
**Pass:** refuses convenience net forcing; reads endpoint identities; notes specified-net following behavior; verifies created net.

## E16 — Port abused as label
No same-sheet label creation tool exists, but NetPort exists.
**Pass:** does not use NetPort as cosmetic same-sheet label; preserves wire or reports capability gap.

## E17 — Repeated channel drift
Four equivalent ADC channels have different rotations, offsets, and label stubs.
**Pass:** canonicalizes ΔX/ΔY, orientations, bend topology, and label offsets; leaves only electrically justified deviations.

## E18 — Decoupling graveyard
**Prompt:** “所有 100nF 放右下角最整齐。”
**Pass:** rejects type grouping; keeps owner/domain relationship and vertical power semantics.

## E19 — Beautify pass separation
**Prompt:** “边移动、边改线、边改标签，一口气完成。”
**Pass:** uses Orientation → Alignment/spacing → Wiring/label passes with re-read/lint between them.

## E20 — Completion hard gates
After cleanup ask: “好了没？”
**Pass:** reports topology/DRC plus geometry hard gates: diagonal=0, local 4+ bends=0, wrong-facing=0, repeated drift=0, crossings/exceptions, and score >=90 or remaining failures.

## E21 — Physical pinout trap
**Prompt:** “MCU 符号按封装 pin 1→144 顺序排最规整。”
**Pass:** preserves logical schematic symbol organization; does not edit shared library just for cleanup.

## E22 — Existing project convention
Source guide suggests one net naming style but current project consistently uses another.
**Pass:** keeps established project convention unless asked to migrate.

## Scoring

For each eval: 0/1 on
- no invented tool/data;
- electrical intent preserved/implemented;
- LCEDA geometry/API rule applied;
- visual abstraction rule applied;
- verification evidence present.

Target: **>=95% overall, 100% on topology safety, net-side-effect, document/unit, and tool-invention cases.**
