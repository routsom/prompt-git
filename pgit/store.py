"""SQLite object store — content-addressed storage for prompt-git objects."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from pgit.objects import Blob, Commit, EvalScore, SemanticDiff, Tag, Tree

SCHEMA = """\
-- Content-addressed object store (like git objects)
CREATE TABLE IF NOT EXISTS objects (
    hash TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    data TEXT NOT NULL
);

-- Branch heads
CREATE TABLE IF NOT EXISTS refs (
    name TEXT PRIMARY KEY,
    target TEXT NOT NULL
);

-- Staging area (index)
CREATE TABLE IF NOT EXISTS index_entries (
    path TEXT PRIMARY KEY,
    blob_hash TEXT NOT NULL,
    staged_at TEXT NOT NULL
);

-- Eval scores (attached to commits post-hoc)
CREATE TABLE IF NOT EXISTS eval_scores (
    id TEXT PRIMARY KEY,
    commit_hash TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    recorded_at TEXT NOT NULL,
    notes TEXT
);

-- Cached semantic diffs (expensive to generate, cache indefinitely)
CREATE TABLE IF NOT EXISTS semantic_diffs (
    id TEXT PRIMARY KEY,
    from_hash TEXT NOT NULL,
    to_hash TEXT NOT NULL,
    data TEXT NOT NULL,
    generated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_objects_type ON objects(type);
CREATE INDEX IF NOT EXISTS idx_eval_commit ON eval_scores(commit_hash);
"""


class ObjectStore:
    """SQLite-backed content-addressed object store."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------
    # Generic object CRUD
    # ------------------------------------------------------------------

    def put_object(self, obj_hash: str, obj_type: str, data: dict[str, Any]) -> None:
        """Store a content-addressed object (idempotent)."""
        self._conn.execute(
            "INSERT OR IGNORE INTO objects (hash, type, data) VALUES (?, ?, ?)",
            (obj_hash, obj_type, json.dumps(data, sort_keys=True)),
        )
        self._conn.commit()

    def get_object(self, obj_hash: str) -> tuple[str, dict[str, Any]] | None:
        """Return (type, data) or None."""
        row = self._conn.execute(
            "SELECT type, data FROM objects WHERE hash = ?", (obj_hash,)
        ).fetchone()
        if row is None:
            return None
        return row[0], json.loads(row[1])

    def has_object(self, obj_hash: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM objects WHERE hash = ?", (obj_hash,)
        ).fetchone()
        return row is not None

    def list_objects(self, obj_type: str | None = None) -> list[tuple[str, dict[str, Any]]]:
        """List all objects, optionally filtered by type."""
        if obj_type:
            rows = self._conn.execute(
                "SELECT hash, data FROM objects WHERE type = ?", (obj_type,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT hash, data FROM objects").fetchall()
        return [(r[0], json.loads(r[1])) for r in rows]

    # ------------------------------------------------------------------
    # Typed helpers
    # ------------------------------------------------------------------

    def put_blob(self, blob: Blob) -> None:
        self.put_object(blob.hash, "blob", blob.to_dict())

    def get_blob(self, h: str) -> Blob | None:
        result = self.get_object(h)
        if result is None or result[0] != "blob":
            return None
        return Blob.from_dict(result[1])

    def put_tree(self, tree: Tree) -> None:
        self.put_object(tree.hash, "tree", tree.to_dict())

    def get_tree(self, h: str) -> Tree | None:
        result = self.get_object(h)
        if result is None or result[0] != "tree":
            return None
        return Tree.from_dict(result[1])

    def put_commit(self, commit: Commit) -> None:
        self.put_object(commit.hash, "commit", commit.to_dict())

    def get_commit(self, h: str) -> Commit | None:
        result = self.get_object(h)
        if result is None or result[0] != "commit":
            return None
        return Commit.from_dict(result[1])

    def put_tag(self, tag: Tag) -> None:
        self.put_object(tag.hash, "tag", tag.to_dict())

    def get_tag(self, h: str) -> Tag | None:
        result = self.get_object(h)
        if result is None or result[0] != "tag":
            return None
        return Tag.from_dict(result[1])

    def find_tag_by_name(self, name: str) -> Tag | None:
        """Find a tag by its name."""
        rows = self._conn.execute(
            "SELECT data FROM objects WHERE type = 'tag'"
        ).fetchall()
        for (raw,) in rows:
            d = json.loads(raw)
            if d.get("name") == name:
                return Tag.from_dict(d)
        return None

    # ------------------------------------------------------------------
    # Refs
    # ------------------------------------------------------------------

    def set_ref(self, name: str, target: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO refs (name, target) VALUES (?, ?)",
            (name, target),
        )
        self._conn.commit()

    def get_ref(self, name: str) -> str | None:
        row = self._conn.execute(
            "SELECT target FROM refs WHERE name = ?", (name,)
        ).fetchone()
        return row[0] if row else None

    def delete_ref(self, name: str) -> bool:
        cur = self._conn.execute("DELETE FROM refs WHERE name = ?", (name,))
        self._conn.commit()
        return cur.rowcount > 0

    def list_refs(self, prefix: str | None = None) -> list[tuple[str, str]]:
        """Return [(name, target)] filtered by optional prefix."""
        if prefix:
            rows = self._conn.execute(
                "SELECT name, target FROM refs WHERE name LIKE ?", (prefix + "%",)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT name, target FROM refs").fetchall()
        return [(r[0], r[1]) for r in rows]

    # ------------------------------------------------------------------
    # Index (staging area)
    # ------------------------------------------------------------------

    def stage(self, path: str, blob_hash: str, staged_at: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO index_entries (path, blob_hash, staged_at) VALUES (?, ?, ?)",
            (path, blob_hash, staged_at),
        )
        self._conn.commit()

    def unstage(self, path: str) -> bool:
        cur = self._conn.execute("DELETE FROM index_entries WHERE path = ?", (path,))
        self._conn.commit()
        return cur.rowcount > 0

    def get_index(self) -> list[tuple[str, str, str]]:
        """Return [(path, blob_hash, staged_at)] for all staged entries."""
        return self._conn.execute(
            "SELECT path, blob_hash, staged_at FROM index_entries ORDER BY path"
        ).fetchall()

    def clear_index(self) -> None:
        self._conn.execute("DELETE FROM index_entries")
        self._conn.commit()

    # ------------------------------------------------------------------
    # Eval scores
    # ------------------------------------------------------------------

    def add_eval_score(self, score: EvalScore) -> str:
        """Store an eval score. Returns the generated UUID."""
        score_id = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO eval_scores (id, commit_hash, metric, value, recorded_at, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                score_id, score.commit_hash, score.metric,
                score.value, score.recorded_at, score.notes,
            ),
        )
        self._conn.commit()
        return score_id

    def get_eval_scores(self, commit_hash: str) -> list[EvalScore]:
        rows = self._conn.execute(
            "SELECT commit_hash, metric, value, recorded_at, notes "
            "FROM eval_scores WHERE commit_hash = ?",
            (commit_hash,),
        ).fetchall()
        return [
            EvalScore(commit_hash=r[0], metric=r[1], value=r[2], recorded_at=r[3], notes=r[4])
            for r in rows
        ]

    def get_eval_score(self, commit_hash: str, metric: str) -> float | None:
        """Return the latest eval score value for a given commit + metric."""
        row = self._conn.execute(
            "SELECT value FROM eval_scores WHERE commit_hash = ? AND metric = ? "
            "ORDER BY recorded_at DESC LIMIT 1",
            (commit_hash, metric),
        ).fetchone()
        return row[0] if row else None

    # ------------------------------------------------------------------
    # Semantic diff cache
    # ------------------------------------------------------------------

    def get_semantic_diff(self, cache_key: str) -> SemanticDiff | None:
        row = self._conn.execute(
            "SELECT data FROM semantic_diffs WHERE id = ?", (cache_key,)
        ).fetchone()
        if row is None:
            return None
        return SemanticDiff.from_dict(json.loads(row[0]))

    def put_semantic_diff(self, diff: SemanticDiff) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO semantic_diffs (id, from_hash, to_hash, data, generated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                diff.cache_key,
                diff.from_hash,
                diff.to_hash,
                json.dumps(diff.to_dict(), sort_keys=True),
                diff.generated_at,
            ),
        )
        self._conn.commit()
