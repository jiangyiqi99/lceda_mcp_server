"""Runtime settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    rpc_timeout_seconds: float = 30.0
    registration_timeout_seconds: float = 5.0
    heartbeat_timeout_seconds: float = 30.0
    heartbeat_check_seconds: float = 5.0
    image_ttl_seconds: float = 300.0
    max_image_bytes: int = 12 * 1024 * 1024
    public_base_url: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            host=os.getenv("JLCEDA_HOST", defaults.host),
            port=int(os.getenv("JLCEDA_PORT", str(defaults.port))),
            rpc_timeout_seconds=float(
                os.getenv("JLCEDA_RPC_TIMEOUT", str(defaults.rpc_timeout_seconds))
            ),
            registration_timeout_seconds=float(
                os.getenv(
                    "JLCEDA_REGISTRATION_TIMEOUT",
                    str(defaults.registration_timeout_seconds),
                )
            ),
            heartbeat_timeout_seconds=float(
                os.getenv(
                    "JLCEDA_HEARTBEAT_TIMEOUT",
                    str(defaults.heartbeat_timeout_seconds),
                )
            ),
            heartbeat_check_seconds=float(
                os.getenv(
                    "JLCEDA_HEARTBEAT_CHECK",
                    str(defaults.heartbeat_check_seconds),
                )
            ),
            image_ttl_seconds=float(
                os.getenv("JLCEDA_IMAGE_TTL", str(defaults.image_ttl_seconds))
            ),
            max_image_bytes=int(
                os.getenv("JLCEDA_MAX_IMAGE_BYTES", str(defaults.max_image_bytes))
            ),
            public_base_url=os.getenv("JLCEDA_PUBLIC_BASE_URL") or None,
        )
