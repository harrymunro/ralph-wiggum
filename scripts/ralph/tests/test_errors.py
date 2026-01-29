"""Tests for the error classes module."""

import pytest

from shared.errors import (
    RalphError,
    PRDNotFoundError,
    ClaudeNotFoundError,
    GitNotInitializedError,
    ValidationFailedError,
    StoryNotFoundError,
)


class TestRalphError:
    """Test suite for base RalphError class."""

    def test_ralph_error_message(self) -> None:
        """Test that RalphError stores message correctly."""
        error = RalphError("Test error message")
        assert str(error) == "Test error message"

    def test_ralph_error_suggestion(self) -> None:
        """Test that RalphError stores suggestion correctly."""
        error = RalphError("Test error", "Fix by doing this")
        assert error.suggestion == "Fix by doing this"

    def test_ralph_error_empty_suggestion(self) -> None:
        """Test that RalphError defaults to empty suggestion."""
        error = RalphError("Test error")
        assert error.suggestion == ""


class TestPRDNotFoundError:
    """Test suite for PRDNotFoundError class."""

    def test_prd_not_found_with_path(self) -> None:
        """Test PRDNotFoundError with a specific path."""
        error = PRDNotFoundError("/path/to/prd.json")
        assert "prd.json" in str(error).lower() or "prd" in str(error).lower()
        assert "/path/to/prd.json" in str(error)
        assert error.path == "/path/to/prd.json"

    def test_prd_not_found_without_path(self) -> None:
        """Test PRDNotFoundError without a path."""
        error = PRDNotFoundError()
        assert "prd" in str(error).lower()
        assert error.path == ""

    def test_prd_not_found_suggestion_with_path(self) -> None:
        """Test that suggestion includes the path."""
        error = PRDNotFoundError("/my/project/prd.json")
        assert "/my/project/prd.json" in error.suggestion
        assert len(error.suggestion) > 10  # Should have meaningful text

    def test_prd_not_found_suggestion_without_path(self) -> None:
        """Test suggestion when no path provided."""
        error = PRDNotFoundError()
        assert len(error.suggestion) > 10  # Should have meaningful text
        assert "--prd" in error.suggestion or "prd.json" in error.suggestion

    def test_prd_not_found_is_ralph_error(self) -> None:
        """Test that PRDNotFoundError is a RalphError."""
        error = PRDNotFoundError()
        assert isinstance(error, RalphError)
        assert isinstance(error, Exception)


class TestClaudeNotFoundError:
    """Test suite for ClaudeNotFoundError class."""

    def test_claude_not_found_default_path(self) -> None:
        """Test ClaudeNotFoundError with default path."""
        error = ClaudeNotFoundError()
        assert "claude" in str(error).lower()
        assert error.path == "claude"

    def test_claude_not_found_custom_path(self) -> None:
        """Test ClaudeNotFoundError with custom path."""
        error = ClaudeNotFoundError("/usr/local/bin/claude")
        assert "/usr/local/bin/claude" in str(error)
        assert error.path == "/usr/local/bin/claude"

    def test_claude_not_found_suggestion(self) -> None:
        """Test that suggestion includes installation instructions."""
        error = ClaudeNotFoundError()
        suggestion = error.suggestion
        assert len(suggestion) > 10
        # Should mention installation or PATH
        assert "install" in suggestion.lower() or "path" in suggestion.lower()

    def test_claude_not_found_is_ralph_error(self) -> None:
        """Test that ClaudeNotFoundError is a RalphError."""
        error = ClaudeNotFoundError()
        assert isinstance(error, RalphError)


class TestGitNotInitializedError:
    """Test suite for GitNotInitializedError class."""

    def test_git_not_initialized_with_path(self) -> None:
        """Test GitNotInitializedError with a specific path."""
        error = GitNotInitializedError("/my/project")
        assert "git" in str(error).lower()
        assert "/my/project" in str(error)
        assert error.path == "/my/project"

    def test_git_not_initialized_without_path(self) -> None:
        """Test GitNotInitializedError without a path."""
        error = GitNotInitializedError()
        assert "git" in str(error).lower()
        assert error.path == ""

    def test_git_not_initialized_suggestion_with_path(self) -> None:
        """Test that suggestion includes git init instructions with path."""
        error = GitNotInitializedError("/my/project")
        suggestion = error.suggestion
        assert "git init" in suggestion
        assert "/my/project" in suggestion

    def test_git_not_initialized_suggestion_without_path(self) -> None:
        """Test suggestion when no path provided."""
        error = GitNotInitializedError()
        suggestion = error.suggestion
        assert "git init" in suggestion

    def test_git_not_initialized_is_ralph_error(self) -> None:
        """Test that GitNotInitializedError is a RalphError."""
        error = GitNotInitializedError()
        assert isinstance(error, RalphError)


class TestValidationFailedError:
    """Test suite for ValidationFailedError class."""

    def test_validation_failed_with_command(self) -> None:
        """Test ValidationFailedError with a command."""
        error = ValidationFailedError("npm test")
        assert "validation" in str(error).lower()
        assert "npm test" in str(error)
        assert error.command == "npm test"

    def test_validation_failed_without_command(self) -> None:
        """Test ValidationFailedError without a command."""
        error = ValidationFailedError()
        assert "validation" in str(error).lower()
        assert error.command == ""

    def test_validation_failed_with_output(self) -> None:
        """Test ValidationFailedError with command output."""
        error = ValidationFailedError("npm test", "Error: test failed at line 42")
        assert error.output == "Error: test failed at line 42"
        assert "Error: test failed at line 42" in error.suggestion

    def test_validation_failed_suggestion_without_output(self) -> None:
        """Test suggestion when no output provided."""
        error = ValidationFailedError("npm test")
        suggestion = error.suggestion
        assert len(suggestion) > 10

    def test_validation_failed_is_ralph_error(self) -> None:
        """Test that ValidationFailedError is a RalphError."""
        error = ValidationFailedError()
        assert isinstance(error, RalphError)


class TestStoryNotFoundError:
    """Test suite for StoryNotFoundError class."""

    def test_story_not_found_with_id(self) -> None:
        """Test StoryNotFoundError with a story ID."""
        error = StoryNotFoundError("US-001")
        assert "story" in str(error).lower()
        assert "US-001" in str(error)
        assert error.story_id == "US-001"

    def test_story_not_found_without_id(self) -> None:
        """Test StoryNotFoundError without a story ID."""
        error = StoryNotFoundError()
        assert "story" in str(error).lower()
        assert error.story_id == ""

    def test_story_not_found_with_available_ids(self) -> None:
        """Test StoryNotFoundError with available IDs list."""
        available = ["US-001", "US-002", "US-003"]
        error = StoryNotFoundError("US-999", available)
        assert error.available_ids == available
        suggestion = error.suggestion
        # Should list available IDs
        assert "US-001" in suggestion
        assert "US-002" in suggestion
        assert "US-003" in suggestion

    def test_story_not_found_truncates_long_list(self) -> None:
        """Test that suggestion truncates very long ID lists."""
        available = [f"US-{i:03d}" for i in range(1, 21)]  # 20 IDs
        error = StoryNotFoundError("US-999", available)
        suggestion = error.suggestion
        # Should show first 10 and indicate more exist
        assert "US-001" in suggestion
        assert "more" in suggestion.lower()

    def test_story_not_found_suggestion_without_ids(self) -> None:
        """Test suggestion when no available IDs provided."""
        error = StoryNotFoundError("US-001")
        suggestion = error.suggestion
        assert len(suggestion) > 10
        assert "status" in suggestion.lower() or "US-001" in suggestion

    def test_story_not_found_is_ralph_error(self) -> None:
        """Test that StoryNotFoundError is a RalphError."""
        error = StoryNotFoundError()
        assert isinstance(error, RalphError)


class TestErrorInheritance:
    """Test suite for error class inheritance."""

    def test_all_errors_are_exceptions(self) -> None:
        """Test that all error classes can be raised and caught."""
        errors = [
            PRDNotFoundError("test"),
            ClaudeNotFoundError(),
            GitNotInitializedError(),
            ValidationFailedError(),
            StoryNotFoundError("test"),
        ]
        for error in errors:
            with pytest.raises(Exception):
                raise error

    def test_all_errors_can_be_caught_as_ralph_error(self) -> None:
        """Test that all custom errors can be caught as RalphError."""
        errors = [
            PRDNotFoundError("test"),
            ClaudeNotFoundError(),
            GitNotInitializedError(),
            ValidationFailedError(),
            StoryNotFoundError("test"),
        ]
        for error in errors:
            try:
                raise error
            except RalphError as e:
                assert e.suggestion is not None

    def test_all_errors_have_suggestion_property(self) -> None:
        """Test that all error classes have a suggestion property."""
        errors = [
            PRDNotFoundError("test"),
            ClaudeNotFoundError(),
            GitNotInitializedError("/path"),
            ValidationFailedError("cmd"),
            StoryNotFoundError("US-001"),
        ]
        for error in errors:
            assert hasattr(error, 'suggestion')
            assert isinstance(error.suggestion, str)
            assert len(error.suggestion) > 0
