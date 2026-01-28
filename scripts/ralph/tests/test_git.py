"""Unit tests for shared/git.py module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from shared.git import (
    CommitResult,
    GitError,
    commit_story,
    get_dirty_files,
    get_staged_files,
    reset_staged,
    _run_git,
    _GitResult,
)


class TestCommitStory:
    """Tests for commit_story function."""

    @patch("shared.git._run_git")
    def test_commits_whitelisted_files_only(self, mock_run_git: MagicMock) -> None:
        """Test that only whitelisted files are staged and committed."""
        # Setup mocks for file checks and commit
        mock_run_git.side_effect = [
            # First file - diff check shows changes
            _GitResult(0, "file1.py\n", ""),
            # Second file - diff check shows changes
            _GitResult(0, "file2.py\n", ""),
            # Stage file1
            _GitResult(0, "", ""),
            # Stage file2
            _GitResult(0, "", ""),
            # Commit
            _GitResult(0, "", ""),
            # Get SHA
            _GitResult(0, "abc123def456\n", ""),
        ]

        with patch.object(Path, "exists", return_value=True):
            result = commit_story("US-001", "Test Story", ["file1.py", "file2.py"])

        assert result.success is True
        assert result.sha == "abc123def456"

    @patch("shared.git._run_git")
    def test_commit_message_format(self, mock_run_git: MagicMock) -> None:
        """Test commit message follows format: feat: [ID] - [Title]."""
        mock_run_git.side_effect = [
            _GitResult(0, "file1.py\n", ""),  # diff check
            _GitResult(0, "", ""),  # stage
            _GitResult(0, "", ""),  # commit
            _GitResult(0, "sha123\n", ""),  # get SHA
        ]

        with patch.object(Path, "exists", return_value=True):
            commit_story("US-042", "My Feature Title", ["file1.py"])

        # Find the commit call
        commit_call = None
        for c in mock_run_git.call_args_list:
            if c[0][0][0] == "commit":
                commit_call = c
                break

        assert commit_call is not None
        assert commit_call[0][0] == ["commit", "-m", "feat: US-042 - My Feature Title"]

    @patch("shared.git._run_git")
    def test_returns_commit_sha_on_success(self, mock_run_git: MagicMock) -> None:
        """Test that commit SHA is returned on successful commit."""
        mock_run_git.side_effect = [
            _GitResult(0, "file.py\n", ""),  # diff
            _GitResult(0, "", ""),  # stage
            _GitResult(0, "", ""),  # commit
            _GitResult(0, "deadbeef1234567890\n", ""),  # rev-parse
        ]

        with patch.object(Path, "exists", return_value=True):
            result = commit_story("US-001", "Title", ["file.py"])

        assert result.success is True
        assert result.sha == "deadbeef1234567890"

    @patch("shared.git._run_git")
    def test_ignores_non_whitelisted_dirty_files(self, mock_run_git: MagicMock) -> None:
        """Test that unrelated dirty files are not committed."""
        # Only check for whitelisted file, not others
        mock_run_git.side_effect = [
            _GitResult(0, "whitelisted.py\n", ""),  # diff check
            _GitResult(0, "", ""),  # stage
            _GitResult(0, "", ""),  # commit
            _GitResult(0, "abc123\n", ""),  # SHA
        ]

        with patch.object(Path, "exists", return_value=True):
            result = commit_story("US-001", "Title", ["whitelisted.py"])

        # Should only stage the whitelisted file
        stage_calls = [c for c in mock_run_git.call_args_list if c[0][0][0] == "add"]
        assert len(stage_calls) == 1
        assert stage_calls[0][0][0] == ["add", "whitelisted.py"]
        assert result.success is True

    @patch("shared.git._run_git")
    def test_fails_gracefully_with_empty_whitelist(self, mock_run_git: MagicMock) -> None:
        """Test that empty file list returns error."""
        result = commit_story("US-001", "Title", [])

        assert result.success is False
        assert "No files" in result.error

    @patch("shared.git._run_git")
    def test_fails_gracefully_when_no_changes(self, mock_run_git: MagicMock) -> None:
        """Test failure when whitelisted files have no changes."""
        mock_run_git.side_effect = [
            _GitResult(0, "", ""),  # diff check - no changes
            _GitResult(0, "", ""),  # untracked check - not untracked
        ]

        with patch.object(Path, "exists", return_value=True):
            result = commit_story("US-001", "Title", ["unchanged.py"])

        assert result.success is False
        assert "No whitelisted files have changes" in result.error

    @patch("shared.git._run_git")
    def test_handles_stage_failure(self, mock_run_git: MagicMock) -> None:
        """Test handling when staging fails."""
        mock_run_git.side_effect = [
            _GitResult(0, "file.py\n", ""),  # diff
            _GitResult(1, "", "fatal: pathspec 'file.py' did not match any files"),  # stage fails
        ]

        with patch.object(Path, "exists", return_value=True):
            result = commit_story("US-001", "Title", ["file.py"])

        assert result.success is False
        assert "Failed to stage" in result.error

    @patch("shared.git._run_git")
    def test_handles_commit_failure(self, mock_run_git: MagicMock) -> None:
        """Test handling when commit fails."""
        mock_run_git.side_effect = [
            _GitResult(0, "file.py\n", ""),  # diff
            _GitResult(0, "", ""),  # stage
            _GitResult(1, "", "error: unable to create commit"),  # commit fails
        ]

        with patch.object(Path, "exists", return_value=True):
            result = commit_story("US-001", "Title", ["file.py"])

        assert result.success is False
        assert "Commit failed" in result.error

    @patch("shared.git._run_git")
    def test_handles_nothing_to_commit(self, mock_run_git: MagicMock) -> None:
        """Test handling when nothing to commit after staging."""
        mock_run_git.side_effect = [
            _GitResult(0, "file.py\n", ""),  # diff
            _GitResult(0, "", ""),  # stage
            _GitResult(1, "nothing to commit, working tree clean", ""),  # commit
        ]

        with patch.object(Path, "exists", return_value=True):
            result = commit_story("US-001", "Title", ["file.py"])

        assert result.success is False
        assert "Nothing to commit" in result.error

    @patch("shared.git._run_git")
    def test_skips_nonexistent_files(self, mock_run_git: MagicMock) -> None:
        """Test that non-existent files in whitelist are skipped."""
        # existing.py exists and has changes, missing.py doesn't exist
        mock_run_git.side_effect = [
            _GitResult(0, "existing.py\n", ""),  # diff for existing
            _GitResult(0, "", ""),  # stage existing
            _GitResult(0, "", ""),  # commit
            _GitResult(0, "sha123\n", ""),  # SHA
        ]

        def exists_side_effect(self):
            return str(self).endswith("existing.py")

        with patch.object(Path, "exists", exists_side_effect):
            result = commit_story("US-001", "Title", ["existing.py", "missing.py"])

        assert result.success is True
        # Only existing.py should be staged
        stage_calls = [c for c in mock_run_git.call_args_list if c[0][0][0] == "add"]
        assert len(stage_calls) == 1

    @patch("shared.git._run_git")
    def test_handles_untracked_files(self, mock_run_git: MagicMock) -> None:
        """Test that new untracked files can be committed."""
        mock_run_git.side_effect = [
            _GitResult(0, "", ""),  # diff - no diff because new file
            _GitResult(0, "newfile.py\n", ""),  # ls-files shows untracked
            _GitResult(0, "", ""),  # stage
            _GitResult(0, "", ""),  # commit
            _GitResult(0, "sha456\n", ""),  # SHA
        ]

        with patch.object(Path, "exists", return_value=True):
            result = commit_story("US-001", "Title", ["newfile.py"])

        assert result.success is True
        assert result.sha == "sha456"

    @patch("shared.git._run_git")
    def test_working_dir_passed_to_git(self, mock_run_git: MagicMock) -> None:
        """Test that working directory is passed to git commands."""
        mock_run_git.side_effect = [
            _GitResult(0, "file.py\n", ""),
            _GitResult(0, "", ""),
            _GitResult(0, "", ""),
            _GitResult(0, "sha\n", ""),
        ]

        with patch.object(Path, "exists", return_value=True):
            commit_story("US-001", "Title", ["file.py"], working_dir="/custom/path")

        # All calls should have cwd set
        for c in mock_run_git.call_args_list:
            assert c[1]["cwd"] == "/custom/path"

    @patch("shared.git._run_git")
    def test_returns_unknown_sha_if_rev_parse_fails(self, mock_run_git: MagicMock) -> None:
        """Test that 'unknown' SHA returned if rev-parse fails but commit succeeded."""
        mock_run_git.side_effect = [
            _GitResult(0, "file.py\n", ""),  # diff
            _GitResult(0, "", ""),  # stage
            _GitResult(0, "", ""),  # commit succeeds
            _GitResult(1, "", "error"),  # rev-parse fails
        ]

        with patch.object(Path, "exists", return_value=True):
            result = commit_story("US-001", "Title", ["file.py"])

        assert result.success is True
        assert result.sha == "unknown"


class TestRunGit:
    """Tests for _run_git helper function."""

    @patch("shared.git.subprocess.run")
    def test_runs_git_command(self, mock_run: MagicMock) -> None:
        """Test that git command is executed correctly."""
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")

        result = _run_git(["status"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["git", "status"]

    @patch("shared.git.subprocess.run")
    def test_captures_output(self, mock_run: MagicMock) -> None:
        """Test that stdout and stderr are captured."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="stdout text", stderr="stderr text"
        )

        result = _run_git(["status"])

        assert result.stdout == "stdout text"
        assert result.stderr == "stderr text"
        assert result.returncode == 0

    @patch("shared.git.subprocess.run")
    def test_handles_timeout(self, mock_run: MagicMock) -> None:
        """Test handling of timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=30)

        result = _run_git(["status"])

        assert result.returncode == -1
        assert "timed out" in result.stderr.lower()

    @patch("shared.git.subprocess.run")
    def test_handles_git_not_found(self, mock_run: MagicMock) -> None:
        """Test handling when git is not installed."""
        mock_run.side_effect = FileNotFoundError()

        result = _run_git(["status"])

        assert result.returncode == -1
        assert "git" in result.stderr.lower()
        assert "not found" in result.stderr.lower()

    @patch("shared.git.subprocess.run")
    def test_handles_unexpected_error(self, mock_run: MagicMock) -> None:
        """Test handling of unexpected errors."""
        mock_run.side_effect = RuntimeError("unexpected")

        result = _run_git(["status"])

        assert result.returncode == -1
        assert "unexpected" in result.stderr.lower()

    @patch("shared.git.subprocess.run")
    def test_uses_working_dir(self, mock_run: MagicMock) -> None:
        """Test that working directory is passed to subprocess."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        _run_git(["status"], cwd="/some/path")

        assert mock_run.call_args[1]["cwd"] == "/some/path"


class TestGetStagedFiles:
    """Tests for get_staged_files function."""

    @patch("shared.git._run_git")
    def test_returns_staged_files(self, mock_run_git: MagicMock) -> None:
        """Test that staged files are returned."""
        mock_run_git.return_value = _GitResult(0, "file1.py\nfile2.py\n", "")

        files = get_staged_files()

        assert files == ["file1.py", "file2.py"]

    @patch("shared.git._run_git")
    def test_returns_empty_on_no_staged(self, mock_run_git: MagicMock) -> None:
        """Test empty list when no files staged."""
        mock_run_git.return_value = _GitResult(0, "", "")

        files = get_staged_files()

        assert files == []

    @patch("shared.git._run_git")
    def test_returns_empty_on_error(self, mock_run_git: MagicMock) -> None:
        """Test empty list on git error."""
        mock_run_git.return_value = _GitResult(1, "", "error")

        files = get_staged_files()

        assert files == []

    @patch("shared.git._run_git")
    def test_passes_working_dir(self, mock_run_git: MagicMock) -> None:
        """Test that working directory is passed."""
        mock_run_git.return_value = _GitResult(0, "", "")

        get_staged_files(working_dir="/path")

        assert mock_run_git.call_args[1]["cwd"] == "/path"


class TestGetDirtyFiles:
    """Tests for get_dirty_files function."""

    @patch("shared.git._run_git")
    def test_returns_modified_files(self, mock_run_git: MagicMock) -> None:
        """Test that modified files are returned."""
        mock_run_git.side_effect = [
            _GitResult(0, "modified.py\n", ""),  # tracked changes
            _GitResult(0, "", ""),  # untracked
        ]

        files = get_dirty_files()

        assert "modified.py" in files

    @patch("shared.git._run_git")
    def test_includes_untracked_files(self, mock_run_git: MagicMock) -> None:
        """Test that untracked files are included."""
        mock_run_git.side_effect = [
            _GitResult(0, "", ""),  # no tracked changes
            _GitResult(0, "untracked.py\n", ""),  # untracked
        ]

        files = get_dirty_files()

        assert "untracked.py" in files

    @patch("shared.git._run_git")
    def test_combines_tracked_and_untracked(self, mock_run_git: MagicMock) -> None:
        """Test that both tracked and untracked are returned."""
        mock_run_git.side_effect = [
            _GitResult(0, "tracked.py\n", ""),
            _GitResult(0, "untracked.py\n", ""),
        ]

        files = get_dirty_files()

        assert "tracked.py" in files
        assert "untracked.py" in files

    @patch("shared.git._run_git")
    def test_returns_empty_on_clean_working_dir(self, mock_run_git: MagicMock) -> None:
        """Test empty list on clean working directory."""
        mock_run_git.side_effect = [
            _GitResult(0, "", ""),
            _GitResult(0, "", ""),
        ]

        files = get_dirty_files()

        assert files == []


class TestResetStaged:
    """Tests for reset_staged function."""

    @patch("shared.git._run_git")
    def test_returns_true_on_success(self, mock_run_git: MagicMock) -> None:
        """Test True returned on successful reset."""
        mock_run_git.return_value = _GitResult(0, "", "")

        result = reset_staged()

        assert result is True
        mock_run_git.assert_called_with(["reset", "HEAD"], cwd=None)

    @patch("shared.git._run_git")
    def test_returns_false_on_failure(self, mock_run_git: MagicMock) -> None:
        """Test False returned on reset failure."""
        mock_run_git.return_value = _GitResult(1, "", "error")

        result = reset_staged()

        assert result is False

    @patch("shared.git._run_git")
    def test_passes_working_dir(self, mock_run_git: MagicMock) -> None:
        """Test that working directory is passed."""
        mock_run_git.return_value = _GitResult(0, "", "")

        reset_staged(working_dir="/path")

        assert mock_run_git.call_args[1]["cwd"] == "/path"


class TestCommitResultDataclass:
    """Tests for CommitResult dataclass."""

    def test_creates_success_result(self) -> None:
        """Test creating successful result."""
        result = CommitResult(success=True, sha="abc123")

        assert result.success is True
        assert result.sha == "abc123"
        assert result.error == ""

    def test_creates_failure_result(self) -> None:
        """Test creating failure result."""
        result = CommitResult(success=False, error="Something went wrong")

        assert result.success is False
        assert result.sha == ""
        assert result.error == "Something went wrong"

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        result = CommitResult(success=True)

        assert result.sha == ""
        assert result.error == ""


class TestGitErrorException:
    """Tests for GitError exception."""

    def test_can_raise_git_error(self) -> None:
        """Test that GitError can be raised with message."""
        with pytest.raises(GitError) as exc_info:
            raise GitError("Test git error")

        assert "Test git error" in str(exc_info.value)
