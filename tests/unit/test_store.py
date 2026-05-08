"""Tests for the SQLite object store."""

import tempfile
from pathlib import Path

import pytest

from pgit.objects import Blob, Commit, EvalScore, SemanticDiff, Tag, Tree
from pgit.store import ObjectStore


@pytest.fixture
def store(tmp_path):
    s = ObjectStore(tmp_path / "test.db")
    yield s
    s.close()


class TestObjectCRUD:
    def test_put_and_get_blob(self, store):
        blob = Blob.create("test content", "plaintext")
        store.put_blob(blob)
        result = store.get_blob(blob.hash)
        assert result is not None
        assert result.content == "test content"

    def test_get_nonexistent(self, store):
        assert store.get_blob("nonexistent") is None

    def test_idempotent_put(self, store):
        blob = Blob.create("test", "plaintext")
        store.put_blob(blob)
        store.put_blob(blob)  # Should not raise
        assert store.get_blob(blob.hash).content == "test"

    def test_put_and_get_tree(self, store):
        tree = Tree.create({"a.md": "hash1"})
        store.put_tree(tree)
        result = store.get_tree(tree.hash)
        assert result is not None
        assert result.entries == {"a.md": "hash1"}

    def test_put_and_get_commit(self, store):
        c = Commit.create(None, "tree1", "msg", "author", "2026-01-01T00:00:00Z")
        store.put_commit(c)
        result = store.get_commit(c.hash)
        assert result is not None
        assert result.message == "msg"

    def test_put_and_get_tag(self, store):
        tag = Tag.create("v1.0", "commit1", "release", "2026-01-01T00:00:00Z")
        store.put_tag(tag)
        result = store.get_tag(tag.hash)
        assert result is not None
        assert result.name == "v1.0"

    def test_find_tag_by_name(self, store):
        tag = Tag.create("v1.0", "commit1", "release", "2026-01-01T00:00:00Z")
        store.put_tag(tag)
        result = store.find_tag_by_name("v1.0")
        assert result is not None
        assert result.target == "commit1"

    def test_has_object(self, store):
        blob = Blob.create("test", "plaintext")
        assert not store.has_object(blob.hash)
        store.put_blob(blob)
        assert store.has_object(blob.hash)

    def test_list_objects(self, store):
        b1 = Blob.create("a", "plaintext")
        b2 = Blob.create("b", "plaintext")
        store.put_blob(b1)
        store.put_blob(b2)
        objects = store.list_objects("blob")
        assert len(objects) == 2


class TestRefs:
    def test_set_and_get_ref(self, store):
        store.set_ref("HEAD", "refs/heads/main")
        assert store.get_ref("HEAD") == "refs/heads/main"

    def test_update_ref(self, store):
        store.set_ref("HEAD", "abc")
        store.set_ref("HEAD", "def")
        assert store.get_ref("HEAD") == "def"

    def test_delete_ref(self, store):
        store.set_ref("HEAD", "abc")
        assert store.delete_ref("HEAD")
        assert store.get_ref("HEAD") is None

    def test_list_refs(self, store):
        store.set_ref("refs/heads/main", "abc")
        store.set_ref("refs/heads/dev", "def")
        store.set_ref("refs/tags/v1", "ghi")
        heads = store.list_refs("refs/heads/")
        assert len(heads) == 2


class TestIndex:
    def test_stage_and_get(self, store):
        store.stage("a.md", "hash1", "2026-01-01T00:00:00Z")
        entries = store.get_index()
        assert len(entries) == 1
        assert entries[0][0] == "a.md"

    def test_clear_index(self, store):
        store.stage("a.md", "hash1", "2026-01-01T00:00:00Z")
        store.clear_index()
        assert len(store.get_index()) == 0


class TestEvalScores:
    def test_add_and_get_eval_scores(self, store):
        score = EvalScore("commit1", "pass_rate", 0.95, "2026-01-01T00:00:00Z", None)
        store.add_eval_score(score)
        scores = store.get_eval_scores("commit1")
        assert len(scores) == 1
        assert scores[0].value == 0.95

    def test_get_eval_score_by_metric(self, store):
        s1 = EvalScore("commit1", "pass_rate", 0.95, "2026-01-01T00:00:00Z", None)
        s2 = EvalScore("commit1", "cost", 0.003, "2026-01-01T00:00:00Z", None)
        store.add_eval_score(s1)
        store.add_eval_score(s2)
        assert store.get_eval_score("commit1", "pass_rate") == 0.95
        assert store.get_eval_score("commit1", "cost") == 0.003


class TestSemanticDiffCache:
    def test_cache_semantic_diff(self, store):
        diff = SemanticDiff(
            from_hash="aaa", to_hash="bbb", summary="test",
            additions=["a"], removals=["b"], tone_shift=None,
            structural_changes=[], model_used="test", generated_at="2026-01-01T00:00:00Z",
        )
        store.put_semantic_diff(diff)
        cached = store.get_semantic_diff("aaa:bbb")
        assert cached is not None
        assert cached.summary == "test"

    def test_cache_miss(self, store):
        assert store.get_semantic_diff("xxx:yyy") is None
