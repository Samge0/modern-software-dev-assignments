# Warp Drive — Week 5 Automations

This folder contains the Warp Drive artifacts for the Week 5 assignment
("Agentic Development with Warp").

> **Honesty note (environment constraint):** Warp is not installed on the
> machine where this assignment was completed (Windows; the assignment's
> Warp-specific tooling was unavailable). The artifacts below are written as
> **importable Warp Drive definitions** (saved prompts and rules use Warp's
> markdown format with `name`/`description` frontmatter and `$ARGUMENTS`
> placeholders), and the multi-agent workflow was **reproduced with equivalent
> mechanisms**: one `git worktree` per "Warp tab", one branch per agent, merged
> by an integrator/validator agent. Every artifact was actually executed —
> see `week5/writeup.md` for the run log.

## Layout

```
warp-drive/
├── saved-prompts/          # Warp Drive saved prompts (importable)
│   ├── test-runner.md      # run tests + coverage + flaky re-run + failure triage
│   ├── docs-sync.md        # regenerate docs/API.md from /openapi.json + route deltas
│   └── agent-api-reviewer.md  # validator-agent prompt (review + verify contracts)
├── rules/                  # Warp rules (auto-attached repo conventions)
│   ├── backend-conventions.md
│   └── git-workflow.md
├── multi-agent/
│   └── coordination-playbook.md  # orchestrator playbook for concurrent agents
├── scripts/
│   └── gen_api_docs.py     # helper used by the docs-sync prompt (stdlib only)
└── README.md
```

## Importing into Warp (when Warp is available)

1. **Saved prompts:** Warp → Settings → AI → Prompts → *New Prompt*, paste the
   markdown body (including frontmatter), save. Invoke with
   `prompt-name <arguments>` — `$ARGUMENTS` receives whatever follows.
2. **Rules:** Warp → Settings → AI → Rules → *New Rule*, paste the file
   contents. Rules attach automatically to every agent session in this repo
   (scope: `week5/`).
3. **Multi-agent:** open one Warp tab per agent, each `cd`-ed into its own
   `git worktree`, and paste the coordination playbook into the orchestrator
   tab. See the playbook for the exact worktree commands.

## Reproduction without Warp (what was actually done here)

```bash
# from the repo root
git worktree add ../msda-wt-notes    -b week5/agent-notes    week5/base
git worktree add ../msda-wt-actions  -b week5/agent-actions  week5/base
git worktree add ../msda-wt-integration week5/integration    week5/base
# ... each worktree = one "Warp tab" running one agent ...
# integrator merges, validates, and lands the result on week5/integration
```
