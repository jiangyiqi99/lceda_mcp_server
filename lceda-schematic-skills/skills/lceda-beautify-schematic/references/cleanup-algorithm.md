# Existing-Schematic Cleanup Algorithm

## Phase 0 — Snapshot

Capture, when supported:
- current Netlist;
- DRC result;
- component IDs, positions, rotations;
- wire IDs, segment geometry, nets;
- labels/ports/text in target region.

Define whether the task is **geometry-only** or allows electrical corrections. Default is geometry-only.

## Phase 1 — Diagnose

Classify defects:
- mixed functions;
- bad signal direction;
- misplaced supporting parts;
- uneven spacing;
- one-grid misalignment;
- long wires;
- excess bends;
- crossings/four-way junctions;
- label soup;
- text collision;
- inconsistent repeated channels;
- overloaded page.

## Phase 2 — Move blocks

Move functional clusters before touching individual wire lanes. Preserve association between support parts and owners.

## Phase 3 — Align internals

Within each block:
- align component anchors;
- normalize repeated passive orientations;
- normalize label/reference/value offsets;
- leave pin escape room.

## Phase 4 — Rebuild only affected wires

Use short Manhattan paths. Avoid global re-route. Every deleted wire must have an explicit replacement plan tied to the same intended net/endpoints.

## Phase 5 — Reduce ambiguity

Remove avoidable crossings and four-way junctions. Replace genuinely long non-local wires with meaningful labels/ports only where topology remains understandable.

## Phase 6 — Documentation cleanup

Fix overlapping text, normalize hierarchy, add only high-value local notes. Remove decorative frames that convey no engineering boundary only if they are not part of project standard.

## Phase 7 — Invariant verification

For geometry-only cleanup:
- pre/post Netlist equivalent;
- same relevant component identities/designators;
- no new DRC errors;
- no newly dangling intended pins/nets;
- repeated channels still electrically equivalent where expected.

If any invariant fails, identify the first changed batch and repair/revert that batch before continuing.
