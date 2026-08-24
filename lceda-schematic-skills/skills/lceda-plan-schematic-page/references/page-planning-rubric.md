# Page Planning Rubric

## A. Page theme

Good names: `Power_Input`, `MCU_Core`, `USB`, `Ethernet_PHY`, `CAN_Interface`, `Sensors`, `Debug`.

Bad names: `Sheet2`, `Circuit_B`, or pages mixing power + MCU + all connectors just to reduce page count.

## B. System map first for complex projects

A useful top page is an architectural map whose blocks correspond to lower-level pages. A reader should understand the system before implementation detail.

## C. Region planning

Recommended conceptual layout:

```text
┌────────────────────────────────────────────┐
│ Page title                                 │
│                                            │
│ INPUT       PROCESSING          OUTPUT     │
│ [block] →   [block] → [block] → [block]   │
│                                            │
│          Supporting / power block          │
│                                            │
│ Notes                            title area │
└────────────────────────────────────────────┘
```

Exact geometry depends on the editor and symbol sizes; the pattern is conceptual, not a coordinate mandate.

## D. Graph-derived ordering

For each main signal chain:
1. classify components into functional blocks;
2. identify source/sink direction;
3. topologically order blocks when possible;
4. place bidirectional/shared blocks centrally;
5. place feedback near the block it closes, even if it runs right→left.

## E. Supporting block attachment

Every support block should have a clear owner:
- decoupling → supply pin/domain;
- pull-up/down → controlled signal/receiver;
- termination → driver/receiver depending topology;
- oscillator → clock pins;
- reset → reset pin/system reset path;
- ESD/protection → external boundary.

If ownership is unclear, placement will become arbitrary.

## F. Hierarchy boundary test

Split into another page when one or more are true:
- page has multiple independent narratives;
- long unrelated wires cross central regions;
- zoom-to-fit no longer reveals function;
- a block has enough internal detail to hide the system path;
- cross-page interfaces are cleaner than keeping everything visible.

## G. Planning acceptance

A plan is ready when another engineer could predict where to look for:
- source power;
- main inputs;
- main outputs;
- core IC;
- external interfaces;
- debug/test points.
