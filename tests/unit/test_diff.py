"""Tests for the line diff engine."""

from pgit.diff import diff_stats, line_diff


class TestLineDiff:
    def test_identical_texts(self):
        result = line_diff("hello", "hello")
        assert result == ""

    def test_simple_change(self):
        result = line_diff("hello\nworld\n", "hello\nearth\n")
        assert "-world" in result
        assert "+earth" in result

    def test_addition(self):
        result = line_diff("line1\n", "line1\nline2\n")
        assert "+line2" in result

    def test_deletion(self):
        result = line_diff("line1\nline2\n", "line1\n")
        assert "-line2" in result

    def test_labels(self):
        result = line_diff("a\n", "b\n", from_label="old.md", to_label="new.md")
        assert "old.md" in result
        assert "new.md" in result


class TestDiffStats:
    def test_no_changes(self):
        stats = diff_stats("hello", "hello")
        assert stats == {"insertions": 0, "deletions": 0}

    def test_insertions(self):
        stats = diff_stats("a", "a\nb\nc")
        assert stats["insertions"] == 2
        assert stats["deletions"] == 0

    def test_deletions(self):
        stats = diff_stats("a\nb\nc", "a")
        assert stats["deletions"] == 2
        assert stats["insertions"] == 0

    def test_mixed(self):
        stats = diff_stats("a\nb", "a\nc")
        assert stats["insertions"] == 1
        assert stats["deletions"] == 1
