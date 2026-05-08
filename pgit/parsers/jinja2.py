"""Jinja2 template prompt parser — .j2, .jinja, .jinja2 files."""

from __future__ import annotations

import re


def parse(content: str) -> list[str]:
    """Parse Jinja2 template into logical segments.

    Splits on Jinja2 block-level tags ({% block %}, {% if %}, {% for %}, etc.)
    while preserving the template structure.
    """
    # Split on Jinja2 block delimiters, keeping delimiters
    pattern = r'(\{%[-\s].*?[-\s]%\})'
    parts = re.split(pattern, content, flags=re.DOTALL)

    segments: list[str] = []
    current: list[str] = []

    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        # Check if this is a block-level delimiter
        if re.match(r'\{%[-\s]*(block|endblock|if|endif|for|endfor|macro|endmacro)', stripped):
            if current:
                segments.append("".join(current))
                current = []
            segments.append(part)
        else:
            current.append(part)

    if current:
        segments.append("".join(current))

    return segments if segments else [content]


def serialize(segments: list[str]) -> str:
    """Serialize segments back to Jinja2 template."""
    return "".join(segments)
