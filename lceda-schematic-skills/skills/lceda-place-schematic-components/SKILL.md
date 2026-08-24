---
name: lceda-place-schematic-components
description: Use when LCEDA schematic components need to be placed, moved, aligned, rotated, mirrored, grouped, or made visually consistent before or during wiring.
---

# Place LCEDA Schematic Components

REQUIRED: apply `lceda-establish-schematic-style`, `lceda-plan-schematic-page`, and for MCP edits `lceda-adapt-mcp-tools`.

## Placement before wiring

Do not solve a placement problem by drawing increasingly complex wires. Arrange the page until the intended topology can be drawn simply.

## Placement priorities, in order

1. **Functional correctness of grouping** — keep a block's essential parts together.
2. **Reading direction** — inputs left, outputs right, supply relationships vertical.
3. **Pin accessibility** — orient/position parts so relevant pins face their partners.
4. **Alignment** — snap to the existing editor/project grid.
5. **Whitespace** — clear separation between blocks; compact cohesion inside blocks.
6. **Repetition** — identical channels use identical anchors/spacing/orientation.

## Core placement patterns

- External connector near page boundary.
- Protection immediately inward from external connector.
- Transceiver/conditioner between boundary and controller.
- Local decoupling close to the served power pin/domain in schematic semantics.
- Pull resistors next to the signal they define.
- Series termination next to its driving source.
- Crystal and load network adjacent to oscillator pins.
- Feedback divider adjacent to regulator/amplifier feedback path.

## Safe MCP movement

Read component IDs, positions, rotations, and associated pins before moving. Move a small block at a time. Re-read after movement before rewriting wires.

Do not edit a shared symbol/library merely because its pin arrangement is inconvenient. Library symbol redesign is a separate explicit task.

Read `references/placement-patterns.md` when balancing dense or repeated blocks.
