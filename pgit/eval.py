"""Eval score attachment and retrieval."""

from __future__ import annotations

from datetime import datetime, timezone

from pgit.objects import EvalScore
from pgit.store import ObjectStore


class EvalManager:
    """Attach and retrieve eval scores for commits."""

    def __init__(self, store: ObjectStore) -> None:
        self._store = store

    def attach(
        self,
        commit_hash: str,
        metric: str,
        value: float,
        notes: str | None = None,
    ) -> str:
        """Attach an eval score to a commit. Returns the score UUID."""
        # Verify commit exists
        if not self._store.has_object(commit_hash):
            raise ValueError(f"Commit '{commit_hash[:8]}' not found")

        now = datetime.now(timezone.utc).isoformat()
        score = EvalScore(
            commit_hash=commit_hash,
            metric=metric,
            value=value,
            recorded_at=now,
            notes=notes,
        )
        return self._store.add_eval_score(score)

    def get_scores(self, commit_hash: str) -> list[EvalScore]:
        """Get all eval scores for a commit."""
        return self._store.get_eval_scores(commit_hash)

    def get_score(self, commit_hash: str, metric: str) -> float | None:
        """Get the latest score for a specific metric on a commit."""
        return self._store.get_eval_score(commit_hash, metric)

    def compare(
        self, commit_a: str, commit_b: str, metric: str
    ) -> tuple[float | None, float | None]:
        """Compare eval scores between two commits for a given metric."""
        return (
            self.get_score(commit_a, metric),
            self.get_score(commit_b, metric),
        )
