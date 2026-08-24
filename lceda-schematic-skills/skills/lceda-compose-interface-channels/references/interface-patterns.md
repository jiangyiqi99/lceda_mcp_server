# Interface and Repeated-Channel Patterns

## 1. Generic external interface

```text
INTERNAL LOGIC ↔ TRANSCEIVER ↔ FILTER/PROTECTION ↔ CONNECTOR
```

For a mostly input path, mirror semantic direction only if that improves reading; keep overall page conventions stable.

## 2. System boundary semantics

A connector is not “just another component”. Its placement says “inside vs outside”. Protection closest to that boundary makes its role obvious.

## 3. Repeated analog channels

```text
CH1 → R → node → ADC1
          │
          C
          │
         GND

CH2 → R → node → ADC2
          │
          C
          │
         GND
```

Use equal offsets. If CH3 intentionally differs, add a concise local note if the reason is not obvious.

## 4. Differential pairs

Keep P/N or +/− signals adjacent and parallel in visual order. Use one naming convention throughout the project. Do not allow labels to swap visual order between transmitter and receiver unless pin arrangement forces it; if forced, route clearly without ambiguous crossings.

## 5. Connector pin fanout

Create short, aligned stubs from connector pins. Group related nets. Avoid a dense comb that immediately crosses itself; use labels/ports at a sensible boundary if necessary.

## 6. Isolation/safety boundaries

This is one of the cases where a rectangle or explicit boundary note can add information. Label the boundary with its meaning (e.g. isolation domain), not decoration.

## 7. Variants

When channels or interface parts are DNP/configurable, keep their normal placement in the functional chain and annotate the variant locally. Do not exile optional components to a corner, which hides the intended alternate topology.
