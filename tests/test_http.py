from __future__ import annotations

from starlette.testclient import TestClient

from application import create_app
from settings import Settings


def test_health_and_temporary_image() -> None:
    app = create_app(Settings(image_ttl_seconds=60))
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["connected_projects"] == 0

        upload = client.post(
            "/upload/image",
            content=b"\x89PNG\r\n\x1a\nmock",
            headers={"Content-Type": "image/png"},
        )
        assert upload.status_code == 201
        image = client.get(upload.json()["url"])
        assert image.status_code == 200
        assert image.headers["content-type"] == "image/png"


def test_reject_non_image_upload() -> None:
    app = create_app(Settings(image_ttl_seconds=60))
    with TestClient(app) as client:
        response = client.post(
            "/upload/image", content=b"hello", headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 415

