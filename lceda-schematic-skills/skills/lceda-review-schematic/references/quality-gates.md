# LCEDA Schematic Quality Gates

## Hard electrical/operation gates

### H1 — Topology invariant
For beautification: pre/post Netlist must be equivalent after normalizing irrelevant ordering/serialization differences.

### H2 — DRC regression
No new DRC errors. Existing errors must be identified separately; do not silently claim they were introduced or fixed.

### H3 — Verified mutations
Every write batch has a post-read or equivalent verification.

### H4 — No fabricated capability
No tool, UUID, enum, library ID, net, pin position, or result was invented.

## Visual score: 100 points

### 1. Signal flow — 20
- 18–20: main path obvious; exceptions (feedback/bidirectional) self-explanatory.
- 12–17: understandable with minor backtracking.
- <12: frequent reverse tracing or scattered path.

### 2. Wiring/topology visibility — 20
- short orthogonal local wires;
- minimal crossings;
- few bends;
- clear junctions;
- no label soup.

### 3. Grouping & whitespace — 15
- functional units visually coherent;
- unrelated blocks separated;
- no crowded islands or detached support parts.

### 4. Alignment & consistency — 15
- grid alignment;
- stable orientations;
- consistent label/ref/value offsets;
- repeated channels repeat visually.

### 5. Naming & abstraction — 10
- meaningful net names;
- project-consistent active-low/differential/clock/power syntax;
- correct use of label/port/power abstraction.

### 6. Power/support clarity — 10
- power domains visible;
- decoupling ownership clear;
- pull/termination/clock/reset support located near owners.

### 7. Documentation — 10
- concise block titles and intent notes;
- important expected values/variants/test points visible;
- no prose clutter.

**Pass target: ≥85**, but hard gates dominate the numeric score.

## Anti-gaming rules

Do not improve score by:
- deleting electrically required parts;
- hiding connections behind excessive labels;
- renaming nets away from established project convention;
- shrinking text below readable size;
- adding boxes/colors that only create decorative hierarchy;
- moving schematic items to mimic PCB physical layout.

## Optional rendered checks

When export/render is genuinely available:
- inspect zoom-to-fit architecture;
- inspect labels for overlap;
- inspect grayscale/black-white readability if possible;
- verify margins and page density.
