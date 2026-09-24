# v1 — Flask Notes API

Flask 3 + raw sqlite3, single file.

## Setup
Use the repo-root `.venv` (Python 3.11, flask installed).

## Run
```
python app.py          # http://127.0.0.1:5001
```

## Test
```
python -m pytest test_app.py -q
```

## Endpoints
GET/POST /notes, GET/PUT/DELETE /notes/{id}, GET /health. Validation: 400 on
bad payloads, 404 on missing ids. DB: notes.db (gitignored artifact).
