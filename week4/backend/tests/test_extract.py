from backend.app.services.extract import extract_action_items, extract_tags


def test_extract_action_items():
    text = """
    This is a note
    - TODO: write tests
    - Ship it!
    Not actionable
    """.strip()
    items = extract_action_items(text)
    assert "TODO: write tests" in items
    assert "Ship it!" in items


def test_extract_tags_finds_unique_tags_in_order():
    text = "Plan #week4 launch and review #notes, then revisit #week4"
    assert extract_tags(text) == ["week4", "notes"]


def test_extract_tags_ignores_bare_hash_and_plain_words():
    assert extract_tags("no tags here # and # alone") == []


def test_extract_tags_normalizes_case():
    assert extract_tags("mix of #Python and #python") == ["python"]
