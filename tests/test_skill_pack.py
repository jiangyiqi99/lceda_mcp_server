from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "lceda-schematic-skills"
SKILLS = PACK / "skills"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_plugin_metadata_and_manifest_are_consistent() -> None:
    plugin = _json(PACK / ".codex-plugin" / "plugin.json")
    manifest = _json(PACK / "manifest.json")
    skill_dirs = sorted(path.name for path in SKILLS.iterdir() if path.is_dir())

    assert plugin["name"] == manifest["name"]
    assert plugin["version"] == manifest["version"]
    assert manifest["skills"] == skill_dirs


def test_every_packaged_reference_is_routed_from_its_skill() -> None:
    reference_pattern = re.compile(r"references/[A-Za-z0-9._-]+\.md")

    for skill_dir in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        routed = set(reference_pattern.findall(skill_text))
        packaged = {
            path.relative_to(skill_dir).as_posix()
            for path in (skill_dir / "references").glob("*.md")
        }

        assert routed == packaged, (
            f"{skill_dir.name}: missing routes={sorted(packaged - routed)}, "
            f"broken routes={sorted(routed - packaged)}"
        )


def test_label_capabilities_and_strict_bend_policy_are_declared() -> None:
    adapt_skill = (
        SKILLS / "lceda-adapt-mcp-tools" / "SKILL.md"
    ).read_text(encoding="utf-8")
    capability_contract = (
        SKILLS
        / "lceda-adapt-mcp-tools"
        / "references"
        / "mcp-capability-contract.md"
    ).read_text(encoding="utf-8")
    server_tools = (ROOT / "mcp_api" / "tools.py").read_text(encoding="utf-8")

    for alias in ("READ_NET_LABELS", "CREATE_NET_LABEL", "MODIFY_NET_LABEL"):
        assert alias in adapt_skill
        assert f"`{alias}`" in capability_contract

    assert 'name="schematic.create_net_label"' in server_tools
    assert 'name="schematic.modify_net_label"' in server_tools

    manifest = _json(PACK / "manifest.json")
    assert manifest["policy"]["local_wire_four_plus_bends_fail"] is True

    review_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            SKILLS / "lceda-review-schematic" / "SKILL.md",
            SKILLS
            / "lceda-review-schematic"
            / "references"
            / "quality-gates.md",
        )
    )
    assert "unless explicitly documented as unavoidable" not in review_text
    assert "unless an explicit documented exception" not in review_text
    assert review_text.count("A written rationale does not waive this gate.") == 2


def test_checksums_cover_every_packaged_file_and_match() -> None:
    checksums = {}
    for line in (PACK / "CHECKSUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, relative_path = line.split("  ", 1)
        checksums[relative_path] = digest

    packaged = {
        path.relative_to(PACK).as_posix()
        for path in PACK.rglob("*")
        if path.is_file() and path.name != "CHECKSUMS.txt"
    }
    assert set(checksums) == packaged

    for relative_path, expected_digest in checksums.items():
        actual_digest = hashlib.sha256((PACK / relative_path).read_bytes()).hexdigest()
        assert actual_digest == expected_digest, relative_path


def test_each_skill_archive_matches_its_source_directory() -> None:
    for skill_dir in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
        archive_path = PACK / "individual-zips" / f"{skill_dir.name}.zip"
        source_files = {
            path.relative_to(skill_dir).as_posix(): path.read_bytes()
            for path in skill_dir.rglob("*")
            if path.is_file()
        }

        with ZipFile(archive_path) as archive:
            archived_files = {
                name: archive.read(name)
                for name in archive.namelist()
                if not name.endswith("/")
            }

        assert archived_files == source_files
