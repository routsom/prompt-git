"""YAML multi-turn prompt parser — .yaml, .yml files."""

from __future__ import annotations

import yaml


def parse(content: str) -> list[str]:
    """Parse YAML multi-turn prompt into logical segments (one per turn)."""
    data = yaml.safe_load(content)

    if isinstance(data, list):
        segments: list[str] = []
        for item in data:
            if isinstance(item, dict):
                role = item.get("role", "unknown")
                text = item.get("content", str(item))
                segments.append(f"[{role}] {text}")
            else:
                segments.append(str(item))
        return segments if segments else [content]

    if isinstance(data, dict):
        segments = []
        for key, value in data.items():
            segments.append(f"{key}: {value}")
        return segments if segments else [content]

    return [content]


def serialize(segments: list[str]) -> str:
    """Serialize segments back to YAML format."""
    turns: list[dict[str, str]] = []
    for seg in segments:
        if seg.startswith("[") and "] " in seg:
            bracket_end = seg.index("]")
            role = seg[1:bracket_end]
            text = seg[bracket_end + 2:]
            turns.append({"role": role, "content": text})
        else:
            turns.append({"role": "user", "content": seg})
    return yaml.dump(turns, default_flow_style=False, sort_keys=False)
