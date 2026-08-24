---
name: lceda-organize-power-support
description: Use when arranging or reviewing LCEDA schematic power rails, grounds, decoupling, pull resistors, clocks, resets, terminations, feedback networks, or other supporting circuits around a main device.
---

# Organize Power and Supporting Circuits

REQUIRED: apply `lceda-establish-schematic-style`; use `lceda-adapt-mcp-tools` for edits.

## Power is visible architecture

Show power relationships explicitly. Place positive rails above served circuitry and ground below; negative rails below ground where applicable. Do not hide multi-domain power intent merely to reduce visual objects.

## Decoupling belongs to an owner

Each local decoupling group must visibly belong to a device pin or power domain. Avoid a detached “capacitor graveyard”. Group bulk/local values by served domain, and keep annotations minimal but enough to identify the domain.

## Support parts stay local

- Pull-up/down near the signal/device whose default state they define.
- Series termination near the driver/source.
- Crystal/load network near clock pins.
- Feedback network near the regulator/op-amp and along its feedback path.
- Reset support near reset pin/path.

## Naming and project rules

Honor existing project naming for rails, active-low signals, differential pairs, and clocks. Do not import a company-specific `VCC*` rule or another source's naming convention unless this project explicitly uses it.

## Visual separation vs electrical association

Use whitespace to separate power blocks from the main signal lane, but do not move support components so far that ownership is unclear.

## Verification

After moving power/support parts, verify the same nets still serve the same pins. DRC and Netlist are the authority; aesthetic alignment is not.

Read `references/power-patterns.md` for common visual templates.
