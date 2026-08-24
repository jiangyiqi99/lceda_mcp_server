from __future__ import annotations

import asyncio
from typing import Any

import pytest

from broker.registry import ProjectRegistry
from broker.router import (
    CapabilityUnavailableError,
    ExtensionRpcError,
    ExtensionTimeoutError,
    RequestRouter,
)
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


@pytest.mark.asyncio
async def test_router_timeout_contains_diagnostics(caplog: pytest.LogCaptureFixture) -> None:
    registry = ProjectRegistry()
    websocket = FakeWebSocket()
    await registry.register(
        project_id="board-a",
        extension_id="ext-a",
        capabilities=frozenset({"schematic"}),
        websocket=websocket,
        project_name="Demo board",
    )
    router = RequestRouter(registry, timeout_seconds=0.01)

    with pytest.raises(ExtensionTimeoutError) as caught:
        await router.request(
            "board-a",
            "schematic.create_net_label",
            {"net": "VDDA", "x": 10, "y": 20},
            capability="schematic",
        )

    message = str(caught.value)
    request_id = websocket.messages[0]["id"]
    assert "schematic.create_net_label" in message
    assert f"request_id={request_id}" in message
    assert "project='Demo board'" in message
    assert "extension_id='ext-a'" in message
    assert "last_heartbeat=" in message
    assert "VDDA" in caplog.text


@pytest.mark.asyncio
async def test_router_extension_error_contains_diagnostics(
    caplog: pytest.LogCaptureFixture,
) -> None:
    registry = ProjectRegistry()
    websocket = FakeWebSocket()
    await registry.register(
        project_id="board-a",
        extension_id="ext-a",
        capabilities=frozenset({"schematic"}),
        websocket=websocket,
    )
    router = RequestRouter(registry, timeout_seconds=1)

    request_task = asyncio.create_task(
        router.request(
            "board-a",
            "schematic.modify_net_label",
            {"primitive_id": "label-1", "side": "right"},
            capability="schematic",
        )
    )
    await asyncio.sleep(0)
    request_id = websocket.messages[0]["id"]
    assert router.resolve(
        RpcResponse(
            type="response",
            id=request_id,
            success=False,
            error={"code": "LABEL_MODIFY_FAILED", "message": "label not found"},
        )
    )
    with pytest.raises(ExtensionRpcError):
        await request_task

    assert "schematic.modify_net_label" in caplog.text
    assert request_id in caplog.text
    assert "LABEL_MODIFY_FAILED" in caplog.text
    assert "label-1" in caplog.text
