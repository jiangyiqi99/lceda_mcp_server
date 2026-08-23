from __future__ import annotations

import pytest

from protocol.rpc import ProtocolError, Registration, parse_inbound_message


def test_parse_registration() -> None:
    message = parse_inbound_message(
        {
            "type": "register",
            "extension_id": "extension-1",
            "project_id": "board-a",
            "capabilities": ["pcb", "capture"],
        }
    )
    assert isinstance(message, Registration)
    assert message.project_id == "board-a"
    assert message.capabilities == frozenset({"pcb", "capture"})


def test_reject_invalid_capabilities() -> None:
    with pytest.raises(ProtocolError):
        parse_inbound_message(
            {
                "type": "register",
                "extension_id": "extension-1",
                "project_id": "board-a",
                "capabilities": "pcb",
            }
        )

