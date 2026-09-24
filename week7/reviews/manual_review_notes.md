# Manual Review Notes — week7 PRs (line-by-line, done before reading the AI reviews)

Reviewer: Samge (author + manual reviewer; paired-review not available, so a
deliberate second pass with fresh eyes on the diff, one PR at a time).

## PR #1 (task1: DELETE + stats + validation)

- `notes.py` delete_note: `db.delete()` + flush only, no commit — matches the
  `get_db` commit-on-success convention documented in week4/CLAUDE.md. ✅
- 204 with no body: correct REST semantics; re-delete 404 covered by test. ✅
- stats endpoint: pure function of stored content; no injection surface
  (no SQL, dict literal response). Note: `words` uses `.split()` so
  whitespace-joined CJK text counts as 1 word — acceptable, documented.
- schemas: `NotePatch` fields now `min_length=1` — empty-string PATCH → 422
  instead of silent wipe. **My concern**: PATCH semantics = partial update;
  making both fields optional-with-validation is right.
- conftest teardown: `engine.dispose()` before `rmtree(ignore_errors=True)` —
  the ignore_errors is deliberate (Windows handles), documented in fixture
  docstring. Verdict: **approve**.

## PR #2 (task2: extraction)

- `_is_action_line` vs `_strip_bullet` duplication of prefix knowledge — minor
  wart, kept for readability. nit.
- `_clean_item(keep_exclaim=...)`: the exclamation branch preserves "Ship it!"
  while rstrip(".") still applies — traced through the 3 call sites. ✅
- Imperative wordlist: fixed vocabulary, "please" included — bounded, no dep.
- `extract_tags` regex `#([A-Za-z0-9_]+)`: "#tag-two" yields "tag" only
  (hyphen not in class) — pinned by test with an explanatory comment. ✅
- Risk I flagged: keyword-prefix stripping changes public output shape
  ("TODO: write tests" → "Write tests") — breaking change for any consumer
  comparing raw strings; covered by updated test expectations. Verdict:
  **approve with note**.

## PR #3 (task3: tags)

- `note_tags` join table with CASCADE both sides; `ActionItem.note_id`
  SET NULL — deleting a note keeps orphan action items (intended: they're
  standalone todos), deleting a tag removes only associations. ✅
- `_get_or_create_tag` races: two concurrent attaches could INSERT twice →
  IntegrityError on unique(name). Test-level fine; production would need a
  catch-and-reselect. **warn** (documented, not fixed — out of scope).
- `attach_tags` idempotency via membership set: verified by re-attach test. ✅
- Tag name lowercase normalization: display casing lost; accepted trade-off.
  Verdict: **approve**.

## PR #4 (task4: pagination tests)

- Found and fixed a real bug: `skip` had no `ge=0` → negative skip accepted
  (SQLite treats OFFSET -1 as 0, so it silently worked but the contract was
  wrong; some DBs error). Fix is 1-line `Query(0, ge=0)`. ✅
- `test_sort_desc_is_default_and_reverses`: first assertion is tautological
  (`or True` fallback for same-second timestamps) — I left the deterministic
  id-based mirror check as the real assertion. Self-noted as a weak test.
- Disjoint-page proof (set isdisjoint) is the strongest assertion in the
  batch. Verdict: **approve**.

## Cross-cutting

- All 4 PRs: no commits/pushes inside agent flow beyond branch pushes; no
  secrets; no new dependencies.
- Suite progression across stack: 7 → 15 → 20 → 30 passed.
