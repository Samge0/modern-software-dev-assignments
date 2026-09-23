---
description: Sync week4/docs/API.md with the live OpenAPI schema and list route deltas
allowed-tools: Bash(../.venv/Scripts/python.exe:*), Read, Write, Edit, Grep, Glob
---

# Docs Sync

Regenerate `week4/docs/API.md` from the application's real OpenAPI schema and
report any drift between docs and implementation.

## Steps

1. `cd week4`.
2. Dump the OpenAPI schema without starting a server:

   ```bash
   ../.venv/Scripts/python.exe -c "import json; from backend.app.main import app; print(json.dumps(app.openapi(), indent=2))" > /tmp/openapi.json
   ```

3. Read `/tmp/openapi.json` and extract for every path: method, summary,
   path parameters, query parameters, request body schema (field names,
   types, constraints such as `minLength`), response codes and schema.
4. Read the current `docs/API.md` (create it if missing) and compare:
   - routes present in OpenAPI but missing from the docs → add
   - routes documented but no longer implemented → remove, and note it
   - payload/response mismatch → update the docs to match the code
5. Rewrite `docs/API.md` with:
   - a one-line overview + base URL (`http://localhost:8000`)
   - a table of all endpoints (method | path | purpose)
   - per-endpoint sections: request/response examples, error codes (400/404/422)
   - a "Verified against /openapi.json on <date>" footer
6. Print a delta summary: `+ added`, `- removed`, `~ updated`, `= unchanged`
   for every route, and list any TODOs for the human reviewer.

## Rules

- The code is the source of truth; never "fix" the code from this command.
- Do not start a long-running server; use `app.openapi()` directly.
- No `git commit` / `git push`.
