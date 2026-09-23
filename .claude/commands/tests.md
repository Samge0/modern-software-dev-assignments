---
description: Run week4 backend tests (optionally filtered), report failures, suggest fixes
allowed-tools: Bash(../.venv/Scripts/python.exe -m pytest:*), Read, Grep, Glob
---

# Test Runner

Run the week4 test suite with the repo's Windows venv and report results.

## Steps

1. `cd week4` (all commands below run from the `week4/` directory; on this
   machine the venv python is `../.venv/Scripts/python.exe`).
2. Run the suite:

   ```bash
   ../.venv/Scripts/python.exe -m pytest backend/tests -q --maxfail=1 $ARGUMENTS
   ```

   `$ARGUMENTS` may be empty (full suite), a node id
   (`backend/tests/test_notes.py::test_search`), or extra pytest flags
   (`-k search`).
3. If everything passes, report the pass count and stop — do not touch code.
4. If a test fails:
   - Read the failing test first (`Read` the test file) to understand intent.
   - Read the matching source module under `backend/app/`.
   - Diagnose the root cause; propose the **minimal** fix consistent with the
     existing code style (no drive-by refactors).
   - Apply the fix, then re-run the full suite (`-q`, no `--maxfail`).
5. Summarize: tests before → after, files changed, and any behavior that
   remains broken with a suggested next step.

## Rules

- Never modify a test to make it pass unless the test itself is wrong; if the
  test is wrong, explain why before changing it.
- Never `git commit` or `git push` — leave the working tree dirty for review.
- Keep changes small enough to review in one glance.
