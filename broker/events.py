"""Bounded in-memory buffer for events emitted by connected EDA extensions."""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BufferedEvent:
    sequence: int
    event: str
    data: Any


class EventBuffer:
    def __init__(self, max_events_per_project: int = 1000) -> None:
        self._events: dict[str, deque[BufferedEvent]] = defaultdict(
            lambda: deque(maxlen=max_events_per_project)
        )
        self._sequences: dict[str, int] = defaultdict(int)
        self._condition = asyncio.Condition()

    async def append(self, project_id: str, event: str, data: Any) -> BufferedEvent:
        async with self._condition:
            self._sequences[project_id] += 1
            item = BufferedEvent(self._sequences[project_id], event, data)
            self._events[project_id].append(item)
            self._condition.notify_all()
            return item

    async def poll(
        self,
        project_id: str,
        after_sequence: int = 0,
        limit: int = 100,
        timeout_seconds: float = 0,
    ) -> dict[str, Any]:
        def available() -> list[BufferedEvent]:
            return [
                event
                for event in self._events[project_id]
                if event.sequence > after_sequence
            ][:limit]

        async with self._condition:
            items = available()
            if not items and timeout_seconds > 0:
                try:
                    await asyncio.wait_for(
                        self._condition.wait_for(lambda: bool(available())),
                        timeout=timeout_seconds,
                    )
                except TimeoutError:
                    pass
                items = available()
            latest = self._sequences[project_id]
        return {
            "events": [
                {"sequence": item.sequence, "event": item.event, "data": item.data}
                for item in items
            ],
            "latest_sequence": latest,
        }
