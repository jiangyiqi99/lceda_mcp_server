#!/usr/bin/env python3
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
errors = []


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


skill_dirs = sorted(path for path in SKILLS.iterdir() if path.is_dir())
for directory in skill_dirs:
    skill_file = directory / "SKILL.md"
    if not skill_file.exists():
        errors.append(f"{directory.name}: missing SKILL.md")
        continue

    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{directory.name}: missing YAML frontmatter")
        continue

    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{directory.name}: malformed frontmatter")
        continue

    frontmatter = parts[1]
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.M)
    description_match = re.search(r"^description:\s*(.+)$", frontmatter, re.M)
    if not name_match or not description_match:
        errors.append(f"{directory.name}: name/description required")
        continue

    name = name_match.group(1).strip()
    description = description_match.group(1).strip()
    if name != directory.name:
        errors.append(f"{directory.name}: frontmatter name {name!r} != directory")
    if not re.fullmatch(r"[A-Za-z0-9-]+", name):
        errors.append(f"{directory.name}: invalid skill name")
    if not description.startswith("Use when"):
        errors.append(f"{directory.name}: description must start with 'Use when'")
    if len(("name: " + name + "\ndescription: " + description).encode()) > 1024:
        errors.append(f"{directory.name}: frontmatter fields exceed 1024 bytes")

    body = parts[2]
    for alias in ["READ_COMPONENTS(", "CREATE_WIRE(", "PLACE_COMPONENT(", "READ_NETLIST("]:
        if alias in body:
            errors.append(f"{directory.name}: semantic alias appears callable: {alias}")

    routed_references = set(re.findall(r"references/[A-Za-z0-9._-]+\.md", text))
    packaged_references = {
        path.relative_to(directory).as_posix()
        for path in (directory / "references").glob("*.md")
    }
    for relative_path in sorted(routed_references - packaged_references):
        errors.append(f"{directory.name}: missing referenced file {relative_path}")
    for relative_path in sorted(packaged_references - routed_references):
        errors.append(f"{directory.name}: packaged reference is not routed: {relative_path}")


manifest = load_json("manifest.json")
plugin = load_json(".codex-plugin/plugin.json")
skill_names = [path.name for path in skill_dirs]
if manifest.get("skills") != skill_names:
    errors.append("manifest skills do not match packaged skill directories")
if plugin.get("name") != manifest.get("name"):
    errors.append("plugin and manifest names differ")
if plugin.get("version") != manifest.get("version"):
    errors.append("plugin and manifest versions differ")


adapt_skill = (SKILLS / "lceda-adapt-mcp-tools" / "SKILL.md").read_text(
    encoding="utf-8"
)
capability_contract = (
    SKILLS
    / "lceda-adapt-mcp-tools"
    / "references"
    / "mcp-capability-contract.md"
).read_text(encoding="utf-8")
for alias in ("READ_NET_LABELS", "CREATE_NET_LABEL", "MODIFY_NET_LABEL"):
    if alias not in adapt_skill or f"`{alias}`" not in capability_contract:
        errors.append(f"Net Label capability is not fully mapped: {alias}")


if manifest.get("policy", {}).get("local_wire_four_plus_bends_fail") is not True:
    errors.append("manifest must declare local 4+ bend routes as failures")
bend_policy_paths = (
    ROOT / "README.md",
    ROOT / "REFINEMENT_NOTES.md",
    ROOT / "examples" / "AGENTS.md.snippet",
    SKILLS / "lceda-beautify-schematic" / "SKILL.md",
    SKILLS / "lceda-beautify-schematic" / "references" / "cleanup-algorithm.md",
    SKILLS / "lceda-draw-readable-schematic" / "SKILL.md",
    SKILLS
    / "lceda-draw-readable-schematic"
    / "references"
    / "workflow-state-machine.md",
    SKILLS / "lceda-review-schematic" / "SKILL.md",
    SKILLS / "lceda-review-schematic" / "references" / "geometry-lint.md",
    SKILLS / "lceda-review-schematic" / "references" / "quality-gates.md",
    SKILLS / "lceda-route-schematic-wires" / "SKILL.md",
    SKILLS
    / "lceda-route-schematic-wires"
    / "references"
    / "label-route-decision-tree.md",
    SKILLS / "lceda-route-schematic-wires" / "references" / "wiring-patterns.md",
)
waiver_pattern = re.compile(
    r"^.*(?:4\+|>=4).*(?:unless\s+.*(?:unavoidable|exception)|"
    r"(?:may|can)\s+(?:be\s+)?(?:accepted|retained|passed|waived)).*$",
    re.IGNORECASE | re.MULTILINE,
)
for policy_path in bend_policy_paths:
    if waiver_pattern.search(policy_path.read_text(encoding="utf-8")):
        errors.append(
            f"strict local 4+ bend gate has a waiver in {policy_path.relative_to(ROOT)}"
        )
for review_path in (
    SKILLS / "lceda-review-schematic" / "SKILL.md",
    SKILLS / "lceda-review-schematic" / "references" / "quality-gates.md",
):
    if "do not declare completion" not in review_path.read_text(encoding="utf-8"):
        errors.append(
            f"strict local 4+ bend gate lacks completion behavior in "
            f"{review_path.relative_to(ROOT)}"
        )


checksum_path = ROOT / "CHECKSUMS.txt"
checksums = {}
checksum_pattern = re.compile(r"([0-9a-f]{64})  (.+)")
for line_number, line in enumerate(
    checksum_path.read_text(encoding="utf-8").splitlines(), start=1
):
    match = checksum_pattern.fullmatch(line)
    if not match:
        errors.append(f"malformed checksum line {line_number}")
        continue
    digest, relative_path = match.groups()
    if relative_path in checksums:
        errors.append(f"duplicate checksum path {relative_path}")
        continue
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"unsafe checksum path {relative_path}")
        continue
    checksums[relative_path] = digest
packaged_files = {
    path.relative_to(ROOT).as_posix()
    for path in ROOT.rglob("*")
    if path.is_file() and path != checksum_path
}
for relative_path in sorted(packaged_files - set(checksums)):
    errors.append(f"checksum missing for {relative_path}")
for relative_path in sorted(set(checksums) - packaged_files):
    errors.append(f"checksum references missing file {relative_path}")
for relative_path, expected_digest in checksums.items():
    path = ROOT / relative_path
    if path.exists() and sha256(path.read_bytes()).hexdigest() != expected_digest:
        errors.append(f"checksum mismatch for {relative_path}")


archive_paths = sorted((ROOT / "individual-zips").glob("*.zip"))
archive_names = [path.stem for path in archive_paths]
if archive_names != skill_names:
    errors.append("individual ZIP set does not match manifest skills")

for directory in skill_dirs:
    archive_path = ROOT / "individual-zips" / f"{directory.name}.zip"
    if not archive_path.exists():
        errors.append(f"{directory.name}: missing individual ZIP")
        continue
    source_files = {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }
    with ZipFile(archive_path) as archive:
        member_names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(member_names) != len(set(member_names)):
            errors.append(f"{directory.name}: individual ZIP has duplicate members")
        archived_files = {
            name: archive.read(name)
            for name in member_names
        }
    if archived_files != source_files:
        errors.append(f"{directory.name}: individual ZIP differs from skill source")


if errors:
    print("FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print(f"OK: {len(skill_dirs)} skills and package integrity validated")
