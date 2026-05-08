"""Line diff engine — unified diff between two prompt texts."""

from __future__ import annotations

import difflib


def line_diff(from_text: str, to_text: str, from_label: str = "a", to_label: str = "b") -> str:
    """Generate a unified diff between two prompt texts."""
    from_lines = from_text.splitlines(keepends=True)
    to_lines = to_text.splitlines(keepends=True)
    diff = difflib.unified_diff(from_lines, to_lines, fromfile=from_label, tofile=to_label)
    return "".join(diff)


def diff_stats(from_text: str, to_text: str) -> dict[str, int]:
    """Return insertion/deletion stats."""
    from_lines = from_text.splitlines()
    to_lines = to_text.splitlines()
    matcher = difflib.SequenceMatcher(None, from_lines, to_lines)
    insertions = 0
    deletions = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            deletions += i2 - i1
            insertions += j2 - j1
        elif tag == "delete":
            deletions += i2 - i1
        elif tag == "insert":
            insertions += j2 - j1
    return {"insertions": insertions, "deletions": deletions}
