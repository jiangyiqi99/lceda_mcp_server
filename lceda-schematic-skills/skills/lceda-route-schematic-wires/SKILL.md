---
name: lceda-route-schematic-wires
description: Use when adding, rerouting, simplifying, or reviewing LCEDA schematic wires, net labels, net ports, branches, junctions, crossings, or signal names.
---

# Route LCEDA Schematic Wires

REQUIRED: apply `lceda-establish-schematic-style` and `lceda-adapt-mcp-tools`. Placement must already be coherent.

## Wire geometry is constrained

LCEDA `SCH_PrimitiveWire` uses a continuous polyline. Every segment must be orthogonal by default: consecutive vertices must share X or Y. No diagonal wire is acceptable in a finished schematic.

### Pin escape first

From a pin, draw a short straight **pin escape** before the first bend, branch, or junction. Target one major visual grid; increase when the symbol is dense. Never branch directly on a crowded component outline when a short escape is possible.

### Bend budget

- 0–2 bends: normal;
- 3 bends: allowed only when it clearly avoids a collision/crossing;
- **>=4 bends: fail the route** — return to placement or replace a genuinely non-local connection with the correct label/port abstraction.

Do not accept zig-zags, U-shaped detours, repeated direction reversals, or a route that hugs unrelated component bodies.

## Wire vs label vs port vs net flag

Apply this order:

1. power/ground infrastructure → NetFlag/power symbol;
2. cross-sheet/module boundary → NetPort/off-page construct;
3. strong local electrical relationship → visible Wire;
4. same-sheet non-local identity that would otherwise cross unrelated blocks, create excessive length/bends, or duplicate a shared net across regions → Net Label **if the live MCP exposes a real label capability**;
5. if label creation is unavailable, do not misuse NetPort as a cosmetic label; preserve a readable wire or report the limitation.

Local topology such as `MCU → Rseries → Flash` or `signal → R → C → GND` must remain visibly traceable.

## Crossing and junction rules

Target zero avoidable crossings. Prefer T-junctions. Four-way connected junctions are a defect unless topology makes them clearly superior. Non-connected crossing ambiguity should be removed by moving blocks, shifting lanes, or using a justified non-local abstraction.

## LCEDA net safety

Before creating/modifying a wire, read both endpoint pins/nets. Passing an explicit `net` to `SCH_PrimitiveWire.create(...)` can cause touching primitives without explicit network identity to follow that specified net. Therefore **never pass a net merely to make creation succeed**. Use the actual intended net and verify the created wire's `line` and `net` afterward.

Read `references/wiring-patterns.md` and `references/label-route-decision-tree.md`.
