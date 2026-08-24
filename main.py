"""Run the standalone JLCEDA AI backend with ``python main.py``."""

from __future__ import annotations

import logging

import uvicorn

from settings import Settings


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # The stateless MCP transport opens and closes a session for every request.
    # Its INFO message is expected lifecycle noise, not a useful health signal.
    logging.getLogger("mcp.server.streamable_http").setLevel(logging.WARNING)
    uvicorn.run(
        "application:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        access_log=settings.access_log,
    )


if __name__ == "__main__":
    main()
