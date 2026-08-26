# Existing-Schematic Cleanup Algorithm

## Phase 0 — Snapshot

Capture, when supported:
- current Netlist/topology;
- DRC result;
- component IDs, x/y/rotation/mirror;
- pin geometry for moved components;
- wire IDs, polyline geometry, nets;
- labels/ports/text in target region.

Default mode is **geometry-only**.

## Phase 1 — Functional diagnosis

Identify page purpose, main chains, block ownership, repeated channels, and support ownership before judging coordinates.

## Phase 2 — Orientation pass

For each suspect part:
1. read current pins;
2. score orthogonal candidates;
3. choose best pin-facing/main-flow/support orientation;
4. modify one local group;
5. re-read pins and verify.

Reject arbitrary rotation/mirror used only to pack space.

## Phase 3 — Alignment/spacing pass

1. establish block anchors and main/support lanes;
2. align anchors to project rhythm/grid;
3. make main-chain X progression monotonic;
4. normalize repeated ΔX/ΔY;
5. reserve pin-escape corridors;
6. keep support parts attached to owners;
7. separate unrelated blocks with clearly larger gaps.

Do not touch wire abstraction yet.

## Phase 4 — Wiring/label pass

For each affected net:
1. read endpoints and explicit net identity;
2. choose Wire/Label/Port/NetFlag using the decision tree;
3. route Wire with straight pin escape and 0–2 bends target;
4. 3 bends require a real obstacle; `>=4` means reposition/re-abstract;
5. eliminate diagonal segments and collinear duplicate vertices;
6. reduce crossings and four-way junctions;
7. re-read wire `line` and `net`.

## Phase 5 — Text/document cleanup

Align labels, references, values, and short annotations after geometry is stable. Do not use text position to compensate for badly placed components.

## Phase 6 — Geometry lint

Count or inspect:
- diagonal segments;
- >=4-bend local wires;
- backtracking/U-turn routes;
- avoidable crossings;
- four-way junctions;
- wrong-facing role components;
- one-grid/one-lane alignment outliers;
- repeated-channel position/orientation deviations;
- label/text overlaps.

Fix causes, not counts.

## Phase 7 — Invariant verification

For geometry-only cleanup:
- pre/post Netlist equivalent;
- same relevant component identities/designators;
- no new DRC errors;
- no newly dangling intended pins/nets;
- repeated channels electrically equivalent where expected.

If an invariant fails, repair/revert the first changed batch before continuing.
