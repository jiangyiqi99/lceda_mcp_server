# LCEDA Orientation and Grid Algorithm

This reference converts visual rules into coordinate operations that can be executed through LCEDA MCP/API capabilities.

## A. Coordinate model

LCEDA schematic coordinates use `0.01 inch = 10mil` per unit. Keep PCB and schematic units separate.

Determine a major visual grid `G`:
1. inspect existing component-anchor deltas and wire vertices;
2. preserve the project rhythm when clear;
3. for a new/default sheet, start with `G = 10` schematic units = 100mil for component anchors;
4. do not force pin endpoints off their native symbol coordinates simply to satisfy `G`.

## B. Build a pin-side model

For component anchor `(cx, cy)` and pin `(px, py)`, classify the pin side using the dominant vector `(px-cx, py-cy)`:
- `|dx| > |dy|`, `dx < 0` → LEFT;
- `|dx| > |dy|`, `dx > 0` → RIGHT;
- otherwise `dy < 0`/`dy > 0` → TOP/BOTTOM according to the editor coordinate convention observed from existing symbols.

Use `pin.rotation` as corroborating information, not the only source of truth, because library conventions may vary.

## C. Orientation candidate score

For each candidate orthogonal rotation, estimate:

`score = 6*partner_side + 4*main_flow + 3*power_semantics + 2*wire_simplicity + 2*repeat_consistency - penalties`

Where:
- `partner_side`: important signal pins lie on the side nearest their partner/block;
- `main_flow`: input/output groups support left→right flow;
- `power_semantics`: supply/ground-related pins support top/bottom support lanes;
- `wire_simplicity`: fewer bends and crossings are expected;
- `repeat_consistency`: matches canonical channel orientation.

Penalties:
- mirror without a real need: `-5`;
- important pin faces away from partner: `-6` each;
- series passive becomes vertical on a horizontal main path: `-4`;
- decoupling/pull branch becomes horizontal without reason: `-3`;
- candidate forces immediate U-turn/backtracking: `-6`.

Choose the highest score. If top candidates are near-equal, prefer no mirror and the project's established orientation.

## D. Placement pitch

Let `P` be the median nearest-neighbor distance of components inside one clean existing functional block. Use it as a local pitch reference.

- closely coupled parts: about `0.5P–1.0P`;
- sequential main-path devices: about `1.0P–2.0P` depending on symbol width;
- unrelated functional blocks: gap should visibly exceed internal pitch, commonly `>= 2P`.

This is a relative rule; do not force exact distances through another symbol's body or text.

## E. LCEDA write/read loop

For each placement batch:
1. read component + pins;
2. compute candidate transform;
3. `modify(primitiveId, {x,y,rotation,mirror})` through the mapped MCP/API capability;
4. re-read component + pins;
5. verify actual orientation/position;
6. only then route affected nets.

If pin geometry after modification does not match the assumed transform, stop using the assumption and derive from the returned pin coordinates.
