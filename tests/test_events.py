from __future__ import annotations

import pytest

from broker.events import EventBuffer


@pytest.mark.asyncio
async def test_event_buffer_sequences_and_filters() -> None:
    events = EventBuffer(max_events_per_project=3)
    await events.append("board-a", "schematic.changed", {"step": 1})
    await events.append("board-a", "eda.api_event", {"step": 2})

    result = await events.poll("board-a", after_sequence=1)

    assert result["latest_sequence"] == 2
    assert result["events"] == [
        {
            "sequence": 2,
            "event": "eda.api_event",
            "data": {"step": 2},
        }
    ]
