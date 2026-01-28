"""Unit tests for micro_v/executor.py module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from shared.prd import UserStory
from micro_v.executor import (
    ExecutionResult,
    ExecutorConfig,
    ExecutionOutput,
    execute_story,
    _load_coder_prompt,
    _format_prompt,
    _run_validation,
    _log,
)


@pytest.fixture
def sample_story() -> UserStory:
    """Create a sample user story for testing."""
    return UserStory(
        id="US-001",
        title="Test Story",
        description="A test user story for testing",
        acceptanceCriteria=["Criterion 1", "Criterion 2"],
        priority=1,
        passes=False,
        notes="",
        attempts=0,
    )


@pytest.fixture
def default_config() -> ExecutorConfig:
    """Create a default executor config for testing."""
    return ExecutorConfig(
        max_retries=5,
        validation_command="python -m pytest",
        working_dir="/test/path",
        coder_prompt_path="micro_v/prompts/coder.md",
        learnings="Some learnings",
        files_whitelist=["file1.py", "file2.py"],
        claude_timeout=300,
    )


@pytest.fixture
def sample_prompt_template() -> str:
    """Sample coder prompt template."""
    return """# Coder Prompt
## Goal
{{goal}}

## Files
{{files}}

## Criteria
{{criteria}}

## Learnings
{{learnings}}
"""


class TestExecutionResult:
    """Tests for ExecutionResult enum."""

    def test_success_value(self) -> None:
        """Test SUCCESS enum value."""
        assert ExecutionResult.SUCCESS.value == "success"

    def test_failed_value(self) -> None:
        """Test FAILED enum value."""
        assert ExecutionResult.FAILED.value == "failed"

    def test_escalated_value(self) -> None:
        """Test ESCALATED enum value."""
        assert ExecutionResult.ESCALATED.value == "escalated"


class TestExecutorConfig:
    """Tests for ExecutorConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default config values."""
        config = ExecutorConfig()
        assert config.max_retries == 5
        assert config.validation_command == ""
        assert config.working_dir == "."
        assert config.coder_prompt_path == "micro_v/prompts/coder.md"
        assert config.learnings == ""
        assert config.files_whitelist is None
        assert config.claude_timeout == 300

    def test_custom_values(self) -> None:
        """Test custom config values."""
        config = ExecutorConfig(
            max_retries=10,
            validation_command="npm test",
            working_dir="/my/dir",
        )
        assert config.max_retries == 10
        assert config.validation_command == "npm test"
        assert config.working_dir == "/my/dir"


class TestExecutionOutput:
    """Tests for ExecutionOutput dataclass."""

    def test_success_output(self) -> None:
        """Test creating success output."""
        output = ExecutionOutput(
            result=ExecutionResult.SUCCESS,
            story_id="US-001",
            iterations=2,
        )
        assert output.result == ExecutionResult.SUCCESS
        assert output.story_id == "US-001"
        assert output.iterations == 2
        assert output.last_error == ""
        assert output.escalation_reason == ""

    def test_failed_output(self) -> None:
        """Test creating failed output with error."""
        output = ExecutionOutput(
            result=ExecutionResult.FAILED,
            story_id="US-002",
            iterations=5,
            last_error="Test failed",
        )
        assert output.result == ExecutionResult.FAILED
        assert output.last_error == "Test failed"

    def test_escalated_output(self) -> None:
        """Test creating escalated output with reason."""
        output = ExecutionOutput(
            result=ExecutionResult.ESCALATED,
            story_id="US-003",
            iterations=3,
            escalation_reason="Design ambiguity",
        )
        assert output.result == ExecutionResult.ESCALATED
        assert output.escalation_reason == "Design ambiguity"


class TestLoadCoderPrompt:
    """Tests for _load_coder_prompt function."""

    def test_loads_existing_prompt(self, tmp_path: Path) -> None:
        """Test loading an existing prompt file."""
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("Test prompt content")

        result = _load_coder_prompt(str(prompt_file))

        assert result == "Test prompt content"

    def test_raises_for_missing_file(self) -> None:
        """Test that FileNotFoundError is raised for missing prompt."""
        with pytest.raises(FileNotFoundError) as exc_info:
            _load_coder_prompt("/nonexistent/path/prompt.md")

        assert "Coder prompt not found" in str(exc_info.value)


class TestFormatPrompt:
    """Tests for _format_prompt function."""

    def test_replaces_goal_placeholder(
        self, sample_prompt_template: str, sample_story: UserStory
    ) -> None:
        """Test that {{goal}} placeholder is replaced."""
        result = _format_prompt(
            template=sample_prompt_template,
            story=sample_story,
            learnings="",
            files_whitelist=None,
        )

        assert "US-001: Test Story" in result
        assert "A test user story for testing" in result

    def test_replaces_criteria_placeholder(
        self, sample_prompt_template: str, sample_story: UserStory
    ) -> None:
        """Test that {{criteria}} placeholder is replaced."""
        result = _format_prompt(
            template=sample_prompt_template,
            story=sample_story,
            learnings="",
            files_whitelist=None,
        )

        assert "- Criterion 1" in result
        assert "- Criterion 2" in result

    def test_replaces_files_placeholder_with_whitelist(
        self, sample_prompt_template: str, sample_story: UserStory
    ) -> None:
        """Test that {{files}} placeholder is replaced with whitelist."""
        result = _format_prompt(
            template=sample_prompt_template,
            story=sample_story,
            learnings="",
            files_whitelist=["src/main.py", "tests/test_main.py"],
        )

        assert "- src/main.py" in result
        assert "- tests/test_main.py" in result

    def test_replaces_files_placeholder_without_whitelist(
        self, sample_prompt_template: str, sample_story: UserStory
    ) -> None:
        """Test that {{files}} placeholder shows no whitelist message."""
        result = _format_prompt(
            template=sample_prompt_template,
            story=sample_story,
            learnings="",
            files_whitelist=None,
        )

        assert "No whitelist specified" in result

    def test_replaces_learnings_placeholder(
        self, sample_prompt_template: str, sample_story: UserStory
    ) -> None:
        """Test that {{learnings}} placeholder is replaced."""
        result = _format_prompt(
            template=sample_prompt_template,
            story=sample_story,
            learnings="Use pytest for testing",
            files_whitelist=None,
        )

        assert "Use pytest for testing" in result

    def test_replaces_learnings_placeholder_without_learnings(
        self, sample_prompt_template: str, sample_story: UserStory
    ) -> None:
        """Test that {{learnings}} shows no learnings message."""
        result = _format_prompt(
            template=sample_prompt_template,
            story=sample_story,
            learnings="",
            files_whitelist=None,
        )

        assert "No previous learnings available" in result

    def test_includes_error_context(
        self, sample_prompt_template: str, sample_story: UserStory
    ) -> None:
        """Test that error context is included in goal."""
        result = _format_prompt(
            template=sample_prompt_template,
            story=sample_story,
            learnings="",
            files_whitelist=None,
            error_context="Tests failed: assertion error",
        )

        assert "Previous Iteration Failed" in result
        assert "Tests failed: assertion error" in result


class TestRunValidation:
    """Tests for _run_validation function."""

    @patch("micro_v.executor.subprocess.run")
    def test_returns_success_on_zero_exit(self, mock_run: MagicMock) -> None:
        """Test that validation returns success on exit code 0."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="All tests passed", stderr=""
        )

        success, output = _run_validation("pytest", "/test")

        assert success is True
        assert "All tests passed" in output

    @patch("micro_v.executor.subprocess.run")
    def test_returns_failure_on_nonzero_exit(self, mock_run: MagicMock) -> None:
        """Test that validation returns failure on non-zero exit code."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Test failed"
        )

        success, output = _run_validation("pytest", "/test")

        assert success is False
        assert "Test failed" in output

    @patch("micro_v.executor.subprocess.run")
    def test_handles_timeout(self, mock_run: MagicMock) -> None:
        """Test that validation handles timeout gracefully."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=120)

        success, output = _run_validation("pytest", "/test")

        assert success is False
        assert "timed out" in output.lower()

    @patch("micro_v.executor.subprocess.run")
    def test_handles_exception(self, mock_run: MagicMock) -> None:
        """Test that validation handles exceptions gracefully."""
        mock_run.side_effect = Exception("Command not found")

        success, output = _run_validation("pytest", "/test")

        assert success is False
        assert "Command not found" in output

    def test_skips_empty_command(self) -> None:
        """Test that empty validation command is skipped."""
        success, output = _run_validation("", "/test")

        assert success is True
        assert output == ""


class TestExecuteStory:
    """Tests for execute_story function."""

    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_success_on_first_try(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        sample_story: UserStory,
        default_config: ExecutorConfig,
    ) -> None:
        """Test successful execution on first iteration."""
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Code written", "", 0)
        mock_validate.return_value = (True, "Tests passed")

        result = execute_story(sample_story, default_config)

        assert result.result == ExecutionResult.SUCCESS
        assert result.story_id == "US-001"
        assert result.iterations == 1

    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_success_after_retry(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        sample_story: UserStory,
        default_config: ExecutorConfig,
    ) -> None:
        """Test successful execution after retry."""
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Code written", "", 0)
        # Fail first, succeed second
        mock_validate.side_effect = [(False, "Tests failed"), (True, "Tests passed")]

        result = execute_story(sample_story, default_config)

        assert result.result == ExecutionResult.SUCCESS
        assert result.iterations == 2

    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_circuit_breaker_triggered(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        sample_story: UserStory,
    ) -> None:
        """Test circuit breaker after max retries."""
        config = ExecutorConfig(max_retries=3, validation_command="pytest")
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Code written", "", 0)
        mock_validate.return_value = (False, "Always fails")

        result = execute_story(sample_story, config)

        assert result.result == ExecutionResult.FAILED
        assert result.iterations == 3
        assert "Always fails" in result.last_error

    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_claude_invocation_failure(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        sample_story: UserStory,
    ) -> None:
        """Test handling of Claude invocation failure."""
        config = ExecutorConfig(max_retries=2, validation_command="pytest")
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        # Claude fails with non-zero exit
        mock_claude.return_value = ("", "Claude error", -1)
        mock_validate.return_value = (True, "")

        result = execute_story(sample_story, config)

        # Should fail because Claude never succeeds
        assert result.result == ExecutionResult.FAILED
        assert result.iterations == 2

    @patch("micro_v.executor._load_coder_prompt")
    def test_missing_prompt_file(
        self,
        mock_load: MagicMock,
        sample_story: UserStory,
        default_config: ExecutorConfig,
    ) -> None:
        """Test handling of missing coder prompt file."""
        mock_load.side_effect = FileNotFoundError("Coder prompt not found: /path")

        result = execute_story(sample_story, default_config)

        assert result.result == ExecutionResult.FAILED
        assert result.iterations == 0
        assert "not found" in result.last_error.lower()

    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_error_context_passed_on_retry(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        sample_story: UserStory,
        default_config: ExecutorConfig,
    ) -> None:
        """Test that validation error is passed to next iteration."""
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Code written", "", 0)
        mock_validate.side_effect = [
            (False, "TypeError: missing argument"),
            (True, "Tests passed"),
        ]

        result = execute_story(sample_story, default_config)

        assert result.result == ExecutionResult.SUCCESS
        # Check that claude was called with error context on second iteration
        assert mock_claude.call_count == 2
        second_call_prompt = mock_claude.call_args_list[1][1]["prompt"]
        assert "TypeError: missing argument" in second_call_prompt

    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_returns_structured_result(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        sample_story: UserStory,
        default_config: ExecutorConfig,
    ) -> None:
        """Test that result is properly structured ExecutionOutput."""
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Code written", "", 0)
        mock_validate.return_value = (True, "")

        result = execute_story(sample_story, default_config)

        assert isinstance(result, ExecutionOutput)
        assert isinstance(result.result, ExecutionResult)
        assert isinstance(result.story_id, str)
        assert isinstance(result.iterations, int)

    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    @patch("builtins.print")
    def test_logs_each_iteration(
        self,
        mock_print: MagicMock,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        sample_story: UserStory,
    ) -> None:
        """Test that each iteration is logged to terminal."""
        config = ExecutorConfig(max_retries=3, validation_command="pytest")
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Code written", "", 0)
        mock_validate.side_effect = [
            (False, "Error 1"),
            (False, "Error 2"),
            (True, "Passed"),
        ]

        execute_story(sample_story, config)

        # Verify logging occurred
        log_calls = [str(call) for call in mock_print.call_args_list]
        log_text = " ".join(log_calls)

        assert "Iteration 1" in log_text
        assert "Iteration 2" in log_text
        assert "Iteration 3" in log_text


class TestLog:
    """Tests for _log function."""

    @patch("builtins.print")
    def test_log_format(self, mock_print: MagicMock) -> None:
        """Test that log messages have correct format."""
        _log("Test message")

        mock_print.assert_called_once_with("[executor] Test message")
