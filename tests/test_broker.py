from __future__ import annotations

import asyncio
from typing import Any

import pytest

from broker.registry import ProjectRegistry
from broker.router import CapabilityUnavailableError, RequestRouter
from protocol.rpc import RpcResponse


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def send_json(self, data: Any) -> None:
        self.messages.append(data)

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        return None


@pytest.mark.asyncio
async def test_router_round_trip() -> None:
    registry = ProjectRegistry()
    websocket = FakeWebSocket()
    await registry.register(
        project_id="board-a",
        extension_id="ext-a",
        capabilities=frozenset({"pcb"}),
        websocket=websocket,
    )
    router = RequestRouter(registry, timeout_seconds=1)

    request_task = asyncio.create_task(
        router.request("board-a", "pcb.get_info", capability="pcb")
    )
    await asyncio.sleep(0)
    request_id = websocket.messages[0]["id"]
    assert router.resolve(
        RpcResponse(type="response", id=request_id, success=True, result={"ok": True})
    )
    assert await request_task == {"ok": True}


@pytest.mark.asyncio
async def test_router_checks_capability() -> None:
    registry = ProjectRegistry()
    websocket = FakeWebSocket()
    await registry.register(
        project_id="board-a",
        extension_id="ext-a",
        capabilities=frozenset({"schematic"}),
        websocket=websocket,
    )
    router = RequestRouter(registry)
    with pytest.raises(CapabilityUnavailableError):
        await router.request("board-a", "pcb.get_info", capability="pcb")

