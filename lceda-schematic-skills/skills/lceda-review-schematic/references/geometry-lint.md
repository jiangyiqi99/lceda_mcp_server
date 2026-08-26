# LCEDA Geometry Lint

This is a structural review that can be performed from returned LCEDA coordinates even without a rendered screenshot.

## 1. Wire orthogonality

For every adjacent polyline vertex pair, flag if both X and Y change.

## 2. Bend count

Normalize a wire first:
- remove duplicate consecutive vertices;
- merge collinear segments.

Then `bends = normalized_segments - 1`.
- 0–2: normal;
- 3: warning;
- >=4: fail for local route.

## 3. Backtracking

For main left→right routes, flag repeated X direction changes (`+ → - → +`) unless the net is a deliberate feedback/return path. Similar logic applies to vertical support branches.

## 4. Crossings

For axis-aligned segments, detect horizontal/vertical intersections. Exclude intentional shared endpoints/junctions. Classify remaining intersections as:
- connected junction;
- non-connected visual crossing;
- avoidable crossing needing relocation/lane/label review.

## 5. Pin escape

Flag when a branch, junction, or first bend occurs essentially at the component outline/pin origin instead of after a clear straight escape, when geometry allows one.

## 6. Wrong-facing components

Use component anchor + actual pin locations + functional partner direction. Flag a role component when the majority of relevant pins are on the side away from their partners and another orthogonal rotation would materially simplify routing.

For passives:
- series main-path element should normally align with the main route axis;
- decoupling/pull/divider branch should normally align vertically with rail/ground semantics.

## 7. Alignment outliers

Within each declared row/column/lane, compare anchor coordinates to the median. A one-grid outlier with no electrical reason is a defect, not harmless noise.

## 8. Repeated-channel drift

Choose a canonical channel. Compare every peer for:
- component orientation/mirror;
- relative ΔX/ΔY;
- wire bend topology;
- label stub orientation/offset;
- reference/value placement.

A difference must map to an electrical difference or be corrected.

## 9. Label economy

Flag both extremes:
- long wires traversing unrelated blocks where a same-sheet label would reduce noise;
- local causal chains fragmented into labels so topology disappears.

Use the routing skill's decision tree rather than a raw “more/fewer labels” count.
