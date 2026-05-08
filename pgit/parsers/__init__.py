"""Prompt format parsers — detect and parse different prompt file formats."""

from __future__ import annotations

from collections.abc import Callable

from pgit.parsers.jinja2 import parse as parse_jinja2
from pgit.parsers.json_messages import parse as parse_json_messages
from pgit.parsers.plaintext import parse as parse_plaintext
from pgit.parsers.yaml_turns import parse as parse_yaml_turns

PARSERS: dict[str, Callable[[str], list[str]]] = {
    "plaintext": parse_plaintext,
    "jinja2": parse_jinja2,
    "json_messages": parse_json_messages,
    "yaml_turns": parse_yaml_turns,
}

FORMAT_EXTENSIONS: dict[str, str] = {
    ".txt": "plaintext",
    ".md": "plaintext",
    ".j2": "jinja2",
    ".jinja": "jinja2",
    ".jinja2": "jinja2",
    ".json": "json_messages",
    ".yaml": "yaml_turns",
    ".yml": "yaml_turns",
}


def detect_format(filename: str) -> str:
    """Detect prompt format from filename extension."""
    for ext, fmt in FORMAT_EXTENSIONS.items():
        if filename.endswith(ext):
            return fmt
    return "plaintext"


def parse(content: str, format: str) -> list[str]:
    """Parse prompt content into logical segments."""
    parser = PARSERS.get(format)
    if parser is None:
        raise ValueError(f"Unknown format: {format}")
    return parser(content)

__all__ = ["detect_format", "parse", "PARSERS", "FORMAT_EXTENSIONS"]
