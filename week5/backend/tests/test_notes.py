def _create(client, title="Test", content="Hello world"):
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
    body = r.json()
    assert body["total"] >= 1
    assert len(body["items"]) >= 1

    r = client.get("/notes/search/")
    assert r.status_code == 200

    r = client.get("/notes/search/", params={"q": "Hello"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) >= 1


# ---------- TASK 2: search + pagination + sorting ----------


def test_search_is_case_insensitive(client):
    _create(client, title="Alpha Plan", content="Zeta contents")
    _create(client, title="other", content="mentions ALPHA briefly")
    r = client.get("/notes/search/", params={"q": "alpha"})
    assert r.status_code == 200
    assert r.json()["total"] == 2


def test_search_no_match_returns_empty_items(client):
    r = client.get("/notes/search/", params={"q": "zzz-no-such-note"})
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 1


def test_search_pagination_payload_shape(client):
    for i in range(7):
        _create(client, title=f"note {i}", content="same body")
    r = client.get("/notes/search/", params={"q": "same body", "page": 1, "page_size": 3})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"items", "total", "page", "page_size"}
    assert len(body["items"]) == 3
    assert body["total"] == 7
    assert body["page"] == 1 and body["page_size"] == 3

    r = client.get("/notes/search/", params={"q": "same body", "page": 3, "page_size": 3})
    assert len(r.json()["items"]) == 1  # last partial page

    # empty last page still 200 with real total (not 404)
    r = client.get("/notes/search/", params={"q": "same body", "page": 9, "page_size": 3})
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_search_sorting(client):
    _create(client, title="banana", content="c1")
    _create(client, title="apple", content="c2")
    _create(client, title="cherry", content="c3")

    r = client.get("/notes/search/", params={"sort": "title_asc", "page_size": 10})
    titles = [n["title"] for n in r.json()["items"]]
    assert titles == sorted(titles)

    r = client.get("/notes/search/", params={"sort": "title_desc", "page_size": 10})
    titles = [n["title"] for n in r.json()["items"]]
    assert titles == sorted(titles, reverse=True)

    # default created_desc: later insert first
    r = client.get("/notes/search/", params={"page_size": 10, "sort": "created_desc"})
    items = r.json()["items"]
    assert items[0]["title"] == "cherry"

    r = client.get("/notes/search/", params={"sort": "bogus"})
    assert r.status_code == 422


# ---------- TASK 3: full CRUD + validation ----------


def test_update_note_success_and_404(client):
    note = _create(client)
    r = client.put(f"/notes/{note['id']}", json={"title": "Updated", "content": "New body"})
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"

    r = client.put("/notes/99999", json={"title": "X", "content": "Y"})
    assert r.status_code == 404


def test_delete_note_success_and_404(client):
    note = _create(client)
    r = client.delete(f"/notes/{note['id']}")
    assert r.status_code == 204

    r = client.get(f"/notes/{note['id']}")
    assert r.status_code == 404

    r = client.delete("/notes/99999")
    assert r.status_code == 404


def test_create_note_validation_errors(client):
    r = client.post("/notes/", json={"title": "", "content": "ok"})
    assert r.status_code == 422
    r = client.post("/notes/", json={"title": "ok", "content": ""})
    assert r.status_code == 422
    r = client.post("/notes/", json={"title": "x" * 201, "content": "ok"})
    assert r.status_code == 422


def test_update_note_validation_errors(client):
    note = _create(client)
    r = client.put(f"/notes/{note['id']}", json={"title": "", "content": "ok"})
    assert r.status_code == 422


# ---------- TASK 8 (notes half): list pagination ----------


def test_list_notes_pagination(client):
    for i in range(12):
        _create(client, title=f"p-note {i:02d}", content="body")
    r = client.get("/notes/", params={"page": 1, "page_size": 5})
    body = r.json()
    assert body["total"] == 12
    assert len(body["items"]) == 5

    r = client.get("/notes/", params={"page": 3, "page_size": 5})
    assert len(r.json()["items"]) == 2

    # page past the end: empty items, real total
    r = client.get("/notes/", params={"page": 99, "page_size": 5})
    assert r.status_code == 200
    assert r.json()["items"] == []
    assert r.json()["total"] == 12


def test_list_notes_pagination_bounds(client):
    r = client.get("/notes/", params={"page": 0})
    assert r.status_code == 422
    r = client.get("/notes/", params={"page_size": 0})
    assert r.status_code == 422
    r = client.get("/notes/", params={"page_size": 101})
    assert r.status_code == 422
