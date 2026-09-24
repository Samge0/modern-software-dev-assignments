# v3 — Django + DRF Notes API

Django 5 + DRF in a single module (settings.configure, app_label model,
schema_editor table creation). Satisfies the non-JS-language requirement.

## Run
```
python api.py           # http://127.0.0.1:8003
```

## Test
```
python -m pytest test_api.py -q
```

## Notes
DRF validation errors return 400 (not FastAPI's 422) — documented contract
difference. Tables created via schema_editor; notes.db is a gitignored artifact.
