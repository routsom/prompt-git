"""Branch and HEAD management."""

from __future__ import annotations

from pgit.store import ObjectStore


class BranchManager:
    """Manage branches and HEAD using the refs table."""

    HEAD = "HEAD"
    HEADS_PREFIX = "refs/heads/"
    TAGS_PREFIX = "refs/tags/"

    def __init__(self, store: ObjectStore) -> None:
        self._store = store

    def get_head(self) -> str | None:
        return self._store.get_ref(self.HEAD)

    def set_head(self, target: str) -> None:
        self._store.set_ref(self.HEAD, target)

    def resolve_head(self) -> str | None:
        head = self.get_head()
        if head is None:
            return None
        if head.startswith(self.HEADS_PREFIX):
            return self._store.get_ref(head)
        return head

    def current_branch(self) -> str | None:
        head = self.get_head()
        if head and head.startswith(self.HEADS_PREFIX):
            return head[len(self.HEADS_PREFIX):]
        return None

    def create_branch(self, name: str, commit_hash: str) -> None:
        ref = self.HEADS_PREFIX + name
        if self._store.get_ref(ref) is not None:
            raise ValueError(f"Branch '{name}' already exists")
        self._store.set_ref(ref, commit_hash)

    def switch_branch(self, name: str) -> str:
        ref = self.HEADS_PREFIX + name
        target = self._store.get_ref(ref)
        if target is None:
            raise ValueError(f"Branch '{name}' does not exist")
        self.set_head(ref)
        return target

    def delete_branch(self, name: str) -> None:
        ref = self.HEADS_PREFIX + name
        current = self.get_head()
        if current == ref:
            raise ValueError(f"Cannot delete the current branch '{name}'")
        if not self._store.delete_ref(ref):
            raise ValueError(f"Branch '{name}' does not exist")

    def list_branches(self) -> list[tuple[str, str]]:
        refs = self._store.list_refs(self.HEADS_PREFIX)
        return [(name[len(self.HEADS_PREFIX):], target) for name, target in refs]

    def update_branch(self, name: str, commit_hash: str) -> None:
        ref = self.HEADS_PREFIX + name
        if self._store.get_ref(ref) is None:
            raise ValueError(f"Branch '{name}' does not exist")
        self._store.set_ref(ref, commit_hash)

    def get_branch_commit(self, name: str) -> str | None:
        return self._store.get_ref(self.HEADS_PREFIX + name)
