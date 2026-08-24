---
name: lceda-establish-schematic-style
description: Use when drawing, reviewing, or restyling LCEDA Pro schematics where readability, visual consistency, signal flow, grouping, or professional presentation matters.
---

# Establish LCEDA Schematic Style

## Core principle

A schematic is a **human-readable visual model of circuit intent**, not a prettier Netlist. Optimize first for comprehension, review, debug, and visual error detection; electrical correctness remains a hard constraint.

## Non-negotiable visual grammar

- Main signal/information flow: **left → right** by default.
- Positive supply/power domain: **above** the circuit; GND: **below**; negative rail below GND when relevant.
- Group by **function**, never by component type.
- Related parts form one visual unit; unrelated functions are separated by whitespace.
- Align to the editor/project grid. Never introduce a new arbitrary grid just for aesthetics.
- Prefer orthogonal orientation and text. A reader should not rotate their head to read the page.
- Use Wire for local topology, Label/Port for identity and distance.
- Target zero ambiguous crossings; prefer T-junctions over four-way junctions.
- Repeated channels use repeated geometry.
- Connector/protection/interface circuitry stays at the system boundary.

## Readability beats compactness

Do not fill empty space merely because it exists. Whitespace is a structural delimiter. Conversely, do not separate strongly related R/C/support parts so far that their relationship disappears.

## Consistency is an engineering tool

Keep reference/value placement, orientations, label offsets, channel spacing, and block-title styling stable. When repeated structures are visually identical, a missing part becomes conspicuous.

## Exceptions

Left-to-right is a default, not dogma. Feedback may naturally run right → left. Bidirectional buses may be centered. The exception must make the circuit *easier* to understand than strict compliance.

## Required reference

Read `references/visual-language.md` before making style judgments on a complex page.
