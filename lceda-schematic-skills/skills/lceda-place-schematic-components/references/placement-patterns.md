# Placement Patterns

## 1. Anchor hierarchy

Place in this order:
1. system-boundary connectors;
2. main ICs and major functional devices;
3. mandatory interface/protection devices;
4. supporting R/C/L/clock/reset components;
5. test points and notes.

Do not alternate “place one part → wire it → place next part”. That freezes bad early geometry.

## 2. Anchor / lane model

Represent every functional block with an anchor. Main-path anchors occupy a horizontal **lane** and should be monotonic in X. Supporting circuits use secondary lanes above/below their owner.

Recommended hierarchy:

```text
POWER / pull-up / reference lane
             ↓
INPUT → CONDITIONING → CORE → DRIVER → OUTPUT
             ↓
GND / pull-down / local return lane
```

Do not place an unrelated block inside the visual hull of another block.

## 3. Relationship distance

Treat visual distance as semantic distance:
- strong relationship → one compact local cluster;
- same block but weaker relationship → same region with a small gap;
- separate subsystem → gap clearly larger than the block-internal pitch or separate page.

A detached capacitor, pull resistor, termination, or feedback resistor is a placement defect even when electrically correct.

## 4. Orientation

Choose orientation from pin geometry, not from symbol bounding-box aesthetics. For each candidate `0/90/180/270°`, transform relevant pin positions around the component anchor and judge which side they occupy relative to their partners.

Defaults by role:
- two-terminal series R/L/fuse/FB on signal path → horizontal;
- decoupling capacitor → vertical, rail above and GND below;
- pull-up/pull-down → vertical;
- voltage-divider legs → vertical unless the project has a strong alternate convention;
- connector at left page boundary → circuit-facing pins point inward/right where symbol semantics allow;
- connector at right boundary → circuit-facing pins point inward/left;
- IC → input-oriented pin groups toward upstream, output groups toward downstream; support pins face their support lane when practical.

## 5. Pin escape reserve

Reserve a short clear orthogonal corridor from each actively wired pin before another component, text, branch, or unrelated wire. One major visual grid is a good default; dense symbols may need two.

This reduces pin-crowded junctions and makes later routing deterministic.

## 6. Repeated channel template

Choose one channel as canonical and copy:
- anchor offset;
- component orientation;
- local wire entry/exit points;
- label positions;
- reference/value offsets.

A repeated channel is allowed to differ only when the electrical function differs. Visual variation without electrical reason is a review defect.

## 7. Dense-page rescue

1. identify 3–8 functional groups;
2. move groups apart before moving individual passives;
3. align block anchors to lanes;
4. orient components from pin-facing score;
5. compress only within blocks;
6. re-evaluate whether one block belongs on another sheet.

## 8. Don't confuse schematic and PCB layout

Schematic placement communicates logic. Physical board position does not dictate schematic direction. Keep physical constraints as concise notes rather than bending logical flow.
