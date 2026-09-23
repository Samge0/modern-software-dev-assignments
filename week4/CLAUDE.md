# Week 4 — Developer's Command Center (FastAPI + SQLAlchemy + static frontend)

## Map

- `backend/app/main.py` — FastAPI app, mounts `/static`, serves `frontend/index.html` at `/`
- `backend/app/routers/notes.py` — notes CRUD + `/notes/search/`
- `backend/app/routers/action_items.py` — action items CRUD + `/action-items/{id}/complete`
- `backend/app/models.py` — SQLAlchemy models (`Note`, `ActionItem`), `Base = declarative_base()`
- `backend/app/schemas.py` — Pydantic v2 schemas (`model_validate`, `from_attributes`)
- `backend/app/db.py` — engine/`SessionLocal`, `get_db` dependency, seed loader (`data/seed.sql`, runs only when the DB file is newly created)
- `backend/app/services/extract.py` — plain-Python note → action-item extraction
- `frontend/` — no build step; `app.js` speaks JSON to the API
- `backend/tests/` — pytest + FastAPI `TestClient`, per-test temp SQLite via `conftest.py`

## Commands (run from `week4/`)

- Run app: `PYTHONPATH=. ../.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload`
- Tests: `../.venv/Scripts/python.exe -m pytest backend/tests -q`
- Format: `../.venv/Scripts/python.exe -m black .` (line length 100)
- Lint: `../.venv/Scripts/python.exe -m ruff check .` (rules E/F/I/UP/B, E501 ignored)
- pre-commit: `../.venv/Scripts/python.exe -m pre_commit run --all-files` (config: `pre-commit-config.yaml` in this folder)

## Conventions

- Python 3.10+, SQLAlchemy 2.0 style (`select()` + `db.execute`, `db.get(Model, id)`), Pydantic v2.
- Routers own their `HTTPException`s; 404 detail strings are human-readable ("Note not found").
- DB writes go through `get_db` (commit on success, rollback on error) — do not commit inside handlers.
- Frontend fetches via `fetchJSON()`; keep the no-toolchain constraint (no npm).

## Workflow guardrails

- When asked to add an endpoint: write a failing test first, implement the
  smallest change, re-run the suite, then check docs drift (`/docs-sync`).
- Never `git commit` or `git push`; leave changes staged-in-working-tree for
  human review.
- Windows host: venv interpreter is `../.venv/Scripts/python.exe`, bash is
  git-bash (POSIX paths work).
