import os

import pytest

from ..app.services.extract import extract_action_items
from ..app.services.extract_llm import _parse_items, extract_action_items_llm

# ---------------------------------------------------------------------------
# Heuristic extractor (existing behaviour, kept as regression baseline)
# ---------------------------------------------------------------------------


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


def test_extract_keyword_prefixed():
    # Keyword prefixes are detected but only bullet prefixes are stripped by the
    # current heuristic — documented behaviour this test pins down.
    items = extract_action_items("todo: call vendor\nnext: schedule retro")
    assert items == ["todo: call vendor", "next: schedule retro"]


def test_extract_empty_input():
    assert extract_action_items("") == []
    assert extract_action_items("   \n\t  ") == []


# ---------------------------------------------------------------------------
# LLM extractor (TODO 2)
# ---------------------------------------------------------------------------


def test_llm_parse_items_plain_array():
    assert _parse_items('["Fix bug", "Update docs"]') == ["Fix bug", "Update docs"]


def test_llm_parse_items_fenced_with_prose():
    raw = 'Here you go:\n```json\n["A", "B"]\n```\nDone.'
    assert _parse_items(raw) == ["A", "B"]


def test_llm_parse_items_dict_shapes_and_dedup():
    raw = '[{"item": "A"}, {"text": "B"}, "a", ""]'
    assert _parse_items(raw) == ["A", "B"]


def test_llm_parse_items_invalid_json_returns_empty():
    assert _parse_items("not json at all") == []


@pytest.mark.skipif(
    os.environ.get("LLM_EXTRACT_MODEL") == "" or not os.environ.get("OPENAI_API_KEY"),
    reason="no local LLM endpoint configured",
)
class TestLLMExtractorLive:
    def test_bullet_list(self):
        text = "Sync notes:\n- [ ] ship migration\n- review PR"
        items = extract_action_items_llm(text)
        assert any("migration" in i.lower() for i in items)
        assert any("review" in i.lower() for i in items)

    def test_keyword_prefixed_lines(self):
        items = extract_action_items_llm(
            "TODO: ping legal about the DPA\nNext: schedule design review"
        )
        assert len(items) >= 2

    def test_empty_input_short_circuits(self):
        assert extract_action_items_llm("") == []
        assert extract_action_items_llm("   ") == []

    def test_prose_implies_actions(self):
        items = extract_action_items_llm(
            "We agreed the team should update the runbook before Friday."
        )
        assert any("runbook" in i.lower() for i in items)
