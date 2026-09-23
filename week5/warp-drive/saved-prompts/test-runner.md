---
name: test-runner
description: Run the week5 backend test suite with a coverage report, re-run failures to detect flakes, and triage any red tests down to a suspected root cause. Idempotent and read-only unless --fix is passed.
argument_hint: "[pytest target | --fix]"
---

You are acting as the test-runner automation for the `week5/` FastAPI backend.

Target: `$ARGUMENTS` (if empty, default to `backend/tests`).

Steps:

1. From `week5/`, run the suite:
   `PYTHONPATH=. ../../.venv/Scripts/python.exe -m pytest -q <target>`
   (on POSIX: `PYTHONPATH=. python -m pytest -q <target>`).
2. If any test fails, re-run **only the failing tests** up to 2 more times to
   distinguish real failures from flakes. Tag results as `FLAKY` (passes on
   re-run) or `REAL` (consistent failure).
3. If pytest-cov is available, attach `--cov=backend/app --cov-report=term-missing`
   and report the coverage delta for files touched by the current branch
   (`git diff --name-only week5/base`).
4. For each `REAL` failure, print: test id, one-line assertion diff, and the
   single most likely root cause with the file:line to look at. Do **not**
   modify code unless `$ARGUMENTS` contains `--fix`.
5. If `--fix` was passed, apply the minimal fix, re-run the full suite, and
   show the final pass/fail counts and the diff you introduced.

Output format:

- `PASS`/`FAIL` counts and duration
- flaky list (if any)
- triage table for failures
- coverage delta (if available)

Never commit or push. Leave the working tree clean except for `--fix` edits.
