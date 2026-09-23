def _create_note(client, title="Test", content="Hello world"):
    r = client.post("/notes/", json={"title": title, "content": content})
    assert r.status_code == 201, r.text
    return r.json()


def test_create_and_list_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/search/")
    assert r.status_code == 200

    r = client.get("/notes/search/", params={"q": "Hello"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1


def test_search_notes_matches_title_and_content(client):
    _create_note(client, title="Groceries list", content="milk and eggs")
    _create_note(client, title="Ideas", content="GROCERY loyalty app")

    # "groceries" does NOT contain "grocery" as a substring — only the second
    # note (content match, case-insensitive) hits for this query.
    r = client.get("/notes/search/", params={"q": "grocery"})
    assert r.status_code == 200
    hits = r.json()
    assert {n["title"] for n in hits} == {"Ideas"}

    # "grocer" IS a substring of both "Groceries" (title) and "GROCERY" (content).
    r = client.get("/notes/search/", params={"q": "grocer"})
    assert {n["title"] for n in r.json()} == {"Groceries list", "Ideas"}

    r = client.get("/notes/search/", params={"q": "milk"})
    assert [n["title"] for n in r.json()] == ["Groceries list"]


def test_search_notes_no_match_returns_empty(client):
    r = client.get("/notes/search/", params={"q": "zzz-no-such-note"})
    assert r.status_code == 200
    assert r.json() == []


def test_update_note(client):
    note = _create_note(client, title="Old title", content="old body")

    r = client.put(f"/notes/{note['id']}", json={"title": "New title", "content": "new body"})
    assert r.status_code == 200, r.text
    updated = r.json()
    assert updated["title"] == "New title"
    assert updated["content"] == "new body"
    assert updated["id"] == note["id"]

    r = client.get(f"/notes/{note['id']}")
    assert r.json()["title"] == "New title"


def test_update_note_not_found(client):
    r = client.put("/notes/99999", json={"title": "x", "content": "y"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Note not found"


def test_delete_note(client):
    note = _create_note(client, title="Doomed", content="delete me")

    r = client.delete(f"/notes/{note['id']}")
    assert r.status_code == 204

    r = client.get(f"/notes/{note['id']}")
    assert r.status_code == 404

    r = client.delete(f"/notes/{note['id']}")
    assert r.status_code == 404


def test_create_note_validation_errors(client):
    r = client.post("/notes/", json={"title": "", "content": "ok"})
    assert r.status_code == 422
    assert any(err["loc"][-1] == "title" for err in r.json()["detail"])

    r = client.post("/notes/", json={"title": "ok", "content": ""})
    assert r.status_code == 422

    r = client.post("/notes/", json={"title": "x" * 201, "content": "ok"})
    assert r.status_code == 422


def test_update_note_validation_errors(client):
    note = _create_note(client)
    r = client.put(f"/notes/{note['id']}", json={"title": "", "content": "ok"})
    assert r.status_code == 422


def test_get_note_not_found(client):
    r = client.get("/notes/99999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Note not found"
