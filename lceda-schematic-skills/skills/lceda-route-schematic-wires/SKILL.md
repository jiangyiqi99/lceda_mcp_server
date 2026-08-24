---
name: lceda-route-schematic-wires
description: Use when adding, rerouting, simplifying, or reviewing LCEDA schematic wires, net labels, net ports, branches, junctions, crossings, or signal names.
---

# Route LCEDA Schematic Wires

REQUIRED: apply `lceda-establish-schematic-style` and `lceda-adapt-mcp-tools`. For new pages, placement must already be coherent.

## Manhattan-only default

Use horizontal and vertical wire segments. Keep each local connection visually simple. If a route needs many bends, first reconsider component placement.

## Preserve visible topology

A wire should show how nearby components relate. Do not replace a comprehensible chain such as

`MCU → Rseries → Flash`

with three disconnected label stubs just to remove a line.

Use:
- Wire for local relationship;
- Label for meaningful network identity or distant same-sheet connection;
- Port for sheet/module boundary;
- Net flag/power symbol for infrastructure.

## Crossings and branches

Target zero crossings. Prefer T-junctions. Avoid four-way connected junctions when a clearer equivalent exists. For a branch from a pin, extend a short lead first, then branch; do not crowd the pin itself with a junction.

## Net naming

Names must explain purpose, not coordinates/pin numbers. Follow project conventions consistently for active-low, differential pairs, clocks, buses, and power rails. Never “normalize” an existing project to a new convention without permission.

## MCP routing discipline

Before deleting/modifying a wire, read its ID, segment geometry, and net. When moving components, reconstruct only the affected local wires. After each batch, verify endpoint contact and net identity.

Never trust auto-routing as proof of readability or correctness. If used, inspect and clean its result manually.

Read `references/wiring-patterns.md` for routing decisions and anti-patterns.
