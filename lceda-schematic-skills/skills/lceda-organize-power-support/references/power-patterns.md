# Power and Support Visual Patterns

## 1. Rail stack

```text
        +12V / +5V / +3V3
               │
        local power circuit
               │
              GND
```

A reader should understand relative potential before reading every label.

## 2. Decoupling service group

```text
U1 power domain
VDD ───── +3V3
  │
  ├─ Cx 100n ─ GND
  └─ Cy 1u   ─ GND
```

Exact topology follows the actual design; the visual point is ownership. For multiple pins, group by power domain and annotate only where association could be ambiguous.

## 3. Pull state

Show the pull resistor as part of the signal's story, preferably vertically toward its rail:

```text
 +3V3
   │
  Rpull
   │
RESET_N ── device pin
```

## 4. Source termination

```text
driver ── Rseries ── SIGNAL_NAME ── receiver
```

The series element is visibly tied to the source. Avoid hiding it in a passive-component cluster.

## 5. Clock/reset

Clock and reset are architectural signals. Keep their source, optional conditioning/termination, and destination clear. Name clocks meaningfully and retain frequency information when that is the project convention.

## 6. Feedback

Feedback is a legitimate right→left exception. Arrange it so the loop is visually obvious instead of forcing the path into the left→right rule.

## 7. Multi-domain IC

For complex ICs, power pins should be visible by domain. If the library uses a separate power unit, place that unit near its decoupling groups and label domains clearly. Never alter the shared symbol automatically as part of page cleanup.
