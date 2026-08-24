# Annotation Patterns

## 1. Useful vs redundant information

Default passive display:
- reference;
- value.

Add tolerance/voltage/material/part-number only when that parameter is part of design intent. A deliberately displayed parameter should signal “review this”.

## 2. Expected values

Examples:

```text
TP3  VREF_1V25
Expected: 1.25 V ±2%
```

```text
RESET_N
Power-up: LOW ~10 ms, then HIGH
```

Expected values reduce future re-derivation and improve bring-up.

## 3. Local formulas

A compact formula can be useful near a feedback network, e.g. gain/divider relationship. Keep it short; full derivations belong in design documentation.

## 4. DNP / variant

Explicitly mark compatibility, debug-only, or normally-not-fitted parts without hiding their place in the functional circuit.

## 5. Critical PCB intent

Useful schematic notes include:
- place decoupling close to a specific pin;
- controlled differential/single-ended impedance;
- Kelvin sense;
- crystal loop constraint;
- keepout/routing constraint with functional reason.

Do not rearrange schematic geometry to mimic PCB placement; record physical constraints as notes.

## 6. Titles and visual paragraphs

Use block headings plus whitespace. Avoid a rectangle around every section. A frame should mean something.

## 7. Text orientation

Prefer readable 0° text. If an existing project has a consistent 90° side-text convention, preserve it sparingly. Avoid upside-down or mixed orientations.
