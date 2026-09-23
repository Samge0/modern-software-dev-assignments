# Week 4 Write-up
Tip: To preview this markdown file
- On Mac: press `Command (⌘) + Shift + V`
- On Windows/Linux: press `Ctrl + Shift + V`

## SUBMISSION DETAILS

Name: Samge \
SUNet ID: N/A (non-matriculated self-study) \
Citations: Anthropic Claude Code best practices (anthropic.com/engineering/claude-code-best-practices); Claude Code SubAgents docs (docs.anthropic.com/en/docs/claude-code/sub-agents); starter code under `week4/` by course staff.

This assignment took me about **6** hours to do.

## YOUR RESPONSES

### Automation #1 — `/tests` custom slash command

a. Design inspiration
> Claude Code best practices — "CURSOR/Claude Code works best with a curated list of allowed tools" and "customize system reminders / create reusable workflows for repeated routines". Test-running is the single most repeated routine in this repo (every TASK ends with "add tests"), so encoding the exact interpreter path, cwd, fail-fast flags, and the *diagnose-before-edit* discipline into a slash command removes both the invocation friction and the drift when the venv path changes.

b. Design (goals / inputs / outputs / steps)
> - Goal: one-keystroke, deterministic test run for the week4 backend, with a controlled repair loop when red.
> - Input: optional `$ARGUMENTS` — pytest node id, `-k` filter, or extra flags; empty = full suite.
> - Output: pass/fail count, root-cause diagnosis and minimal fix for failures, final suite state.
> - Steps: run `../.venv/Scripts/python.exe -m pytest backend/tests -q --maxfail=1 $ARGUMENTS` from `week4/` → if green, stop; if red, read failing test + matching source, apply the minimal fix consistent with house style, re-run the full suite (no `--maxfail`), summarize before→after.
> - File: `.claude/commands/tests.md` (repo root — visible to all weeks; parameterized by the `week4/` cwd convention documented in `week4/CLAUDE.md`).

c. How to run / expected output / rollback
> Run: in Claude Code at repo root, type `/tests` (or `/tests -k search`).
> Expected: `N passed` line from pytest; on failure, a diagnosis + the applied minimal diff.
> Safety: command file declares `allowed-tools` restricted to the venv pytest invocation plus Read/Grep/Glob; explicit rule forbids weakening tests to make them pass, forbids `git commit`/`git push`. Rollback: all changes are working-tree only — `git checkout -- <file>` reverts anything.

d. Before vs. after
> Before: recall or re-derive the correct interpreter (`../.venv/Scripts/python.exe`), remember to `cd week4` (running from repo root raises `ModuleNotFoundError`), remember flags, then hand-write the diagnosis prompt each time. ~5 minutes and error-prone every cycle.
> After: `/tests` → done. The repair loop follows the same discipline every time.

e. How it enhanced the starter app
> TASKS 2–6 are test-heavy (16 new tests were added across `test_notes.py`, `test_action_items.py`, `test_extract.py`). `/tests` was the gate after each task. Concretely, it caught: (1) the pre-existing Windows teardown `PermissionError` in `conftest.py` (fixed: per-test temp dir + `engine.dispose()`), and (2) a bad test expectation in `test_search_notes_matches_title_and_content` — `"groceries"` does not contain the substring `"grocery"`, verified against SQLite directly (`'groceries list' LIKE '%grocery%'` → false), so the assertion was corrected and a `q="grocer"` case added that genuinely matches both notes.

### Automation #2 — `/docs-sync` custom slash command

a. Design inspiration
> Best-practices doc section on generating docs and commit-message style — "have Claude read the code and produce docs; keep humans for review". TASK 7 ("docs drift check") exists precisely because hand-written API docs rot; the command turns the check into a one-shot regeneration with an explicit delta report instead of a manual eyeball diff.

b. Design (goals / inputs / outputs / steps)
> - Goal: regenerate `week4/docs/API.md` from the *live* OpenAPI schema and report route-level drift.
> - Input: none (works off the current code state).
> - Output: rewritten `docs/API.md` (route table, per-endpoint sections, error codes) + a `+ added / - removed / ~ updated / = unchanged` delta summary.
> - Steps: dump `app.openapi()` to JSON without starting a server → extract methods/params/schemas/constraints → diff against current `docs/API.md` → rewrite docs → print deltas and any TODOs for the human.
> - File: `.claude/commands/docs-sync.md`.

c. How to run / expected output / rollback
> Run: `/docs-sync` in Claude Code.
> Expected: `docs/API.md` rewritten; delta list printed. Verified output this session: the generated file documents all 10 routes including the new `PUT/DELETE /notes/{id}` and `GET /notes/search/?q=`, plus the `NoteUpdate` schema and the `title` 1–200 length constraint surfaced from Pydantic into the spec.
> Safety: "code is the source of truth" rule — the command never edits code, never starts a long-running server (uses `app.openapi()` in-process). Rollback: `git checkout -- week4/docs/API.md`.

d. Before vs. after
> Before (TASK 7 as written): read `main.py` and both routers, hand-transcribe endpoints into `API.md`, then manually compare against `http://localhost:8000/openapi.json` in a browser — 30+ minutes, silently wrong within one PR.
> After: `/docs-sync` regenerates and diffs in one pass; drift becomes mechanically detectable (`routes in spec but not in docs`).

e. How it enhanced the starter app
> Produced `week4/docs/API.md` (TASK 7) covering: 3 root routes + notes CRUD/search + action-items + complete endpoint; per-schema field constraints (`NoteCreate.title` 1–200 chars, `content` ≥ 1); the 404/422 error contract; and an inline re-verification command so future maintainers can repeat the check without the automation.

### *(Optional) Automation #3* — SubAgents + `CLAUDE.md` + `/refactor-module`

a. Design inspiration
> SubAgents docs: "delegate bounded, well-specified subtasks (like test generation) to agents with their own context window, restricted tools, and a single responsibility." Plus the best-practices advice to keep a `CLAUDE.md` as the always-loaded source of truth for repo layout and conventions. I combined three mechanisms:

b. Design (goals / inputs / outputs / steps)
> - `week4/CLAUDE.md` — always-on context: project map (which file does what), exact Windows commands (venv interpreter path, `cd week4` requirement), SQLAlchemy 2.0 / Pydantic v2 conventions, and workflow guardrails (test-first for new endpoints; **never commit/push**).
> - `week4/.claude/agents/test-runner.md` — SubAgent owning tests only. Input: description of a change. Output: pytest files in house style + suite result. Hard rule: if app code is wrong, reports the failure as a work order instead of fixing it (separation of powers).
> - `week4/.claude/agents/code-reviewer.md` — SubAgent reviewing the pending `git diff` against a 6-point checklist (spec fit / style via black+ruff / safety / error contract / docs drift / tests) with a `approve / request-changes / blocked` verdict. Read-only by construction (no Edit tool).
> - `/refactor-module` — slash command that renames/moves a backend module, fixes all importers, and gates on ruff → black → pytest before reporting.

c. How to run / expected output / rollback
> - `CLAUDE.md`: automatic (Claude Code reads it whenever working under `week4/`). Observed effect: no more wrong-interpreter or wrong-cwd command proposals.
> - SubAgents: `@test-runner please cover the new PUT /notes/{id} endpoint` or let Claude Code auto-delegate (the agents' `description` fields mark them proactive: test-runner fires on backend changes, code-reviewer after edits).
> - `/refactor-module backend/app/services/extract.py backend/app/services/parser.py` → expected: file moved, imports updated, `ruff check` clean, `black --check` clean, `18 passed`.
> - Rollback: nothing commits; `git checkout -- .` (scoped) reverts. SubAgents have no push/commit rights.

d. Before vs. after
> Before: every session re-explains the repo layout and the Windows venv quirk; review is ad-hoc ("looks fine"); refactors are hope-and-pray with manual import chasing.
> After: layout/conventions load automatically; review produces an explicit checklist verdict; refactors carry a mechanical three-gate verification.

e. How it enhanced the starter app
> The test-runner SubAgent pattern (tests written against the documented contract, failures reported not patched) directly produced the TASK 2–6 test layer: 9 notes tests (search case-insensitivity on both sides via `func.lower()`, update/delete 404 paths, validation 422s), 4 action-item tests (complete idempotency, 404, isolation, validation), 3 extraction tests (`#tag` parsing with punctuation stripping + case-insensitive dedupe). `CLAUDE.md`'s guardrail kept the whole session commit-free as required.

## Summary of TASKS.md completion

| Task | Status | Key changes |
|---|---|---|
| 1. pre-commit | Done | Installed pre-commit 4.6.2 + black 26.5.1 + ruff 0.16.8 into `.venv`; `pre-commit run --all-files` executed; ruff `Optional`→`\| None` and black formatting applied. Root `.pre-commit-config.yaml` added (pre-commit requires it at repo root). Note: the EOF/trailing-whitespace hooks also normalized ~80 files across other weeks — legitimate hook output; scope with `git checkout -- week5 week6 week7 week8` if undesired. |
| 2. Search endpoint | Done | `GET /notes/search/?q=` with `func.lower()` both sides (true case-insensitive substring on title+content); frontend search form + clear button; 4 tests. |
| 3. Complete action-item flow | Done | `PUT /action-items/{id}/complete` implemented, idempotent, 404 path; UI already wired; 4 tests. |
| 4. Extraction `#tag` support | Done | `extract_tags()` in `services/extract.py` (punctuation-stripped, case-insensitive dedupe); 3 tests. Optional `POST /notes/{id}/extract` not implemented (scope choice). |
| 5. Notes CRUD PUT/DELETE | Done | `PUT /notes/{id}` (404 on missing), `DELETE /notes/{id}` (204/404); frontend Edit (prompt-based) + Delete (confirm) per note; 4 tests. |
| 6. Validation & errors | Done | `schemas.py`: `Field(min_length=1, max_length=200)` on title, `min_length=1` on content, `NoteUpdate` schema; 422 tests. |
| 7. API.md docs | Done | Generated via the `/docs-sync` automation (see Automation #2). |

Test suite: **3 passed (baseline, with 2 teardown errors) → 18 passed, 0 failed.**

Nothing was committed or pushed; all changes are in the working tree for review.
