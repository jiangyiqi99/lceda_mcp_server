---
name: lceda-place-schematic-components
description: Use when LCEDA schematic components need to be placed, moved, aligned, rotated, mirrored, grouped, or made visually consistent before or during wiring.
---

# Place LCEDA Schematic Components

REQUIRED: apply `lceda-establish-schematic-style`, `lceda-plan-schematic-page`, and for MCP edits `lceda-adapt-mcp-tools`.

## Placement is a geometry problem, not a taste problem

Do not start from arbitrary X/Y coordinates. Read the active schematic, component anchors, relevant pin coordinates, existing grid rhythm, and neighboring functional blocks first. In LCEDA schematic space, coordinates use 0.01 inch = **10mil per unit**; never reuse PCB-unit assumptions.

## Deterministic placement order

1. page/system boundary connectors;
2. main functional ICs;
3. protection/transceiver/conditioning devices;
4. supporting R/C/L/clock/reset/termination parts;
5. test points, labels, notes.

Place all anchors before local wiring. If a connection requires ugly geometry, fix placement before optimizing the wire.

## Orientation candidate scoring

For every movable non-trivial component, read `x/y/rotation/mirror` and `getAllPinsByPrimitiveId(...)`. Evaluate the orthogonal **orientation candidate** set `0/90/180/270°`; keep `mirror=false` by default.

Score each candidate by this priority:

1. **pin-facing**: relevant pins land on the side facing their electrical partner or intended lane;
2. main-path direction: upstream side left, downstream side right when semantics allow;
3. power semantics: supply-facing support above, ground-facing support below;
4. passive role: series R/L horizontal; pull-up/down, decoupling, divider legs normally vertical;
5. shortest clean pin escape with minimal bends/crossings;
6. consistency with repeated channels and nearby identical roles.

Do not rotate a component merely to fill empty space. Do not mirror ordinary parts unless rotation alone cannot produce a readable symbol and the symbol semantics remain unambiguous.

## Anchor, lane, and grid rules

Derive the project grid from existing geometry when possible. If a new page has no established rhythm, use a major visual grid of 10 schematic units (100mil) for component anchors, while respecting actual symbol-pin coordinates.

- Main signal-chain anchors should be monotonic in X.
- Power/support branches should occupy stable Y lanes above/below their owner.
- Related components cluster tightly; unrelated blocks are separated by at least a visibly larger gap.
- Repeated channels reuse the same ΔX/ΔY, orientations, label offsets, and pin-entry geometry.
- Leave at least one major-grid unit of unobstructed pin-escape space where practical.

## LCEDA mutation discipline

Move/rotate only a small block at a time. Re-read the component and pins after `modify(...)`; then rebuild only affected local wires. A library-symbol edit is never a shortcut for bad sheet placement.

Read `references/placement-patterns.md` and `references/lceda-orientation-grid.md` for the executable geometry rules.
