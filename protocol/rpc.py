"""Validation helpers for the JSON messages sent by the EDA extension."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


class ProtocolError(ValueError):
    """Raised when an extension sends an invalid protocol message."""


@dataclass(frozen=True, slots=True)
class Registration:
    type: Literal["register"]
    extension_id: str
    project_id: str
    capabilities: frozenset[str]
    project_name: str | None = None
    project_uuid: str | None = None


@dataclass(frozen=True, slots=True)
class Heartbeat:
    type: Literal["heartbeat"]
    project_id: str


@dataclass(frozen=True, slots=True)
class RpcResponse:
    type: Literal["response"]
    id: str
    success: bool
    result: Any = None
    error: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class Event:
    type: Literal["event"]
    event: str
    project_id: str
    data: Any = None


InboundMessage = Registration | Heartbeat | RpcResponse | Event


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError(f"{key} must be a non-empty string when provided")
    return value.strip()


def parse_inbound_message(data: Any) -> InboundMessage:
    if not isinstance(data, dict):
        raise ProtocolError("message must be a JSON object")

    message_type = data.get("type")
    if message_type == "register":
        raw_capabilities = data.get("capabilities")
        if not isinstance(raw_capabilities, list) or not all(
            isinstance(item, str) and item.strip() for item in raw_capabilities
        ):
            raise ProtocolError("capabilities must be an array of non-empty strings")
        return Registration(
            type="register",
            extension_id=_required_string(data, "extension_id"),
            project_id=_required_string(data, "project_id"),
            capabilities=frozenset(item.strip() for item in raw_capabilities),
            project_name=_optional_string(data, "project_name"),
            project_uuid=_optional_string(data, "project_uuid"),
        )
    if message_type == "heartbeat":
        return Heartbeat(
            type="heartbeat", project_id=_required_string(data, "project_id")
        )
    if message_type == "response":
        success = data.get("success")
        if not isinstance(success, bool):
            raise ProtocolError("success must be a boolean")
        error = data.get("error")
        if error is not None and not isinstance(error, dict):
            raise ProtocolError("error must be an object")
        return RpcResponse(
            type="response",
            id=_required_string(data, "id"),
            success=success,
            result=data.get("result"),
            error=error,
        )
    if message_type == "event":
        return Event(
            type="event",
            event=_required_string(data, "event"),
            project_id=_required_string(data, "project_id"),
            data=data.get("data"),
        )
    raise ProtocolError(f"unsupported message type: {message_type!r}")


def rpc_request(request_id: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": request_id,
        "type": "request",
        "method": method,
        "params": params,
    }

