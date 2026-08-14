from fastapi.testclient import TestClient

from project_brain.api.main import create_app


def test_healthz() -> None:
    client = TestClient(create_app())
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_v1_requires_api_key() -> None:
    client = TestClient(create_app())
    res = client.get("/v1/context")
    assert res.status_code == 401
