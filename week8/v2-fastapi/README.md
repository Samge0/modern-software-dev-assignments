# v2 — FastAPI Notes API

FastAPI + SQLAlchemy 2 + Pydantic v2. AI-generated (local qwen38; bolt.new
substitute — see ../writeup.md), manually reviewed and tested.

## Run
```
uvicorn app:app --port 5002    # OpenAPI docs at /docs
```

## Test
```
python -m pytest test_app.py -q   # temp DB auto-isolated
```

## Env
No .env needed; DB is notes.db (gitignored).
