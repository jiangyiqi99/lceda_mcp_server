---
name: lceda-draw-readable-schematic
description: Use when creating, substantially redrawing, completing, or end-to-end improving an LCEDA Pro schematic page or multi-page circuit through a skill-capable coding agent and the LCEDA MCP integration.
---

# Draw a Readable LCEDA Schematic

This is the orchestration entry point. Load only the companion skills needed, but always load:

- `lceda-establish-schematic-style`
- `lceda-adapt-mcp-tools`
- `lceda-review-schematic`

## Determine task class

**New drawing** → planning → placement → wiring → power/support → interfaces/channels → documentation → review.

**Existing cleanup** → `lceda-beautify-schematic` → review.

**Localized edit** → load only affected technique skill(s), then review affected topology.

## Before mutation

1. establish MCP capability map;
2. identify target project/page/region from actual editor state;
3. read existing relevant components/wires/nets;
4. capture Netlist/DRC baseline when available;
5. state internally whether electrical changes are allowed.

## Execute incrementally

Never perform a giant “draw everything” mutation. Work by functional block or repeated channel family. Placement precedes routing. Each batch ends with a re-read.

## Resolve conflicts by priority

1. explicit user circuit requirements;
2. electrical correctness/topology;
3. project/team naming/library conventions;
4. schematic readability principles;
5. aesthetic preference.

A prettier diagram may never override a required electrical connection.

## Finish only after review

Apply hard gates and quality score. Save coherent state. Report unsupported checks explicitly instead of claiming them.

For detailed state transitions, read `references/workflow-state-machine.md`.
