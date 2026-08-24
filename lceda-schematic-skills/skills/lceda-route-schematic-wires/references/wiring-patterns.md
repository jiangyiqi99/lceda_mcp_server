# Wiring Patterns

## 1. Bend budget

A local wire should usually use 0–3 bends. Four or more bends are a warning that placement or abstraction is wrong.

## 2. Crossings

Decision order when a crossing appears:
1. move one component/block;
2. shift a wire lane;
3. change branch topology;
4. use a meaningful label/port if the connection is genuinely non-local;
5. accept a crossing only when alternatives reduce clarity.

Never add labels solely to “win” a crossing metric if topology becomes harder to see.

## 3. Junctions

Prefer:

```text
────●────
    │
```

over a four-direction connected cross. Avoid visually ambiguous non-connected crossings.

## 4. Short local topology

Good:

```text
MCU ── R1 ──┬── ADC_IN
             │
             C1
             │
            GND
```

Bad: split `MCU`, `R1`, `C1` into separate label islands.

## 5. Long-distance same sheet

Use labels when long wires merely traverse unrelated blocks. Place label stubs at logical block edges and align them consistently.

## 6. Cross-page

Use ports/off-page constructs with direction consistent with signal flow. Port names should be stable architectural interface names.

## 7. Naming examples

Common readable forms include:
- `UART1_TX`, `UART1_RX`
- `SPI1_SCK`, `SPI1_MOSI`, `SPI1_MISO`, `SPI1_CS_N`
- `I2C1_SCL`, `I2C1_SDA`
- `ETH_TX_P`, `ETH_TX_N`
- `RESET_N`, `INT_N`

These are examples, not permission to rename an established project.

## 8. Critical source-side series elements

When a series termination is part of signal intent, keep the resistor visually adjacent to the driver and name the net on the post-resistor side according to the project convention. This both reveals the termination and avoids misleading identity before it.

## 9. Netlist safety

Geometry can change without electrical change only if endpoints/net identity remain equivalent. For beautification, compare pre/post Netlist rather than inferring correctness from visual contact alone.
