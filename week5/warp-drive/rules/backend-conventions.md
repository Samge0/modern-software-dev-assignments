---
name: backend-conventions
description: API/contract conventions for the week5 FastAPI backend — response envelopes, pagination, validation, error codes. Attach to every agent session that touches week5/backend.
scope: week5/
---

Rules for all changes under `week5/backend/`:

1. **Response envelope (TASK 7).** Every JSON API response is wrapped:
   - success: `{"ok": true, "data": <payload>}`
   - error: `{"ok": false, "error": {"code": "<CODE>", "message": "<human readable>"}}`
   - error codes: `NOT_FOUND` (404), `VALIDATION_ERROR` (422),
     `BAD_REQUEST` (400), `CONFLICT` (409), `INTERNAL_ERROR` (500).
   - Envelope is applied by middleware in `app/main.py`; route handlers return
     bare payloads. `/`, `/static/*`, `/docs`, `/openapi.json` are exempt.
2. **Pagination (TASK 8).** Collection endpoints (`GET /notes/`,
   `GET /action-items/`, `GET /notes/search/`) accept `page` (>=1, default 1)
   and `page_size` (1..100, default 10) and return
   `{"items": [...], "total": <int>, "page": <int>, "page_size": <int>}`.
   A page past the end returns `items: []` with the real `total` — not 404.
3. **Validation.** Write-models (Create/Update) use `Field(min_length=1, ...)`
   with `max_length` 200 for titles, 2000 for action-item descriptions, and
   10000 for note content. Empty-string payloads must produce 422 with the
   `VALIDATION_ERROR` envelope.
4. **Search (TASK 2).** `q` matches case-insensitively over both
   `notes.title` and `notes.content`. `sort` is one of
   `created_desc|created_asc|title_asc|title_desc` (default `created_desc`);
   reject anything else with 422.
5. **Bulk mutations (TASK 4).** Validate **all** ids before mutating any row;
   if any id is missing return 404 and leave the table untouched (the session
   dependency rolls back). `ids` must be a non-empty list.
6. **Tests.** Every new endpoint ships with tests in `backend/tests/`:
   happy path, validation failure, and 404. Tests must pass on Windows
   (temp dirs, not `mkstemp` files that SQLite keeps locked).
7. Never edit files outside `week5/`. Never `git push`.
