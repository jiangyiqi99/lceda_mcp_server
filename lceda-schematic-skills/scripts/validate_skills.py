#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
errors = []

for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
    f = d / "SKILL.md"
    if not f.exists():
        errors.append(f"{d.name}: missing SKILL.md")
        continue
    text = f.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{d.name}: missing YAML frontmatter")
        continue
    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{d.name}: malformed frontmatter")
        continue
    fm = parts[1]
    name_m = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc_m = re.search(r"^description:\s*(.+)$", fm, re.M)
    if not name_m or not desc_m:
        errors.append(f"{d.name}: name/description required")
        continue
    name = name_m.group(1).strip()
    desc = desc_m.group(1).strip()
    if name != d.name:
        errors.append(f"{d.name}: frontmatter name {name!r} != directory")
    if not re.fullmatch(r"[A-Za-z0-9-]+", name):
        errors.append(f"{d.name}: invalid skill name")
    if not desc.startswith("Use when"):
        errors.append(f"{d.name}: description must start with 'Use when'")
    if len(("name: "+name+"\ndescription: "+desc).encode()) > 1024:
        errors.append(f"{d.name}: frontmatter fields exceed 1024 bytes")
    # Catch a common failure: pretending semantic aliases are real MCP tool calls.
    body = parts[2]
    for alias in ["READ_COMPONENTS(", "CREATE_WIRE(", "PLACE_COMPONENT(", "READ_NETLIST("]:
        if alias in body:
            errors.append(f"{d.name}: semantic alias appears callable: {alias}")

required = {
    "lceda-establish-schematic-style": "references/visual-language.md",
    "lceda-adapt-mcp-tools": "references/mcp-capability-contract.md",
    "lceda-plan-schematic-page": "references/page-planning-rubric.md",
    "lceda-place-schematic-components": "references/placement-patterns.md",
    "lceda-route-schematic-wires": "references/wiring-patterns.md",
    "lceda-organize-power-support": "references/power-patterns.md",
    "lceda-compose-interface-channels": "references/interface-patterns.md",
    "lceda-document-schematic-intent": "references/annotation-patterns.md",
    "lceda-beautify-schematic": "references/cleanup-algorithm.md",
    "lceda-review-schematic": "references/quality-gates.md",
    "lceda-draw-readable-schematic": "references/workflow-state-machine.md",
}
for skill, rel in required.items():
    if not (SKILLS/skill/rel).exists():
        errors.append(f"{skill}: missing {rel}")

if errors:
    print("FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print(f"OK: {len(required)} skills validated")
