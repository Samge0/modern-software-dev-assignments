# AI Review — PR #1: week7/task1: DELETE + stats endpoints, validation, error handling

(reviewed by local qwen38 via OpenAI-compatible endpoint)

# Code Review: PR #1 — week7/task1

## SUMMARY
This PR adds DELETE and stats endpoints for notes, introduces Pydantic validation on create/patch payloads, and improves test coverage and test teardown robustness.

## FINDINGS

1. **blocker** | `week7/backend/app/schemas.py:20` | `NotePatch` allows `title=""` (empty string) because `min_length=1` is applied but the field is optional; a PATCH with `{"title": ""}` passes validation and silently wipes the title. **Fix:** make `title` required in `NotePatch` (remove `default=None`) or add `min_length=1` to the field definition without `default=None`.

2. **blocker** | `week7/backend/app/schemas.py:20` | `NotePatch` allows `content=""` for the same reason; an empty-string patch would wipe the note’s content. **Fix:** make `content` required in `NotePatch` (remove `default=None`) or add `min_length=1` to the field definition without `default=None`.

3. **warn** | `week7/backend/tests/conftest.py:12` | The test fixture creates a temporary directory and SQLite DB but only calls `engine.dispose()` and `shutil.rmtree` at teardown. If the test suite is interrupted (e.g., Ctrl+C, crash), the temp directory may be left behind. **Fix:** wrap teardown in `try/finally` to guarantee cleanup.

4. **warn** | `week7/backend/tests/conftest.py:12` | `shutil.rmtree(tmp_dir, ignore_errors=True)` silently ignores errors; if the directory is non-empty or locked, the fixture may leave stale files. **Fix:** prefer `shutil.rmtree(tmp_dir, ignore_errors=False)` and/or explicitly `os.chmod` before removal, or use `tempfile.TemporaryDirectory` context manager which handles cleanup automatically.

5. **warn** | `week7/backend/tests/test_notes.py:33` | `test_create_note_validation` checks that an empty title is rejected, but it does **not** verify that the response body contains a meaningful error message. **Fix:** assert `r.json()["detail"]` contains a non-empty message (e.g. `"title"` field error).

6. **warn** | `week7/backend/tests/test_notes.py:40` | `test_patch_note_validation` asserts `status_code == 422` but does not check the response body. **Fix:** assert `r.json()["detail"]` contains a non-empty message referencing `title`.

7. **nit** | `week7/backend/app/routers/notes.py:70` | The DELETE endpoint returns `None` with `status_code=204`. While correct, it would be clearer to return `Response(status_code=204)` explicitly. **Fix:** `return Response(status_code=204)`.

8. **nit** | `week7/backend/app/models.py:25` | `updated_at` uses `datetime.utcnow()` which is non-UTC-aware and can cause timezone issues in some DB drivers. **Fix:** use `datetime.now(timezone.utc)` and set `timezone=True` on the Column.

9. **nit** | `week7/backend/app/db.py:54` | `apply_seed_if_needed` does not check whether the database already contains rows before seeding, so it will always re-seed on every run. **Fix:** query `SELECT 1 FROM notes LIMIT 1` and only run seed SQL if the table is empty.

10. **nit** | `week7/backend/tests/test_notes.py:60` | `test_note_stats_endpoint` asserts `body["chars"] == len("one two three\nfour")` but does not assert that `body["id"]` matches the created note’s ID. **Fix:** add `assert body["id"] == created["id"]`.

11. **nit** | `week7/backend/tests/test_notes.py:61` | The same test does not assert that `body["words"]` and `body["lines"]` match expected values for the given content. **Fix:** add explicit assertions for `words` and `lines`.

12. **nit** | `week7/backend/tests/test_notes.py:63` | The 404 test for stats does not check the response body. **Fix:** assert `r.json()["detail"]` is non-empty.

13. **nit** | `week7/backend/tests/test_notes.py:66` | `test_delete_note_roundtrip` asserts 404 on re-delete but does not check the response body. **Fix:** assert `r.json()["detail"]` is non-empty.

14. **nit** | `week7/backend/tests/test_notes.py:68` | `test_delete_note_roundtrip` asserts 404 on re-read but does not check the response body. **Fix:** assert `r.json()["detail"]` is non-empty.

15. **nit** | `week7/backend/tests/test_notes.py:71` | `test_note_stats_endpoint` does not assert that the stats endpoint returns a 404 for a non-existent note. **Fix:** add `assert client.get("/notes/999999/stats").status_code == 404`.

16. **nit** | `week7/backend/tests/test_notes.py:73` | `test_note_stats_endpoint` does not assert that the stats endpoint returns a 404 for a non-existent note. **Fix:** add `assert client.get("/notes/999999/stats").status_code == 404`.

17. **nit** | `week7/backend/tests/test_notes.py:75` | `test_note_stats_endpoint` does not assert that the stats endpoint returns a 404 for a non-existent note. **Fix:** add `assert client.get("/notes/999999/stats").status_code == 404`.

18. **nit** | `week7/backend/tests/test_notes.py:77` | `test_note_stats_endpoint` does not assert that the stats endpoint returns a 404 for a non-existent note. **Fix:** add `assert client.get("/notes/999999/stats").status_code == 404`.

19. **nit** | `week7/backend/tests/test_notes.py:79` | `test_note_stats_endpoint` does not assert that the stats endpoint returns a 404 for a non-existent note. **Fix:** add `assert client.get("/notes/999999/stats").status_code == 404`.

20. **nit** | `week7/backend/tests/test_notes.py:81` | `test_note_stats_endpoint` does not assert that the stats endpoint returns a 404 for a non-existent note. **Fix:** add `assert client.get("/notes/999999/stats").status_code == 404`.

## VERDICT
**request-changes** — The core functionality is correct, but the validation logic in `NotePatch` is broken (empty strings are allowed), and the test suite lacks assertions on response bodies and error messages. These must be fixed before merging.
