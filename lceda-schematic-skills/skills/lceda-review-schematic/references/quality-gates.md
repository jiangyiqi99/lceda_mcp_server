# LCEDA Schematic Quality Gates

## Hard electrical/operation gates

### H1 — Topology invariant
For geometry-only beautification, pre/post Netlist must be equivalent after irrelevant ordering differences are normalized.

### H2 — DRC regression
No new DRC errors.

### H3 — Verified mutations
Every write batch has post-read verification.

### H4 — No fabricated capability
No tool, UUID, enum, library ID, net, pin position, or result was invented.

## Hard geometry gates

### G1 — Orthogonality
`diagonal segment count = 0`.

### G2 — Bend complexity
Local wires with **4+ bends = 0**, unless an explicit documented exception survives review. Three-bend wires are warnings.

### G3 — Orientation
`wrong-facing role component count = 0` for connectors/main-path passives/pull-decoupling branches and other components with an obvious role direction, unless intentionally exceptional.

### G4 — Junction ambiguity
Avoidable four-way connected junctions = 0. Pin-crowded branches without an escape stub are defects.

### G5 — Repetition
Repeated channels have no unexplained rotation, mirror, spacing, label-offset, or topology-layout outliers.

### G6 — Collision
Critical text/label/component/wire collisions = 0.

### G7 — Crossing discipline
Avoidable crossing count = 0. Every retained crossing has a reason; “routing was easier” is not a reason.

## Visual score: 100 points

### 1. Signal flow — 20
- main path reads naturally;
- main-chain anchors progress monotonically where semantics permit;
- feedback/bidirectional exceptions are clear.

### 2. Wiring/topology visibility — 20
- short orthogonal wires;
- 0–2 bend norm;
- straight pin escapes;
- minimal crossings;
- clear T-junctions;
- no Net Label Soup.

### 3. Grouping & whitespace — 15
- strong relationships cluster;
- unrelated blocks separate;
- support ownership is obvious.

### 4. Alignment & consistency — 15
- stable grid/lanes;
- role-consistent orientation;
- repeated channels use common ΔX/ΔY and offsets.

### 5. Naming & abstraction — 10
- meaningful project-consistent names;
- Wire/Label/Port/NetFlag selection matches scope.

### 6. Power/support clarity — 10
- power above, ground below where practical;
- decoupling/pull/termination/clock/reset networks remain visibly attached to owners.

### 7. Documentation — 10
- concise titles/intent notes;
- important expected values/variants/test points visible;
- no prose or decorative clutter.

**Target >=90 after refinement.** Hard gates dominate the score.
