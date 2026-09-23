# API Reference — Week 4 Starter App

> Generated from the live OpenAPI spec (`/openapi.json`) via the `/docs-sync`
> automation. Verify drift with: `make docs-sync` (or re-run `/docs-sync`).

Base URL (local dev): `http://localhost:8000`

## Routes

| Method | Path | Summary | Success | Notes |
|---|---|---|---|---|
| GET | `/` | Root | 200 | Service info |
| GET | `/notes/` | List notes | 200 | Returns `NoteRead[]` |
| POST | `/notes/` | Create note | 201 | Body: `NoteCreate` |
| GET | `/notes/search/?q=` | Search notes | 200 | Case-insensitive substring match on title and content (SQLAlchemy `func.lower()` on both sides); empty/missing `q` returns all notes |
| GET | `/notes/{note_id}` | Get note | 200 / 404 | |
| PUT | `/notes/{note_id}` | Update note | 200 / 404 | Body: `NoteUpdate` (full replace of title+content) |
| DELETE | `/notes/{note_id}` | Delete note | 204 / 404 | |
| GET | `/action-items/` | List action items | 200 | Returns `ActionItemRead[]` |
| POST | `/action-items/` | Create action item | 201 | Body: `ActionItemCreate` |
| PUT | `/action-items/{item_id}/complete` | Mark complete | 200 / 404 | Idempotent — completing an already-completed item succeeds |

## Schemas

### `NoteCreate` / `NoteUpdate`
- `title`: string, **1–200 chars** (422 on violation)
- `content`: string, **min 1 char** (422 on violation)

### `NoteRead`
- `id`: integer
- `title`: string
- `content`: string

### `ActionItemCreate`
- `description`: string, **min 1 char**

### `ActionItemRead`
- `id`: integer
- `description`: string
- `completed`: boolean

### Errors
- `404`: `{"detail": "Note not found"}` / `{"detail": "Action item not found"}`
- `422`: FastAPI `HTTPValidationError` (field-level validation messages)

## Drift check

The OpenAPI spec is the source of truth. To regenerate this file:

```bash
cd week4
../.venv/Scripts/python.exe -c "import sys; sys.path.insert(0,'backend'); from app.main import app; import json; print(json.dumps(app.openapi(), indent=1))"
```

Compare routes above against `paths` in the output (or open `http://localhost:8000/openapi.json` while the app runs).
