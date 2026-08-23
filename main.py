"""Run the standalone JLCEDA AI backend with ``python main.py``."""

from __future__ import annotations

import logging

import uvicorn

from settings import Settings


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    uvicorn.run(
        "application:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()

