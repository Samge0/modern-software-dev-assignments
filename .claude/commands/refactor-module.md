---
description: Safely refactor a week4 backend module (rename/move) keeping imports, lint and tests green
allowed-tools: Bash(../.venv/Scripts/python.exe:*), Read, Write, Edit, Grep, Glob
---

# Refactor Module

Rename or move a module under `week4/backend/app/` and fix every reference.

Usage: `/refactor-module <path> <new_path>` (paths relative to `week4/`,
e.g. `backend/app/services/extract.py backend/app/services/parser.py`).
With no arguments, analyze $ARGUMENTS as free-form refactor intent and
produce a plan first.

## Steps

1. `cd week4`. Parse `$ARGUMENTS` into old path and new path. If either is
   missing or ambiguous, stop and ask before touching anything.
2. Inventory references before moving:
   - `Grep` for the old module name across `backend/` and `frontend/`.
   - Note every importer, string reference, and test that imports it.
3. Do the move/rename with `Edit`/`Write` (create the new file with the old
   content, then delete the old one). Preserve the existing code style.
4. Update all importers found in step 2 (relative imports inside the package,
   absolute imports in tests).
5. Verify, in order, stopping at first failure:
   - `../.venv/Scripts/python.exe -m ruff check backend`
   - `../.venv/Scripts/python.exe -m black --check backend`
   - `../.venv/Scripts/python.exe -m pytest backend/tests -q`
6. Report a checklist: files created / deleted / modified, verification
   results, and anything left for the human (e.g. docs referencing the old
   module name).

## Safety

- One module per invocation; no opportunistic refactors of neighboring code.
- If tests fail after the move and the fix is not obvious in 2 attempts,
   revert (`git checkout -- .` scoped to the touched files) and report.
- Never `git commit` / `git push`.
