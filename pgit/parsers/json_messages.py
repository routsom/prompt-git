"""OpenAI-style JSON messages parser — [{role, content}] format."""

from __future__ import annotations

import json


def parse(content: str) -> list[str]:
    """Parse JSON messages array into logical segments (one per message)."""
    data = json.loads(content)
    if not isinstance(data, list):
        return [content]

    segments: list[str] = []
    for msg in data:
        if isinstance(msg, dict):
            role = msg.get("role", "unknown")
            text = msg.get("content", "")
            segments.append(f"[{role}] {text}")
        else:
            segments.append(str(msg))

    return segments if segments else [content]


def serialize(segments: list[str]) -> str:
    """Serialize segments back to JSON messages format."""
    messages: list[dict[str, str]] = []
    for seg in segments:
        if seg.startswith("[") and "] " in seg:
            bracket_end = seg.index("]")
            role = seg[1:bracket_end]
            text = seg[bracket_end + 2:]
            messages.append({"role": role, "content": text})
        else:
            messages.append({"role": "user", "content": seg})
    return json.dumps(messages, indent=2)
