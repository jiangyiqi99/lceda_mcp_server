---
name: lceda-organize-power-support
description: Use when arranging or reviewing LCEDA schematic power rails, grounds, decoupling, pull resistors, clocks, resets, terminations, feedback networks, or other supporting circuits around a main device.
---

# Organize Power and Supporting Circuits

REQUIRED: apply style + placement; use MCP adaptation for edits.

## Power/support has a default axis

Use vertical semantics unless circuit function demands otherwise:
- positive rail/reference above;
- served node/device in the middle;
- ground below;
- negative rail below ground when applicable.

Role defaults:
- decoupling capacitor vertical;
- pull-up/down vertical;
- divider branches vertical;
- series termination horizontal with the signal path and close to source;
- feedback path arranged compactly around the device it closes;
- crystal/load network adjacent to oscillator pins with minimal crossing.

These are defaults, not license to rotate against actual pin geometry. Use the placement skill's candidate scoring.

## Ownership

Every support component must have an obvious owner. Do not create capacitor/resistor graveyards. If a support part is visually closer to an unrelated circuit than to its owner, placement is suspect.

## Verification

After moves, re-read served pins/nets. Geometry cannot prove the supply or default-state connection; Netlist/DRC remain authoritative.
