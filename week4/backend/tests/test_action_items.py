def _create_item(client, description="Ship it"):
    r = client.post("/action-items/", json={"description": description})
    assert r.status_code == 201, r.text
    return r.json()


def test_create_and_complete_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["completed"] is True


def test_complete_action_item_is_idempotent(client):
    item = _create_item(client, "Water the plants")

    for _ in range(2):
        r = client.put(f"/action-items/{item['id']}/complete")
        assert r.status_code == 200
        assert r.json()["completed"] is True


def test_complete_action_item_not_found(client):
    r = client.put("/action-items/99999/complete")
    assert r.status_code == 404
    assert r.json()["detail"] == "Action item not found"


def test_complete_only_targets_requested_item(client):
    a = _create_item(client, "First")
    b = _create_item(client, "Second")

    r = client.put(f"/action-items/{a['id']}/complete")
    assert r.status_code == 200

    items = {i["id"]: i for i in client.get("/action-items/").json()}
    assert items[a["id"]]["completed"] is True
    assert items[b["id"]]["completed"] is False


def test_create_action_item_validation_error(client):
    r = client.post("/action-items/", json={"description": ""})
    assert r.status_code == 422
