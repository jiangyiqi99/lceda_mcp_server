---
name: lceda-beautify-schematic
description: Use when an existing LCEDA schematic is electrically intended to remain the same but looks cluttered, inconsistent, hard to trace, poorly aligned, over-labeled, crossing-heavy, or visually unprofessional.
---

# Beautify an Existing LCEDA Schematic

REQUIRED: apply `lceda-adapt-mcp-tools`, `lceda-establish-schematic-style`, and `lceda-review-schematic`.

## Iron rule

**Beautification must not change electrical intent.** Before the first mutation, capture a topology baseline: Netlist if available, plus component/wire/net state for the affected region.

## Fix causes, not symptoms

Prioritize changes in this order:

1. functional grouping;
2. component orientation/placement;
3. alignment and block spacing;
4. local wire geometry;
5. crossing/junction cleanup;
6. label/port cleanup;
7. text/reference/value alignment;
8. short intent annotations.

If a wire needs many bends, move the parts before “routing prettier”. If the page is label soup, restore visible local topology rather than simply moving labels.

## Work in local batches

Beautify one block or one channel family at a time. After each batch, re-read geometry and compare affected topology. Do not perform a whole-sheet destructive rewrite unless explicitly requested and fully verifiable.

## Auto-layout policy

Whole-sheet `autoLayout`/`autoRouting` is disabled by default. It may be tried on a disposable/copy context or tightly scoped subset only when the result can be compared and selectively kept.

## Completion

Run the hard gates in `lceda-review-schematic`. If rendering/export is unavailable, report that visual checks were coordinate/structure-based rather than pretending to have viewed the rendered page.

Read `references/cleanup-algorithm.md` for the full pass order.
