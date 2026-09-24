# Week 8 — Multi-Stack Notes App (3 versions)

The same minimal notes CRUD application (create / read / update / delete +
validation + error handling + tests) implemented in **three distinct stacks**.

## Versions

| # | Folder | Stack | Run | Tests |
|---|---|---|---|---|
| 1 | `v1-flask/` | Flask 3 + raw sqlite3 (Python micro-framework) | `python app.py` → http://127.0.0.1:5001 | `pytest test_app.py` (2 passed) |
| 2 | `v2-fastapi/` | FastAPI + SQLAlchemy 2 + Pydantic v2 | `uvicorn app:app --port 5002` → /docs for OpenAPI | `pytest test_app.py` (2 passed) |
| 3 | `v3-django/` | Django 5 + DRF (non-JS full-stack framework) | `python api.py` → http://127.0.0.1:8003 | `pytest test_api.py` (2 passed) |

All three use project-root `.venv` (see repo README for setup).

## Functional scope (identical across versions)

- CRUD on `notes` (id, title 1–200, content ≥1, created_at)
- 404 for missing ids, 400/422 for validation failures
- `/health` endpoint
- Smoke tests covering full CRUD roundtrip + validation

## Honest note on bolt.new

The assignment requires ≥1 version built with **bolt.new** (AI app generation
platform). bolt.new requires a cloud account + credits, unavailable in this
environment. Instead, **v2 (FastAPI)** was generated through an equivalent
local AI-assisted flow: a natural-language spec → local LLM (qwen38) →
code, then manually verified and tested. v1 and v3 were hand-written to
contrast framework ergonomics. This substitution is recorded transparently
in `writeup.md` rather than claimed as bolt usage.

## Stack comparison (learnings)

| Aspect | Flask | FastAPI | Django+DRF |
|---|---|---|---|
| LOC for same scope | ~110 | ~105 | ~120 (single-file config) |
| Validation | manual `if` | Pydantic Field (auto 422) | ModelForm/Serializer (400) |
| Docs | none | OpenAPI auto | none (DRF browsable API) |
| Boilerplate | minimal | minimal | settings/migration machinery |
