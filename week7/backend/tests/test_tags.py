"""Task 3 tests: Tag model, many-to-many note<->tag, action-item note link."""
from fastapi.testclient import TestClient


def test_tag_crud(client: TestClient):
    r = client.post("/tags/", json={"name": "urgent"})
    assert r.status_code == 201, r.text
    tag = r.json()
    assert tag["name"] == "urgent"

    # duplicate -> 409
    dup = client.post("/tags/", json={"name": "urgent"})
    assert dup.status_code == 409

    listed = client.get("/tags/").json()
    assert any(t["name"] == "urgent" for t in listed)

    gone = client.delete(f"/tags/{tag['id']}")
    assert gone.status_code == 204
    assert client.delete(f"/tags/{tag['id']}").status_code == 404


def test_tag_validation(client: TestClient):
    assert client.post("/tags/", json={"name": ""}).status_code == 422
    assert client.post("/tags/", json={"name": "x" * 65}).status_code == 422
    assert client.post("/tags/", json={"name": "bad#tag"}).status_code == 422


def test_attach_tags_to_note(client: TestClient):
    note = client.post("/notes/", json={"title": "Tagged", "content": "hello"}).json()

    r = client.post(f"/tags/notes/{note['id']}", json={"names": ["Work", "review"]})
    assert r.status_code == 200
    names = {t["name"] for t in r.json()}
    assert names == {"work", "review"}  # normalized to lower

    # idempotent re-attach
    r2 = client.post(f"/tags/notes/{note['id']}", json={"names": ["work"]})
    assert r2.status_code == 200
    assert len(r2.json()) == 2  # no duplicate join rows

    # unknown note -> 404
    assert client.post("/tags/notes/999999", json={"names": ["x"]}).status_code == 404


def test_many_to_many_shared_tags(client: TestClient):
    a = client.post("/notes/", json={"title": "A", "content": "a"}).json()
    b = client.post("/notes/", json={"title": "B", "content": "b"}).json()
    client.post(f"/tags/notes/{a['id']}", json={"names": ["shared"]})
    client.post(f"/tags/notes/{b['id']}", json={"names": ["shared"]})

    tags = client.get("/tags/").json()
    shared = [t for t in tags if t["name"] == "shared"]
    assert len(shared) == 1  # one Tag row, two join rows


def test_attach_creates_missing_tags(client: TestClient):
    note = client.post("/notes/", json={"title": "C", "content": "c"}).json()
    client.post(f"/tags/notes/{note['id']}", json={"names": ["brand-new"]})
    listed = client.get("/tags/").json()
    assert any(t["name"] == "brand-new" for t in listed)
