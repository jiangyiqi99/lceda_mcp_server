# Placement Patterns

## 1. Anchor hierarchy

Place in this order:
1. system-boundary connectors;
2. main ICs and major functional devices;
3. mandatory interface/protection devices;
4. supporting R/C/L/clock/reset components;
5. test points and notes.

Do not alternate “place one part → wire it → place next part”. That freezes bad early geometry.

## 2. Relationship distance

Treat visual distance as semantic distance:
- strong relationship: 1 local cluster;
- same block but weak relationship: same region with whitespace;
- separate subsystem: clear gap or separate page.

## 3. Orientation

Prefer orientations that make pin direction intuitive. For passives, use the same orientation for the same role across the page. For ICs, physical package pin order is irrelevant; the placed symbol's logical pin sides should drive orientation.

## 4. Repeated channels

Choose an anchor point per channel and duplicate:
- X/Y offset;
- component orientation;
- local wire entry/exit points;
- label positions;
- reference/value offsets.

Then deviations become intentional and reviewable.

## 5. Dense-page rescue

If a page is cluttered:
1. identify 3–8 functional groups;
2. move groups apart before individual parts;
3. align block anchors;
4. compress only within blocks;
5. re-evaluate whether one block deserves a separate sheet.

## 6. Don't confuse schematic and PCB layout

Schematic placement communicates logic. A connector's physical location on the PCB does not force it to appear on that side of the schematic. Keep layout constraints as concise notes instead of distorting logical flow.

## 7. Geometry heuristics

- Main-path X coordinates should generally be monotonic.
- Power/support branches should generally occupy Y above/below their owner.
- Avoid placing unrelated parts inside another block's convex visual area.
- Leave enough room around pins for a short orthogonal lead before a bend or branch.
