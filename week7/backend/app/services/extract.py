"""Note text -> action item extraction.

Extended pattern recognition (Task 2):
- bullet / checkbox / numbered list items
- todo:/action:/next: keyword prefixes (prefix stripped)
- imperative-sentence heuristic fallback
- #hashtag collection
- priority detection (!! = high)
"""

_BULLET_PREFIXES = ("-", "*", "•", "+")
_KEYWORD_PREFIXES = ("todo:", "action:", "next:", "follow up:", "follow-up:")

_IMPERATIVE_STARTERS = {
    "add", "build", "call", "check", "clean", "create", "design", "document",
    "email", "fix", "follow", "gather", "implement", "improve", "investigate",
    "launch", "look", "make", "please", "prepare", "refactor", "review",
    "schedule", "send", "set", "ship", "test", "update", "verify", "write",
}


def _strip_bullet(line: str) -> str:
    stripped = line.lstrip()
    for prefix in _BULLET_PREFIXES:
        if stripped.startswith(prefix + " "):
            return stripped[len(prefix):].strip()
    # numbered list "1. " / "1) "
    if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".)":
        return stripped[2:].strip()
    return stripped


def _strip_keyword(line: str) -> str:
    lowered = line.lower()
    for prefix in _KEYWORD_PREFIXES:
        if lowered.startswith(prefix):
            return line[len(prefix):].strip()
    return line


def _is_action_line(line: str) -> bool:
    stripped = line.lstrip()
    lowered = stripped.lower()
    if not stripped:
        return False
    if "[ ]" in stripped or "[x]" in lowered:
        return True
    if any(lowered.startswith(p) for p in _KEYWORD_PREFIXES):
        return True
    for prefix in _BULLET_PREFIXES:
        if stripped.startswith(prefix + " "):
            return True
    if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".)":
        return True
    return False


def _looks_imperative(sentence: str) -> bool:
    first = sentence.lstrip().split(" ", 1)[0].strip(".,!?;:").lower()
    return first in _IMPERATIVE_STARTERS


def _clean_item(text: str, keep_exclaim: bool = False) -> str:
    """Normalize one extracted item: trim, drop terminal '.', capitalize first letter.

    keep_exclaim preserves a terminal '!' (used for enthusiastic imperatives
    like 'Ship it!') while still trimming a trailing period.
    """
    cleaned = text.strip()
    if not keep_exclaim and cleaned.endswith("!"):
        cleaned = cleaned.rstrip("!").strip()
    cleaned = cleaned.rstrip(".").strip()
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def extract_action_items(text: str) -> list[str]:
    """Extract action items from free-form note text."""
    if not text or not text.strip():
        return []

    results: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = _strip_keyword(_strip_bullet(line))
            # drop checkbox markers
            if cleaned.lower().startswith("[ ]"):
                cleaned = cleaned[3:].strip()
            elif cleaned.lower().startswith("[x]"):
                cleaned = cleaned[3:].strip()
            cleaned = _clean_item(cleaned)
            if cleaned:
                results.append(cleaned)
        elif line.endswith("!") and _looks_imperative(line.rstrip("!").strip()):
            results.append(_clean_item(line, keep_exclaim=True))

    # fallback: imperative sentences from prose
    if not results:
        import re

        for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
            s = sentence.strip()
            if s and _looks_imperative(s):
                results.append(s)

    # dedupe, preserve order
    seen: set[str] = set()
    unique: list[str] = []
    for item in results:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def extract_tags(text: str) -> list[str]:
    """Collect #hashtags (letters/digits/underscore), deduped, order kept."""
    import re

    tags = re.findall(r"#([A-Za-z0-9_]+)", text or "")
    seen: set[str] = set()
    ordered: list[str] = []
    for tag in tags:
        low = tag.lower()
        if low not in seen:
            seen.add(low)
            ordered.append(tag)
    return ordered


def detect_priority(item: str) -> str:
    """ crude urgency signal: '!!' or 'asap'/'urgent' => high, else normal."""
    lowered = item.lower()
    if "!!" in item or "asap" in lowered or "urgent" in lowered:
        return "high"
    return "normal"
