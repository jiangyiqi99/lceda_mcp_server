---
name: lceda-plan-schematic-page
description: Use when starting a new LCEDA schematic page, splitting an overloaded sheet, or deciding how functions, inputs, outputs, power domains, and hierarchy should be arranged before drawing.
---

# Plan an LCEDA Schematic Page

REQUIRED: apply `lceda-establish-schematic-style`. If the plan will be executed through MCP, also apply `lceda-adapt-mcp-tools` before mutation.

## Do not draw yet

First produce a **page intent model**:

1. one sentence: “This page implements ___.”
2. external inputs and where they enter;
3. external outputs and where they leave;
4. main functional chain(s);
5. power domains and references;
6. supporting blocks;
7. cross-page interfaces;
8. repeated channels/variants;
9. critical notes/test points.

If the page cannot be described in roughly 2–4 words, consider splitting it.

## Build a functional graph

Represent the main path as a simple ordered graph, for example:

`USB-C → ESD → USB-UART → MCU`

Assign main blocks increasing X coordinates. Assign supply/support relations by Y: power above, local support adjacent, ground below.

## Allocate visual regions

Use whitespace, not decorative boxes, as the default boundary. Reserve margins around the sheet. Give the main signal path the central visual lane. Put external connectors on page edges; supporting circuits should not interrupt the main reading path.

## Decide connection abstraction

Before wiring, classify connections:

- local within a block → Wire;
- medium/long same-sheet identity → Label where it reduces noise;
- cross-sheet/module → Port;
- power infrastructure → net flag/power symbol.

## Output of this skill

The plan must list block order, rough regions/anchors, I/O sides, cross-page nets, and any exceptions to left→right/top→bottom. Do not place arbitrary coordinates until the actual editor grid and existing page geometry are known.

Read `references/page-planning-rubric.md` for complex pages.
