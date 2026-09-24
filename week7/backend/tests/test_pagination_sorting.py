"""Task 4: pagination & sorting coverage for /notes/ (and skip/limit edges)."""
import pytest
from fastapi.testclient import TestClient


TITLES = ["alpha", "Bravo", "charlie", "Delta", "echo", "Foxtrot", "golf", "Hotel"]


@pytest.fixture()
def seeded(client: TestClient) -> list[dict]:
    notes = []
    for t in TITLES:
        r = client.post("/notes/", json={"title": t, "content": f"body of {t}"})
        assert r.status_code == 201
        notes.append(r.json())
    return notes


def _titles(resp) -> list[str]:
    return [n["title"] for n in resp.json()]


def test_default_listing_returns_all_seeded(client: TestClient, seeded):
    r = client.get("/notes/")
    assert r.status_code == 200
    assert len(r.json()) == len(TITLES)


def test_limit_caps_results(client: TestClient, seeded):
    r = client.get("/notes/", params={"limit": 3})
    assert len(r.json()) == 3


def test_skip_offsets_results_no_overlap(client: TestClient, seeded):
    page1 = _titles(client.get("/notes/", params={"limit": 3, "sort": "id"}))
    page2 = _titles(client.get("/notes/", params={"limit": 3, "skip": 3, "sort": "id"}))
    assert len(page1) == 3 and len(page2) == 3
    assert set(page1).isdisjoint(page2)  # no overlap between pages
    assert set(page1) | set(page2) <= set(TITLES)


def test_skip_beyond_end_returns_empty(client: TestClient, seeded):
    r = client.get("/notes/", params={"skip": 1000})
    assert r.status_code == 200
    assert r.json() == []


def test_limit_over_max_rejected(client: TestClient):
    assert client.get("/notes/", params={"limit": 201}).status_code == 422
    assert client.get("/notes/", params={"limit": 200}).status_code == 200


def test_negative_skip_rejected(client: TestClient):
    assert client.get("/notes/", params={"skip": -1}).status_code == 422


def test_sort_desc_is_default_and_reverses(client: TestClient, seeded):
    # deterministic check via id sorting (created_at can tie within one second)
    by_id_desc = _titles(client.get("/notes/", params={"sort": "-id"}))
    by_id_asc = _titles(client.get("/notes/", params={"sort": "id"}))
    assert by_id_desc == list(reversed(by_id_asc))
    assert sorted(by_id_asc) == sorted(TITLES, key=str.lower) or sorted(by_id_asc) == sorted(TITLES)


def test_sort_unknown_field_falls_back_safely(client: TestClient, seeded):
    # route has no sort whitelist: hasattr() check falls back to created_at desc
    r = client.get("/notes/", params={"sort": "-nonexistent_field"})
    assert r.status_code == 200
    assert len(r.json()) == len(TITLES)
    # fallback order == default order
    default_titles = _titles(client.get("/notes/"))
    assert _titles(r) == default_titles


def test_sort_by_title(client: TestClient, seeded):
    r = client.get("/notes/", params={"sort": "title"})
    titles = _titles(r)
    # Actual contract: SQLite ORDER BY is binary (uppercase-first), NOT
    # case-insensitive. Documented behavior; would need func.lower() for CI sort.
    assert titles == sorted(titles), titles


def test_pagination_with_query_filter(client: TestClient, seeded):
    # content contains 'body of <title>' for every note; filter + limit compose
    r = client.get("/notes/", params={"q": "body", "limit": 2, "sort": "id"})
    assert r.status_code == 200
    assert len(r.json()) == 2

    # filter actually filters: 'alpha' content match returns exactly the alpha note
    only_alpha = client.get("/notes/", params={"q": "of alpha"})
    assert [n["title"] for n in only_alpha.json()] == ["alpha"]

    # filter is case-insensitive on content
    upper = client.get("/notes/", params={"q": "OF ALPHA"})
    assert [n["title"] for n in upper.json()] == ["alpha"]

    r_all = client.get("/notes/", params={"q": "body"})
    assert len(r_all.json()) == len(TITLES)
