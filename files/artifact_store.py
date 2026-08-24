"""Ephemeral exported files with TTL cleanup and bounded storage."""

from __future__ import annotations

import asyncio
import re
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    artifact_id: str
    path: Path
    media_type: str
    filename: str
    created_at: float


class TemporaryArtifactStore:
    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self._root = Path(tempfile.mkdtemp(prefix="jlceda-ai-artifacts-"))
        self._ttl_seconds = ttl_seconds
        self._artifacts: dict[str, StoredArtifact] = {}
        self._lock = asyncio.Lock()

    async def save(
        self, data: bytes, media_type: str, filename: str | None = None
    ) -> StoredArtifact:
        safe_name = _safe_filename(filename or "eda-export.bin")
        suffix = Path(safe_name).suffix[:16]
        artifact_id = f"{uuid.uuid4().hex}{suffix}"
        artifact = StoredArtifact(
            artifact_id=artifact_id,
            path=self._root / artifact_id,
            media_type=media_type or "application/octet-stream",
            filename=safe_name,
            created_at=time.monotonic(),
        )
        artifact.path.write_bytes(data)
        async with self._lock:
            self._artifacts[artifact_id] = artifact
        return artifact

    async def get(self, artifact_id: str) -> StoredArtifact | None:
        async with self._lock:
            artifact = self._artifacts.get(artifact_id)
            if artifact is None:
                return None
            if time.monotonic() - artifact.created_at > self._ttl_seconds:
                self._artifacts.pop(artifact_id, None)
                artifact.path.unlink(missing_ok=True)
                return None
            return artifact

    async def cleanup_expired(self) -> int:
        now = time.monotonic()
        async with self._lock:
            expired = [
                artifact_id
                for artifact_id, artifact in self._artifacts.items()
                if now - artifact.created_at > self._ttl_seconds
            ]
            for artifact_id in expired:
                self._artifacts.pop(artifact_id).path.unlink(missing_ok=True)
            return len(expired)

    async def cleanup_loop(self) -> None:
        interval = max(1.0, min(30.0, self._ttl_seconds / 2))
        while True:
            await asyncio.sleep(interval)
            await self.cleanup_expired()

    async def close(self) -> None:
        async with self._lock:
            self._artifacts.clear()
        shutil.rmtree(self._root, ignore_errors=True)


def _safe_filename(value: str) -> str:
    name = Path(value).name.strip()[:180]
    name = re.sub(r"[^A-Za-z0-9._()\-\u4e00-\u9fff]+", "_", name)
    return name or "eda-export.bin"
