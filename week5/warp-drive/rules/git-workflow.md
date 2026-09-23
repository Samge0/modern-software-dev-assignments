---
name: git-workflow
description: Branch/worktree discipline for the week5 multi-agent workflow — where agents may write, how branches are named, and how merges are gated.
scope: week5/
---

Rules for agents working in this repo:

1. **Never commit to `master` and never push.** All work lands on
   `week5/*` local branches; the human reviews and pushes.
2. **One task group per branch**, named `week5/agent-<role>` for implementers
   and `week5/integration` for the integrator.
3. **Worktrees, not stash.** Concurrent agents each get their own
   `git worktree`; an agent never edits a worktree it does not own.
4. **File ownership matrix** (reduces merge conflicts — respect it):
   - notes agent: `backend/app/routers/notes.py`, notes schemas,
     notes part of the frontend, `backend/tests/test_notes.py`
   - actions agent: `backend/app/routers/action_items.py`, action schemas,
     actions part of the frontend, `backend/tests/test_action_items.py`
   - shared files (`app.js`, `index.html`, `schemas.py`, `conftest.py`):
     edit only your section; the integrator owns the merge resolution.
5. Before handing a branch to the integrator: run the full test suite from
   your worktree and confirm green.
6. Merge order: integrator merges implementer branches into
   `week5/integration` one at a time, running tests between merges.
