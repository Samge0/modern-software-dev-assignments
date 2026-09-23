---
name: docs-sync
description: Regenerate week5/docs/API.md from the live /openapi.json of the running FastAPI app and report route deltas (added/removed/changed) against the previous revision. Read-only against source code; writes only docs/API.md.
argument_hint: "[base_url] (default http://127.0.0.1:8000)"
---

You are acting as the docs-sync automation for the `week5/` backend.

Base URL: `$ARGUMENTS` (default `http://127.0.0.1:8000`).

Steps:

1. If the API is not running, start it headlessly from `week5/`:
   `PYTHONPATH=. python -m uvicorn backend.app.main:app --port 8000 &`
   and wait until `GET <base_url>/openapi.json` answers.
2. Run the helper script (stdlib only, no extra deps):
   `python warp-drive/scripts/gen_api_docs.py --base-url <base_url> --out docs/API.md --diff-against docs/API.md`
   The script rewrites `docs/API.md` from the OpenAPI document and prints a
   **route delta** section (added / removed / changed endpoints with a short
   parameter-level diff).
3. If the delta is empty, say so and stop (idempotent no-op).
4. If routes changed, append the delta summary to the generated file's
   changelog section and report the delta back to the user in one table.

Constraints:

- Never modify application source or tests.
- The generated doc must include, for each endpoint: method, path, query
  params (with defaults/constraints), request schema, response schema, and
  error envelope codes.
- Keep it deterministic: two consecutive runs on the same app must produce
  byte-identical output.
