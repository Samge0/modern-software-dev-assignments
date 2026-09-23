"""TASK 4 tests: completion filter, bulk complete, transactional rollback."""
from fastapi.testclient import TestClient


def _create(client: TestClient, desc: str) -> dict:
    r = client.post("/action-items/", json={"description": desc})
    assert r.status_code == 201, r.text
    return r.json()


def test_filter_by_completed(client: TestClient):
    a = _create(client, "open task")
    b = _create(client, "done task")
    client.put(f"/action-items/{b['id']}/complete")

    open_only = client.get("/action-items/", params={"completed": "false"}).json()
    assert open_only["total"] == 1
    assert open_only["items"][0]["id"] == a["id"]

    done_only = client.get("/action-items/", params={"completed": "true"}).json()
    assert done_only["total"] == 1
    assert done_only["items"][0]["id"] == b["id"]

    everything = client.get("/action-items/").json()
    assert everything["total"] == 2


def test_bulk_complete_marks_all(client: TestClient):
    items = [_create(client, f"task {i}") for i in range(3)]
    ids = [it["id"] for it in items]

    r = client.post("/action-items/bulk-complete", json={"ids": ids})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["updated_count"] == 3
    assert body["ids"] == sorted(ids)

    done = client.get("/action-items/", params={"completed": "true"}).json()
    assert done["total"] == 3


def test_bulk_complete_is_idempotent(client: TestClient):
    item = _create(client, "twice task")
    for _ in range(2):
        r = client.post("/action-items/bulk-complete", json={"ids": [item["id"]]})
        assert r.status_code == 200
    assert client.get("/action-items/", params={"completed": "true"}).json()["total"] == 1


def test_bulk_complete_unknown_id_rolls_back_everything(client: TestClient):
    """Transactional guarantee: one bad id must leave ALL items untouched."""
    kept = _create(client, "should stay open")
    doomed = _create(client, "would be completed")

    r = client.post("/action-items/bulk-complete", json={"ids": [doomed["id"], 999999]})
    assert r.status_code == 404
    # TASK 7 envelope: {ok:false, error:{code, message, missing_ids}}
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["missing_ids"] == [999999]

    # Rollback verified: neither item was mutated
    after = client.get("/action-items/", params={"completed": "false"}).json()
    assert after["total"] == 2
    assert {it["id"] for it in after["items"]} == {kept["id"], doomed["id"]}


def test_bulk_complete_empty_ids_rejected(client: TestClient):
    r = client.post("/action-items/bulk-complete", json={"ids": []})
    assert r.status_code == 422


def test_action_items_pagination(client: TestClient):
    for i in range(15):
        _create(client, f"page task {i}")

    page1 = client.get("/action-items/", params={"page": 1, "page_size": 10}).json()
    assert page1["total"] == 15
    assert len(page1["items"]) == 10

    page2 = client.get("/action-items/", params={"page": 2, "page_size": 10}).json()
    assert len(page2["items"]) == 5


def test_action_items_sort_by_description(client: TestClient):
    for name in ("charlie", "alpha", "bravo"):
        _create(client, name)
    r = client.get("/action-items/", params={"sort": "description_asc", "page_size": 3}).json()
    descs = [it["description"] for it in r["items"]]
    assert descs == sorted(descs)
