from __future__ import annotations

import json
import tomllib
from pathlib import Path

from install import (
    MCP_SERVER_NAME,
    ClientSpec,
    get_supported_clients,
    normalize_mcp_url,
    resolve_clients,
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


def test_url_normalization() -> None:
    assert normalize_mcp_url("http://localhost:8000") == "http://localhost:8000/mcp"
    assert normalize_mcp_url("https://example.test/custom/") == "https://example.test/custom"
