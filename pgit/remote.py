"""Remote sync — push/pull objects to/from a remote store."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pgit.store import ObjectStore


class RemoteBase(ABC):
    """Abstract base for remote backends."""

    @abstractmethod
    def push(self, store: ObjectStore, branch: str) -> int:
        """Push objects to the remote. Returns count of objects pushed."""
        ...

    @abstractmethod
    def pull(self, store: ObjectStore, branch: str) -> int:
        """Pull objects from the remote. Returns count of objects pulled."""
        ...


class LocalRemote(RemoteBase):
    """Local filesystem remote — syncs by copying SQLite objects."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _get_remote_store(self) -> ObjectStore:
        db_path = self.path / "store.db"
        return ObjectStore(db_path)

    def push(self, store: ObjectStore, branch: str) -> int:
        """Push local objects that the remote doesn't have."""
        remote_store = self._get_remote_store()
        pushed = 0

        # Push all objects
        for obj_hash, data in store.list_objects():
            if not remote_store.has_object(obj_hash):
                result = store.get_object(obj_hash)
                if result:
                    obj_type, obj_data = result
                    remote_store.put_object(obj_hash, obj_type, obj_data)
                    pushed += 1

        # Push branch ref
        ref_name = f"refs/heads/{branch}"
        ref_target = store.get_ref(ref_name)
        if ref_target:
            remote_store.set_ref(ref_name, ref_target)

        remote_store.close()
        return pushed

    def pull(self, store: ObjectStore, branch: str) -> int:
        """Pull remote objects that we don't have locally."""
        remote_store = self._get_remote_store()
        pulled = 0

        for obj_hash, data in remote_store.list_objects():
            if not store.has_object(obj_hash):
                result = remote_store.get_object(obj_hash)
                if result:
                    obj_type, obj_data = result
                    store.put_object(obj_hash, obj_type, obj_data)
                    pulled += 1

        # Pull branch ref
        ref_name = f"refs/heads/{branch}"
        ref_target = remote_store.get_ref(ref_name)
        if ref_target:
            store.set_ref(ref_name, ref_target)

        remote_store.close()
        return pulled
