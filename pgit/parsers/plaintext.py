"""Plaintext prompt parser — .txt, .md files."""

from __future__ import annotations


def parse(content: str) -> list[str]:
    """Parse plaintext prompt into logical segments (paragraphs)."""
    segments: list[str] = []
    current: list[str] = []

    for line in content.splitlines():
        if line.strip() == "":
            if current:
                segments.append("\n".join(current))
                current = []
        else:
            current.append(line)

    if current:
        segments.append("\n".join(current))

    return segments if segments else [content]


def serialize(segments: list[str]) -> str:
    """Serialize segments back to plaintext."""
    return "\n\n".join(segments)
