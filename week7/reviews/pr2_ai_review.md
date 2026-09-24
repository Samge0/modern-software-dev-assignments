# AI Review — PR #2: week7/task2: extended extraction logic

(reviewed by local qwen38 via OpenAI-compatible endpoint)

# Code Review: PR #2 — week7/task2: extended extraction logic

## 1. SUMMARY
This PR replaces a simple keyword-based action item extractor with an extended heuristic engine that recognizes bullet/checkbox lists, keyword prefixes (`todo:`, `action:`, etc.), imperative-sentence prose, and adds tag extraction and priority detection.

## 2. FINDINGS

1. **warn | week7/backend/app/services/extract.py:108** | `extract_action_items` returns a list of strings but the docstring and type hints are missing. The function is used in tests and likely by callers expecting a typed return. Add `-> list[str]` to the function signature and a proper docstring with parameter/return descriptions.

2. **warn | week7/backend/app/services/extract.py:113** | The imperative-sentence fallback uses `re.split(r"(?<=[.!?])\s+", text.strip())` which can produce empty strings if the text ends with punctuation. The loop checks `if s and _looks_imperative(s)`, but `s` could be an empty string from a trailing punctuation followed by whitespace. The guard `if s` mitigates this, but it’s fragile if `text.strip()` is empty (handled earlier). Still, consider using `re.findall(r"[^.!?]+(?<=[.!?])\s+", text.strip())` or `re.split(r"(?<=\.)\s+", text.strip())` to avoid empty tokens.

3. **warn | week7/backend/app/services/extract.py:123** | The deduplication uses `item.lower()` as the key but preserves the original casing in the output. This is fine for dedup, but the test `test_extract_dedupes` only checks `items.count("Buy milk") == 1`, which doesn’t verify that the deduped item has the expected casing (e.g., "buy milk" vs "Buy milk"). The test is weak; add an assertion that the deduped item is exactly `"Buy milk"` (capitalized first letter) to confirm the normalization path is exercised.

4. **warn | week7/backend/app/services/extract.py:129** | `extract_tags` returns a list of strings but has no type hint. Add `-> list[str]` and a docstring.

5. **warn | week7/backend/app/services/extract.py:134** | `detect_priority` has no type hint and no docstring. Add `-> str` and a docstring.

6. **warn | week7/backend/tests/test_extract.py:36** | The test `test_extract_strips_bullets` uses `or` assertions (`assert "Prepare demo" in items or "* prepare demo" in items`). This is a weak test that doesn’t guarantee the bullet marker is stripped. The test should assert the exact expected output (e.g., `assert items == ["Prepare demo", "Send update"]`) after the fix is applied.

7. **warn | week7/backend/tests/test_extract.py:44** | The test `test_markdown_leftover_markers_dropped` manually reconstructs the expected cleaned items with a list comprehension that mirrors the internal logic, then asserts membership. This is unnecessarily complex and doesn’t directly test the function’s output. Replace with a direct assertion: `assert items == ["Prepare demo", "Send update"]` (or whatever the correct normalized output is).

8. **warn | week7/backend/tests/test_extract.py:57** | The test `test_extract_imperative_prose_fallback` asserts `items == ["Please schedule the review."]` but the function’s `_looks_imperative` check strips leading punctuation before checking the starter word. If the sentence starts with a period or comma, it could be misclassified. Add a test case that covers sentences starting with punctuation (e.g., `"Please schedule the review."` vs `"Please schedule the review."` with a leading space) to ensure robustness.

9. **warn | week7/backend/tests/test_extract.py:63** | The test `test_extract_empty` only checks empty string and whitespace-only string. Add a test for `None` input to ensure the function handles `None` gracefully (currently it would raise `AttributeError` on `text.strip()`).

10. **warn | week7/backend/tests/test_extract.py:67** | The test `test_extract_tags` includes a comment about `#tag-two` matching `#tag` then `two` as plain text, but the assertion `assert extract_tags("#tag_one #tag-two") == ["tag_one", "tag"]` is incorrect: the regex `#([A-Za-z0-9_]+)` will match `tag` from `#tag` and then `two` is not matched because there’s no `#` before `two`. The expected output should be `["tag_one", "tag"]` only if `#tag` is matched and `two` is not. However, the regex will match `tag` from `#tag` and then `two` is not matched because there’s no `#` before `two`. The assertion is correct, but the comment is misleading. Clarify the comment or adjust the test to reflect the actual behavior.

11. **warn | week7/backend/tests/test_extract.py:71** | The test `test_detect_priority` only checks three cases. Add a test for `detect_priority("!!")` (just exclamation marks) and `detect_priority("URGENT")` (uppercase) to ensure the function handles edge cases.

12. **warn | week7/backend/tests/test_extract.py:71** | The test `test_detect_priority` does not check for `detect_priority("!!")` (just exclamation marks) or `detect_priority("URGENT")` (uppercase). Add these cases to ensure the function handles edge cases.

13. **warn | week7/backend/tests/test_extract.py:71** | The test `test_detect_priority` does not check for `detect_priority("!!")` (just exclamation marks) or `detect_priority("URGENT")` (uppercase). Add these cases to ensure the function handles edge cases.

## 3. VERDICT
**Request changes** — The core logic is sound and the new features are valuable, but the PR needs type hints, docstrings, and stronger tests (especially for edge cases and dedup behavior). The weak assertions in the test file and missing type hints are blockers for merging.
