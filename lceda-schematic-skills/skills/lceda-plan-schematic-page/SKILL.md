---
name: lceda-plan-schematic-page
description: Use when an LCEDA schematic page is being created or substantially reorganized and its functions, inputs, outputs, power domains, and hierarchy should be arranged before drawing.
---

# Plan an LCEDA Schematic Page

REQUIRED: apply `lceda-establish-schematic-style`. If execution will use MCP, also apply `lceda-adapt-mcp-tools` before mutation.

Read `references/page-planning-rubric.md` when naming/splitting pages, arranging hierarchy, or checking whether the page plan is ready to execute.

## Do not draw yet

Build a page intent model:
1. one sentence: “This page implements ___.”
2. external inputs/outputs and boundary side;
3. main functional chain(s);
4. power domains/references;
5. supporting blocks and their owners;
6. cross-page interfaces;
7. repeated channels/variants;
8. critical notes/test points.

If the page cannot be named in roughly 2–4 words, consider splitting it.

## Convert the functional graph into lanes

For each main chain, topologically order blocks and assign increasing X anchors:

`INPUT → CONDITIONING → PROCESSING → DRIVER → OUTPUT`

Reserve:
- a central main-signal lane;
- power/pull/reference lanes above;
- ground/pull-down/support lanes below;
- page-edge regions for external connectors;
- clear inter-block whitespace larger than block-internal spacing.

Bidirectional and feedback paths are explicit exceptions, not excuses for arbitrary placement.

## Plan orientation before coordinates

For every anchor device, record which pin group should face upstream, downstream, power/support, or boundary. During execution, actual LCEDA pin coordinates determine the final `0/90/180/270°` orientation.

## Decide abstraction before routing

- local causal topology → Wire;
- same-sheet non-local identity → Label when it reduces meaningless travel and label capability exists;
- cross-sheet/module → Port;
- power/ground → NetFlag/power symbol.

Do not assign arbitrary coordinates until current page/grid geometry is read. Output block order, lanes, anchors, boundary sides, intended pin-facing directions, and abstraction decisions.
