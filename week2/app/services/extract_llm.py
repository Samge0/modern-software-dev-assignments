"""LLM-powered action item extraction.

Calls an OpenAI-compatible endpoint (local vLLM by default, via env vars) and
returns a JSON array of action item strings. Mirrors the course's Ollama-based
`extract_action_items_llm` task: the assignment suggests Ollama structured
outputs; here we use the equivalent `response_format` JSON mode + strict prompt.
"""

from __future__ import annotations

import json
import os
import re
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:16869/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "EMPTY")
MODEL = os.environ.get("LLM_EXTRACT_MODEL", "qwen38")

SYSTEM_PROMPT = (
    "You extract action items from free-form notes. "
    "Return ONLY a JSON array of strings, each an action item phrased as a short imperative sentence. "
    "Rules:\n"
    "1. Include tasks, to-dos, and requested follow-ups (bulleted, checkboxed, 'todo:', or implied in prose).\n"
    "2. Exclude narrative context, dates without tasks, questions, and headers.\n"
    "3. Preserve the original wording of each item; strip bullet/checkbox/keyword prefixes.\n"
    "4. Deduplicate. If there are no action items, return [].\n"
    'Example input: "Meeting notes. - [ ] fix login bug. We also should update the docs."\n'
    'Example output: ["Fix login bug", "Update the docs"]'
)


def _client() -> OpenAI:
    return OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=120.0)


def _parse_items(raw: str) -> List[str]:
    """Tolerant parsing: model may wrap the JSON array in prose or code fences."""
    text = raw.strip()
    # strip code fences
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    # find the outermost JSON array
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out: List[str] = []
    for entry in data:
        if isinstance(entry, str) and entry.strip():
            out.append(entry.strip())
        elif isinstance(entry, dict):
            # tolerate {"item": "..."} / {"text": "..."} shapes
            for key in ("item", "text", "action_item", "action"):
                if isinstance(entry.get(key), str) and entry[key].strip():
                    out.append(entry[key].strip())
                    break
    # de-dup preserve order
    seen: set = set()
    unique: List[str] = []
    for s in out:
        k = s.lower()
        if k not in seen:
            seen.add(k)
            unique.append(s)
    return unique


def extract_action_items_llm(text: str) -> List[str]:
    """LLM-powered alternative to the heuristic extract_action_items()."""
    if not text or not text.strip():
        return []
    client = _client()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0.0,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": False},
            "guided_json": {"type": "array", "items": {"type": "string"}},
        },
    )
    content = resp.choices[0].message.content or ""
    return _parse_items(content)


if __name__ == "__main__":
    demo = (
        "Weekly sync notes.\n"
        "- [ ] Ship the migration script\n"
        "TODO: ping legal about the DPA\n"
        "The team also agreed that we should schedule a design review next week.\n"
        "Nice dinner last night!"
    )
    print(json.dumps(extract_action_items_llm(demo), indent=2, ensure_ascii=False))
