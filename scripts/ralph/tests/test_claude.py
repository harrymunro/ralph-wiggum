"""Unit tests for shared/claude.py module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from shared.claude import (
    ClaudeError,
    ClaudeResult,
    invoke_claude,
    _kill_process_tree,
)


class TestInvokeClaude:
    """Tests for invoke_claude function."""

    @patch("shared.claude.subprocess.Popen")
    def test_returns_stdout_stderr_exit_code(self, mock_popen: MagicMock) -> None:
        """Test that invoke_claude returns tuple of stdout, stderr, exit_code."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        stdout, stderr, exit_code = invoke_claude("test prompt")

        assert stdout == "output"
        assert stderr == ""
        assert exit_code == 0

    @patch("shared.claude.subprocess.Popen")
    def test_spawns_claude_with_p_flag(self, mock_popen: MagicMock) -> None:
        """Test that claude is spawned with -p flag and prompt."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        invoke_claude("my test prompt")

        mock_popen.assert_called_once()
        args = mock_popen.call_args
        assert args[0][0] == ["claude", "-p", "my test prompt"]

    @patch("shared.claude.subprocess.Popen")
    def test_captures_stderr_output(self, mock_popen: MagicMock) -> None:
        """Test that stderr is captured in the return."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("stdout", "stderr output")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        stdout, stderr, exit_code = invoke_claude("prompt")

        assert stdout == "stdout"
        assert stderr == "stderr output"
        assert exit_code == 1

    @patch("shared.claude.subprocess.Popen")
    def test_handles_timeout_gracefully(self, mock_popen: MagicMock) -> None:
        """Test that timeout kills process and returns timeout error."""
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(
            cmd="claude", timeout=10
        )
        mock_process.terminate = MagicMock()
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        stdout, stderr, exit_code = invoke_claude("prompt", timeout=10)

        assert stdout == ""
        assert "Timeout" in stderr
        assert "10s" in stderr
        assert exit_code == -1

    @patch("shared.claude.subprocess.Popen")
    def test_process_killed_on_timeout(self, mock_popen: MagicMock) -> None:
        """Test that process is fully terminated on timeout."""
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(
            cmd="claude", timeout=10
        )
        mock_process.wait = MagicMock()  # Don't raise TimeoutExpired for wait
        mock_popen.return_value = mock_process

        invoke_claude("prompt", timeout=10)

        # Verify terminate was called (graceful shutdown)
        mock_process.terminate.assert_called_once()

    @patch("shared.claude.subprocess.Popen")
    def test_uses_provided_timeout(self, mock_popen: MagicMock) -> None:
        """Test that the provided timeout value is used."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        invoke_claude("prompt", timeout=60)

        mock_process.communicate.assert_called_once_with(timeout=60)

    @patch("shared.claude.subprocess.Popen")
    def test_default_timeout_is_300(self, mock_popen: MagicMock) -> None:
        """Test that default timeout is 300 seconds."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        invoke_claude("prompt")

        mock_process.communicate.assert_called_once_with(timeout=300)

    @patch("shared.claude.subprocess.Popen")
    def test_handles_claude_not_found(self, mock_popen: MagicMock) -> None:
        """Test graceful handling when claude command not in PATH."""
        mock_popen.side_effect = FileNotFoundError()

        stdout, stderr, exit_code = invoke_claude("prompt")

        assert stdout == ""
        assert "claude" in stderr.lower()
        assert "not found" in stderr.lower()
        assert exit_code == -1

    @patch("shared.claude.subprocess.Popen")
    def test_process_not_zombie(self, mock_popen: MagicMock) -> None:
        """Test that process is fully reaped, no zombies left."""
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(
            cmd="claude", timeout=1
        )
        # First wait succeeds (graceful termination)
        mock_process.wait = MagicMock()
        mock_popen.return_value = mock_process

        invoke_claude("prompt", timeout=1)

        # wait() should be called to reap the process
        assert mock_process.wait.called

    @patch("shared.claude.subprocess.Popen")
    def test_force_kill_if_terminate_fails(self, mock_popen: MagicMock) -> None:
        """Test that kill() is used if terminate() doesn't stop process."""
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(
            cmd="claude", timeout=1
        )
        # First wait (after terminate) times out
        mock_process.wait = MagicMock(
            side_effect=[subprocess.TimeoutExpired(cmd="", timeout=5), None]
        )
        mock_popen.return_value = mock_process

        invoke_claude("prompt", timeout=1)

        # Should have tried terminate first, then kill
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    @patch("shared.claude.subprocess.Popen")
    def test_working_dir_passed_to_subprocess(self, mock_popen: MagicMock) -> None:
        """Test that working directory is passed to subprocess."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        invoke_claude("prompt", working_dir="/some/path")

        args = mock_popen.call_args
        assert args[1]["cwd"] == "/some/path"

    @patch("shared.claude.subprocess.Popen")
    def test_handles_unexpected_exception(self, mock_popen: MagicMock) -> None:
        """Test that unexpected exceptions are handled gracefully."""
        mock_popen.side_effect = RuntimeError("Unexpected error")

        stdout, stderr, exit_code = invoke_claude("prompt")

        assert stdout == ""
        assert "Unexpected error" in stderr
        assert exit_code == -1


class TestKillProcessTree:
    """Tests for _kill_process_tree helper function."""

    def test_calls_terminate_first(self) -> None:
        """Test that terminate() is called before kill()."""
        mock_process = MagicMock()
        mock_process.wait = MagicMock()

        _kill_process_tree(mock_process)

        mock_process.terminate.assert_called_once()

    def test_calls_kill_if_terminate_times_out(self) -> None:
        """Test that kill() is called if terminate() doesn't work."""
        mock_process = MagicMock()
        mock_process.wait = MagicMock(
            side_effect=[subprocess.TimeoutExpired(cmd="", timeout=5), None]
        )

        _kill_process_tree(mock_process)

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    def test_handles_already_terminated_process(self) -> None:
        """Test handling of already-terminated process (ProcessLookupError)."""
        mock_process = MagicMock()
        mock_process.terminate.side_effect = ProcessLookupError()

        # Should not raise
        _kill_process_tree(mock_process)

    def test_waits_for_process_to_reap(self) -> None:
        """Test that wait() is called to reap the zombie process."""
        mock_process = MagicMock()
        mock_process.wait = MagicMock()

        _kill_process_tree(mock_process)

        # wait should be called after terminate
        mock_process.wait.assert_called()


class TestClaudeResultDataclass:
    """Tests for ClaudeResult dataclass."""

    def test_creates_result_with_defaults(self) -> None:
        """Test creating ClaudeResult with default timed_out=False."""
        result = ClaudeResult(stdout="out", stderr="err", exit_code=0)

        assert result.stdout == "out"
        assert result.stderr == "err"
        assert result.exit_code == 0
        assert result.timed_out is False

    def test_creates_result_with_timeout(self) -> None:
        """Test creating ClaudeResult with timed_out=True."""
        result = ClaudeResult(stdout="", stderr="timeout", exit_code=-1, timed_out=True)

        assert result.timed_out is True


class TestClaudeErrorException:
    """Tests for ClaudeError exception."""

    def test_can_raise_claude_error(self) -> None:
        """Test that ClaudeError can be raised with message."""
        with pytest.raises(ClaudeError) as exc_info:
            raise ClaudeError("Test error message")

        assert "Test error message" in str(exc_info.value)
