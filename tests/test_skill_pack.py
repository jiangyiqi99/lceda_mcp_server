from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

from broker.registry import ProjectRegistry
from broker.router import RequestRouter
from mcp_api.server import create_mcp_server


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
    for alias in ("READ_NET_LABELS", "CREATE_NET_LABEL", "MODIFY_NET_LABEL"):
        assert alias in adapt_skill
        assert f"`{alias}`" in capability_contract

    registry = ProjectRegistry()
    server = create_mcp_server(registry, RequestRouter(registry))
    tool_names = {tool.name for tool in server._tool_manager.list_tools()}
    assert {
        "schematic.get_info",
        "schematic.create_net_label",
        "schematic.modify_net_label",
    } <= tool_names

    manifest = _json(PACK / "manifest.json")
    assert manifest["policy"]["local_wire_four_plus_bends_fail"] is True

    bend_policy_paths = (
        PACK / "README.md",
        PACK / "REFINEMENT_NOTES.md",
        PACK / "examples" / "AGENTS.md.snippet",
        SKILLS / "lceda-beautify-schematic" / "SKILL.md",
        SKILLS
        / "lceda-beautify-schematic"
        / "references"
        / "cleanup-algorithm.md",
        SKILLS / "lceda-draw-readable-schematic" / "SKILL.md",
        SKILLS
        / "lceda-draw-readable-schematic"
        / "references"
        / "workflow-state-machine.md",
        SKILLS / "lceda-review-schematic" / "SKILL.md",
        SKILLS
        / "lceda-review-schematic"
        / "references"
        / "geometry-lint.md",
        SKILLS
        / "lceda-review-schematic"
        / "references"
        / "quality-gates.md",
        SKILLS / "lceda-route-schematic-wires" / "SKILL.md",
        SKILLS
        / "lceda-route-schematic-wires"
        / "references"
        / "label-route-decision-tree.md",
        SKILLS
        / "lceda-route-schematic-wires"
        / "references"
        / "wiring-patterns.md",
    )
    waiver_pattern = re.compile(
        r"^.*(?:4\+|>=4).*(?:unless\s+.*(?:unavoidable|exception)|"
        r"(?:may|can)\s+(?:be\s+)?(?:accepted|retained|passed|waived)).*$",
        re.IGNORECASE | re.MULTILINE,
    )
    for policy_path in bend_policy_paths:
        assert not waiver_pattern.search(policy_path.read_text(encoding="utf-8")), (
            f"4+ bend waiver in {policy_path.relative_to(PACK)}"
        )

    for review_path in (
        SKILLS / "lceda-review-schematic" / "SKILL.md",
        SKILLS
        / "lceda-review-schematic"
        / "references"
        / "quality-gates.md",
    ):
        assert "do not declare completion" in review_path.read_text(encoding="utf-8")


def test_checksums_cover_every_packaged_file_and_match() -> None:
    checksums = {}
    checksum_pattern = re.compile(r"([0-9a-f]{64})  (.+)")
    for line_number, line in enumerate(
        (PACK / "CHECKSUMS.txt").read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        match = checksum_pattern.fullmatch(line)
        assert match, f"malformed checksum line {line_number}"
        digest, relative_path = match.groups()
        assert relative_path not in checksums, f"duplicate checksum path {relative_path}"
        assert not Path(relative_path).is_absolute()
        assert ".." not in Path(relative_path).parts
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
    skill_dirs = sorted(path for path in SKILLS.iterdir() if path.is_dir())
    archive_paths = sorted((PACK / "individual-zips").glob("*.zip"))
    assert [path.stem for path in archive_paths] == [path.name for path in skill_dirs]

    for skill_dir, archive_path in zip(skill_dirs, archive_paths, strict=True):
        source_files = {
            path.relative_to(skill_dir).as_posix(): path.read_bytes()
            for path in skill_dir.rglob("*")
            if path.is_file()
        }

        with ZipFile(archive_path) as archive:
            member_names = [name for name in archive.namelist() if not name.endswith("/")]
            assert len(member_names) == len(set(member_names)), archive_path.name
            archived_files = {
                name: archive.read(name)
                for name in member_names
            }

        assert archived_files == source_files
