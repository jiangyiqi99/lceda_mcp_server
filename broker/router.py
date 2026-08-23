"""Request routing between stateless MCP tools and extension connections."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any

from broker.registry import ProjectRegistry
from protocol.rpc import RpcResponse, rpc_request


class BrokerError(RuntimeError):
    code = "BROKER_ERROR"


class ProjectOfflineError(BrokerError):
    code = "PROJECT_OFFLINE"


class CapabilityUnavailableError(BrokerError):
    code = "CAPABILITY_UNAVAILABLE"


class ExtensionTimeoutError(BrokerError):
    code = "EXTENSION_TIMEOUT"


class ExtensionRpcError(BrokerError):
    def __init__(self, code: str, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data


@dataclass(slots=True)
class PendingRequest:
    project_id: str
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
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending[request_id] = PendingRequest(project_id, future)
        try:
            async with connection.send_lock:
                await connection.websocket.send_json(
                    rpc_request(request_id, method, params or {})
                )
            try:
                return await asyncio.wait_for(future, timeout=self._timeout_seconds)
            except TimeoutError as exc:
                raise ExtensionTimeoutError(
                    f"extension timed out while handling {method!r}"
                ) from exc
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

