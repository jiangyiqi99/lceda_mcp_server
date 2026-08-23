"""Combined HTTP, WebSocket, and MCP ASGI application."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import quote

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route, WebSocketRoute

from broker.registry import ProjectRegistry
from broker.router import RequestRouter
from broker.websocket_server import WebSocketBroker
from files.image_store import TemporaryImageStore
from mcp_api.server import create_mcp_server
from settings import Settings

logger = logging.getLogger(__name__)


def _create_mcp_app(server: Any) -> Any:
    try:
        return server.streamable_http_app(
            streamable_http_path="/mcp",
            stateless_http=True,
            json_response=True,
        )
    except TypeError:
        # MCP SDK 1.x takes these options in the FastMCP constructor.
        return server.streamable_http_app()


def create_app(settings: Settings | None = None) -> Starlette:
    settings = settings or Settings.from_env()
    registry = ProjectRegistry(settings.heartbeat_timeout_seconds)
    router = RequestRouter(registry, settings.rpc_timeout_seconds)
    websocket_broker = WebSocketBroker(
        registry,
        router,
        registration_timeout_seconds=settings.registration_timeout_seconds,
        heartbeat_check_seconds=settings.heartbeat_check_seconds,
    )
    images = TemporaryImageStore(settings.image_ttl_seconds)
    mcp_server = create_mcp_server(registry, router)
    mcp_app = _create_mcp_app(mcp_server)

    async def health(_request: Request) -> JSONResponse:
        projects = await registry.list_projects()
        return JSONResponse(
            {
                "service": "jlceda-ai-agent",
                "status": "ok",
                "connected_projects": len(projects),
            }
        )

    async def upload_image(request: Request) -> JSONResponse:
        content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
        if content_type not in images.allowed_media_types:
            return JSONResponse(
                {
                    "error": {
                        "code": "UNSUPPORTED_IMAGE_TYPE",
                        "message": "content-type must be image/png, image/jpeg, or image/webp",
                    }
                },
                status_code=415,
            )
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_image_bytes:
            return JSONResponse(
                {"error": {"code": "IMAGE_TOO_LARGE", "message": "image is too large"}},
                status_code=413,
            )
        data = await request.body()
        if not data:
            return JSONResponse(
                {"error": {"code": "EMPTY_IMAGE", "message": "image body is empty"}},
                status_code=400,
            )
        if len(data) > settings.max_image_bytes:
            return JSONResponse(
                {"error": {"code": "IMAGE_TOO_LARGE", "message": "image is too large"}},
                status_code=413,
            )

        image = await images.save(data, content_type)
        base_url = settings.public_base_url or str(request.base_url).rstrip("/")
        return JSONResponse(
            {
                "url": f"{base_url}/files/{quote(image.image_id)}",
                "expires_in": settings.image_ttl_seconds,
            },
            status_code=201,
            headers={"Cache-Control": "no-store"},
        )

    async def serve_image(request: Request) -> Response:
        image = await images.get(request.path_params["image_id"])
        if image is None:
            return JSONResponse(
                {
                    "error": {
                        "code": "IMAGE_NOT_FOUND",
                        "message": "image does not exist or has expired",
                    }
                },
                status_code=404,
            )
        return FileResponse(
            image.path,
            media_type=image.media_type,
            headers={"Cache-Control": "no-store"},
        )

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        async with contextlib.AsyncExitStack() as stack:
            await stack.enter_async_context(mcp_server.session_manager.run())
            heartbeat_task = asyncio.create_task(websocket_broker.monitor_heartbeats())
            image_task = asyncio.create_task(images.cleanup_loop())
            try:
                yield
            finally:
                for task in (heartbeat_task, image_task):
                    task.cancel()
                await asyncio.gather(heartbeat_task, image_task, return_exceptions=True)
                await images.close()

    inner_app = Starlette(
        debug=False,
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/upload/image", upload_image, methods=["POST"]),
            Route("/files/{image_id:str}", serve_image, methods=["GET"]),
            WebSocketRoute("/ws", websocket_broker.endpoint),
            Mount("/", app=mcp_app),
        ],
        lifespan=lifespan,
    )
    inner_app.state.registry = registry
    inner_app.state.router = router
    inner_app.state.images = images

    return CORSMiddleware(
        app=inner_app,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )


app = create_app()

