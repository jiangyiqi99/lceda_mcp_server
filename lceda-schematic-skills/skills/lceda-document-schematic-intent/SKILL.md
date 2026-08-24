---
name: lceda-document-schematic-intent
description: Use when an LCEDA schematic needs clearer net names, block titles, design-intent notes, expected values, DNP/variant notes, test-point meaning, critical layout constraints, or page hierarchy labels.
---

# Document Schematic Intent

REQUIRED: keep annotation subordinate to circuit structure. A schematic is not a slide deck or essay.

## Name for meaning

Important nets should answer “what does this signal do?” Use stable, concise project syntax. Do not expose generated names such as `NetU3_27` when a meaningful architectural name exists.

## Keep reference/value placement stable

Use a consistent pattern for references and values. Display only information useful for understanding or review. Manufacturer, package, tolerance, voltage rating, etc. belong in properties/BOM unless the parameter is electrically significant enough to deserve emphasis.

## Notes record intent

Good notes are short, local, and actionable, such as:
- expected voltage/timing;
- gain or divider relationship;
- boot/config state;
- DNP/variant behavior;
- “place close to pin X”;
- impedance/Kelvin/critical routing constraint.

Do not write paragraphs that force reviewers to read prose before understanding the circuit.

## Test points are semantic objects

Label test points by function/net and, when useful, expected value. This turns the schematic into a bring-up/debug map.

## Visual hierarchy

Prefer page title + block titles + normal labels. Use rectangles only when they convey a real boundary: isolation, safety, variant, or another engineering domain.

Read `references/annotation-patterns.md` before annotating a large sheet.
