"""End-to-end API tests for the week2 app (TODO 2/4 coverage).

Uses FastAPI TestClient with a temp DB via env override.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Redirect DB to a temp file BEFORE importing the app (module-level init_db)
_TMP = tempfile.mkdtemp(prefix="week2_test_")
os.environ["WEEK2_DB_PATH"] = str(Path(_TMP) / "test_app.db")

from ..app import db as app_db  # noqa: E402
from ..app.main import app  # noqa: E402

# Point DB_PATH at the temp location
app_db.DB_PATH = Path(_TMP) / "test_app.db"
if app_db.DB_PATH.exists():
    app_db.DB_PATH.unlink()
app_db.init_db()

client = TestClient(app)


def test_index_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "Action Item Extractor" in res.text
    assert "Extract LLM" in res.text
    assert "List Notes" in res.text


def test_create_and_get_note():
    res = client.post("/notes", json={"content": "hello world"})
    assert res.status_code == 200
    note = res.json()
    assert note["content"] == "hello world"

    got = client.get(f"/notes/{note['id']}")
    assert got.status_code == 200
    assert got.json()["content"] == "hello world"

    missing = client.get("/notes/99999")
    assert missing.status_code == 404


def test_create_note_validation():
    res = client.post("/notes", json={"content": ""})
    assert res.status_code == 422  # pydantic min_length


def test_list_notes():
    client.post("/notes", json={"content": "note-a"})
    client.post("/notes", json={"content": "note-b"})
    res = client.get("/notes")
    assert res.status_code == 200
    notes = res.json()["notes"]
    assert any(n["content"] == "note-a" for n in notes)
    assert any(n["content"] == "note-b" for n in notes)


def test_extract_heuristic_flow():
    res = client.post(
        "/action-items/extract",
        json={"text": "- [ ] buy milk\n- call mom", "save_note": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["engine"] == "heuristic"
    assert data["note_id"] is not None
    texts = [i["text"] for i in data["items"]]
    assert "Buy milk" in texts or "buy milk" in texts


def test_extract_requires_text():
    res = client.post("/action-items/extract", json={"text": ""})
    assert res.status_code == 422


def test_mark_done_roundtrip():
    res = client.post("/action-items/extract", json={"text": "- [ ] task one"})
    item_id = res.json()["items"][0]["id"]

    done = client.post(f"/action-items/{item_id}/done", json={"done": True})
    assert done.status_code == 200
    assert done.json()["done"] is True

    listed = client.get("/action-items").json()
    match = [i for i in listed if i["id"] == item_id][0]
    assert match["done"] is True

    missing = client.post("/action-items/99999/done", json={"done": True})
    assert missing.status_code == 404


def test_extract_llm_endpoint_live():
    """Live LLM endpoint test (skipped when no endpoint configured)."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("no local LLM endpoint configured")
    res = client.post(
        "/action-items/extract-llm",
        json={"text": "TODO: email the team\nWe should also update the roadmap.", "save_note": False},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["engine"] == "llm"
    assert len(data["items"]) >= 1
    joined = " ".join(i["text"].lower() for i in data["items"])
    assert "email" in joined or "team" in joined
