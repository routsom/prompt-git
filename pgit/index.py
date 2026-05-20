"""Staging area (index) — tracks files staged for the next commit."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pgit.objects import Blob
from pgit.parsers import detect_format
from pgit.store import ObjectStore


class Index:
    """High-level staging area backed by the ObjectStore."""

    def __init__(self, store: ObjectStore, root: Path) -> None:
        self._store = store
        self._root = root

    def add(self, file_path: str, model_hint: str | None = None) -> Blob:
        """Stage a file for commit. Returns the created Blob."""
        abs_path = (self._root / file_path).resolve()
        if not abs_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read content
        content = abs_path.read_text(encoding="utf-8")

        # Detect format
        fmt = detect_format(abs_path.name)

        # Create blob
        blob = Blob.create(content=content, format=fmt, model_hint=model_hint)

        # Store the blob
        self._store.put_blob(blob)

        # Stage it
        now = datetime.now(UTC).isoformat()
        self._store.stage(file_path, blob.hash, now)

        return blob

    def staged_entries(self) -> list[tuple[str, str, str]]:
        """Return [(path, blob_hash, staged_at)] for all staged files."""
        return self._store.get_index()

    def clear(self) -> None:
        """Clear all staged entries (after commit)."""
        self._store.clear_index()

    def unstage(self, path: str) -> bool:
        """Remove a file from the staging area."""
        return self._store.unstage(path)

    def is_empty(self) -> bool:
        """True if nothing is staged."""
        return len(self._store.get_index()) == 0
