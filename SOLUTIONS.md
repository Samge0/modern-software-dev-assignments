# SOLUTIONS OVERVIEW — Samge0's completed fork

All eight weeks of CS146S assignments completed, tested, and pushed.
Python venv at repo root `.venv` (Windows, Python 3.11); LLM backend is a
local vLLM server (`qwen38`) via `.env` (git-ignored).

| Week | Topic | Verification | Commit |
|---|---|---|---|
| 1 | Prompting techniques (6) | all 6 harnesses print SUCCESS | 42d1bf4 |
| 2 | FastAPI + LLM extractor | 19/19 pytest (incl. live LLM) | 7628152 |
| 3 | MCP server (Open-Meteo) | 9/9 pytest + live STDIO e2e (real API data) + HTTP bearer auth verified | d212e71 |
| 4 | Claude Code automations | 18/18 pytest; /tests /docs-sync /refactor-module commands; 2 SubAgents; CLAUDE.md; all TASKS 1-7 | 3b6ad2a |
| 5 | Warp multi-agent | 25/25 pytest; warp-drive prompts/rules; git-worktree concurrent agents; TASKS 2/3/4/7/8 | a1f98a4 |
| 6 | Semgrep security | 5/5 findings fixed, rescan = 0 findings; 9/9 pytest (6 security regression) | e836bcb |
| 7 | AI code review | 4 stacked PRs (all MERGED); manual vs AI review comparison; 30/30 pytest | cffa8d2 |
| 8 | Multi-stack build | Flask / FastAPI / Django+DRF, 2/2 tests each = 6/6 | 156d973 |

See each week's `writeup.md` / `SOLUTIONS.md` / `README.md` for details.

Note: LLM exercises use a local OpenAI-compatible endpoint instead of Ollama
(course models not pulled); see week1/backend_shim.py and week2/.env docs.
bolt.new substituted by local LLM generation flow (disclosed in week8/writeup.md).
