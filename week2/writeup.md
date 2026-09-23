# Week 2 Write-up

## SUBMISSION DETAILS

Name: **Samge** \
Citations: **Completed with an AI coding agent (ZCode) driving Cursor-style agentic development; all prompts and outputs documented below.**

This assignment took me about **4** hours to do (agent-assisted; includes LLM-endpoint adaptation work).

## YOUR RESPONSES

Environment note: instead of Ollama (course default), the LLM backend is a local
OpenAI-compatible vLLM server (`qwen38` = Qwen3.8-9B-GPTQ-Int4). The assignment's
Ollama structured-output feature maps 1:1 to vLLM's `guided_json` JSON-constrained
decoding, so the learning goal (constrained structured outputs from a local model)
is preserved. Configuration lives in the git-ignored `.env`.

### Exercise 1: Scaffold a New Feature
Prompt:
```
Implement extract_action_items_llm(text: str) -> List[str] in week2/app/services/extract_llm.py.
Use the OpenAI-compatible endpoint from .env (OPENAI_BASE_URL/OPENAI_API_KEY/LLM_EXTRACT_MODEL).
Return a JSON array of strings. Use structured/JSON-constrained output (guided_json),
temperature 0, and a system prompt with: include tasks/todos/follow-ups, exclude narrative,
strip bullet prefixes, dedupe, return [] when none. Add a tolerant parser (code fences,
{"item": ...} dict shapes, dedup) and a __main__ demo.
```

Generated Code Snippets:
```
week2/app/services/extract_llm.py (entire file, lines 1-118)
  - extract_action_items_llm(): OpenAI client -> guided_json array-of-strings schema,
    temperature 0.0, thinking disabled for speed
  - _parse_items(): strips fences/prose, accepts dict shapes, dedups preserving order
week2/app/routers/action_items.py: shared _extract() flow calling engine="llm"
```

Verification: standalone run returns `["Ship the migration script", "Ping legal about the DPA", "Schedule a design review next week"]` on the demo input — exactly the 3 actions, narrative excluded.

### Exercise 2: Add Unit Tests
Prompt:
```
Write unit tests for extract_action_items_llm covering: bullet lists, keyword-prefixed lines,
empty input, plus pure-parser tests (plain array, fenced-with-prose, dict shapes + dedup,
invalid JSON). Live-endpoint tests should auto-skip when .env is absent. Also add FastAPI
TestClient end-to-end tests with a temp DB: index page, note CRUD + 404/422, both extract
endpoints, done-marking roundtrip, live LLM extract.
```

Generated Code Snippets:
```
week2/tests/test_extract.py (rewritten: 3 heuristic regression + 4 parser + 4 live LLM tests)
week2/tests/test_api.py (new: 9 TestClient tests with temp DB isolation via env override)
```

Result: `pytest week2/tests -q` → **19 passed** (live LLM tests included; would be 15 if endpoint absent via skip).

### Exercise 3: Refactor Existing Code for Clarity
Prompt:
```
Refactor the week2 backend: introduce app/schemas.py with Pydantic request/response models
(NoteCreate/NoteOut/ExtractRequest/ExtractResponse/ActionItemOutFull/MarkDoneRequest...)
replacing Dict[str, Any] payloads; add GET /notes list endpoint; add db.get_action_item()
so mark_done can 404 on unknown ids; extract a shared _extract() helper for both engines;
keep all existing behaviour compatible.
```

Generated Code Snippets:
```
week2/app/schemas.py (new, entire file — single source of truth for the API contract)
week2/app/routers/notes.py (typed NoteCreate/NoteOut + new GET /notes)
week2/app/routers/action_items.py (typed models, shared _extract(), 404 on missing item)
week2/app/db.py lines 117-125 (get_action_item added)
```

### Exercise 4: Use Agentic Mode to Automate Small Tasks
Prompt:
```
Add POST /action-items/extract-llm endpoint (same request schema, engine="llm", 502 on backend
failure) and GET /notes endpoint. Update frontend/index.html: add "Extract LLM" button calling
the new endpoint, "List Notes" button fetching and rendering all notes, show an engine badge
on extracted items, HTML-escape note content when rendering.
```

Generated Code Snippets:
```
week2/app/routers/action_items.py: extract_llm() endpoint
week2/frontend/index.html: #extract-llm and #list-notes buttons, renderItems()/extract() helpers
```

### Exercise 5: Generate a README from the Codebase
Prompt:
```
Analyze the week2 codebase (app/, frontend/, tests/) and generate week2/README.md covering:
project overview, setup/run instructions including .env for the vLLM endpoint, an API endpoint
table for all 7 routes, error-handling semantics (422/404/502), and how to run the 19 tests.
```

Generated Code Snippets:
```
week2/README.md (new, entire file)
```

## Engineering notes beyond the rubric

1. **JSON-constrained decoding beats prompt-only JSON.** Using vLLM's `guided_json` makes
   malformed output structurally impossible; the tolerant parser then only defends against
   wrapping prose (which the constraint doesn't forbid) — defense in depth.
2. **Pinning existing quirks in tests is a feature.** `test_extract_keyword_prefixed`
   documents that the original heuristic detects `todo:` lines but does not strip the
   prefix; changing that silently would break downstream consumers.
3. **DB isolation for API tests** via env override + module import order keeps the dev
   database untouched while exercising the real FastAPI stack end-to-end.
