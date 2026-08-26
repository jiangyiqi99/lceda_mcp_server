---
name: lceda-draw-readable-schematic
description: Use when creating, substantially redrawing, completing, or end-to-end improving an LCEDA Pro schematic page or multi-page circuit through Codex and the LCEDA MCP integration.
---

# Draw a Readable LCEDA Schematic

This is the orchestration entry point. Always load:
- `lceda-establish-schematic-style`
- `lceda-adapt-mcp-tools`
- `lceda-review-schematic`

For actual drawing/refinement also load placement and routing skills.

## Before mutation

1. establish live MCP capability map;
2. verify active LCEDA schematic document;
3. read relevant components, actual pin geometry, wires, nets, labels/ports;
4. remember schematic units are 10mil per coordinate unit;
5. capture Netlist/DRC baseline when applicable;
6. decide whether electrical change is allowed.

## New drawing state machine

`Plan functional graph → establish anchors/lanes → orient from pin geometry → place all components → route local topology → add labels/ports/flags → organize support circuits → annotate → geometry lint → Netlist/DRC review`

Never alternate uncontrolled “place one → wire one” loops across the whole page.

## Existing cleanup state machine

Use `lceda-beautify-schematic` and its three-pass sequence:
1. Orientation pass;
2. Alignment/spacing pass;
3. Wiring/label pass.

## Batch transaction

Every local batch follows:

`READ → PLAN EXACT GEOMETRY → MUTATE → RE-READ → GEOMETRY LINT → TOPOLOGY/DRC CHECK`

Do not move to the next batch while the current one leaves diagonal wires, >=4-bend local routes, wrong-facing role components, unexplained repeated-channel drift, or ambiguous net state.

## Completion threshold

Hard electrical + geometry gates must pass and refined pages should score >=90/100. Unsupported checks must be stated explicitly.
