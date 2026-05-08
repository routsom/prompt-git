"""Integration tests for the pgit CLI — uses CliRunner with temp .promptgit dirs."""

import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pgit.cli.main import app

runner = CliRunner()


@pytest.fixture
def work_dir(tmp_path):
    """Create a temp working directory and chdir into it."""
    original = os.getcwd()
    os.chdir(tmp_path)
    # Create a sample prompt file
    (tmp_path / "system.md").write_text("You are a helpful assistant.\n\nBe concise.")
    yield tmp_path
    os.chdir(original)


@pytest.fixture
def repo(work_dir):
    """Initialise a pgit repo in the temp dir."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    return work_dir


class TestInit:
    def test_init_creates_promptgit(self, work_dir):
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert (work_dir / ".promptgit").is_dir()
        assert "✓" in result.output

    def test_init_twice_fails(self, work_dir):
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 1


class TestAddAndCommit:
    def test_add_file(self, repo):
        result = runner.invoke(app, ["add", "system.md"])
        assert result.exit_code == 0
        assert "staged" in result.output

    def test_add_nonexistent(self, repo):
        result = runner.invoke(app, ["add", "nonexistent.md"])
        assert "error" in result.output

    def test_commit(self, repo):
        runner.invoke(app, ["add", "system.md"])
        result = runner.invoke(app, [
            "commit", "-m", "initial prompt",
        ])
        assert result.exit_code == 0
        assert "initial prompt" in result.output

    def test_commit_empty_fails(self, repo):
        result = runner.invoke(app, ["commit", "-m", "empty"])
        assert result.exit_code == 1


class TestLog:
    def test_log_empty(self, repo):
        result = runner.invoke(app, ["log"])
        assert result.exit_code == 0
        assert "No commits" in result.output

    def test_log_after_commit(self, repo):
        runner.invoke(app, ["add", "system.md"])
        runner.invoke(app, ["commit", "-m", "first commit"])
        result = runner.invoke(app, ["log"])
        assert result.exit_code == 0
        assert "first commit" in result.output

    def test_log_json(self, repo):
        runner.invoke(app, ["add", "system.md"])
        runner.invoke(app, ["commit", "-m", "json test"])
        result = runner.invoke(app, ["log", "--json"])
        assert result.exit_code == 0
        assert "json test" in result.output


class TestStatus:
    def test_status_clean(self, repo):
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Nothing to commit" in result.output or "no commits" in result.output.lower()

    def test_status_staged(self, repo):
        runner.invoke(app, ["add", "system.md"])
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "system.md" in result.output


class TestDiff:
    def test_diff_no_commits(self, repo):
        result = runner.invoke(app, ["diff"])
        assert result.exit_code == 0

    def test_diff_after_two_commits(self, repo):
        runner.invoke(app, ["add", "system.md"])
        runner.invoke(app, ["commit", "-m", "v1"])
        # Modify the file
        (repo / "system.md").write_text("You are a strict assistant.\n\nBe very concise.")
        runner.invoke(app, ["add", "system.md"])
        runner.invoke(app, ["commit", "-m", "v2"])
        result = runner.invoke(app, ["diff"])
        assert result.exit_code == 0


class TestBranch:
    def test_branch_list_empty(self, repo):
        result = runner.invoke(app, ["branch", "list"])
        # No branches until first commit
        assert result.exit_code == 0

    def test_branch_create_and_switch(self, repo):
        runner.invoke(app, ["add", "system.md"])
        runner.invoke(app, ["commit", "-m", "first"])

        result = runner.invoke(app, ["branch", "create", "experiment"])
        assert result.exit_code == 0
        assert "experiment" in result.output

        result = runner.invoke(app, ["branch", "switch", "experiment"])
        assert result.exit_code == 0

    def test_branch_delete(self, repo):
        runner.invoke(app, ["add", "system.md"])
        runner.invoke(app, ["commit", "-m", "first"])
        runner.invoke(app, ["branch", "create", "feature"])
        result = runner.invoke(app, ["branch", "delete", "feature"])
        assert result.exit_code == 0


class TestTag:
    def test_tag_head(self, repo):
        runner.invoke(app, ["add", "system.md"])
        runner.invoke(app, ["commit", "-m", "release"])
        result = runner.invoke(app, ["tag", "v1.0", "-m", "first release"])
        assert result.exit_code == 0
        assert "v1.0" in result.output


class TestMerge:
    def test_merge_branch(self, repo):
        # Create initial commit
        runner.invoke(app, ["add", "system.md"])
        runner.invoke(app, ["commit", "-m", "initial"])

        # Create and switch to feature branch
        runner.invoke(app, ["branch", "create", "feature"])
        runner.invoke(app, ["branch", "switch", "feature"])

        # Modify and commit on feature
        (repo / "system.md").write_text("Updated prompt on feature branch.")
        runner.invoke(app, ["add", "system.md"])
        runner.invoke(app, ["commit", "-m", "feature update"])

        # Switch back and merge
        runner.invoke(app, ["branch", "switch", "main"])
        result = runner.invoke(app, ["merge", "feature"])
        assert result.exit_code == 0
        assert "Merge" in result.output


class TestEval:
    def test_eval_attach_and_show(self, repo):
        runner.invoke(app, ["add", "system.md"])
        runner.invoke(app, ["commit", "-m", "test"])

        result = runner.invoke(app, ["eval", "attach", "pass_rate", "0.95"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["eval", "show"])
        assert result.exit_code == 0
        assert "pass_rate" in result.output
