"""Discover installed MCP clients and configure the JLCEDA MCP server.

Run this file directly from any directory::

    python /path/to/mcp_server/install.py

The backend is a shared Streamable HTTP service, so client configurations point
at its HTTP endpoint instead of spawning another backend process per client.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse, urlunparse


MCP_SERVER_NAME = "jlceda-ai-agent"
DEFAULT_MCP_URL = "http://127.0.0.1:8000/mcp"


@dataclass(frozen=True, slots=True)
class ClientSpec:
    """Location and JSON/TOML shape used by one supported MCP client."""

    name: str
    config_path: Path
    server_keys: tuple[str, ...] = ("mcpServers",)
    markers: tuple[Path, ...] = ()
    executables: tuple[str, ...] = ()
    config_kind: str = "json"
    config_style: str = "default"

    def is_detected(self) -> bool:
        return (
            self.config_path.is_file()
            or any(marker.exists() for marker in self.markers)
            or any(shutil.which(executable) for executable in self.executables)
        )


@dataclass(frozen=True, slots=True)
class InstallResult:
    client: str
    config_path: Path
    status: str
    detail: str = ""


def _path(base: Path, *parts: str) -> Path:
    return base.joinpath(*parts)


def get_supported_clients(
    *,
    platform: str | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[ClientSpec]:
    """Return global MCP client targets for the requested platform."""

    platform = platform or sys.platform
    environ = os.environ if environ is None else environ
    home = home or Path.home()
    kimi_home = Path(environ.get("KIMI_CODE_HOME", str(_path(home, ".kimi-code"))))

    if platform == "win32":
        appdata = Path(environ.get("APPDATA", str(_path(home, "AppData", "Roaming"))))
        code_user = _path(appdata, "Code", "User")
        insiders_user = _path(appdata, "Code - Insiders", "User")
        claude_dir = _path(appdata, "Claude")
        zed_dir = _path(appdata, "Zed")
    elif platform == "darwin":
        app_support = _path(home, "Library", "Application Support")
        code_user = _path(app_support, "Code", "User")
        insiders_user = _path(app_support, "Code - Insiders", "User")
        claude_dir = _path(app_support, "Claude")
        zed_dir = _path(app_support, "Zed")
    elif platform.startswith("linux"):
        config_home = Path(environ.get("XDG_CONFIG_HOME", str(_path(home, ".config"))))
        code_user = _path(config_home, "Code", "User")
        insiders_user = _path(config_home, "Code - Insiders", "User")
        claude_dir = _path(config_home, "Claude")
        zed_dir = _path(config_home, "zed")
    else:
        return []

    clients = [
        ClientSpec(
            "Cline",
            _path(
                code_user,
                "globalStorage",
                "saoudrizwan.claude-dev",
                "settings",
                "cline_mcp_settings.json",
            ),
            markers=(_path(code_user, "globalStorage", "saoudrizwan.claude-dev"),),
        ),
        ClientSpec(
            "Roo Code",
            _path(
                code_user,
                "globalStorage",
                "rooveterinaryinc.roo-cline",
                "settings",
                "mcp_settings.json",
            ),
            markers=(_path(code_user, "globalStorage", "rooveterinaryinc.roo-cline"),),
        ),
        ClientSpec(
            "Kilo Code",
            _path(
                code_user,
                "globalStorage",
                "kilocode.kilo-code",
                "settings",
                "mcp_settings.json",
            ),
            markers=(_path(code_user, "globalStorage", "kilocode.kilo-code"),),
        ),
        ClientSpec(
            "Claude Desktop",
            _path(claude_dir, "claude_desktop_config.json"),
            markers=(claude_dir,),
            config_style="claude",
        ),
        ClientSpec(
            "Claude Code",
            _path(home, ".claude.json"),
            markers=(_path(home, ".claude"),),
            executables=("claude",),
            config_style="claude",
        ),
        ClientSpec(
            "Cursor",
            _path(home, ".cursor", "mcp.json"),
            markers=(_path(home, ".cursor"),),
            executables=("cursor",),
        ),
        ClientSpec(
            "Windsurf",
            _path(home, ".codeium", "windsurf", "mcp_config.json"),
            markers=(_path(home, ".codeium", "windsurf"),),
            executables=("windsurf",),
        ),
        ClientSpec(
            "Codex",
            _path(home, ".codex", "config.toml"),
            markers=(_path(home, ".codex"),),
            executables=("codex",),
            config_kind="toml",
            config_style="codex",
        ),
        ClientSpec(
            "Kimi Code",
            _path(kimi_home, "mcp.json"),
            markers=(kimi_home,),
            executables=("kimi",),
        ),
        ClientSpec(
            "Zed",
            _path(zed_dir, "settings.json"),
            markers=(zed_dir,),
            executables=("zed",),
        ),
        ClientSpec(
            "Gemini CLI",
            _path(home, ".gemini", "settings.json"),
            markers=(_path(home, ".gemini"),),
            executables=("gemini",),
        ),
        ClientSpec(
            "Qwen Coder",
            _path(home, ".qwen", "settings.json"),
            markers=(_path(home, ".qwen"),),
            executables=("qwen",),
        ),
        ClientSpec(
            "GitHub Copilot CLI",
            _path(home, ".copilot", "mcp-config.json"),
            markers=(_path(home, ".copilot"),),
            executables=("copilot",),
        ),
        ClientSpec(
            "Amazon Q",
            _path(home, ".aws", "amazonq", "mcp_config.json"),
            markers=(_path(home, ".aws", "amazonq"),),
            executables=("q",),
        ),
        ClientSpec(
            "OpenCode",
            _path(home, ".config", "opencode", "opencode.json"),
            server_keys=("mcp",),
            markers=(_path(home, ".config", "opencode"),),
            executables=("opencode",),
            config_style="opencode",
        ),
        ClientSpec(
            "Kiro",
            _path(home, ".kiro", "mcp_config.json"),
            markers=(_path(home, ".kiro"),),
            executables=("kiro",),
        ),
        ClientSpec(
            "Trae",
            _path(home, ".trae", "mcp_config.json"),
            markers=(_path(home, ".trae"),),
            executables=("trae",),
        ),
        ClientSpec(
            "Warp",
            _path(home, ".warp", "mcp_config.json"),
            markers=(_path(home, ".warp"),),
            executables=("warp",),
        ),
        ClientSpec(
            "Antigravity IDE",
            _path(home, ".gemini", "config", "mcp_config.json"),
            markers=(_path(home, ".gemini", "config"),),
            config_style="antigravity",
        ),
        ClientSpec(
            "VS Code",
            _path(code_user, "settings.json"),
            server_keys=("mcp", "servers"),
            markers=(code_user,),
            executables=("code",),
        ),
        ClientSpec(
            "VS Code Insiders",
            _path(insiders_user, "settings.json"),
            server_keys=("mcp", "servers"),
            markers=(insiders_user,),
            executables=("code-insiders",),
        ),
        ClientSpec(
            "LM Studio",
            _path(home, ".lmstudio", "mcp.json"),
            markers=(_path(home, ".lmstudio"),),
        ),
    ]

    if platform == "darwin":
        app_support = _path(home, "Library", "Application Support")
        clients.extend(
            [
                ClientSpec(
                    "BoltAI",
                    _path(app_support, "BoltAI", "config.json"),
                    markers=(_path(app_support, "BoltAI"),),
                ),
                ClientSpec(
                    "Perplexity",
                    _path(app_support, "Perplexity", "mcp_config.json"),
                    markers=(_path(app_support, "Perplexity"),),
                ),
            ]
        )
    return clients


def normalize_mcp_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("MCP URL must be an absolute http:// or https:// URL")
    if parsed.query or parsed.fragment:
        raise ValueError("MCP URL must not contain a query string or fragment")
    path = parsed.path.rstrip("/")
    if not path:
        path = "/mcp"
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def make_server_config(client: ClientSpec, url: str) -> dict[str, Any]:
    if client.config_style == "codex":
        return {"url": url}
    if client.config_style == "opencode":
        return {"type": "remote", "url": url}
    if client.config_style == "antigravity":
        return {"type": "http", "serverUrl": url}
    return {"type": "http", "url": url}


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    old_mode = path.stat().st_mode if path.exists() else None
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        if old_mode is not None:
            os.chmod(temp_path, old_mode)
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("the top-level JSON value is not an object")
    return value


def _server_map(
    config: dict[str, Any], keys: tuple[str, ...], *, create: bool
) -> dict[str, Any] | None:
    current = config
    for key in keys:
        value = current.get(key)
        if value is None:
            if not create:
                return None
            value = {}
            current[key] = value
        if not isinstance(value, dict):
            raise ValueError(f"configuration key {'.'.join(keys)} is not an object")
        current = value
    return current


def _update_json(
    client: ClientSpec, *, url: str, uninstall: bool, dry_run: bool
) -> InstallResult:
    config = _read_json(client.config_path)
    servers = _server_map(config, client.server_keys, create=not uninstall)
    if servers is None or MCP_SERVER_NAME not in servers:
        if uninstall:
            return InstallResult(client.name, client.config_path, "unchanged", "not installed")
    if uninstall:
        assert servers is not None
        del servers[MCP_SERVER_NAME]
    else:
        assert servers is not None
        new_value = make_server_config(client, url)
        if servers.get(MCP_SERVER_NAME) == new_value:
            return InstallResult(client.name, client.config_path, "unchanged", "up to date")
        servers[MCP_SERVER_NAME] = new_value

    content = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    if not dry_run:
        _atomic_write(client.config_path, content)
    return InstallResult(
        client.name,
        client.config_path,
        "would remove" if dry_run and uninstall else "would install" if dry_run else "removed" if uninstall else "installed",
    )


_TOML_TARGET_HEADER = re.compile(
    r"^\s*\[\s*mcp_servers\s*\.\s*(?:jlceda-ai-agent|\"jlceda-ai-agent\"|'jlceda-ai-agent')\s*\]\s*(?:#.*)?$"
)
_TOML_ANY_HEADER = re.compile(r"^\s*\[\[?.*?\]\]?\s*(?:#.*)?$")


def _remove_toml_target_table(content: str) -> tuple[str, bool]:
    lines = content.splitlines(keepends=True)
    output: list[str] = []
    removing = False
    found = False
    for line in lines:
        if _TOML_TARGET_HEADER.match(line.rstrip("\r\n")):
            removing = True
            found = True
            while output and not output[-1].strip():
                output.pop()
            continue
        if removing and _TOML_ANY_HEADER.match(line.rstrip("\r\n")):
            removing = False
        if not removing:
            output.append(line)
    return "".join(output).rstrip() + ("\n" if output else ""), found


def _toml_has_target(config: dict[str, Any]) -> bool:
    servers = config.get("mcp_servers")
    return isinstance(servers, dict) and MCP_SERVER_NAME in servers


def _update_toml(
    client: ClientSpec, *, url: str, uninstall: bool, dry_run: bool
) -> InstallResult:
    content = client.config_path.read_text(encoding="utf-8") if client.config_path.exists() else ""
    try:
        parsed = tomllib.loads(content) if content.strip() else {}
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"invalid TOML: {error}") from error

    content_without_target, found_table = _remove_toml_target_table(content)
    if _toml_has_target(parsed) and not found_table:
        raise ValueError(
            "existing mcp_servers.jlceda-ai-agent uses an unsupported inline TOML form"
        )
    if uninstall and not found_table:
        return InstallResult(client.name, client.config_path, "unchanged", "not installed")

    if uninstall:
        new_content = content_without_target
    else:
        table = (
            f"[mcp_servers.{MCP_SERVER_NAME}]\n"
            f"url = {json.dumps(url, ensure_ascii=False)}\n"
            'default_tools_approval_mode = "approve"\n'
        )
        new_content = content_without_target.rstrip()
        new_content = f"{new_content}\n\n{table}" if new_content else table

    # Refuse to replace the user's file unless the generated TOML parses.
    tomllib.loads(new_content) if new_content.strip() else None
    if new_content == content:
        return InstallResult(client.name, client.config_path, "unchanged", "up to date")
    if not dry_run:
        _atomic_write(client.config_path, new_content)
    return InstallResult(
        client.name,
        client.config_path,
        "would remove" if dry_run and uninstall else "would install" if dry_run else "removed" if uninstall else "installed",
    )


def update_client(
    client: ClientSpec,
    *,
    url: str = DEFAULT_MCP_URL,
    uninstall: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    try:
        if client.config_kind == "toml":
            return _update_toml(client, url=url, uninstall=uninstall, dry_run=dry_run)
        return _update_json(client, url=url, uninstall=uninstall, dry_run=dry_run)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return InstallResult(client.name, client.config_path, "skipped", str(error))


def resolve_clients(
    supported: Sequence[ClientSpec], requested: Sequence[str]
) -> tuple[list[ClientSpec], list[str]]:
    if not requested:
        return [client for client in supported if client.is_detected()], []

    aliases = {
        "claude": "claude desktop",
        "claude-code": "claude code",
        "vscode": "vs code",
        "vscode-insiders": "vs code insiders",
        "copilot": "github copilot cli",
        "gemini": "gemini cli",
        "qwen": "qwen coder",
        "opencode": "opencode",
        "antigravity": "antigravity ide",
    }
    by_name = {client.name.casefold(): client for client in supported}
    selected: list[ClientSpec] = []
    unknown: list[str] = []
    requested_names = [
        name.strip()
        for value in requested
        for name in value.split(",")
        if name.strip()
    ]
    for value in requested_names:
        key = aliases.get(value.strip().casefold(), value.strip().casefold())
        client = by_name.get(key)
        if client is None:
            matches = [item for name, item in by_name.items() if key in name]
            client = matches[0] if len(matches) == 1 else None
        if client is None:
            unknown.append(value)
        elif client not in selected:
            selected.append(client)
    return selected, unknown


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auto-detect MCP clients and configure the JLCEDA AI Agent server."
    )
    parser.add_argument(
        "clients",
        nargs="*",
        metavar="CLIENT",
        help="configure named clients instead of auto-detecting (for example: codex cursor)",
    )
    parser.add_argument("--url", default=DEFAULT_MCP_URL, help="Streamable HTTP MCP URL")
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--install",
        action="store_true",
        help="install this MCP server (the default action)",
    )
    action.add_argument(
        "--uninstall", action="store_true", help="remove this MCP server"
    )
    parser.add_argument("--dry-run", action="store_true", help="show changes without writing files")
    parser.add_argument("--list", action="store_true", help="list supported clients and detection status")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        url = normalize_mcp_url(args.url)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    supported = get_supported_clients()
    if not supported:
        print(f"Unsupported platform: {sys.platform}", file=sys.stderr)
        return 2

    if args.list:
        print("Supported MCP clients:")
        for client in supported:
            status = "found" if client.is_detected() else "not found"
            print(f"  {client.name:<22} {status:<9} {client.config_path}")
        return 0

    selected, unknown = resolve_clients(supported, args.clients)
    if unknown:
        print(f"Unknown client(s): {', '.join(unknown)}", file=sys.stderr)
        print("Use --list to see supported names.", file=sys.stderr)
        return 2
    if not selected:
        print("No supported MCP clients were detected.")
        print("Use --list to inspect targets, or pass a client name explicitly.")
        return 0

    changed = 0
    skipped = 0
    for client in selected:
        result = update_client(
            client,
            url=url,
            uninstall=args.uninstall,
            dry_run=args.dry_run,
        )
        detail = f" ({result.detail})" if result.detail else ""
        print(f"{result.status.capitalize():<13} {result.client}\n  {result.config_path}{detail}")
        if result.status in {"installed", "removed", "would install", "would remove"}:
            changed += 1
        elif result.status == "skipped":
            skipped += 1

    if changed and not args.dry_run:
        print("Restart the updated MCP client(s) for the change to take effect.")
    return 1 if skipped else 0


if __name__ == "__main__":
    raise SystemExit(main())
