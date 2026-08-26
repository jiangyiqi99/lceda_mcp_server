---
name: lceda-review-schematic
description: Use when an LCEDA schematic drawing or cleanup is about to be declared complete, or when a sheet needs checking for electrical regressions, readability defects, visual inconsistency, ambiguous routing, or review readiness.
---

# Review an LCEDA Schematic

REQUIRED: use live MCP/LCEDA reads when available. Do not grade a changed schematic solely from the intended plan.

## Electrical hard gates

A page cannot pass if any applicable condition fails:
- geometry-only task changed electrical Netlist/topology;
- new DRC errors appeared;
- intended connections became dangling/ambiguous;
- a mutation result was not re-read/verified;
- a tool/capability/result was invented.

## Geometry hard gates

For a normal finished page, all applicable items must pass:
- `diagonal_wire_segments == 0`;
- local wires with **4+ bends == 0**. A written rationale does not waive this gate. If placement or abstraction cannot remove one, report the page as unfinished and do not declare completion;
- obvious U-turn/zig-zag/backtracking routes == 0;
- wrong-facing main-chain/support role components == 0 unless documented exception;
- avoidable four-way connected junctions == 0;
- repeated-channel orientation/spacing outliers == 0 unless electrically intentional;
- critical text/label overlaps == 0.

Crossings target zero. A remaining crossing requires a short reason why moving, lane shift, branch change, or justified label/port would be worse.

## Visual score

After hard gates, score with `references/quality-gates.md`. Target **>=90/100** for a freshly drawn/refined page. A numeric score cannot override a hard-gate failure.

## Evidence

Review actual coordinates, pin geometry, wire polylines, labels/ports, Netlist, and DRC. If a render is available, add 3-second/30-second visual tests. Without a render, state that geometry review is a structural proxy.

Read `references/quality-gates.md` and `references/geometry-lint.md`.
