"""Smoke test for v1 Flask notes API."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from app import app, init_db, DB_PATH


@pytest.fixture()
def client():
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    # Windows: close any lingering request-scoped connection before unlink
    import sqlite3 as _s

    try:
        con = _s.connect(DB_PATH)
        con.close()
    except Exception:
        pass
    try:
        DB_PATH.unlink()
    except PermissionError:
        pass


def test_crud_roundtrip(client):
    import json as _json

    def j(resp):
        return _json.loads(resp.data)

    assert client.get("/health").get_json() == {"status": "ok"}

    r = client.post("/notes", json={"title": "First", "content": "hello"})
    assert r.status_code == 201
    note = j(r)
    assert note["title"] == "First" and note["id"] >= 1

    got = client.get(f"/notes/{note['id']}")
    assert got.status_code == 200 and j(got)["content"] == "hello"

    upd = client.put(f"/notes/{note['id']}", json={"title": "Updated", "content": "world"})
    assert upd.status_code == 200 and j(upd)["title"] == "Updated"

    listed = client.get("/notes")
    assert listed.status_code == 200 and len(j(listed)) == 1

    gone = client.delete(f"/notes/{note['id']}")
    assert gone.status_code == 204
    assert client.get(f"/notes/{note['id']}").status_code == 404
    assert client.delete(f"/notes/{note['id']}").status_code == 404


def test_validation(client):
    assert client.post("/notes", json={"title": "", "content": "x"}).status_code == 400
    assert client.post("/notes", json={"title": "t"}).status_code == 400
    assert client.post("/notes", json={"title": "x" * 201, "content": "y"}).status_code == 400
