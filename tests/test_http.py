from __future__ import annotations

from starlette.testclient import TestClient

from application import create_app
from settings import Settings


def test_health_and_temporary_image() -> None:
    app = create_app(Settings(image_ttl_seconds=60))
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
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


def test_schematic_connect_exposes_callable_python_parameter_names() -> None:
    app = create_app()
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={"Accept": "application/json, text/event-stream"},
        )

    assert response.status_code == 200
    tools = response.json()["result"]["tools"]
    connect = next(tool for tool in tools if tool["name"] == "schematic.connect")
    schema = connect["inputSchema"]
    assert schema["required"] == ["project_id", "from_pin", "to_pin"]
    assert set(schema["properties"]) == {
        "project_id",
        "from_pin",
        "to_pin",
        "net",
        "waypoints",
        "allow_crossings",
    }
    assert schema["properties"]["allow_crossings"]["default"] is False
