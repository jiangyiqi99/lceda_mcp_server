"""Starlette WebSocket endpoint and heartbeat monitor."""

from __future__ import annotations

import asyncio
import logging

from starlette.websockets import WebSocket, WebSocketDisconnect

from broker.events import EventBuffer
from broker.registry import ProjectRegistry
from broker.router import RequestRouter
from protocol.rpc import Event, Heartbeat, ProtocolError, Registration, RpcResponse
from protocol.rpc import parse_inbound_message

logger = logging.getLogger(__name__)


class WebSocketBroker:
    def __init__(
        self,
        registry: ProjectRegistry,
        router: RequestRouter,
        events: EventBuffer,
        *,
        registration_timeout_seconds: float = 5.0,
        heartbeat_check_seconds: float = 5.0,
    ) -> None:
        self.registry = registry
        self.router = router
        self.events = events
        self.registration_timeout_seconds = registration_timeout_seconds
        self.heartbeat_check_seconds = heartbeat_check_seconds

    async def endpoint(self, websocket: WebSocket) -> None:
        await websocket.accept()
        current_project_id: str | None = None
        try:
            raw = await asyncio.wait_for(
                websocket.receive_json(), timeout=self.registration_timeout_seconds
            )
            first_message = parse_inbound_message(raw)
            if not isinstance(first_message, Registration):
                raise ProtocolError("the first message must be register")
            current_project_id = await self._register(websocket, first_message, None)

            while True:
                try:
                    message = parse_inbound_message(await websocket.receive_json())
                except ProtocolError as exc:
                    await websocket.send_json(
                        {
                            "type": "protocol_error",
                            "error": {"code": "INVALID_MESSAGE", "message": str(exc)},
                        }
                    )
                    continue

                if isinstance(message, Registration):
                    current_project_id = await self._register(
                        websocket, message, current_project_id
                    )
                elif isinstance(message, Heartbeat):
                    touched = await self.registry.touch(message.project_id, websocket)
                    await websocket.send_json(
                        {
                            "type": "heartbeat_ack",
                            "project_id": message.project_id,
                            "registered": touched,
                        }
                    )
                elif isinstance(message, RpcResponse):
                    if not self.router.resolve(message):
                        logger.warning(
                            "Ignoring late or unknown extension response; request_id=%s; "
                            "project_id=%s; success=%s",
                            message.id,
                            current_project_id,
                            message.success,
                        )
                elif isinstance(message, Event):
                    await self.registry.touch(message.project_id, websocket)
                    await self.events.append(message.project_id, message.event, message.data)
                    logger.debug("EDA event %s from %s", message.event, message.project_id)
        except TimeoutError:
            await websocket.close(code=4408, reason="registration timeout")
        except ProtocolError as exc:
            await websocket.close(code=4400, reason=str(exc)[:120])
        except WebSocketDisconnect:
            pass
        finally:
            if current_project_id is not None:
                removed = await self.registry.unregister(current_project_id, websocket)
                if removed:
                    self.router.cancel_project(
                        current_project_id, "extension disconnected"
                    )

    async def _register(
        self,
        websocket: WebSocket,
        registration: Registration,
        previous_project_id: str | None,
    ) -> str:
        if previous_project_id and previous_project_id != registration.project_id:
            removed = await self.registry.unregister(previous_project_id, websocket)
            if removed:
                self.router.cancel_project(previous_project_id, "extension changed project")

        replaced = await self.registry.register(
            project_id=registration.project_id,
            extension_id=registration.extension_id,
            capabilities=registration.capabilities,
            websocket=websocket,
            project_name=registration.project_name,
            project_uuid=registration.project_uuid,
        )
        if replaced is not None and replaced.websocket is not websocket:
            self.router.cancel_project(
                registration.project_id, "connection replaced by a newer extension"
            )
            try:
                await replaced.websocket.close(code=4001, reason="connection replaced")
            except RuntimeError:
                pass

        await websocket.send_json(
            {"type": "registered", "project_id": registration.project_id}
        )
        return registration.project_id

    async def monitor_heartbeats(self) -> None:
        while True:
            await asyncio.sleep(self.heartbeat_check_seconds)
            for connection in await self.registry.remove_stale():
                self.router.cancel_project(connection.project_id, "heartbeat timed out")
                try:
                    await connection.websocket.close(
                        code=4000, reason="heartbeat timed out"
                    )
                except RuntimeError:
                    pass
