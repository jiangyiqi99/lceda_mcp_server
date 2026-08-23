"""Ephemeral image files with TTL cleanup and no persistent metadata."""

from __future__ import annotations

import asyncio
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StoredImage:
    image_id: str
    path: Path
    media_type: str
    created_at: float


class TemporaryImageStore:
    _EXTENSIONS = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
    }

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self._root = Path(tempfile.mkdtemp(prefix="jlceda-ai-images-"))
        self._ttl_seconds = ttl_seconds
        self._images: dict[str, StoredImage] = {}
        self._lock = asyncio.Lock()

    @property
    def allowed_media_types(self) -> frozenset[str]:
        return frozenset(self._EXTENSIONS)

    async def save(self, data: bytes, media_type: str) -> StoredImage:
        extension = self._EXTENSIONS[media_type]
        image_id = f"{uuid.uuid4().hex}{extension}"
        image = StoredImage(
            image_id=image_id,
            path=self._root / image_id,
            media_type=media_type,
            created_at=time.monotonic(),
        )
        image.path.write_bytes(data)
        async with self._lock:
            self._images[image_id] = image
        return image

    async def get(self, image_id: str) -> StoredImage | None:
        async with self._lock:
            image = self._images.get(image_id)
            if image is None:
                return None
            if time.monotonic() - image.created_at > self._ttl_seconds:
                self._images.pop(image_id, None)
                image.path.unlink(missing_ok=True)
                return None
            return image

    async def cleanup_expired(self) -> int:
        now = time.monotonic()
        async with self._lock:
            expired = [
                image_id
                for image_id, image in self._images.items()
                if now - image.created_at > self._ttl_seconds
            ]
            for image_id in expired:
                self._images.pop(image_id).path.unlink(missing_ok=True)
            return len(expired)

    async def cleanup_loop(self) -> None:
        interval = max(1.0, min(30.0, self._ttl_seconds / 2))
        while True:
            await asyncio.sleep(interval)
            await self.cleanup_expired()

    async def close(self) -> None:
        async with self._lock:
            self._images.clear()
        shutil.rmtree(self._root, ignore_errors=True)

