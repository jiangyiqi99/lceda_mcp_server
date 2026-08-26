# Wiring Patterns

## 1. Geometry invariants

For a wire vertex sequence `(x0,y0)...(xn,yn)`:
- each adjacent pair must have `x_i == x_{i+1}` or `y_i == y_{i+1}`;
- zero-length segments are removed;
- collinear consecutive segments are merged;
- a main-flow connection should not reverse X direction without a clear feedback/return reason.

## 2. Pin escape

Good:

```text
PIN ─────┐
         │
         └──── target
```

Bad:

```text
PIN ┐┌─┐
    └┘ └── target
```

Keep the first segment straight and clear before a bend or branch.

## 3. Bend budget

Target 0–2 bends. Three bends require a concrete obstacle/clarity reason. Four or more bends are not a routing challenge; they are evidence that placement or abstraction is wrong.

## 4. Crossings

Decision order when a crossing appears:
1. move the relevant component/block;
2. shift a shared horizontal/vertical lane;
3. change branch topology;
4. use a meaningful label/port if the connection is genuinely non-local;
5. accept only an unavoidable, unambiguous crossing.

## 5. Junctions

Prefer a T:

```text
────●────
    │
```

Avoid a four-direction connected cross. A branch should occur after a short pin escape, not directly on the pin body.

## 6. Short local topology

Good:

```text
MCU ── R1 ──┬── ADC_IN
             │
             C1
             │
            GND
```

Bad: split MCU, R1, and C1 into disconnected label islands.

## 7. Long-distance same-sheet

Use a same-sheet label only when it removes meaningless travel across unrelated visual regions and preserves network identity. Keep label stubs short, orthogonal, aligned, and pointing outward from their functional block.

## 8. Cross-sheet

Use ports/off-page constructs with `IN`, `OUT`, or `BI` matching architectural direction. Do not use a port merely because it looks like a label.

## 9. Critical source-side series elements

Keep series termination visually adjacent to the driver. Do not name the tiny pre-resistor stub as though it were the post-termination routed network unless that is the project convention.

## 10. Netlist safety

For beautification, geometry may change only while endpoints/net identity remain equivalent. Compare pre/post Netlist rather than trusting visual contact.

## 11. Abstraction decision tree

The full **decision tree** lives in `label-route-decision-tree.md`: same-sheet non-local identity may use a real Net Label, cross-sheet connections use NetPort/off-page constructs, and power/ground use a **Net Flag**. Never substitute one construct merely because another capability is missing.
