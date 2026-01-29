"""Tests for v_ralph CLI argument parsing and commands."""

import argparse
import sys
import pytest
from unittest.mock import patch, MagicMock


class TestVerboseFlag:
    """Tests for the --verbose/-v flag."""

    def test_verbose_flag_long_form_parsed(self):
        """Test that --verbose flag is recognized by the parser."""
        # Import inline to avoid module-level import issues
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--verbose', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.verbose is True

    def test_verbose_flag_short_form_parsed(self):
        """Test that -v flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '-v', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.verbose is True

    def test_verbose_flag_default_is_false(self):
        """Test that verbose flag defaults to False when not provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.verbose is False

    def test_verbose_flag_in_help_output(self):
        """Test that --verbose/-v appears in run --help output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.stdout.write') as mock_write:
                    main()
            # Help exits with code 0
            assert exc_info.value.code == 0


class TestTruncateText:
    """Tests for the truncate_text helper function."""

    def test_truncate_short_text_unchanged(self):
        """Test that text shorter than max_length is returned unchanged."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import truncate_text

        text = "short text"
        result = truncate_text(text, 500)
        assert result == text

    def test_truncate_exact_length_unchanged(self):
        """Test that text exactly at max_length is returned unchanged."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import truncate_text

        text = "x" * 500
        result = truncate_text(text, 500)
        assert result == text
        assert len(result) == 500

    def test_truncate_long_text_with_ellipsis(self):
        """Test that long text is truncated with ellipsis."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import truncate_text

        text = "x" * 600
        result = truncate_text(text, 500)
        assert len(result) == 503  # 500 + "..."
        assert result.endswith("...")
        assert result[:500] == "x" * 500

    def test_truncate_custom_length(self):
        """Test truncation with custom max_length."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import truncate_text

        text = "hello world this is a test"
        result = truncate_text(text, 10)
        assert result == "hello worl..."


class TestVerboseLogging:
    """Tests for verbose logging helper functions."""

    def test_verbose_log_when_enabled(self):
        """Test that verbose_log outputs when verbose=True."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import verbose_log

        with patch('v_ralph.info') as mock_info:
            verbose_log("test message", True)
            mock_info.assert_called_once_with("[VERBOSE] test message")

    def test_verbose_log_when_disabled(self):
        """Test that verbose_log is silent when verbose=False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import verbose_log

        with patch('v_ralph.info') as mock_info:
            verbose_log("test message", False)
            mock_info.assert_not_called()

    def test_verbose_prompt_truncates_to_500(self):
        """Test that verbose_prompt truncates prompt to 500 chars."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import verbose_prompt

        long_prompt = "x" * 1000
        with patch('v_ralph.info') as mock_info:
            verbose_prompt(long_prompt, True)
            # Should be called twice: once for header, once for content
            assert mock_info.call_count == 2
            # First call should include char count
            first_call = mock_info.call_args_list[0][0][0]
            assert "1000 chars" in first_call
            assert "first 500" in first_call
            # Second call should have truncated content
            second_call = mock_info.call_args_list[1][0][0]
            assert "..." in second_call

    def test_verbose_prompt_when_disabled(self):
        """Test that verbose_prompt is silent when verbose=False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import verbose_prompt

        with patch('v_ralph.info') as mock_info:
            verbose_prompt("test prompt", False)
            mock_info.assert_not_called()

    def test_verbose_validation_output_shows_full_output(self):
        """Test that verbose_validation_output shows complete output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import verbose_validation_output

        output = "line1\nline2\nline3"
        with patch('v_ralph.info') as mock_info:
            verbose_validation_output(output, True)
            # Should be called 4 times: header + 3 lines
            assert mock_info.call_count == 4

    def test_verbose_validation_output_when_disabled(self):
        """Test that verbose_validation_output is silent when verbose=False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import verbose_validation_output

        with patch('v_ralph.info') as mock_info:
            verbose_validation_output("test output", False)
            mock_info.assert_not_called()


class TestDebugFlag:
    """Tests for the --debug flag."""

    def test_debug_flag_parsed(self):
        """Test that --debug flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--debug', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.debug is True

    def test_debug_flag_default_is_false(self):
        """Test that debug flag defaults to False when not provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.debug is False

    def test_debug_flag_in_help_output(self):
        """Test that --debug appears in run --help output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.stdout.write') as mock_write:
                    main()
            # Help exits with code 0
            assert exc_info.value.code == 0


class TestDebugLogging:
    """Tests for debug logging helper functions."""

    def test_debug_log_when_enabled(self):
        """Test that debug_log outputs when debug_enabled=True."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import debug_log

        with patch('v_ralph.debug') as mock_debug:
            debug_log("test message", True)
            mock_debug.assert_called_once_with("[DEBUG] test message")

    def test_debug_log_when_disabled(self):
        """Test that debug_log is silent when debug_enabled=False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import debug_log

        with patch('v_ralph.debug') as mock_debug:
            debug_log("test message", False)
            mock_debug.assert_not_called()

    def test_debug_prompt_shows_full_text(self):
        """Test that debug_prompt shows full prompt without truncation."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import debug_prompt

        long_prompt = "line1\nline2\nline3"
        with patch('v_ralph.debug') as mock_debug:
            debug_prompt(long_prompt, True)
            # Should be called 4 times: header + 3 lines
            assert mock_debug.call_count == 4
            # Header should include full char count (17 chars for "line1\nline2\nline3")
            first_call = mock_debug.call_args_list[0][0][0]
            assert "17 chars" in first_call

    def test_debug_prompt_when_disabled(self):
        """Test that debug_prompt is silent when debug_enabled=False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import debug_prompt

        with patch('v_ralph.debug') as mock_debug:
            debug_prompt("test prompt", False)
            mock_debug.assert_not_called()

    def test_debug_file_path_when_enabled(self):
        """Test that debug_file_path outputs when debug_enabled=True."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import debug_file_path

        with patch('v_ralph.debug') as mock_debug:
            debug_file_path("/path/to/file", "PRD file", True)
            mock_debug.assert_called_once_with("[DEBUG] PRD file: /path/to/file")

    def test_debug_file_path_when_disabled(self):
        """Test that debug_file_path is silent when debug_enabled=False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import debug_file_path

        with patch('v_ralph.debug') as mock_debug:
            debug_file_path("/path/to/file", "PRD file", False)
            mock_debug.assert_not_called()

    def test_debug_environment_when_enabled(self):
        """Test that debug_environment outputs when debug_enabled=True."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import debug_environment

        with patch('v_ralph.debug') as mock_debug:
            debug_environment(True)
            # Should output header + 3 info lines (python, platform, working dir)
            assert mock_debug.call_count == 4
            # Check header
            first_call = mock_debug.call_args_list[0][0][0]
            assert "Environment info" in first_call

    def test_debug_environment_when_disabled(self):
        """Test that debug_environment is silent when debug_enabled=False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import debug_environment

        with patch('v_ralph.debug') as mock_debug:
            debug_environment(False)
            mock_debug.assert_not_called()


class TestExecutionSummary:
    """Tests for the ExecutionSummary dataclass."""

    def test_execution_summary_default_values(self):
        """Test that ExecutionSummary has correct default values."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        assert summary.stories_attempted == 0
        assert summary.stories_passed == 0
        assert summary.stories_failed == 0
        assert summary.total_iterations == 0
        assert summary.files_changed == 0
        assert summary.commits == []
        assert summary.escalated_stories == []
        assert summary.end_time is None

    def test_execution_summary_elapsed_time_before_finish(self):
        """Test that elapsed_time works before finish() is called."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary
        import time

        summary = ExecutionSummary()
        time.sleep(0.1)
        elapsed = summary.elapsed_time
        assert elapsed >= 0.1

    def test_execution_summary_finish_sets_end_time(self):
        """Test that finish() sets the end_time."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        assert summary.end_time is None
        summary.finish()
        assert summary.end_time is not None

    def test_execution_summary_elapsed_time_formatted_seconds(self):
        """Test elapsed_time_formatted for short durations (seconds)."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary
        import time

        summary = ExecutionSummary()
        summary.start_time = time.time() - 30  # 30 seconds ago
        summary.finish()
        formatted = summary.elapsed_time_formatted
        assert "s" in formatted
        assert "m" not in formatted

    def test_execution_summary_elapsed_time_formatted_minutes(self):
        """Test elapsed_time_formatted for medium durations (minutes)."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary
        import time

        summary = ExecutionSummary()
        summary.start_time = time.time() - 125  # 2 minutes 5 seconds ago
        summary.finish()
        formatted = summary.elapsed_time_formatted
        assert "2m" in formatted
        assert "5s" in formatted

    def test_execution_summary_elapsed_time_formatted_hours(self):
        """Test elapsed_time_formatted for long durations (hours)."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary
        import time

        summary = ExecutionSummary()
        summary.start_time = time.time() - 3665  # 1 hour, 1 minute, 5 seconds ago
        summary.finish()
        formatted = summary.elapsed_time_formatted
        assert "1h" in formatted
        assert "1m" in formatted

    def test_execution_summary_add_escalation(self):
        """Test that add_escalation adds to escalated_stories list."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.add_escalation("US-001", "Test failure after 3 retries")
        assert len(summary.escalated_stories) == 1
        assert summary.escalated_stories[0] == ("US-001", "Test failure after 3 retries")

    def test_execution_summary_multiple_escalations(self):
        """Test that multiple escalations are tracked."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.add_escalation("US-001", "Reason 1")
        summary.add_escalation("US-002", "Reason 2")
        assert len(summary.escalated_stories) == 2

    def test_execution_summary_display_calls_summary_box(self):
        """Test that display() calls summary_box function."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.stories_attempted = 3
        summary.stories_passed = 2
        summary.stories_failed = 1
        summary.finish()

        with patch('v_ralph.summary_box') as mock_box:
            summary.display()
            mock_box.assert_called_once()
            # Check that title is "Execution Summary"
            call_args = mock_box.call_args
            assert call_args[0][0] == "Execution Summary"

    def test_execution_summary_display_red_style_on_failure(self):
        """Test that display uses red style when there are failures."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.stories_failed = 1
        summary.finish()

        with patch('v_ralph.summary_box') as mock_box:
            summary.display()
            call_kwargs = mock_box.call_args[1]
            assert call_kwargs.get('style') == 'red'

    def test_execution_summary_display_green_style_on_success(self):
        """Test that display uses green style when stories pass and no failures."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.stories_passed = 3
        summary.stories_failed = 0
        summary.finish()

        with patch('v_ralph.summary_box') as mock_box:
            summary.display()
            call_kwargs = mock_box.call_args[1]
            assert call_kwargs.get('style') == 'green'

    def test_execution_summary_display_red_style_on_escalation(self):
        """Test that display uses red style when there are escalations."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.stories_passed = 1
        summary.add_escalation("US-001", "Test reason")
        summary.finish()

        with patch('v_ralph.summary_box') as mock_box:
            summary.display()
            call_kwargs = mock_box.call_args[1]
            assert call_kwargs.get('style') == 'red'

    def test_execution_summary_display_shows_commits(self):
        """Test that display shows commit SHAs when commits are made."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.commits = ["abc123", "def456"]
        summary.finish()

        with patch('v_ralph.summary_box') as mock_box:
            summary.display()
            lines = mock_box.call_args[0][1]
            # Check that commits are in the lines
            lines_text = "\n".join(lines)
            assert "abc123" in lines_text
            assert "def456" in lines_text
