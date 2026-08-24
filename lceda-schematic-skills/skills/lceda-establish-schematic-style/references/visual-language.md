# Visual Language Reference

## 1. Two-dimensional syntax

Treat the page as a language with two dominant axes:

```text
                 POWER
                   ↓
INPUT → CONDITIONING → PROCESSING → OUTPUT
                   ↓
                  GND
```

Horizontal distance communicates system progression. Vertical position communicates supply/support relationship.

## 2. Functional grouping

A block is defined by the smallest set of components needed to understand a function. Examples:

- Buck: controller + input caps + bootstrap + switch/inductor + feedback + output caps.
- MCU reset: reset pin + pull resistor + button/supervisor + capacitor if used.
- CAN: MCU-side TX/RX + transceiver + termination/bias + protection + connector.
- Crystal: oscillator pins + crystal + load components + any damping resistor.

Do not move feedback resistors, protection devices, or decoupling to a “resistor/capacitor area.”

## 3. Whitespace

Whitespace belongs **between** blocks. Inside a block, strongly coupled elements should be close enough that the eye sees one unit. A page with 50–70% visual occupancy can be healthier than one filled to 95%; this is not a PCB placement problem.

## 4. Alignment

Create repeated visual rails:
- connector edges;
- component centers;
- reference/value baselines;
- net-label baselines;
- repeated channel anchors.

One-grid misalignments produce visual noise. Snap deliberately.

## 5. Wires

- Horizontal/vertical only unless the editor forces otherwise.
- Prefer 1–3 bends per local connection.
- Avoid crossings. If many are required, reconsider placement before routing harder.
- Prefer a T branch to a four-direction junction.
- Extend a short lead from a component pin before branching; do not build a junction directly on the pin when avoidable.

## 6. Wire vs Label vs Port

Use this mental model:

- **Wire = relationship/topology**: `MCU → Rseries → Flash CLK`.
- **Label = identity**: “this net is `SPI1_SCK`”.
- **Port = architectural boundary**: this signal crosses a sheet/module.
- **Power symbol/net flag = infrastructure**.

Avoid “Net Label Soup”, where every two-centimeter local connection is broken into labels and the visible topology disappears.

## 7. Symbols

A schematic symbol explains logical behavior, not package geography. Inputs naturally face inward from the left, outputs leave on the right, supplies belong to coherent power units/domains, and pins of the same peripheral stay adjacent when library editing is explicitly in scope.

Do not redesign a shared library symbol as a side effect of cleaning a sheet. Escalate it as a separate library-edit task.

## 8. Text

Use 2–3 hierarchy levels:
1. page title;
2. block title;
3. normal reference/value/net/note.

Avoid a typography zoo. Notes are short, local, and actionable. A displayed parameter should be displayed because it matters.

## 9. Quick visual anti-patterns

Reject or refactor:
- one giant sheet with unrelated functions;
- capacitor graveyard without power-domain association;
- physical-pin-order MCU/FPGA symbol that hides function;
- label soup;
- dense crossings;
- large boxes around every minor function;
- decorative color as primary information carrier;
- rotated labels and scattered reference/value text;
- repeated channels drawn with different geometry for no functional reason.

## 10. Three-second test

At zoom-to-fit, a reader should be able to answer “What is this page for?” from its structure. Fine values and pin numbers are zoom-in information; architecture is zoom-out information.
