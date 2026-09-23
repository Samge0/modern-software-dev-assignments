"""Security regression tests for the week6 fixes (Semgrep remediation)."""
from fastapi.testclient import TestClient


def test_search_is_injection_safe(client: TestClient):
    # Classic LIKE-injection payload: %' OR 1=1 --
    # (trailing slash matters: without it the path is captured by /notes/{note_id})
    r = client.get("/notes/unsafe-search/", params={"q": "%' OR 1=1 --"})
    assert r.status_code == 200
    # The escaped pattern must match literal text, not open the WHERE clause.
    # With no such note present, expect no rows (no blanket match).
    assert r.json() == []

    r2 = client.get("/notes/unsafe-search/", params={"q": "50%"})
    assert r2.status_code == 200  # literal % treated as escaped wildcard

    r3 = client.get("/notes/unsafe-search/", params={"q": "_"})
    assert r3.status_code == 200  # literal _ escaped too


def test_eval_endpoint_removed(client: TestClient):
    r = client.get("/notes/debug/eval", params={"expr": "__import__('os').getcwd()"})
    assert r.status_code in (404, 405)  # endpoint gone entirely


def test_calc_endpoint_safe(client: TestClient):
    ok = client.get("/notes/debug/calc", params={"expr": "2*(3+4)"})
    assert ok.status_code == 200
    assert ok.json()["result"] == "14"

    rce = client.get("/notes/debug/calc", params={"expr": "__import__('os').getcwd()"})
    assert rce.status_code == 400

    letters = client.get("/notes/debug/calc", params={"expr": "abc"})
    assert letters.status_code == 400


def test_run_endpoint_removed(client: TestClient):
    r = client.get("/notes/debug/run", params={"cmd": "echo pwned"})
    assert r.status_code in (404, 405)


def test_fetch_blocks_file_scheme_and_localhost(client: TestClient):
    file = client.get("/notes/debug/fetch", params={"url": "file:///C:/Windows/win.ini"})
    assert file.status_code == 400

    local = client.get("/notes/debug/fetch", params={"url": "http://127.0.0.1:8000/"})
    assert local.status_code == 400


def test_read_restricted_to_data_dir(client: TestClient):
    traversal = client.get("/notes/debug/read", params={"path": "../../backend/app/main.py"})
    assert traversal.status_code == 400

    absolute = client.get("/notes/debug/read", params={"path": "C:/Windows/win.ini"})
    assert absolute.status_code == 400
