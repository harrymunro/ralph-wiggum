"""Unit tests for micro_v/auditor.py module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from micro_v.auditor import (
    AuditVerdict,
    AuditResult,
    AuditorError,
    audit_implementation,
    _load_auditor_prompt,
    _format_auditor_prompt,
    _parse_verdict,
    _log,
)


class TestAuditVerdict:
    """Tests for AuditVerdict enum."""

    def test_pass_value(self) -> None:
        """Test PASS enum value."""
        assert AuditVerdict.PASS.value == "pass"

    def test_retry_value(self) -> None:
        """Test RETRY enum value."""
        assert AuditVerdict.RETRY.value == "retry"

    def test_escalate_value(self) -> None:
        """Test ESCALATE enum value."""
        assert AuditVerdict.ESCALATE.value == "escalate"


class TestAuditResult:
    """Tests for AuditResult dataclass."""

    def test_pass_result(self) -> None:
        """Test creating a PASS result."""
        result = AuditResult(verdict=AuditVerdict.PASS)
        assert result.verdict == AuditVerdict.PASS
        assert result.feedback == ""
        assert result.reason == ""

    def test_retry_result_with_feedback(self) -> None:
        """Test creating a RETRY result with feedback."""
        result = AuditResult(
            verdict=AuditVerdict.RETRY,
            feedback="Missing error handling for null input",
        )
        assert result.verdict == AuditVerdict.RETRY
        assert result.feedback == "Missing error handling for null input"
        assert result.reason == ""

    def test_escalate_result_with_reason(self) -> None:
        """Test creating an ESCALATE result with reason."""
        result = AuditResult(
            verdict=AuditVerdict.ESCALATE,
            reason="Spec does not define acceptable latency",
        )
        assert result.verdict == AuditVerdict.ESCALATE
        assert result.feedback == ""
        assert result.reason == "Spec does not define acceptable latency"


class TestLoadAuditorPrompt:
    """Tests for _load_auditor_prompt function."""

    def test_loads_existing_prompt(self, tmp_path: Path) -> None:
        """Test loading an existing prompt file."""
        prompt_file = tmp_path / "auditor.md"
        prompt_file.write_text("Auditor prompt content with {{spec}} and {{diff}}")

        result = _load_auditor_prompt(str(prompt_file))

        assert "Auditor prompt content" in result
        assert "{{spec}}" in result
        assert "{{diff}}" in result

    def test_raises_for_missing_file(self) -> None:
        """Test that FileNotFoundError is raised for missing prompt."""
        with pytest.raises(FileNotFoundError) as exc_info:
            _load_auditor_prompt("/nonexistent/path/auditor.md")

        assert "Auditor prompt not found" in str(exc_info.value)


class TestFormatAuditorPrompt:
    """Tests for _format_auditor_prompt function."""

    def test_replaces_spec_placeholder(self) -> None:
        """Test that {{spec}} placeholder is replaced."""
        template = "Verify this spec:\n{{spec}}\n\nAgainst this diff:\n{{diff}}"
        spec = "Function must return sum of numbers"
        diff = "+ def sum_numbers(lst): return sum(lst)"

        result = _format_auditor_prompt(template, spec, diff)

        assert "Function must return sum of numbers" in result
        assert "{{spec}}" not in result

    def test_replaces_diff_placeholder(self) -> None:
        """Test that {{diff}} placeholder is replaced."""
        template = "Verify this spec:\n{{spec}}\n\nAgainst this diff:\n{{diff}}"
        spec = "Function must return sum of numbers"
        diff = "+ def sum_numbers(lst): return sum(lst)"

        result = _format_auditor_prompt(template, spec, diff)

        assert "def sum_numbers" in result
        assert "{{diff}}" not in result

    def test_handles_multiline_content(self) -> None:
        """Test that multiline spec and diff are handled correctly."""
        template = "SPEC:\n{{spec}}\n\nDIFF:\n{{diff}}"
        spec = "Line 1\nLine 2\nLine 3"
        diff = "+ added line 1\n+ added line 2\n- removed line"

        result = _format_auditor_prompt(template, spec, diff)

        assert "Line 1\nLine 2\nLine 3" in result
        assert "+ added line 1\n+ added line 2" in result


class TestParseVerdict:
    """Tests for _parse_verdict function."""

    def test_parses_pass(self) -> None:
        """Test parsing PASS verdict."""
        output = "PASS"
        result = _parse_verdict(output)

        assert result.verdict == AuditVerdict.PASS
        assert result.feedback == ""
        assert result.reason == ""

    def test_parses_pass_with_surrounding_text(self) -> None:
        """Test parsing PASS with explanatory text."""
        output = """After reviewing the implementation:

PASS

The code correctly implements all criteria."""
        result = _parse_verdict(output)

        assert result.verdict == AuditVerdict.PASS

    def test_parses_retry_with_feedback(self) -> None:
        """Test parsing RETRY verdict with feedback."""
        output = "RETRY: Missing edge case handling for empty list input."
        result = _parse_verdict(output)

        assert result.verdict == AuditVerdict.RETRY
        assert "empty list" in result.feedback

    def test_parses_retry_with_multiline_feedback(self) -> None:
        """Test parsing RETRY with multiline feedback."""
        output = """RETRY: Multiple issues found:
1. Missing null check
2. Error message not descriptive
3. Return type incorrect"""
        result = _parse_verdict(output)

        assert result.verdict == AuditVerdict.RETRY
        assert "Multiple issues found" in result.feedback
        assert "null check" in result.feedback

    def test_parses_escalate_with_reason(self) -> None:
        """Test parsing ESCALATE verdict with reason."""
        output = "ESCALATE: Spec says 'fast' but no latency target defined."
        result = _parse_verdict(output)

        assert result.verdict == AuditVerdict.ESCALATE
        assert "latency target" in result.reason

    def test_parses_escalate_with_multiline_reason(self) -> None:
        """Test parsing ESCALATE with multiline reason."""
        output = """ESCALATE: Design ambiguity detected.
The spec requires integration with ExternalService but:
- No API endpoint specified
- Authentication method unclear"""
        result = _parse_verdict(output)

        assert result.verdict == AuditVerdict.ESCALATE
        assert "Design ambiguity" in result.reason

    def test_defaults_to_retry_for_unclear_output(self) -> None:
        """Test that unclear output defaults to RETRY (conservative)."""
        output = "The implementation looks mostly correct but I'm not sure."
        result = _parse_verdict(output)

        assert result.verdict == AuditVerdict.RETRY
        assert "unclear" in result.feedback.lower()

    def test_parses_pass_in_code_block(self) -> None:
        """Test parsing PASS when in a code block format."""
        output = """Based on my review:
```
PASS
```
Everything looks good."""
        result = _parse_verdict(output)

        assert result.verdict == AuditVerdict.PASS

    def test_truncates_feedback_at_code_block(self) -> None:
        """Test that feedback is truncated at code block markers."""
        output = """RETRY: Fix the error handling.
```
some code example
```
More text after."""
        result = _parse_verdict(output)

        assert result.verdict == AuditVerdict.RETRY
        assert "some code example" not in result.feedback
        assert "Fix the error handling" in result.feedback

    def test_handles_empty_output(self) -> None:
        """Test handling of empty output."""
        result = _parse_verdict("")

        assert result.verdict == AuditVerdict.RETRY
        assert "unclear" in result.feedback.lower()


class TestAuditImplementation:
    """Tests for audit_implementation function."""

    @patch("micro_v.auditor.invoke_claude")
    @patch("micro_v.auditor._load_auditor_prompt")
    def test_returns_pass_verdict(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
    ) -> None:
        """Test that PASS verdict is returned correctly."""
        mock_load.return_value = "{{spec}}\n{{diff}}"
        mock_claude.return_value = ("PASS", "", 0)

        result = audit_implementation(
            spec="Function returns sum",
            diff="+ def sum(lst): return sum(lst)",
        )

        assert result.verdict == AuditVerdict.PASS

    @patch("micro_v.auditor.invoke_claude")
    @patch("micro_v.auditor._load_auditor_prompt")
    def test_returns_retry_verdict(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
    ) -> None:
        """Test that RETRY verdict is returned correctly."""
        mock_load.return_value = "{{spec}}\n{{diff}}"
        mock_claude.return_value = ("RETRY: Missing edge case for empty input.", "", 0)

        result = audit_implementation(
            spec="Function returns sum",
            diff="+ def sum(lst): return sum(lst)",
        )

        assert result.verdict == AuditVerdict.RETRY
        assert "empty input" in result.feedback

    @patch("micro_v.auditor.invoke_claude")
    @patch("micro_v.auditor._load_auditor_prompt")
    def test_returns_escalate_verdict(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
    ) -> None:
        """Test that ESCALATE verdict is returned correctly."""
        mock_load.return_value = "{{spec}}\n{{diff}}"
        mock_claude.return_value = ("ESCALATE: No performance target specified.", "", 0)

        result = audit_implementation(
            spec="Function must be fast",
            diff="+ def process(): time.sleep(1)",
        )

        assert result.verdict == AuditVerdict.ESCALATE
        assert "performance" in result.reason

    @patch("micro_v.auditor.invoke_claude")
    @patch("micro_v.auditor._load_auditor_prompt")
    def test_handles_claude_failure(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
    ) -> None:
        """Test handling of Claude invocation failure."""
        mock_load.return_value = "{{spec}}\n{{diff}}"
        mock_claude.return_value = ("", "Timeout error", -1)

        result = audit_implementation(
            spec="Test spec",
            diff="Test diff",
        )

        # Should return RETRY on invocation failure
        assert result.verdict == AuditVerdict.RETRY
        assert "failed" in result.feedback.lower()

    @patch("micro_v.auditor._load_auditor_prompt")
    def test_raises_on_missing_prompt(
        self,
        mock_load: MagicMock,
    ) -> None:
        """Test that AuditorError is raised for missing prompt file."""
        mock_load.side_effect = FileNotFoundError("Auditor prompt not found: /path")

        with pytest.raises(AuditorError) as exc_info:
            audit_implementation(
                spec="Test spec",
                diff="Test diff",
            )

        assert "not found" in str(exc_info.value).lower()

    @patch("micro_v.auditor.invoke_claude")
    @patch("micro_v.auditor._load_auditor_prompt")
    def test_uses_default_prompt_path(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
    ) -> None:
        """Test that default prompt path is used."""
        mock_load.return_value = "{{spec}}\n{{diff}}"
        mock_claude.return_value = ("PASS", "", 0)

        audit_implementation(spec="Test", diff="Test")

        mock_load.assert_called_once_with("micro_v/prompts/auditor.md")

    @patch("micro_v.auditor.invoke_claude")
    @patch("micro_v.auditor._load_auditor_prompt")
    def test_uses_custom_prompt_path(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
    ) -> None:
        """Test that custom prompt path is used."""
        mock_load.return_value = "{{spec}}\n{{diff}}"
        mock_claude.return_value = ("PASS", "", 0)

        audit_implementation(
            spec="Test",
            diff="Test",
            prompt_path="/custom/auditor.md",
        )

        mock_load.assert_called_once_with("/custom/auditor.md")

    @patch("micro_v.auditor.invoke_claude")
    @patch("micro_v.auditor._load_auditor_prompt")
    def test_passes_timeout_to_claude(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
    ) -> None:
        """Test that timeout is passed to Claude invocation."""
        mock_load.return_value = "{{spec}}\n{{diff}}"
        mock_claude.return_value = ("PASS", "", 0)

        audit_implementation(
            spec="Test",
            diff="Test",
            timeout=60,
        )

        mock_claude.assert_called_once()
        assert mock_claude.call_args[1]["timeout"] == 60

    @patch("micro_v.auditor.invoke_claude")
    @patch("micro_v.auditor._load_auditor_prompt")
    def test_passes_working_dir_to_claude(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
    ) -> None:
        """Test that working directory is passed to Claude invocation."""
        mock_load.return_value = "{{spec}}\n{{diff}}"
        mock_claude.return_value = ("PASS", "", 0)

        audit_implementation(
            spec="Test",
            diff="Test",
            working_dir="/my/project",
        )

        mock_claude.assert_called_once()
        assert mock_claude.call_args[1]["working_dir"] == "/my/project"

    @patch("micro_v.auditor.invoke_claude")
    @patch("micro_v.auditor._load_auditor_prompt")
    def test_auditor_receives_only_spec_and_diff(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
    ) -> None:
        """Test that auditor only receives spec and diff (no context)."""
        mock_load.return_value = "SPEC:\n{{spec}}\n\nDIFF:\n{{diff}}"
        mock_claude.return_value = ("PASS", "", 0)

        spec = "User story: implement sum function"
        diff = "+ def sum(lst): return sum(lst)"

        audit_implementation(spec=spec, diff=diff)

        # Verify the prompt contains spec and diff
        call_args = mock_claude.call_args
        prompt = call_args[1]["prompt"]
        assert spec in prompt
        assert diff in prompt
        # Verify no extra context is added
        assert "SPEC:" in prompt
        assert "DIFF:" in prompt


class TestLog:
    """Tests for _log function."""

    @patch("builtins.print")
    def test_log_format(self, mock_print: MagicMock) -> None:
        """Test that log messages have correct format."""
        _log("Test message")

        mock_print.assert_called_once_with("[auditor] Test message")
