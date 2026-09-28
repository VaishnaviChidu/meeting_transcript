import re
from typing import Any


_SPEAKER_LINE = re.compile(
    r"^\s*(?:(?:\[\d{1,2}:\d{2}(?::\d{2})?\]|\d{1,2}:\d{2}(?::\d{2})?)\s*)?"
    r"([A-Za-z][A-Za-z0-9 .'-]{0,49}?)\s*:",
    re.MULTILINE,
)


def _normalized(name: str) -> str:
    return " ".join(name.casefold().split())


def extract_speaker_labels(transcript: str) -> list[str]:
    """Return unique names used as transcript line labels (for example, 'Maya:')."""
    labels: list[str] = []
    seen: set[str] = set()
    for match in _SPEAKER_LINE.finditer(transcript):
        label = " ".join(match.group(1).split()).strip(" .")
        key = _normalized(label)
        if key and key not in seen:
            labels.append(label)
            seen.add(key)
    return labels


def validate_action_owners(result: dict[str, Any], speakers: list[str]) -> None:
    """Clear owners not present as transcript speakers and flag them for review."""
    known_speakers = {_normalized(speaker) for speaker in speakers}
    for item in result.get("action_items", []):
        owner = item.get("owner")
        if owner and _normalized(str(owner)) not in known_speakers:
            item["owner"] = None
            item["needs_clarification"] = True
