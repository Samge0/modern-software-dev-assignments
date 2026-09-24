"""Smoke test for v2 FastAPI notes API (temp DB per run)."""
import os
import tempfile
from pathlib import Path

os.chdir(Path(__file__).resolve().parent)  # sqlite file lands next to app.py

# isolate DB before importing app
import app as app_mod

_tmp = tempfile.mkdtemp(prefix="v2_test_")
app_mod.engine.dispose()
app_mod.engine = __import__("sqlalchemy").create_engine(
    f"sqlite:///{_tmp}/test.db", connect_args={"check_same_thread": False}
)
app_mod.SessionLocal = __import__("sqlalchemy").orm.sessionmaker(bind=app_mod.engine)
app_mod.Base.metadata.create_all(bind=app_mod.engine)  # bare TestClient skips startup hooks

from fastapi.testclient import TestClient

client = TestClient(app_mod.app)


def test_crud_roundtrip():
    assert client.get("/health").json() == {"status": "ok"}

    r = client.post("/notes", json={"title": "First", "content": "hello"})
    assert r.status_code == 201
    note = r.json()
    assert note["title"] == "First"

    assert client.get(f"/notes/{note['id']}").json()["content"] == "hello"
    upd = client.put(f"/notes/{note['id']}", json={"title": "Updated", "content": "world"})
    assert upd.status_code == 200 and upd.json()["title"] == "Updated"

    assert len(client.get("/notes").json()) == 1

    assert client.delete(f"/notes/{note['id']}").status_code == 204
    assert client.get(f"/notes/{note['id']}").status_code == 404


def test_validation():
    assert client.post("/notes", json={"title": "", "content": "x"}).status_code == 422
    assert client.post("/notes", json={"title": "t"}).status_code == 422
    assert client.post("/notes", json={"title": "x" * 201, "content": "y"}).status_code == 422
