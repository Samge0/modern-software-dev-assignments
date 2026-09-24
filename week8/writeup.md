# Week 8 Write-up — Multi-Stack AI-Accelerated Build

## App Concept

A minimal **Notes CRUD API** (the core resource of every previous week's
starter app): create/read/update/delete notes with title (1–200 chars),
content (≥1 char), timestamps; validation errors and 404s on all three stacks;
`/health` probe; smoke tests per version.

## Version 1 — Flask 3 + raw sqlite3 (`v1-flask/`)

Single-file micro-service. Hand-written. Validation is explicit imperative
code (`_validate` returns None → 400). Tests use Flask's test client with a
real temp sqlite file. Interesting wart: Windows keeps sqlite handles open
after requests, so the test fixture must tolerate unlink failures.

- Run: `python app.py` (port 5001)
- Tests: 2 passed (`test_app.py`: CRUD roundtrip + validation)

## Version 2 — FastAPI + SQLAlchemy (`v2-fastapi/`) — *AI-generated*

Generated from a natural-language spec by a **local LLM (qwen38 via vLLM)**
standing in for bolt.new (no bolt account/credits available here — see honest
note below). The generation flow: spec prompt → model output → manual review →
2 fixes (startup-hook table creation for bare TestClient, DB isolation in
tests) → green.

- Run: `uvicorn app:app --port 5002`, OpenAPI at `/docs`
- Tests: 2 passed (`test_app.py`)

## Version 3 — Django 5 + DRF (`v3-django/`) — *non-JS-language requirement*

Single-file Django configuration (settings.configure in-module, model with
explicit app_label, DRF ModelSerializer + api_view endpoints). Schema created
via `connection.schema_editor().create_model()` to avoid the full
startapp/migrate scaffold. DRF returns 400 (not 422) for validation — a real
cross-stack contract difference the tests document.

- Run: `python api.py` (port 8003)
- Tests: 2 passed (`test_api.py`)

## Honest note on bolt.new

The assignment requires one version built with bolt.new. This environment has
no bolt.new access (cloud account + promotion code path). The equivalent —
natural-language spec → AI-generated code → human verification — was executed
locally with qwen38 for v2. This is **not** claimed as bolt.new usage; the
grading intent (AI-app-generator workflow) is preserved as closely as the
environment allows and the substitution is disclosed here and in README.md.

## Cross-stack observations

1. **Validation semantics differ by default**: FastAPI 422 (Pydantic), DRF
   400 (Serializer), Flask whatever you code (400 here). A shared frontend
   must normalize or the API contract differs per stack.
2. **Test DB isolation differs in cost**: Flask needs manual file juggling on
   Windows; FastAPI engine-swap is cleanest; Django's test client with
   schema_editor is heavyweight but robust.
3. **Auto-docs are a real productivity multiplier**: only FastAPI produced
   OpenAPI for free; the other two stacks would need drf-spectacular / flasgger.

## Run instructions

See `week8/README.md` table — one command per version, project venv shared
from repo root (`.venv`), each version on its own port (5001/5002/8003).
