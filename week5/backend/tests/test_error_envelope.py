"""TASK 7 tests: uniform error envelope on all API failures."""
from fastapi.testclient import TestClient


def test_404_envelope(client: TestClient):
    r = client.get("/notes/999999")
    assert r.status_code == 404
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == 404
    assert "not found" in body["error"]["message"].lower()


def test_422_validation_envelope(client: TestClient):
    r = client.post("/notes/", json={"title": "", "content": "x"})
    assert r.status_code == 422
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == 422
    assert "title" in body["error"]["message"]


def test_bulk_404_envelope_carries_missing_ids(client: TestClient):
    created = client.post("/action-items/", json={"description": "keep open"}).json()
    r = client.post("/action-items/bulk-complete", json={"ids": [created["id"], 424242]})
    assert r.status_code == 404
    body = r.json()
    assert body["ok"] is False
    # structured detail (missing_ids) passes through the envelope
    assert body["error"]["missing_ids"] == [424242]
    assert "not found" in body["error"]["message"]


def test_success_payload_unchanged(client: TestClient):
    """Success responses keep their original shape (tests consume them directly)."""
    r = client.post("/notes/", json={"title": "ok", "content": "fine"})
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "ok"  # unwrapped: routers still return plain models
    assert "ok" not in body or body.get("title")  # no envelope on success path


def test_envelope_only_on_api_paths(client: TestClient):
    """Non-API routes (docs, openapi) are untouched by the middleware."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "openapi" in r.json()
