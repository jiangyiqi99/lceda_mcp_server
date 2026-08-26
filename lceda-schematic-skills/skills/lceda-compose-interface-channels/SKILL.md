---
name: lceda-compose-interface-channels
description: Use when drawing or cleaning LCEDA external interfaces, connectors, ESD/protection chains, transceivers, filters, repeated sensor/ADC channels, or other structurally repeated circuitry.
---

# Compose Interfaces and Repeated Channels

REQUIRED: apply planning, placement, routing, and review skills.

Read `references/interface-patterns.md` when the task includes differential pairs, connector fanout, isolation boundaries, variants, or repeated analog channels.

## Boundary geometry

Keep external connectors on the page edge. Orient them so circuit-facing pins point inward where the symbol permits; do not leave the active pins facing the page boundary and compensate with U-turn wires.

Build a readable chain:

`Connector ↔ Protection/Termination ↔ Transceiver/Conditioning ↔ System Logic`

For primarily input interfaces, this naturally reads left→right from the external boundary. For outputs, preserve the same spatial chain even when signal direction is opposite.

## Protection and termination

Keep ESD/TVS/filter/termination directly attached to the interface chain. Series elements follow the horizontal main lane; shunt/return protection branches are normally vertical toward their reference/ground.

## Repeated channels

Choose one canonical channel and copy exact relative geometry:
- component rotations/mirror state;
- ΔX/ΔY;
- wire bend topology;
- label-stub direction/offset;
- annotation offsets.

Any visual deviation must correspond to a real electrical difference. This makes missing parts and wrong values visually obvious.

## Bidirectional interfaces

USB/Ethernet/CAN/GPIO may be bidirectional; do not force fake one-way semantics. Keep P/N or TX/RX ordering stable and the interface chain spatially coherent.
