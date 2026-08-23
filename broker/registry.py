"""In-memory project connection registry."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Protocol


class WebSocketConnection(Protocol):
    async def send_json(self, data: Any) -> None: ...

    async def close(self, code: int = 1000, reason: str | None = None) -> None: ...


@dataclass(slots=True)
class ProjectConnection:
    project_id: str
    extension_id: str
    capabilities: frozenset[str]
    websocket: WebSocketConnection
    project_name: str | None = None
    project_uuid: str | None = None
    last_seen: float = field(default_factory=time.monotonic)
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class ProjectRegistry:
    """The broker's only project/connection state store."""

    def __init__(self, heartbeat_timeout_seconds: float = 30.0) -> None:
        self._projects: dict[str, ProjectConnection] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_timeout_seconds = heartbeat_timeout_seconds

    async def register(
        self,
        *,
        project_id: str,
        extension_id: str,
        capabilities: frozenset[str],
        websocket: WebSocketConnection,
        project_name: str | None = None,
        project_uuid: str | None = None,
    ) -> ProjectConnection | None:
        connection = ProjectConnection(
            project_id=project_id,
            extension_id=extension_id,
            capabilities=capabilities,
            websocket=websocket,
            project_name=project_name,
            project_uuid=project_uuid,
        )
        async with self._lock:
            previous = self._projects.get(project_id)
            self._projects[project_id] = connection
        return previous

    async def unregister(
        self, project_id: str, websocket: WebSocketConnection
    ) -> bool:
        async with self._lock:
            current = self._projects.get(project_id)
            if current is None or current.websocket is not websocket:
                return False
            del self._projects[project_id]
            return True

    async def touch(self, project_id: str, websocket: WebSocketConnection) -> bool:
        async with self._lock:
            current = self._projects.get(project_id)
            if current is None or current.websocket is not websocket:
                return False
            current.last_seen = time.monotonic()
            return True

    async def get(self, project_id: str) -> ProjectConnection | None:
        async with self._lock:
            connection = self._projects.get(project_id)
            if connection is None:
                return None
            if time.monotonic() - connection.last_seen > self._heartbeat_timeout_seconds:
                return None
            return connection

    async def list_projects(self) -> list[dict[str, Any]]:
        now = time.monotonic()
        async with self._lock:
            return [
                {
                    "project_id": connection.project_id,
                    "project_name": connection.project_name,
                    "project_uuid": connection.project_uuid,
                    "extension_id": connection.extension_id,
                    "capabilities": sorted(connection.capabilities),
                    "status": "online",
                    "last_seen_seconds_ago": round(now - connection.last_seen, 3),
                }
                for connection in self._projects.values()
                if now - connection.last_seen <= self._heartbeat_timeout_seconds
            ]

    async def remove_stale(self) -> list[ProjectConnection]:
        now = time.monotonic()
        async with self._lock:
            stale_ids = [
                project_id
                for project_id, connection in self._projects.items()
                if now - connection.last_seen > self._heartbeat_timeout_seconds
            ]
            return [self._projects.pop(project_id) for project_id in stale_ids]

