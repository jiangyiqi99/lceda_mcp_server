---
name: lceda-review-schematic
description: Use when an LCEDA schematic drawing or cleanup is about to be declared complete, or when a sheet needs checking for electrical regressions, readability defects, visual inconsistency, ambiguous routing, or review readiness.
---

# Review an LCEDA Schematic

REQUIRED: use live MCP/LCEDA reads when available. Do not grade a changed schematic solely from the plan that was intended.

## Hard gates

A page cannot pass if any applicable condition fails:

- geometry-only task changed the electrical Netlist/topology;
- new DRC errors appeared;
- intended connections became dangling/ambiguous;
- tool capability was missing but completion is claimed anyway;
- text overlaps critical circuit information;
- a mutation result was not re-read/verified.

For a new design, Netlist “equality” is not applicable; instead compare against the requested connectivity/specification.

## Visual score

Score the page with `references/quality-gates.md`. Target **≥85/100** with no hard-gate failure. Do not game the score by replacing visible topology with labels or removing necessary annotations.

## Reader tests

At zoom-to-fit/render, if available:
- 3-second test: page purpose is obvious;
- 30-second test: power source, inputs, outputs, core IC, interfaces, debug path can be identified quickly.

If no render/image capability exists, perform a structural proxy using coordinates, functional groups, wire geometry, and labels, and say that it is a proxy.

## Finish with evidence

Report what was checked: Netlist, DRC, affected regions, visual score, remaining exceptions. Never say “looks good” without stating the basis.
