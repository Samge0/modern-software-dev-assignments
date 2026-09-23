def extract_action_items(text: str) -> list[str]:
    lines = [line.strip("- ") for line in text.splitlines() if line.strip()]
    return [line for line in lines if line.endswith("!") or line.lower().startswith("todo:")]


def extract_tags(text: str) -> list[str]:
    """Return unique #tags from text in order of first appearance."""
    tags: list[str] = []
    for token in text.replace("!", " ").split():
        if token.startswith("#") and len(token) > 1:
            tag = token.strip("#").strip(".,;:!?()[]").lower()
            if tag and tag not in tags:
                tags.append(tag)
    return tags
