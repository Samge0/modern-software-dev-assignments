# AI Review — PR #3: week7/task3: Tag model + note-tag M2M

(reviewed by local qwen38 via OpenAI-compatible endpoint)

# Code Review: PR #3 — Tag model + note-tag M2M

## 1. SUMMARY
This PR introduces a `Tag` model with a many-to-many relationship to `Note`, adds CRUD endpoints for tags, and links action items to notes — all implemented correctly with proper schema validation, idempotent tag attachment, and cascade behavior.

## 2. FINDINGS

1. **warn** | `week7/backend/app/models.py:21` | `ondelete="CASCADE"` on `note_tags.note_id` is correct, but `ondelete="SET NULL"` on `action_items.note_id` silently drops the FK reference without warning — if the note is deleted, the action item loses its link without any audit trail.  
   **Suggestion:** Use `ondelete="CASCADE"` instead, or at least add a `default`/`nullable=True` with a comment explaining the business rule.

2. **warn** | `week7/backend/app/routers/tags.py:40` | `db.delete(tag)` followed by `db.flush()` is unnecessary — `delete()` already issues the DELETE statement and `flush()` is redundant here.  
   **Suggestion:** Remove `db.flush()` to reduce unnecessary DB round-trips.

3. **nit** | `week7/backend/app/routers/tags.py:42` | The docstring says “idempotent per tag” but the function does not prevent duplicate *join rows* if the same tag is attached twice in one request. It only prevents duplicate tags across notes.  
   **Suggestion:** Add a check inside the loop to skip adding a tag if it’s already in `note.tags` (already done via `current` set, but the docstring could be more precise: “idempotent per tag per note”).

4. **nit** | `week7/backend/app/schemas.py:52` | `TagAddRequest.names` allows empty strings (e.g. `[""]`) which would create an empty tag name after `.strip().lower()`.  
   **Suggestion:** Add `min_length=1` to each element: `names: list[str] = Field(min_length=1, max_length=20, min_items=1, max_items=20)`.

5. **nit** | `week7/backend/tests/test_tags.py:53` | The test `test_attach_creates_missing_tags` does not assert that the tag was actually created (no `client.get("/tags/")` check).  
   **Suggestion:** Add an assertion that the new tag appears in the tag list after attachment.

## 3. VERDICT
**approve** — The implementation is functionally correct and complete for the stated task; the findings above are minor improvements for robustness and clarity.
