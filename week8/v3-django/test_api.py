"""Smoke test for v3 Django+DRF notes API (fresh in-memory-style sqlite)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import api as api_mod

# fresh DB per run
db_file = Path(__file__).resolve().parent / "notes.db"
if db_file.exists():
    db_file.unlink()

from django.db import connection

with connection.schema_editor() as editor:
    editor.create_model(api_mod.Note)

from django.test import Client

client = Client()


def test_crud_roundtrip():
    import json

    r = client.get("/health")
    assert r.status_code == 200 and json.loads(r.content) == {"status": "ok"}

    r = client.post(
        "/notes", data=json.dumps({"title": "First", "content": "hello"}),
        content_type="application/json",
    )
    assert r.status_code == 201, r.content
    note = json.loads(r.content)
    assert note["title"] == "First" and note["id"] >= 1

    got = client.get(f"/notes/{note['id']}")
    assert got.status_code == 200 and json.loads(got.content)["content"] == "hello"

    upd = client.put(
        f"/notes/{note['id']}",
        data=json.dumps({"title": "Updated", "content": "world"}),
        content_type="application/json",
    )
    assert upd.status_code == 200 and json.loads(upd.content)["title"] == "Updated"

    listed = client.get("/notes")
    assert listed.status_code == 200 and len(json.loads(listed.content)) == 1

    gone = client.delete(f"/notes/{note['id']}")
    assert gone.status_code == 204
    assert client.get(f"/notes/{note['id']}").status_code == 404


def test_validation():
    import json

    r = client.post(
        "/notes", data=json.dumps({"title": "", "content": "x"}),
        content_type="application/json",
    )
    assert r.status_code == 400  # DRF raises ValidationError -> 400

    r = client.post(
        "/notes", data=json.dumps({"title": "x" * 201, "content": "y"}),
        content_type="application/json",
    )
    assert r.status_code == 400
