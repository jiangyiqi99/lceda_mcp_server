---
name: lceda-compose-interface-channels
description: Use when drawing or cleaning LCEDA external interfaces, connectors, ESD/protection chains, transceivers, filters, repeated sensor/ADC channels, or other structurally repeated circuitry.
---

# Compose Interfaces and Repeated Channels

REQUIRED: apply the style, planning, placement, and routing skills relevant to the page.

## Interfaces form a readable chain

Place boundary circuitry so a reader can trace, without searching the page:

`System logic ↔ Transceiver/Conditioning ↔ Protection/Termination ↔ Connector`

or the reverse direction when the interface is primarily an input. The external connector remains near the page/system boundary.

## Keep protection attached to the boundary

ESD/TVS/filter/termination parts should remain visually associated with the interface they protect or condition. Do not scatter them into generic diode/resistor sections.

## Repeated channels are visual templates

Choose one channel as the canonical pattern. Duplicate its topology, spacing, orientation, label position, and annotation placement across channels. Differences must be explainable by circuit function.

## Bidirectional interfaces

For USB, Ethernet, CAN, GPIO, or other bidirectional links, do not force all arrows into a fake one-way narrative. Keep the connector at the edge and arrange TX/RX or P/N nets consistently so the block still reads as one coherent interface.

## Review benefit

Symmetry is a functional review aid. A missing filter cap, termination, or pull resistor should look visually wrong.

Read `references/interface-patterns.md` for templates and exception handling.
