from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
checks = {
    'placement_orientation_scoring': (
        root/'skills/lceda-place-schematic-components/SKILL.md',
        ['orientation candidate', 'pin-facing', '0/90/180/270']
    ),
    'placement_anchor_lanes': (
        root/'skills/lceda-place-schematic-components/references/placement-patterns.md',
        ['anchor', 'lane', 'monotonic', 'repeated channel']
    ),
    'routing_hard_bend_gate': (
        root/'skills/lceda-route-schematic-wires/SKILL.md',
        ['>=4', 'placement', 'pin escape']
    ),
    'routing_label_decision_tree': (
        root/'skills/lceda-route-schematic-wires/references/wiring-patterns.md',
        ['decision tree', 'same-sheet', 'cross-sheet', 'net flag']
    ),
    'lceda_units_and_pin_geometry': (
        root/'skills/lceda-adapt-mcp-tools/references/lceda-api-reference.md',
        ['10mil', 'getAllPinsByPrimitiveId', 'rotation', 'mirror']
    ),
    'wire_net_side_effect_warning': (
        root/'skills/lceda-adapt-mcp-tools/references/lceda-api-reference.md',
        ['specified net', 'follow', 'explicit']
    ),
    'beautify_three_pass': (
        root/'skills/lceda-beautify-schematic/SKILL.md',
        ['Orientation pass', 'Alignment/spacing pass', 'Wiring/label pass']
    ),
    'review_geometry_hard_gates': (
        root/'skills/lceda-review-schematic/references/quality-gates.md',
        ['diagonal', '4+ bends', 'wrong-facing', 'crossing']
    ),
}

failed=[]
for name,(path,needles) in checks.items():
    text=path.read_text(encoding='utf-8').lower()
    missing=[n for n in needles if n.lower() not in text]
    if missing:
        failed.append((name,path,missing))

if failed:
    print(f'FAIL: {len(failed)}/{len(checks)} refinement checks missing')
    for name,path,missing in failed:
        print(f'- {name}: {path.relative_to(root)} missing {missing}')
    sys.exit(1)
print(f'PASS: {len(checks)}/{len(checks)} geometry smoke checks')
