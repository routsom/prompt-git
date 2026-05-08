"""Tests for the semantic diff engine — uses golden fixtures, never hits live LLM."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pgit.objects import SemanticDiff
from pgit.semantic_diff import generate_semantic_diff
from pgit.store import ObjectStore

FIXTURES = Path(__file__).parent.parent / "fixtures"
GOLDEN = FIXTURES / "golden"


@pytest.fixture
def store(tmp_path):
    s = ObjectStore(tmp_path / "test.db")
    yield s
    s.close()


class TestSemanticDiffCache:
    def test_returns_cached_diff(self, store):
        """If a cached diff exists, return it without calling the LLM."""
        from pgit.objects import hash_blob

        from_text = "text_a"
        to_text = "text_b"
        from_hash = hash_blob(from_text, "plaintext", None)
        to_hash = hash_blob(to_text, "plaintext", None)

        diff = SemanticDiff(
            from_hash=from_hash, to_hash=to_hash, summary="cached result",
            additions=[], removals=[], tone_shift=None,
            structural_changes=[], model_used="test", generated_at="2026-01-01",
        )
        store.put_semantic_diff(diff)

        # Should return cached result without ever calling the LLM
        result = generate_semantic_diff(from_text, to_text, store)
        assert result.summary == "cached result"

    def test_missing_api_key_raises(self, store):
        """Semantic diff without API key should raise RuntimeError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError, match="PGIT_LLM_KEY"):
                generate_semantic_diff("a", "b", store)


class TestGoldenFixtures:
    def test_golden_schema(self):
        """Verify golden fixtures match SemanticDiff schema."""
        golden_file = GOLDEN / "semantic_diff_safety.json"
        data = json.loads(golden_file.read_text())
        assert "summary" in data
        assert "additions" in data
        assert "removals" in data
        assert "tone_shift" in data
        assert "structural_changes" in data
        assert isinstance(data["additions"], list)
        assert isinstance(data["removals"], list)
