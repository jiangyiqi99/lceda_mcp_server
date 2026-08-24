"""Request routing between stateless MCP tools and extension connections."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

from broker.registry import ProjectRegistry
from protocol.rpc import RpcResponse, rpc_request


logger = logging.getLogger(__name__)


class BrokerError(RuntimeError):
    code = "BROKER_ERROR"


class ProjectOfflineError(BrokerError):
    code = "PROJECT_OFFLINE"


class CapabilityUnavailableError(BrokerError):
    code = "CAPABILITY_UNAVAILABLE"


class ExtensionTimeoutError(BrokerError):
    code = "EXTENSION_TIMEOUT"

    def __init__(
        self,
        *,
        method: str,
        request_id: str,
        project_id: str,
        project_name: str | None,
        extension_id: str,
        timeout_seconds: float,
        last_seen_seconds_ago: float,
    ) -> None:
        self.method = method
        self.request_id = request_id
        self.project_id = project_id
        self.project_name = project_name
        self.extension_id = extension_id
        self.timeout_seconds = timeout_seconds
        self.last_seen_seconds_ago = last_seen_seconds_ago
        project_label = project_name or project_id
        super().__init__(
            f"extension timed out after {timeout_seconds:.3f}s while handling "
            f"{method!r}; request_id={request_id}; project={project_label!r}; "
            f"extension_id={extension_id!r}; "
            f"last_heartbeat={last_seen_seconds_ago:.3f}s ago"
        )


class ExtensionRpcError(BrokerError):
    def __init__(self, code: str, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data


@dataclass(slots=True)
class PendingRequest:
    project_id: str
    method: str
    params: dict[str, Any]
    started_at: float
    future: asyncio.Future[Any]


class RequestRouter:
    def __init__(self, registry: ProjectRegistry, timeout_seconds: float = 30.0) -> None:
        self._registry = registry
        self._timeout_seconds = timeout_seconds
        self._pending: dict[str, PendingRequest] = {}

    async def request(
        self,
        project_id: str,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        capability: str | None = None,
    ) -> Any:
        connection = await self._registry.get(project_id)
        if connection is None:
            raise ProjectOfflineError(f"project {project_id!r} is not connected")
        if capability is not None and capability not in connection.capabilities:
            raise CapabilityUnavailableError(
                f"project {project_id!r} does not advertise {capability!r}"
            )

        request_id = str(uuid.uuid4())
        started_at = time.monotonic()
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        request_params = params or {}
        self._pending[request_id] = PendingRequest(
            project_id=project_id,
            method=method,
            params=request_params,
            started_at=started_at,
            future=future,
        )
        try:
            async with connection.send_lock:
                await connection.websocket.send_json(
                    rpc_request(request_id, method, request_params)
                )
            try:
                return await asyncio.wait_for(future, timeout=self._timeout_seconds)
            except TimeoutError as exc:
                last_seen_seconds_ago = max(0.0, time.monotonic() - connection.last_seen)
                error = ExtensionTimeoutError(
                    method=method,
                    request_id=request_id,
                    project_id=project_id,
                    project_name=connection.project_name,
                    extension_id=connection.extension_id,
                    timeout_seconds=self._timeout_seconds,
                    last_seen_seconds_ago=last_seen_seconds_ago,
                )
                logger.error(
                    "%s; elapsed=%.3fs; params=%r",
                    error,
                    time.monotonic() - started_at,
                    request_params,
                )
                raise error from exc
        finally:
            self._pending.pop(request_id, None)

    def resolve(self, response: RpcResponse) -> bool:
        pending = self._pending.get(response.id)
        if pending is None or pending.future.done():
            return False
        if response.success:
            pending.future.set_result(response.result)
        else:
            error = response.error or {}
            logger.error(
                "extension RPC failed; method=%s; request_id=%s; project_id=%s; "
                "code=%s; message=%r; data=%r; elapsed=%.3fs; params=%r",
                pending.method,
                response.id,
                pending.project_id,
                error.get("code", "EXTENSION_ERROR"),
                error.get("message", "extension request failed"),
                error.get("data"),
                time.monotonic() - pending.started_at,
                pending.params,
            )
            pending.future.set_exception(
                ExtensionRpcError(
                    code=str(error.get("code", "EXTENSION_ERROR")),
                    message=str(error.get("message", "extension request failed")),
                    data=error.get("data"),
                )
            )
        return True

    def cancel_project(self, project_id: str, reason: str) -> None:
        for pending in tuple(self._pending.values()):
            if pending.project_id == project_id and not pending.future.done():
                pending.future.set_exception(ProjectOfflineError(reason))
