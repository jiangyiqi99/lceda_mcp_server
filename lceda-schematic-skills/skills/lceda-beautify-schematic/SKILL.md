---
name: lceda-beautify-schematic
description: Use when an existing LCEDA schematic is electrically intended to remain the same but looks cluttered, inconsistent, hard to trace, poorly aligned, over-labeled, crossing-heavy, or visually unprofessional.
---

# Beautify an Existing LCEDA Schematic

REQUIRED: apply `lceda-adapt-mcp-tools`, `lceda-establish-schematic-style`, `lceda-place-schematic-components`, `lceda-route-schematic-wires`, and `lceda-review-schematic`.

## Iron rule

**Beautification must not change electrical intent.** Capture Netlist/topology + DRC + target-region component/wire/net state before the first mutation.

## Do not mix cleanup dimensions

Perform three explicit passes in this order. Finish and re-read each pass before starting the next.

### 1. Orientation pass

Fix wrong-facing connectors, ICs, series passives, pull/decoupling branches, and inconsistent repeated-channel rotations. Use actual LCEDA pin geometry and the orientation-candidate scoring rule. Do not route yet except for temporary preservation if required by the tool.

### 2. Alignment/spacing pass

Normalize anchors, functional lanes, block gaps, repeated ΔX/ΔY, pin-escape room, and text/value offsets. Move blocks before individual decorative nudges.

### 3. Wiring/label pass

Rebuild only affected local wires. Enforce orthogonal segments, pin escape, bend budget, crossing reduction, T-junction preference, and the Wire/Label/Port/NetFlag decision tree. Convert long non-local wires to labels only when the actual MCP has a label capability.

## Geometry lint after every pass

A pass is not complete while it leaves:
- diagonal wire segments;
- >=4-bend local routes;
- unjustified wrong-facing main-path/support parts;
- avoidable crossing/four-way junction clusters;
- repeated-channel geometry drift;
- obvious label/text collisions.

If the only way to “fix” a route is to add bends, return to the earlier placement pass.

## Work locally

Beautify one functional block or repeated-channel family at a time. Re-read actual coordinates and nets after each batch. Whole-sheet autoLayout/autoRouting remains disabled by default.

Read `references/cleanup-algorithm.md` for the transaction sequence.
