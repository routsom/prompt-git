"""Content-addressed objects — Blob, Tree, Commit, Tag, SemanticDiff, EvalScore."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Hashing helpers — always sort_keys=True for determinism
# ---------------------------------------------------------------------------


def hash_blob(content: str, format: str, model_hint: str | None) -> str:
    """Compute deterministic SHA-256 for a Blob."""
    data = json.dumps(
        {"content": content, "format": format, "model_hint": model_hint},
        sort_keys=True,
    )
    return hashlib.sha256(data.encode()).hexdigest()


def hash_tree(entries: dict[str, str]) -> str:
    """Compute deterministic SHA-256 for a Tree."""
    data = json.dumps({"entries": entries}, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()


def hash_commit(
    parent: str | None,
    tree: str,
    message: str,
    author: str,
    committed_at: str,
) -> str:
    """Compute deterministic SHA-256 for a Commit.

    Note: committed_at IS part of the hash — two commits with identical
    content but different timestamps produce different hashes (intentional).
    """
    data = json.dumps(
        {
            "author": author,
            "committed_at": committed_at,
            "message": message,
            "parent": parent,
            "tree": tree,
        },
        sort_keys=True,
    )
    return hashlib.sha256(data.encode()).hexdigest()


def hash_tag(name: str, target: str, message: str | None, created_at: str) -> str:
    """Compute deterministic SHA-256 for a Tag."""
    data = json.dumps(
        {"created_at": created_at, "message": message, "name": name, "target": target},
        sort_keys=True,
    )
    return hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Blob:
    """Immutable content object — the stored prompt text."""

    hash: str  # SHA-256 of content (content-addressed)
    content: str  # raw prompt text
    format: str  # "plaintext" | "jinja2" | "json_messages" | "yaml_turns"
    model_hint: str | None  # e.g. "claude-sonnet-4-6", for model-specific prompts

    @classmethod
    def create(cls, content: str, format: str, model_hint: str | None = None) -> Blob:
        h = hash_blob(content, format, model_hint)
        return cls(hash=h, content=content, format=format, model_hint=model_hint)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Blob:
        return cls(**d)


@dataclass
class Tree:
    """Maps file paths to Blob hashes — like a git tree."""

    hash: str
    entries: dict[str, str]  # path → blob_hash

    @classmethod
    def create(cls, entries: dict[str, str]) -> Tree:
        h = hash_tree(entries)
        return cls(hash=h, entries=entries)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Tree:
        return cls(**d)


@dataclass
class Commit:
    """Immutable commit object."""

    hash: str  # SHA-256 of the serialised commit data
    parent: str | None  # parent commit hash (None for root)
    tree: str  # tree hash
    message: str
    author: str
    committed_at: str  # ISO-8601
    eval_scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        parent: str | None,
        tree: str,
        message: str,
        author: str,
        committed_at: str,
        metadata: dict[str, Any] | None = None,
    ) -> Commit:
        h = hash_commit(parent, tree, message, author, committed_at)
        return cls(
            hash=h,
            parent=parent,
            tree=tree,
            message=message,
            author=author,
            committed_at=committed_at,
            eval_scores={},
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Commit:
        return cls(**d)


@dataclass
class Tag:
    hash: str
    name: str  # e.g. "v1.0", "production"
    target: str  # commit hash
    message: str | None
    created_at: str

    @classmethod
    def create(cls, name: str, target: str, message: str | None, created_at: str) -> Tag:
        h = hash_tag(name, target, message, created_at)
        return cls(hash=h, name=name, target=target, message=message, created_at=created_at)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Tag:
        return cls(**d)


@dataclass
class SemanticDiff:
    """Output of the LLM semantic diff engine."""

    from_hash: str  # commit or blob hash
    to_hash: str
    summary: str  # one-sentence summary of what changed
    additions: list[str]  # new concepts / rules added
    removals: list[str]  # concepts / rules removed
    tone_shift: str | None  # e.g. "from permissive to strict"
    structural_changes: list[str]  # format or ordering changes
    model_used: str  # which LLM was used to generate this diff
    generated_at: str

    @property
    def cache_key(self) -> str:
        return f"{self.from_hash}:{self.to_hash}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SemanticDiff:
        return cls(**d)


@dataclass
class EvalScore:
    commit_hash: str
    metric: str  # e.g. "pass_rate", "avg_latency_ms", "cost_per_run"
    value: float
    recorded_at: str
    notes: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> EvalScore:
        return cls(**d)
