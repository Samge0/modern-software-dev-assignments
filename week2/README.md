# Action Item Extractor (Week 2)

A FastAPI + SQLite application that converts free-form notes into enumerated action items —
with both a heuristic extractor and an LLM-powered extractor backed by a local
OpenAI-compatible endpoint (vLLM serving `qwen38`).

## Overview

- **Backend**: FastAPI (see `app/`) with typed Pydantic request/response schemas
- **Database**: SQLite via a thin `app/db.py` data-access layer (notes + action_items tables)
- **Frontend**: static HTML/JS served by FastAPI (`frontend/index.html`) — no Node toolchain
- **Extraction engines**:
  - `POST /action-items/extract` — regex/heuristic extraction (original)
  - `POST /action-items/extract-llm` — LLM extraction via local vLLM endpoint (new)

## Setup & Run

```bash
# from repo root, with the project venv active
conda activate cs146s        # or your python >= 3.10 environment
poetry install --no-interaction

# configure the LLM endpoint (git-ignored)
cat > .env <<'EOF'
OPENAI_BASE_URL=http://127.0.0.1:16869/v1
OPENAI_API_KEY=<your-key>
LLM_EXTRACT_MODEL=qwen38
EOF

# run the server (from repo root)
poetry run uvicorn week2.app.main:app --reload
```

Then open http://127.0.0.1:8000/ for the UI and http://127.0.0.1:8000/docs for OpenAPI docs.

> The original assignment targets Ollama structured outputs. This deployment uses the
> OpenAI-compatible JSON mode (`guided_json`) of a local vLLM server, which is the same
> capability with a different transport; `week2/app/services/extract_llm.py` is the only
> place the endpoint is referenced.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/notes` | Create a note (`{"content": str}`) |
| GET | `/notes` | List all notes |
| GET | `/notes/{id}` | Fetch one note (404 if missing) |
| POST | `/action-items/extract` | Heuristic extraction (`{"text": str, "save_note": bool}`) |
| POST | `/action-items/extract-llm` | LLM extraction (same request shape) |
| GET | `/action-items?note_id=` | List action items (optionally filtered by note) |
| POST | `/action-items/{id}/done` | Mark done/undone (`{"done": bool}`) |

All request/response bodies are validated by Pydantic models in `app/schemas.py`;
validation failures return HTTP 422 with details, missing resources return 404,
and LLM backend failures surface as 502.

## Tests

```bash
# from repo root
poetry run pytest week2/tests -q
```

19 tests cover: heuristic extraction (bullets/checkboxes/keywords/empty), LLM output
parsing (fenced JSON, dict shapes, dedup), API CRUD roundtrips, extraction flows,
done-marking, validation errors, and one live LLM endpoint test (auto-skipped
when `.env` is absent).
