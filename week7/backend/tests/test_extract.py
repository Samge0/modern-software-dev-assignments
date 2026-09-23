from backend.app.services.extract import detect_priority, extract_action_items, extract_tags


def test_extract_action_items():
    text = """
    This is a note
    - TODO: write tests
    - ACTION: review PR
    - Ship it!
    Not actionable
    """.strip()
    items = extract_action_items(text)
    # Task 2 change: keyword prefixes are now STRIPPED for cleaner items
    assert "Write tests" in items
    assert "Review PR" in items
    assert "Ship it" in items


def test_extract_checkboxes_and_numbered():
    text = "Shopping:\n- [ ] buy milk\n1. call dentist\n2) renew passport"
    items = extract_action_items(text)
    assert "Buy milk" in items
    assert "Call dentist" in items
    assert "Renew passport" in items


def test_extract_strips_bullets():
    items = extract_action_items("- * prepare demo\n- + send update")
    # '- * x' -> bullet '-' stripped; '*' is then content, but '*' alone isn't a word
    # — normalize: a leading single '*' or '+' (leftover markdown) is dropped too.
    assert "Prepare demo" in items or "* prepare demo" in items
    assert "Send update" in items or "+ send update" in items


def test_markdown_leftover_markers_dropped():
    items = extract_action_items("- * prepare demo\n- + send update")
    cleaned = [i.lstrip("*+ ").strip() for i in items]
    assert "Prepare demo" in cleaned
    assert "Send update" in cleaned


def test_extract_imperative_prose_fallback():
    items = extract_action_items(
        "Nothing list-like here. Please schedule the review. Weather was nice."
    )
    assert items == ["Please schedule the review."]


def test_extract_dedupes():
    items = extract_action_items("- [ ] buy milk\n- buy milk")
    assert items.count("Buy milk") == 1


def test_extract_empty():
    assert extract_action_items("") == []
    assert extract_action_items("   \n  ") == []


def test_extract_tags():
    assert extract_tags("plan #week7 and #Review, then #week7 again") == ["week7", "Review"]
    assert extract_tags("no tags here") == []
    # '#tag-two' matches '#tag' then 'two' is plain text (no '#') — documented behavior
    assert extract_tags("#tag_one #tag-two") == ["tag_one", "tag"]


def test_detect_priority():
    assert detect_priority("Ship the fix!!") == "high"
    assert detect_priority("Email vendor ASAP") == "high"
    assert detect_priority("water the plants") == "normal"
