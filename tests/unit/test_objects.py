"""Tests for content-addressed objects and hashing."""

from pgit.objects import Blob, Commit, Tag, Tree, hash_blob, hash_commit, hash_tag, hash_tree


class TestHashDeterminism:
    """Hash functions must be deterministic — same inputs, same hash."""

    def test_hash_blob_deterministic(self):
        h1 = hash_blob("hello world", "plaintext", None)
        h2 = hash_blob("hello world", "plaintext", None)
        assert h1 == h2

    def test_hash_blob_different_content(self):
        h1 = hash_blob("hello", "plaintext", None)
        h2 = hash_blob("world", "plaintext", None)
        assert h1 != h2

    def test_hash_blob_different_format(self):
        h1 = hash_blob("content", "plaintext", None)
        h2 = hash_blob("content", "jinja2", None)
        assert h1 != h2

    def test_hash_blob_with_model_hint(self):
        h1 = hash_blob("content", "plaintext", None)
        h2 = hash_blob("content", "plaintext", "gpt-4")
        assert h1 != h2

    def test_hash_tree_deterministic(self):
        entries = {"a.md": "abc123", "b.md": "def456"}
        h1 = hash_tree(entries)
        h2 = hash_tree(entries)
        assert h1 == h2

    def test_hash_tree_order_independent(self):
        h1 = hash_tree({"a": "1", "b": "2"})
        h2 = hash_tree({"b": "2", "a": "1"})
        assert h1 == h2  # sort_keys=True makes this deterministic

    def test_hash_commit_deterministic(self):
        h1 = hash_commit(None, "tree1", "msg", "author", "2026-01-01T00:00:00Z")
        h2 = hash_commit(None, "tree1", "msg", "author", "2026-01-01T00:00:00Z")
        assert h1 == h2

    def test_hash_commit_different_timestamp(self):
        """Two commits with same content but different timestamps → different hashes."""
        h1 = hash_commit(None, "tree1", "msg", "author", "2026-01-01T00:00:00Z")
        h2 = hash_commit(None, "tree1", "msg", "author", "2026-01-02T00:00:00Z")
        assert h1 != h2

    def test_hash_tag_deterministic(self):
        h1 = hash_tag("v1.0", "commit1", "release", "2026-01-01T00:00:00Z")
        h2 = hash_tag("v1.0", "commit1", "release", "2026-01-01T00:00:00Z")
        assert h1 == h2


class TestBlobCreate:
    def test_create_blob(self):
        blob = Blob.create("hello world", "plaintext")
        assert blob.content == "hello world"
        assert blob.format == "plaintext"
        assert blob.model_hint is None
        assert len(blob.hash) == 64  # SHA-256

    def test_create_blob_with_model_hint(self):
        blob = Blob.create("test", "plaintext", "gpt-4")
        assert blob.model_hint == "gpt-4"

    def test_blob_roundtrip(self):
        blob = Blob.create("test content", "jinja2", "claude-sonnet-4-6")
        d = blob.to_dict()
        restored = Blob.from_dict(d)
        assert restored.hash == blob.hash
        assert restored.content == blob.content
        assert restored.format == blob.format
        assert restored.model_hint == blob.model_hint


class TestTreeCreate:
    def test_create_tree(self):
        entries = {"prompt.md": "abc123"}
        tree = Tree.create(entries)
        assert tree.entries == entries
        assert len(tree.hash) == 64

    def test_tree_roundtrip(self):
        entries = {"a.md": "hash1", "b.txt": "hash2"}
        tree = Tree.create(entries)
        restored = Tree.from_dict(tree.to_dict())
        assert restored.hash == tree.hash
        assert restored.entries == tree.entries


class TestCommitCreate:
    def test_create_root_commit(self):
        commit = Commit.create(
            parent=None, tree="tree1", message="initial",
            author="test", committed_at="2026-01-01T00:00:00Z",
        )
        assert commit.parent is None
        assert commit.message == "initial"
        assert len(commit.hash) == 64

    def test_create_child_commit(self):
        c1 = Commit.create(None, "t1", "first", "author", "2026-01-01T00:00:00Z")
        c2 = Commit.create(c1.hash, "t2", "second", "author", "2026-01-02T00:00:00Z")
        assert c2.parent == c1.hash
        assert c2.hash != c1.hash

    def test_commit_roundtrip(self):
        commit = Commit.create(None, "t1", "msg", "author", "2026-01-01T00:00:00Z")
        restored = Commit.from_dict(commit.to_dict())
        assert restored.hash == commit.hash


class TestTagCreate:
    def test_create_tag(self):
        tag = Tag.create("v1.0", "commit1", "release", "2026-01-01T00:00:00Z")
        assert tag.name == "v1.0"
        assert tag.target == "commit1"
        assert len(tag.hash) == 64

    def test_tag_roundtrip(self):
        tag = Tag.create("v1.0", "commit1", None, "2026-01-01T00:00:00Z")
        restored = Tag.from_dict(tag.to_dict())
        assert restored.hash == tag.hash
        assert restored.name == tag.name
