from __future__ import annotations

import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

from install import (
    CODEX_PLUGIN_NAME,
    MCP_SERVER_NAME,
    ClientSpec,
    _build_parser,
    get_supported_clients,
    normalize_mcp_url,
    resolve_clients,
    update_client_skills,
    update_codex_plugin,
    update_client,
)


def test_json_install_preserves_other_servers_and_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(
        json.dumps({"theme": "dark", "mcpServers": {"existing": {"url": "x"}}}),
        encoding="utf-8",
    )
    client = ClientSpec("Cursor", path)

    first = update_client(client, url="http://127.0.0.1:8000/mcp")
    second = update_client(client, url="http://127.0.0.1:8000/mcp")

    config = json.loads(path.read_text(encoding="utf-8"))
    assert first.status == "installed"
    assert second.status == "unchanged"
    assert config["theme"] == "dark"
    assert config["mcpServers"]["existing"] == {"url": "x"}
    assert config["mcpServers"][MCP_SERVER_NAME] == {
        "type": "http",
        "url": "http://127.0.0.1:8000/mcp",
    }


def test_vscode_uses_nested_server_map(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"editor.fontSize": 14}', encoding="utf-8")
    client = ClientSpec("VS Code", path, server_keys=("mcp", "servers"))

    result = update_client(client, url="http://localhost:9000/mcp")

    config = json.loads(path.read_text(encoding="utf-8"))
    assert result.status == "installed"
    assert MCP_SERVER_NAME in config["mcp"]["servers"]
    assert config["editor.fontSize"] == 14


def test_codex_toml_install_preserves_content_and_uninstalls(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    original = 'model = "gpt-5"\n\n[mcp_servers.other]\nurl = "http://other/mcp"\n'
    path.write_text(original, encoding="utf-8")
    client = ClientSpec("Codex", path, config_kind="toml", config_style="codex")

    installed = update_client(client, url="http://127.0.0.1:8000/mcp")
    parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    removed = update_client(client, uninstall=True)

    assert installed.status == "installed"
    assert parsed["model"] == "gpt-5"
    assert parsed["mcp_servers"]["other"]["url"] == "http://other/mcp"
    assert parsed["mcp_servers"][MCP_SERVER_NAME]["url"].endswith("/mcp")
    assert (
        parsed["mcp_servers"][MCP_SERVER_NAME]["default_tools_approval_mode"]
        == "approve"
    )
    assert removed.status == "removed"
    assert path.read_text(encoding="utf-8") == original


def test_invalid_json_is_not_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{ invalid", encoding="utf-8")

    result = update_client(ClientSpec("Example", path))

    assert result.status == "skipped"
    assert path.read_text(encoding="utf-8") == "{ invalid"


def test_detection_and_explicit_selection(tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir()
    supported = get_supported_clients(platform="linux", home=tmp_path, environ={})

    detected, unknown = resolve_clients(supported, [])
    explicit, explicit_unknown = resolve_clients(supported, ["cursor,not-real"])

    assert [client.name for client in detected] == ["Codex"]
    assert [client.name for client in explicit] == ["Cursor"]
    assert unknown == []
    assert explicit_unknown == ["not-real"]


def test_codex_and_claude_code_use_their_native_skill_delivery(tmp_path: Path) -> None:
    supported = get_supported_clients(platform="linux", home=tmp_path, environ={})
    clients = {client.name: client for client in supported}

    assert clients["Codex"].installs_codex_plugin is True
    assert clients["Codex"].skills_dir is None
    assert clients["Claude Code"].skills_dir == tmp_path / ".claude" / "skills"


def test_claude_code_skill_install_is_idempotent_and_uninstalls(tmp_path: Path) -> None:
    source = tmp_path / "source"
    skill = source / "lceda-example"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: lceda-example\ndescription: Test skill.\n---\n\nUse it.\n",
        encoding="utf-8",
    )
    client = ClientSpec(
        "Claude Code",
        tmp_path / ".claude.json",
        skills_dir=tmp_path / ".claude" / "skills",
    )

    first = update_client_skills(client, source_dir=source)
    second = update_client_skills(client, source_dir=source)
    removed = update_client_skills(client, source_dir=source, uninstall=True)

    assert first is not None and first.status == "installed"
    assert second is not None and second.status == "unchanged"
    assert removed is not None and removed.status == "removed"
    assert not (client.skills_dir / "lceda-example").exists()


def test_codex_plugin_bundles_mcp_and_skills_and_removes_legacy_config(
    tmp_path: Path, monkeypatch
) -> None:
    home = tmp_path / "home"
    config_path = home / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        f"[mcp_servers.{MCP_SERVER_NAME}]\nurl = \"http://legacy/mcp\"\n",
        encoding="utf-8",
    )
    client = ClientSpec(
        "Codex",
        config_path,
        config_kind="toml",
        config_style="codex",
        installs_codex_plugin=True,
    )
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

    monkeypatch.setattr(shutil, "which", lambda executable: f"/mock/{executable}")
    result = update_codex_plugin(
        client,
        url="http://localhost:9000/mcp",
        run_command=fake_run,
    )

    plugin_path = home / "plugins" / CODEX_PLUGIN_NAME
    mcp_config = json.loads((plugin_path / ".mcp.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (plugin_path / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        (home / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )

    assert result.status == "installed"
    assert mcp_config["mcpServers"][MCP_SERVER_NAME]["url"] == "http://localhost:9000/mcp"
    assert (
        mcp_config["mcpServers"][MCP_SERVER_NAME]["default_tools_approval_mode"]
        == "approve"
    )
    assert (plugin_path / "skills" / "lceda-draw-readable-schematic" / "SKILL.md").is_file()
    assert "+codex." in manifest["version"]
    assert marketplace["plugins"][0]["name"] == CODEX_PLUGIN_NAME
    assert commands == [
        [
            "/mock/codex",
            "plugin",
            "add",
            f"{CODEX_PLUGIN_NAME}@personal",
            "--json",
        ]
    ]
    assert MCP_SERVER_NAME not in tomllib.loads(config_path.read_text(encoding="utf-8")).get(
        "mcp_servers", {}
    )


def test_url_normalization() -> None:
    assert normalize_mcp_url("http://localhost:8000") == "http://localhost:8000/mcp"
    assert normalize_mcp_url("https://example.test/custom/") == "https://example.test/custom"


def test_install_is_the_default_action_without_an_install_flag() -> None:
    args = _build_parser().parse_args(["codex"])

    assert args.clients == ["codex"]
    assert args.uninstall is False
    with pytest.raises(SystemExit):
        _build_parser().parse_args(["--install", "codex"])
