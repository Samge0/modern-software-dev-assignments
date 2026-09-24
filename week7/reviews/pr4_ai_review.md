# AI Review — PR #4: week7/task4: pagination & sorting tests

(reviewed by local qwen38 via OpenAI-compatible endpoint)

1. SUMMARY: PR adds pagination/sorting tests and query param validation to the notes router, but contains a critical logic bug in the sort test and a missing test for the `q` parameter.

2. FINDINGS:
1. [blocker] week7/backend/tests/test_pagination_sorting.py:43 — `test_sort_unknown_field_falls_back_safely` asserts `r.status_code == 200` for an unknown sort field, but the router raises a 422 validation error for invalid `sort` values (no fallback logic exists). This test will fail.
2. [blocker] week7/backend/tests/test_pagination_sorting.py:59 — `test_sort_by_title` uses `sorted(titles, key=str.lower) or titles == sorted(titles)`, which is logically incorrect: `sorted(..., key=str.lower)` always returns a truthy list, so the `or` short-circuits and the assertion always passes regardless of actual ordering.
3. [warn] week7/backend/tests/test_pagination_sorting.py:59 — The test does not verify that sorting by `title` actually sorts alphabetically (case-insensitively); it only checks a tautology.
4. [warn] week7/backend/tests/test_pagination_sorting.py:71 — `test_pagination_with_query_filter` does not assert that the returned titles are actually filtered by `q="body"`; it only checks the count.
5. [warn] week7/backend/tests/test_pagination_sorting.py:71 — The test does not verify that `q` is case-insensitive or that it matches against the correct field(s).
6. [nit] week7/backend/tests/test_pagination_sorting.py:43 — The test name suggests a fallback behavior that does not exist; the test should be renamed or the assertion changed to expect 422.

3. VERDICT: request-changes — fix the sort test logic, correct the unknown-field expectation, and add assertions that the `q` filter actually works.
