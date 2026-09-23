def test_create_list_and_patch_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"
    assert "created_at" in data and "updated_at" in data

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/", params={"q": "Hello", "limit": 10, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    note_id = data["id"]
    r = client.patch(f"/notes/{note_id}", json={"title": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["title"] == "Updated"


# ---------------------------------------------------------------------------
# Task 1 additions: DELETE endpoint, stats endpoint, validation rules
# ---------------------------------------------------------------------------

def test_delete_note_roundtrip(client):
    created = client.post("/notes/", json={"title": "Doomed", "content": "bye"}).json()
    note_id = created["id"]

    gone = client.delete(f"/notes/{note_id}")
    assert gone.status_code == 204

    # 404 on re-read and on re-delete
    assert client.get(f"/notes/{note_id}").status_code == 404
    assert client.delete(f"/notes/{note_id}").status_code == 404


def test_note_stats_endpoint(client):
    created = client.post(
        "/notes/", json={"title": "Stats", "content": "one two three\nfour"}
    ).json()

    r = client.get(f"/notes/{created['id']}/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["chars"] == len("one two three\nfour")
    assert body["words"] == 4
    assert body["lines"] == 2

    assert client.get("/notes/999999/stats").status_code == 404


def test_create_note_validation(client):
    # empty title rejected
    r = client.post("/notes/", json={"title": "", "content": "x"})
    assert r.status_code == 422

    # missing content rejected
    r = client.post("/notes/", json={"title": "t"})
    assert r.status_code == 422

    # title over 200 chars rejected
    r = client.post("/notes/", json={"title": "a" * 201, "content": "x"})
    assert r.status_code == 422


def test_patch_note_validation(client):
    created = client.post("/notes/", json={"title": "v", "content": "c"}).json()
    # patching to an empty title is a validation error, not a silent wipe
    r = client.patch(f"/notes/{created['id']}", json={"title": ""})
    assert r.status_code == 422
