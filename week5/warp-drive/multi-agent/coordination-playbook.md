# Multi-Agent Coordination Playbook (Week 5)

Simulates Warp's "one agent per tab" concurrency using `git worktree`.
This playbook is pasted into the orchestrator tab; each implementer tab also
receives the two `rules/` files as context.

## Roles

| Role | Branch | Worktree | Owns |
|------|--------|----------|------|
| Orchestrator (human + this playbook) | — | main repo | task split, merge gating |
| Agent N1 "notes" (implementer) | `week5/agent-notes` | `../msda-wt-notes` | TASK 2, TASK 3, notes half of TASK 8 |
| Agent N2 "actions" (implementer) | `week5/agent-actions` | `../msda-wt-actions` | TASK 4, actions half of TASK 8 |
| Agent V "validator" | `week5/integration` | `../msda-wt-integration` | TASK 7, TASK 9, TASK 10 tests, merges, docs-sync |

## Bootstrap (orchestrator)

```bash
git checkout -b week5/base          # shared infra commit (conftest fix, warp-drive/, created_at columns)
git worktree add ../msda-wt-notes      -b week5/agent-notes   week5/base
git worktree add ../msda-wt-actions    -b week5/agent-actions week5/base
git worktree add ../msda-wt-integration week5/integration     week5/base
```

## Task briefs

- **N1:** `GET /notes/search` with `q/page/page_size/sort` (TASK 2) +
  `PUT`/`DELETE /notes/{id}` + payload validation (TASK 3) +
  `GET /notes/` pagination (TASK 8-notes). Frontend: search box, sort select,
  pagination, optimistic edit/delete.
- **N2:** `GET /action-items/?completed=` filter + `POST /action-items/bulk-complete`
  (TASK 4) + `GET /action-items/` pagination (TASK 8-actions). Frontend: filter
  toggle, bulk-complete checkboxes, pagination.
- **V:** merge N1 + N2 (resolve the *anticipated* conflicts in
  `app.js`/`index.html`/`schemas.py`), then implement the response envelope
  middleware + error handlers (TASK 7), SQLite indexes + query-plan test
  (TASK 9), cross-cutting error/pagination tests (TASK 10), regenerate
  `docs/API.md` via the docs-sync prompt, and fill `writeup.md`.

## Concurrency protocol

1. All three agents start from the same `week5/base` commit.
2. Implementers work simultaneously in their own worktrees — no locks needed
   because of the file-ownership matrix; shared files are section-scoped.
3. Handoff = "branch pushed" equivalent: agent reports `tests green` and stops.
4. Integrator merges **one branch at a time**, running the suite between merges
   (merge → test → merge → test), so any regression is attributable.
5. Conflicts in shared files are resolved by the integrator following the
   ownership matrix (take N1's notes section + N2's actions section).
6. Validator verdict (`agent-api-reviewer` prompt) gates the final state:
   suite green + rules satisfied, otherwise back to the implementer.

## Wins / risks (recorded for the writeup)

- **Win:** wall-clock ≈ max(N1, N2) instead of N1+N2 for the two independent
  feature sets; worktrees give real file isolation, not just branches.
- **Risk 1:** both agents legitimately need `schemas.py` / `app.js` /
  `index.html` → merge conflicts (anticipated, section-scoped, integrator-owned).
- **Risk 2:** contract drift between agents (e.g. pagination shape) — mitigated
  by the `backend-conventions` rule attached to both agents.
- **Risk 3:** shared test DB / seed drift — mitigated because each worktree has
  its own `data/` dir (gitignored) and tests use per-test temp DBs.
