"""PromptRepo — the core object that orchestrates all prompt-git operations."""

from __future__ import annotations

import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pgit.branch import BranchManager
from pgit.eval import EvalManager
from pgit.index import Index
from pgit.objects import Blob, Commit, Tag, Tree
from pgit.store import ObjectStore

PROMPTGIT_DIR = ".promptgit"
STORE_DB = "store.db"


class PromptRepo:
    """The core prompt-git repository object."""

    def __init__(self, root: Path | None = None) -> None:
        if root is None:
            root = Path.cwd()
        self.root = Path(root).resolve()
        self.pgit_dir = self.root / PROMPTGIT_DIR
        db = os.environ.get("PGIT_DB", str(self.pgit_dir / STORE_DB))
        self.store = ObjectStore(db)
        self.branches = BranchManager(self.store)
        self.index = Index(self.store, self.root)
        self.evals = EvalManager(self.store)

    @classmethod
    def init(cls, root: Path | None = None) -> PromptRepo:
        """Initialise a new prompt repository."""
        if root is None:
            root = Path.cwd()
        root = Path(root).resolve()
        pgit_dir = root / PROMPTGIT_DIR
        if pgit_dir.exists():
            raise FileExistsError(f"Prompt repo already initialised at {pgit_dir}")
        pgit_dir.mkdir(parents=True)
        repo = cls(root)
        # Set HEAD to main branch (symbolic ref)
        repo.branches.set_head("refs/heads/main")
        return repo

    @classmethod
    def open(cls, root: Path | None = None) -> PromptRepo:
        """Open an existing prompt repository."""
        if root is None:
            root = Path.cwd()
        root = Path(root).resolve()
        pgit_dir = root / PROMPTGIT_DIR
        if not pgit_dir.exists():
            raise FileNotFoundError(
                f"No prompt repo found at {pgit_dir}. Run 'pgit init' first."
            )
        return cls(root)

    @staticmethod
    def find_root(start: Path | None = None) -> Path | None:
        """Walk up from start to find the nearest .promptgit directory."""
        if start is None:
            start = Path.cwd()
        current = Path(start).resolve()
        while current != current.parent:
            if (current / PROMPTGIT_DIR).is_dir():
                return current
            current = current.parent
        if (current / PROMPTGIT_DIR).is_dir():
            return current
        return None

    # ------------------------------------------------------------------
    # Authoring
    # ------------------------------------------------------------------

    def _get_author(self) -> str:
        """Get the commit author from env or git config."""
        author = os.environ.get("PGIT_AUTHOR")
        if author:
            return author
        try:
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True, text=True, check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def add(self, file_path: str, model_hint: str | None = None) -> Blob:
        """Stage a file for the next commit."""
        return self.index.add(file_path, model_hint)

    def commit(self, message: str, author: str | None = None) -> Commit:
        """Create a commit from the staged index."""
        if self.index.is_empty():
            raise ValueError("Nothing to commit — stage files with 'pgit add' first")

        if author is None:
            author = self._get_author()

        # Build tree from staged entries
        entries: dict[str, str] = {}
        for path, blob_hash, _ in self.index.staged_entries():
            entries[path] = blob_hash

        tree = Tree.create(entries)
        self.store.put_tree(tree)

        # Get parent
        parent = self.branches.resolve_head()

        now = datetime.now(UTC).isoformat()
        commit = Commit.create(
            parent=parent,
            tree=tree.hash,
            message=message,
            author=author,
            committed_at=now,
        )
        self.store.put_commit(commit)

        # Update branch ref
        branch = self.branches.current_branch()
        if branch:
            # Branch might not exist yet (first commit on main)
            ref = f"refs/heads/{branch}"
            self.store.set_ref(ref, commit.hash)
        else:
            # Detached HEAD
            self.branches.set_head(commit.hash)

        # Clear index
        self.index.clear()

        return commit

    def log(self, branch: str | None = None, limit: int = 20) -> list[Commit]:
        """Return commit history for a branch (default: current)."""
        if branch:
            commit_hash = self.branches.get_branch_commit(branch)
        else:
            commit_hash = self.branches.resolve_head()

        if commit_hash is None:
            return []

        commits: list[Commit] = []
        current: str | None = commit_hash
        while current and len(commits) < limit:
            commit = self.store.get_commit(current)
            if commit is None:
                break
            # Attach eval scores
            scores = self.evals.get_scores(commit.hash)
            commit.eval_scores = {s.metric: s.value for s in scores}
            commits.append(commit)
            current = commit.parent

        return commits

    def diff_texts(
        self, from_ref: str | None = None, to_ref: str | None = None, file_path: str | None = None
    ) -> list[tuple[str, str, str]]:
        """Return list of (path, from_text, to_text) for changed files between refs.

        Default: HEAD~1..HEAD.
        """
        to_hash = self._resolve_ref(to_ref or "HEAD")
        if from_ref is None:
            from_ref = "HEAD~1"
        from_hash = self._resolve_ref(from_ref)

        if to_hash is None:
            return []

        to_commit = self.store.get_commit(to_hash)
        if to_commit is None:
            return []
        to_tree = self.store.get_tree(to_commit.tree)

        from_tree = None
        if from_hash:
            from_commit = self.store.get_commit(from_hash)
            if from_commit:
                from_tree = self.store.get_tree(from_commit.tree)

        diffs: list[tuple[str, str, str]] = []
        to_entries = to_tree.entries if to_tree else {}
        from_entries = from_tree.entries if from_tree else {}

        all_paths = set(to_entries.keys()) | set(from_entries.keys())
        if file_path:
            all_paths = {p for p in all_paths if p == file_path}

        for path in sorted(all_paths):
            from_blob_hash = from_entries.get(path)
            to_blob_hash = to_entries.get(path)

            if from_blob_hash == to_blob_hash:
                continue

            from_text = ""
            to_text = ""
            if from_blob_hash:
                blob = self.store.get_blob(from_blob_hash)
                if blob:
                    from_text = blob.content
            if to_blob_hash:
                blob = self.store.get_blob(to_blob_hash)
                if blob:
                    to_text = blob.content

            diffs.append((path, from_text, to_text))

        return diffs

    def tag(self, name: str, commit_hash: str | None = None, message: str | None = None) -> Tag:
        """Create a tag on a commit (defaults to HEAD)."""
        if commit_hash is None:
            commit_hash = self.branches.resolve_head()
        if commit_hash is None:
            raise ValueError("No commits to tag")

        # Check existing
        if self.store.find_tag_by_name(name):
            raise ValueError(f"Tag '{name}' already exists")

        now = datetime.now(UTC).isoformat()
        tag = Tag.create(name=name, target=commit_hash, message=message, created_at=now)
        self.store.put_tag(tag)
        self.store.set_ref(f"refs/tags/{name}", commit_hash)
        return tag

    def merge(
        self, branch: str, if_better: str | None = None, min_improvement: float = 5.0
    ) -> Commit:
        """Merge a branch into the current branch."""
        current = self.branches.current_branch()
        if current is None:
            raise ValueError("Cannot merge in detached HEAD state")

        source_hash = self.branches.get_branch_commit(branch)
        if source_hash is None:
            raise ValueError(f"Branch '{branch}' does not exist")

        target_hash = self.branches.resolve_head()

        # --if-better check
        if if_better:
            source_score = self.evals.get_score(source_hash, if_better)
            target_score = self.evals.get_score(target_hash, if_better) if target_hash else None

            if source_score is None:
                raise ValueError(f"No '{if_better}' eval score on branch '{branch}'")
            if target_score is None:
                raise ValueError(f"No '{if_better}' eval score on current branch '{current}'")

            improvement = (
                ((source_score - target_score) / abs(target_score)) * 100
                if target_score != 0
                else 100
            )
            if improvement < min_improvement:
                raise ValueError(
                    f"Merge rejected: {if_better} improvement is {improvement:.1f}% "
                    f"(minimum {min_improvement}% required). "
                    f"Source: {source_score}, Target: {target_score}"
                )

        # Get source tree
        source_commit = self.store.get_commit(source_hash)
        if source_commit is None:
            raise ValueError(f"Source commit not found: {source_hash[:8]}")

        source_tree = self.store.get_tree(source_commit.tree)
        target_tree = None
        if target_hash:
            target_commit = self.store.get_commit(target_hash)
            if target_commit:
                target_tree = self.store.get_tree(target_commit.tree)

        # Merge trees — source entries win on conflict
        merged_entries: dict[str, str] = {}
        if target_tree:
            merged_entries.update(target_tree.entries)
        if source_tree:
            merged_entries.update(source_tree.entries)

        merge_tree = Tree.create(merged_entries)
        self.store.put_tree(merge_tree)

        author = self._get_author()
        now = datetime.now(UTC).isoformat()
        merge_commit = Commit.create(
            parent=target_hash,
            tree=merge_tree.hash,
            message=f"Merge branch '{branch}' into {current}",
            author=author,
            committed_at=now,
            metadata={"merge_source": source_hash, "merge_branch": branch},
        )
        self.store.put_commit(merge_commit)

        # Update current branch
        self.branches.update_branch(current, merge_commit.hash)

        return merge_commit

    def status(self) -> dict[str, Any]:
        """Return repository status."""
        staged = self.index.staged_entries()
        head = self.branches.resolve_head()
        branch = self.branches.current_branch()

        # Detect unstaged changes
        unstaged: list[str] = []
        if head:
            head_commit = self.store.get_commit(head)
            if head_commit:
                tree = self.store.get_tree(head_commit.tree)
                if tree:
                    for path in tree.entries:
                        abs_path = self.root / path
                        if abs_path.is_file():
                            current_content = abs_path.read_text(encoding="utf-8")
                            blob = self.store.get_blob(tree.entries[path])
                            if blob and current_content != blob.content:
                                unstaged.append(path)
                        else:
                            unstaged.append(f"{path} (deleted)")

        return {
            "branch": branch,
            "head": head[:8] if head else None,
            "staged": [(p, h[:8]) for p, h, _ in staged],
            "unstaged": unstaged,
        }

    # ------------------------------------------------------------------
    # Ref resolution
    # ------------------------------------------------------------------

    def _resolve_ref(self, ref: str) -> str | None:
        """Resolve a ref to a commit hash.

        Supports: commit hashes, branch names, tag names, HEAD, HEAD~N.
        """
        if ref == "HEAD":
            return self.branches.resolve_head()

        # HEAD~N syntax
        match = re.match(r'^HEAD~(\d+)$', ref)
        if match:
            n = int(match.group(1))
            current = self.branches.resolve_head()
            for _ in range(n):
                if current is None:
                    return None
                commit = self.store.get_commit(current)
                if commit is None:
                    return None
                current = commit.parent
            return current

        # Branch name
        branch_hash = self.branches.get_branch_commit(ref)
        if branch_hash:
            return branch_hash

        # Tag name
        tag = self.store.find_tag_by_name(ref)
        if tag:
            return tag.target

        # Tag ref
        tag_ref = self.store.get_ref(f"refs/tags/{ref}")
        if tag_ref:
            return tag_ref

        # Direct commit hash
        if self.store.has_object(ref):
            return ref

        return None
