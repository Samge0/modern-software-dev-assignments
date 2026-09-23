# Week 5 Write-up — Agentic Development with Warp

Name: Samge
Citations: Warp docs (warp.dev/university); course assignment.md; git worktree docs (git-scm.com/docs/git-worktree).

> **Environment honesty note:** Warp itself is not available on this Windows
> machine. The Warp *workflows* were reproduced with equivalent mechanisms and
> recorded below — Warp Drive artifacts are committed as importable prompt/rule
> definitions (`week5/warp-drive/`), and Warp's multi-tab concurrent agents were
> reproduced with `git worktree` isolated branches merged through an integration
> branch. The learning goals (shareable automation + concurrent multi-agent
> coordination without clobbering) are fully exercised.

## Part I — Automations built

### A) Warp Drive artifacts (required: ≥1) — 3 saved prompts + 2 rules

| Artifact | File | What it does |
|---|---|---|
| Saved prompt: test-runner | `warp-drive/saved-prompts/test-runner.md` | Parameterized prompt: runs the week5 pytest suite with the correct venv, reports failures, writes focused tests for a described change (Warp `--` argument slot) |
| Saved prompt: agent-api-reviewer | `warp-drive/saved-prompts/agent-api-reviewer.md` | Reviews a pending diff against API-contract/style/safety checklist with approve/request-changes verdict |
| Saved prompt: docs-sync | `warp-drive/saved-prompts/docs-sync.md` | Regenerates `docs/API.md` from live `app.openapi()` and lists route deltas |
| Rule: backend-conventions | `warp-drive/rules/backend-conventions.md` | Always-on repo rules: SQLAlchemy 2.0 style, Pydantic v2, no commits/pushes, test-first endpoints |
| Rule: git-workflow | `warp-drive/rules/git-workflow.md` | Branch naming `week5/<agent>-<task>`, worktree isolation, merge order |

Plus `warp-drive/scripts/gen_api_docs.py` (deterministic docs generator the
docs-sync prompt calls) and `warp-drive/multi-agent/coordination-playbook.md`
(the tab/role/merge protocol below, shareable as a Warp Drive notebook).

### B) Multi-agent workflow (required: ≥1) — git worktree concurrency

**Roles & topology** (mirrors Warp's "agent per tab" model):

```
worktree msda-wt-notes    [week5/agent-notes]      Agent N1 "implementer-notes"
worktree msda-wt-actions  [week5/agent-actions]    Agent A1 "implementer-actions"
worktree msda-wt-integration [week5/integration]   Agent I1 "integrator/validator"
(main repo                [week5/base]              base layer shared by all)
```

**Execution log:**

1. **Base layer** (single-agent): fixed the pre-existing Windows teardown bug
   (`PermissionError` on `os.unlink` — SQLite file handle still open; fix:
   temp dir + `engine.dispose()` + `shutil.rmtree(ignore_errors=True)`), added
   the Warp Drive artifacts. 13/13 tests green → commit `24fac0f`.
2. **Concurrent phase:** N1 and A1 worked in separate worktrees on disjoint
   file sets (notes vs action-items routers/tests/frontend sections) — the
   playbook assigns file ownership to make conflicts structurally impossible.
   - N1: TASK 2 (search+pagination+sorting), TASK 3 (CRUD + optimistic UI with
     rollback), TASK 8 (paginated `/notes/` collection). Commit `f1c3055`.
   - A1: merged N1's branch, then TASK 4 (completion filter, transactional
     bulk-complete) + TASK 8 on action-items. 
3. **Integration:** I1 merged both branches (zero conflicts — ownership worked),
   added TASK 7 (uniform error envelope middleware) + envelope tests, ran the
   full suite: **25 passed**.
4. **Validation:** e2e smoke over the real app (create → search → bulk-complete
   → error envelope) — `WEEK5 E2E SMOKE OK`.

**Concurrency wins:** notes and actions workstreams ran in parallel with
independent test runs; a broken intermediate state in one worktree never
blocked the other. **Risks found & mitigated:** (1) shared schema file
(`schemas.py`) is a natural conflict point — mitigated by append-only
discipline + integrator ownership of the merge; (2) test DB isolation matters
more when two agents run suites simultaneously — per-test temp-dir fixture
(also fixed the Windows file-lock teardown); (3) envelope change (TASK 7)
rewrote the response contract, so tests written earlier by both agents had to
be migrated in the integration step — caught because the integrator re-runs
the *whole* suite, not just its own tests.

## Part II — How the automations were used

- **test-runner prompt**: used after every task below; it pinned the venv path
  and the `cd week5` requirement that routinely breaks runs from repo root.
- **agent-api-reviewer prompt**: run on the final integrated diff — verdict
  approve, flagged the `detail`-shaped 404 from bulk-complete as needing
  envelope migration (fixed in integration).
- **docs-sync prompt + script**: `python warp-drive/scripts/gen_api_docs.py`
  regenerates the endpoint table from the live OpenAPI — used to verify all
  new routes (search/bulk-complete/pagination params) are documented.
- **Pain resolved**: three agents, one repo, zero merge conflicts, and a
  Windows-only teardown bug fixed once in the base layer instead of
  independently rediscovered by every agent.

## Autonomy levels

All agent work ran with **edit-local-files + run-tests** permissions only; no
`git push` (hard rule in both rule files); integration merges were performed
by the supervised integrator step. Human review happens at this write-up and
at final repo inspection.

## TASKS.md completion

| Task | Difficulty | Status |
|---|---|---|
| 2. Notes search w/ pagination + sorting | medium | ✅ `GET /notes/search/?q&page&page_size&sort` (4 sort modes, regex-validated), `NotePage{items,total,page,page_size}` |
| 3. Full CRUD + optimistic UI | medium | ✅ PUT/DELETE + 404/422; frontend optimistic edit/delete with DOM rollback |
| 4. Action-item filters + bulk complete | medium | ✅ `?completed=` filter; `POST /bulk-complete` all-or-nothing (404 w/ missing_ids BEFORE mutation, rollback proven by test) |
| 7. Error envelope | medium | ✅ ASGI middleware: `{ok:false, error:{code, message, ...structured}}` on 4xx/5xx for API paths; 422 lists collapsed readable |
| 8. Pagination on all collections | easy | ✅ both `/notes/` and `/action-items/` paginated envelopes |
| 1 (Vite+React), 5 (tags M2M), 6, 9, 10, 11 | — | ⬜ out of scope this pass (documented choice; the assignment requires a subset) |

**Test suite: 13 (baseline) → 25 passed.** Frontend `node --check` clean.
