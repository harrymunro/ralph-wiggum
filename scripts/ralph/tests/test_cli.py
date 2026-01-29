"""Tests for v_ralph CLI argument parsing and commands."""

import argparse
import json
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


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_with_valid_prd(self, tmp_path):
        """Test status command with a valid PRD file."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_status
        import argparse

        # Create a valid PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "branchName": "test/branch",
            "userStories": [
                {"id": "US-001", "title": "Story 1", "priority": 1, "passes": True},
                {"id": "US-002", "title": "Story 2", "priority": 2, "passes": False}
            ]
        }))

        args = argparse.Namespace(prd=str(prd_file))
        exit_code = cmd_status(args)
        assert exit_code == 0

    def test_status_with_missing_prd(self, tmp_path):
        """Test status command with a missing PRD file returns exit code 1."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_status
        import argparse

        # Point to non-existent file
        args = argparse.Namespace(prd=str(tmp_path / "nonexistent.json"))
        exit_code = cmd_status(args)
        assert exit_code == 1

    def test_status_with_empty_stories_list(self, tmp_path):
        """Test status command with empty stories list returns exit code 0."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_status
        import argparse

        # Create PRD with empty stories
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "branchName": "test/branch",
            "userStories": []
        }))

        args = argparse.Namespace(prd=str(prd_file))
        exit_code = cmd_status(args)
        assert exit_code == 0


class TestRunCommandArgumentParsing:
    """Tests for the run command argument parsing."""

    def test_prd_flag_parsing(self):
        """Test that --prd flag is recognized and has default value."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.prd == 'prd.json'  # default value

    def test_prd_flag_custom_value(self):
        """Test that --prd flag accepts custom value."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', '--prd', 'custom.json', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.prd == 'custom.json'

    def test_story_flag_parsing(self):
        """Test that --story flag is recognized."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--story', 'US-001', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.story == 'US-001'

    def test_story_flag_default_is_none(self):
        """Test that --story flag defaults to None."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.story is None

    def test_dry_run_flag_parsing(self):
        """Test that --dry-run flag is recognized."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.dry_run is True

    def test_dry_run_flag_default_is_false(self):
        """Test that --dry-run flag defaults to False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.dry_run is False

    def test_max_retries_flag_parsing(self):
        """Test that --max-retries flag is recognized with custom value."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--max-retries', '5', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.max_retries == 5

    def test_max_retries_flag_default_is_3(self):
        """Test that --max-retries flag defaults to 3."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.max_retries == 3


class TestExitCodes:
    """Tests for CLI exit codes."""

    def test_status_success_returns_0(self, tmp_path):
        """Test that successful status command returns exit code 0."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_status
        import argparse

        # Create a valid PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [{"id": "US-001", "title": "Story 1", "passes": True}]
        }))

        args = argparse.Namespace(prd=str(prd_file))
        exit_code = cmd_status(args)
        assert exit_code == 0

    def test_status_error_returns_1(self, tmp_path):
        """Test that status command with missing PRD returns exit code 1."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_status
        import argparse

        args = argparse.Namespace(prd=str(tmp_path / "missing.json"))
        exit_code = cmd_status(args)
        assert exit_code == 1

    def test_run_dry_run_success_returns_0(self, tmp_path):
        """Test that successful run --dry-run returns exit code 0."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run
        import argparse
        import subprocess

        # Create git repo to pass git check
        subprocess.run(['git', 'init'], cwd=str(tmp_path), capture_output=True)

        # Create a valid PRD file with verification commands
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "verificationCommands": {
                "typecheck": "npm run build",
                "test": "npm test"
            },
            "userStories": [{"id": "US-001", "title": "Story 1", "passes": False}]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=True,
            story=None,
            max_retries=3,
            verbose=False,
            debug=False
        )
        exit_code = cmd_run(args)
        assert exit_code == 0

    def test_run_missing_prd_returns_1(self, tmp_path):
        """Test that run command with missing PRD returns exit code 1."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run
        import argparse

        args = argparse.Namespace(
            prd=str(tmp_path / "missing.json"),
            dry_run=False,
            story=None,
            max_retries=3,
            verbose=False,
            debug=False
        )
        exit_code = cmd_run(args)
        assert exit_code == 1

    def test_run_invalid_story_returns_1(self, tmp_path):
        """Test that run command with invalid story ID returns exit code 1."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run
        import argparse

        # Create a valid PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [{"id": "US-001", "title": "Story 1", "passes": False}]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=False,
            story="INVALID-ID",
            max_retries=3,
            verbose=False,
            debug=False
        )
        exit_code = cmd_run(args)
        assert exit_code == 1

    def test_run_all_complete_returns_0(self, tmp_path):
        """Test that run command when all stories complete returns exit code 0."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run
        import argparse

        # Create PRD with all stories passing
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [
                {"id": "US-001", "title": "Story 1", "passes": True},
                {"id": "US-002", "title": "Story 2", "passes": True}
            ]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=False,
            story=None,
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=False,
            reset_attempts=False,
            skip_validation=False,
            timings=False,
            force=True  # Force flag to bypass git safety checks
        )
        exit_code = cmd_run(args)
        assert exit_code == 0

    def test_help_returns_0(self):
        """Test that --help returns exit code 0."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


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


class TestValidationCheck:
    """Tests for the ValidationCheck dataclass."""

    def test_validation_check_creation(self):
        """Test that ValidationCheck can be created with expected fields."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ValidationCheck

        check = ValidationCheck(
            name="Test check",
            passed=True,
            message="Test passed"
        )
        assert check.name == "Test check"
        assert check.passed is True
        assert check.message == "Test passed"

    def test_validation_check_failed(self):
        """Test ValidationCheck with passed=False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ValidationCheck

        check = ValidationCheck(
            name="Failed check",
            passed=False,
            message="Something went wrong"
        )
        assert check.passed is False


class TestCheckPrdExists:
    """Tests for the check_prd_exists function."""

    def test_prd_exists_when_file_exists(self, tmp_path):
        """Test that check_prd_exists returns passed=True when file exists."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_prd_exists

        prd_file = tmp_path / "prd.json"
        prd_file.write_text("{}")

        check = check_prd_exists(str(prd_file))
        assert check.passed is True
        assert "Found PRD" in check.message

    def test_prd_exists_when_file_missing(self, tmp_path):
        """Test that check_prd_exists returns passed=False when file missing."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_prd_exists

        check = check_prd_exists(str(tmp_path / "missing.json"))
        assert check.passed is False
        assert "not found" in check.message


class TestCheckPrdValidJson:
    """Tests for the check_prd_valid_json function."""

    def test_valid_json_returns_passed(self, tmp_path):
        """Test that check_prd_valid_json returns passed=True for valid JSON."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_prd_valid_json

        prd_file = tmp_path / "prd.json"
        prd_file.write_text('{"project": "Test"}')

        check, data = check_prd_valid_json(str(prd_file))
        assert check.passed is True
        assert data == {"project": "Test"}

    def test_invalid_json_returns_failed(self, tmp_path):
        """Test that check_prd_valid_json returns passed=False for invalid JSON."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_prd_valid_json

        prd_file = tmp_path / "prd.json"
        prd_file.write_text("not valid json {")

        check, data = check_prd_valid_json(str(prd_file))
        assert check.passed is False
        assert data is None
        assert "Invalid JSON" in check.message

    def test_missing_file_returns_failed(self, tmp_path):
        """Test that check_prd_valid_json returns passed=False for missing file."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_prd_valid_json

        check, data = check_prd_valid_json(str(tmp_path / "missing.json"))
        assert check.passed is False
        assert data is None


class TestCheckGitRepoExists:
    """Tests for the check_git_repo_exists function."""

    def test_git_repo_in_existing_repo(self, tmp_path):
        """Test that check_git_repo_exists finds a git repo."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_git_repo_exists
        import subprocess

        # Create a git repo in tmp_path
        subprocess.run(['git', 'init'], cwd=str(tmp_path), capture_output=True)
        prd_file = tmp_path / "prd.json"
        prd_file.write_text("{}")

        check = check_git_repo_exists(str(prd_file))
        assert check.passed is True
        assert "found" in check.message.lower()

    def test_git_repo_not_found(self, tmp_path):
        """Test that check_git_repo_exists fails when no git repo."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_git_repo_exists

        # Use a path outside any git repo
        check = check_git_repo_exists(str(tmp_path / "prd.json"))
        assert check.passed is False


class TestCheckVerificationCommands:
    """Tests for the check_verification_commands function."""

    def test_verification_commands_present(self):
        """Test that check passes when verification commands are set."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_verification_commands

        prd_data = {
            "verificationCommands": {
                "typecheck": "npm run build",
                "test": "npm test"
            }
        }
        check = check_verification_commands(prd_data)
        assert check.passed is True

    def test_verification_commands_missing(self):
        """Test that check fails when verification commands not set."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_verification_commands

        prd_data = {}
        check = check_verification_commands(prd_data)
        assert check.passed is False
        assert "No verificationCommands" in check.message

    def test_verification_commands_partial(self):
        """Test that check fails when some commands missing."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_verification_commands

        prd_data = {
            "verificationCommands": {
                "typecheck": "npm run build"
                # missing "test"
            }
        }
        check = check_verification_commands(prd_data)
        assert check.passed is False
        assert "test" in check.message

    def test_verification_commands_with_none_prd(self):
        """Test that check handles None PRD data."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_verification_commands

        check = check_verification_commands(None)
        assert check.passed is False
        assert "Cannot check" in check.message


class TestRunDryRunValidation:
    """Tests for the run_dry_run_validation function."""

    def test_dry_run_all_checks_pass(self, tmp_path):
        """Test dry-run returns 0 when all checks pass."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import run_dry_run_validation
        import subprocess

        # Create git repo
        subprocess.run(['git', 'init'], cwd=str(tmp_path), capture_output=True)

        # Create valid PRD with verification commands
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test",
            "verificationCommands": {
                "typecheck": "npm run build",
                "test": "npm test"
            }
        }))

        exit_code = run_dry_run_validation(str(prd_file))
        assert exit_code == 0

    def test_dry_run_missing_prd_returns_1(self, tmp_path):
        """Test dry-run returns 1 when PRD is missing."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import run_dry_run_validation

        exit_code = run_dry_run_validation(str(tmp_path / "missing.json"))
        assert exit_code == 1

    def test_dry_run_invalid_json_returns_1(self, tmp_path):
        """Test dry-run returns 1 when PRD has invalid JSON."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import run_dry_run_validation

        prd_file = tmp_path / "prd.json"
        prd_file.write_text("not valid json")

        exit_code = run_dry_run_validation(str(prd_file))
        assert exit_code == 1

    def test_dry_run_reports_all_failures(self, tmp_path):
        """Test that dry-run reports all failures, not stopping at first."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import run_dry_run_validation

        # Create PRD without verification commands (will fail git check too)
        prd_file = tmp_path / "prd.json"
        prd_file.write_text('{"project": "Test"}')

        # Should return 1 for failures
        exit_code = run_dry_run_validation(str(prd_file))
        assert exit_code == 1

    def test_dry_run_cmd_run_integration(self, tmp_path):
        """Test that cmd_run with dry_run=True calls validation."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run
        import subprocess

        # Create git repo
        subprocess.run(['git', 'init'], cwd=str(tmp_path), capture_output=True)

        # Create valid PRD
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test",
            "verificationCommands": {
                "typecheck": "npm run build",
                "test": "npm test"
            },
            "userStories": []
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=True,
            story=None,
            max_retries=3,
            verbose=False,
            debug=False
        )
        exit_code = cmd_run(args)
        assert exit_code == 0


class TestTokenEstimation:
    """Tests for story token estimation functionality."""

    def test_estimate_story_tokens_simple(self):
        """Test token estimation with a simple story."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import estimate_story_tokens

        story = {
            "title": "Simple Story",
            "description": "A simple description with five words",
        }
        tokens = estimate_story_tokens(story)
        # 2 words in title + 6 words in description = 8 words * 1.3 = 10.4 -> 10
        assert tokens == 10

    def test_estimate_story_tokens_with_criteria(self):
        """Test token estimation with acceptance criteria."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import estimate_story_tokens

        story = {
            "title": "Story",
            "description": "Description",
            "acceptanceCriteria": [
                "First criterion here",
                "Second criterion here"
            ]
        }
        tokens = estimate_story_tokens(story)
        # 1 + 1 + 3 + 3 = 8 words * 1.3 = 10.4 -> 10
        assert tokens == 10

    def test_estimate_story_tokens_with_files_whitelist(self):
        """Test token estimation includes files whitelist."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import estimate_story_tokens

        story = {
            "title": "Story",
            "description": "Description",
            "filesWhitelist": [
                "src/file1.py",
                "src/file2.py"
            ]
        }
        tokens = estimate_story_tokens(story)
        # Each file path counts as 1 word (no spaces)
        # 1 + 1 + 1 + 1 = 4 words * 1.3 = 5.2 -> 5
        assert tokens == 5

    def test_estimate_story_tokens_empty_story(self):
        """Test token estimation with empty story."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import estimate_story_tokens

        story = {}
        tokens = estimate_story_tokens(story)
        assert tokens == 0

    def test_estimate_story_tokens_with_all_fields(self):
        """Test token estimation with all fields populated."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import estimate_story_tokens

        story = {
            "title": "Add Feature",
            "description": "As a user I want this feature",
            "acceptanceCriteria": [
                "Criterion one",
                "Criterion two"
            ],
            "filesWhitelist": [
                "src/main.py"
            ]
        }
        tokens = estimate_story_tokens(story)
        # 2 + 7 + 2 + 2 + 1 = 14 words * 1.3 = 18.2 -> 18
        assert tokens == 18


class TestTokenIndicator:
    """Tests for token indicator functionality."""

    def test_get_token_indicator_under_warning(self):
        """Test that tokens under 50% show no indicator."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_token_indicator, CONTEXT_WINDOW_TOKENS

        # 40% of context window
        tokens = int(CONTEXT_WINDOW_TOKENS * 0.40)
        rich_ind, plain_ind = get_token_indicator(tokens)
        assert rich_ind == ""
        assert plain_ind == ""

    def test_get_token_indicator_warning_level(self):
        """Test that tokens >= 50% show warning indicator."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_token_indicator, CONTEXT_WINDOW_TOKENS

        # 55% of context window
        tokens = int(CONTEXT_WINDOW_TOKENS * 0.55)
        rich_ind, plain_ind = get_token_indicator(tokens)
        assert "LARGE" in rich_ind
        assert "yellow" in rich_ind
        assert plain_ind == "[!]"

    def test_get_token_indicator_error_level(self):
        """Test that tokens >= 80% show error indicator."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_token_indicator, CONTEXT_WINDOW_TOKENS

        # 85% of context window
        tokens = int(CONTEXT_WINDOW_TOKENS * 0.85)
        rich_ind, plain_ind = get_token_indicator(tokens)
        assert "TOO LARGE" in rich_ind
        assert "red" in rich_ind
        assert plain_ind == "[!!!]"

    def test_get_token_indicator_at_threshold(self):
        """Test that tokens at exactly 50% show warning."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_token_indicator, CONTEXT_WINDOW_TOKENS

        # Exactly 50%
        tokens = int(CONTEXT_WINDOW_TOKENS * 0.50)
        rich_ind, plain_ind = get_token_indicator(tokens)
        assert "LARGE" in rich_ind
        assert plain_ind == "[!]"

    def test_get_token_indicator_at_error_threshold(self):
        """Test that tokens at exactly 80% show error."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_token_indicator, CONTEXT_WINDOW_TOKENS

        # Exactly 80%
        tokens = int(CONTEXT_WINDOW_TOKENS * 0.80)
        rich_ind, plain_ind = get_token_indicator(tokens)
        assert "TOO LARGE" in rich_ind
        assert plain_ind == "[!!!]"

    def test_get_token_indicator_zero_tokens(self):
        """Test that zero tokens show no indicator."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_token_indicator

        rich_ind, plain_ind = get_token_indicator(0)
        assert rich_ind == ""
        assert plain_ind == ""


class TestEstimateFlag:
    """Tests for the --estimate flag on status command."""

    def test_estimate_flag_parsed(self):
        """Test that --estimate flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'status', '--estimate']):
            with patch('v_ralph.cmd_status') as mock_status:
                mock_status.return_value = 0
                main()
                args = mock_status.call_args[0][0]
                assert args.estimate is True

    def test_estimate_flag_default_is_false(self):
        """Test that --estimate flag defaults to False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'status']):
            with patch('v_ralph.cmd_status') as mock_status:
                mock_status.return_value = 0
                main()
                args = mock_status.call_args[0][0]
                assert args.estimate is False

    def test_estimate_flag_in_help_output(self):
        """Test that --estimate appears in status --help output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'status', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.stdout.write') as mock_write:
                    main()
            # Help exits with code 0
            assert exc_info.value.code == 0

    def test_status_with_estimate_shows_tokens(self, tmp_path):
        """Test that status --estimate shows token counts."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_status
        import argparse

        # Create a PRD with a story
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [
                {
                    "id": "US-001",
                    "title": "Test Story",
                    "description": "A test description with some words",
                    "priority": 1,
                    "passes": False
                }
            ]
        }))

        args = argparse.Namespace(prd=str(prd_file), estimate=True)
        exit_code = cmd_status(args)
        assert exit_code == 0


class TestDisplayRetryFeedback:
    """Tests for the display_retry_feedback function."""

    def test_display_retry_feedback_calls_feedback_panel(self):
        """Test that display_retry_feedback calls feedback_panel correctly."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_retry_feedback

        with patch('v_ralph.feedback_panel') as mock_panel:
            display_retry_feedback("Test feedback message", iteration=2)
            mock_panel.assert_called_once_with("RETRY", "Test feedback message", iteration=2)

    def test_display_retry_feedback_with_verbose_logs(self):
        """Test that display_retry_feedback logs in verbose mode."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_retry_feedback

        with patch('v_ralph.feedback_panel'):
            with patch('v_ralph.verbose_log') as mock_log:
                display_retry_feedback("Test message", iteration=3, verbose=True)
                mock_log.assert_called_once()
                call_args = mock_log.call_args[0]
                assert "iteration 3" in call_args[0]

    def test_display_retry_feedback_without_verbose_no_log(self):
        """Test that display_retry_feedback does not log when verbose is False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_retry_feedback

        with patch('v_ralph.feedback_panel'):
            with patch('v_ralph.verbose_log') as mock_log:
                display_retry_feedback("Test message", iteration=1, verbose=False)
                mock_log.assert_not_called()


class TestDisplayEscalateFeedback:
    """Tests for the display_escalate_feedback function."""

    def test_display_escalate_feedback_calls_escalate_panel(self):
        """Test that display_escalate_feedback calls escalate_panel correctly."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_escalate_feedback

        with patch('v_ralph.escalate_panel') as mock_panel:
            display_escalate_feedback("Blocking issue detected", story_id="US-005")
            mock_panel.assert_called_once_with("Blocking issue detected", story_id="US-005")

    def test_display_escalate_feedback_with_verbose_logs(self):
        """Test that display_escalate_feedback logs in verbose mode."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_escalate_feedback

        with patch('v_ralph.escalate_panel'):
            with patch('v_ralph.verbose_log') as mock_log:
                display_escalate_feedback("Human needed", story_id="US-010", verbose=True)
                mock_log.assert_called_once()
                call_args = mock_log.call_args[0]
                assert "US-010" in call_args[0]
                assert "escalated" in call_args[0]

    def test_display_escalate_feedback_without_verbose_no_log(self):
        """Test that display_escalate_feedback does not log when verbose is False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_escalate_feedback

        with patch('v_ralph.escalate_panel'):
            with patch('v_ralph.verbose_log') as mock_log:
                display_escalate_feedback("Issue", story_id="US-001", verbose=False)
                mock_log.assert_not_called()


class TestDisplayVerboseRetryHistory:
    """Tests for the display_verbose_retry_history function."""

    def test_display_verbose_retry_history_when_verbose(self):
        """Test that retry history is shown when verbose is True."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_verbose_retry_history

        retry_history = [
            (1, "First failure"),
            (2, "Second failure"),
        ]
        with patch('v_ralph.retry_history_panel') as mock_panel:
            with patch('v_ralph.info'):
                display_verbose_retry_history(retry_history, verbose=True)
                mock_panel.assert_called_once_with(retry_history)

    def test_display_verbose_retry_history_not_shown_when_not_verbose(self):
        """Test that retry history is not shown when verbose is False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_verbose_retry_history

        retry_history = [(1, "Failure")]
        with patch('v_ralph.retry_history_panel') as mock_panel:
            display_verbose_retry_history(retry_history, verbose=False)
            mock_panel.assert_not_called()

    def test_display_verbose_retry_history_empty_list(self):
        """Test that empty retry history does not call panel."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_verbose_retry_history

        with patch('v_ralph.retry_history_panel') as mock_panel:
            display_verbose_retry_history([], verbose=True)
            mock_panel.assert_not_called()

    def test_display_verbose_retry_history_prints_info_first(self):
        """Test that info() is called for spacing before panel."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_verbose_retry_history

        retry_history = [(1, "Test")]
        with patch('v_ralph.retry_history_panel'):
            with patch('v_ralph.info') as mock_info:
                display_verbose_retry_history(retry_history, verbose=True)
                # Should print empty line for spacing
                mock_info.assert_called_once_with("")


class TestProgressFileHealth:
    """Tests for the ProgressFileHealth dataclass."""

    def test_progress_file_health_default_values(self):
        """Test that ProgressFileHealth has correct default values."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ProgressFileHealth

        health = ProgressFileHealth()
        assert health.exists is False
        assert health.has_patterns_section is False
        assert health.patterns_count == 0
        assert health.patterns_tokens == 0
        assert health.history_count == 0
        assert health.history_parseable is True
        assert health.parse_errors == []
        assert health.total_tokens == 0

    def test_progress_file_health_with_values(self):
        """Test ProgressFileHealth with custom values."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ProgressFileHealth

        health = ProgressFileHealth(
            exists=True,
            has_patterns_section=True,
            patterns_count=5,
            patterns_tokens=100,
            history_count=10,
            total_tokens=500
        )
        assert health.exists is True
        assert health.patterns_count == 5
        assert health.history_count == 10


class TestEstimateTextTokens:
    """Tests for the estimate_text_tokens function."""

    def test_estimate_text_tokens_simple(self):
        """Test token estimation with simple text."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import estimate_text_tokens

        text = "one two three four five"
        tokens = estimate_text_tokens(text)
        # 5 words * 1.3 = 6.5 -> 6
        assert tokens == 6

    def test_estimate_text_tokens_empty(self):
        """Test token estimation with empty text."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import estimate_text_tokens

        tokens = estimate_text_tokens("")
        assert tokens == 0

    def test_estimate_text_tokens_multiline(self):
        """Test token estimation with multiline text."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import estimate_text_tokens

        text = "line one\nline two\nline three"
        tokens = estimate_text_tokens(text)
        # 6 words * 1.3 = 7.8 -> 7
        assert tokens == 7


class TestParseProgressFile:
    """Tests for the parse_progress_file function."""

    def test_parse_progress_file_not_exists(self, tmp_path):
        """Test parsing a non-existent progress file."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import parse_progress_file

        health = parse_progress_file(str(tmp_path / "nonexistent.txt"))
        assert health.exists is False

    def test_parse_progress_file_exists(self, tmp_path):
        """Test parsing an existing progress file."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import parse_progress_file

        progress_file = tmp_path / "progress.txt"
        progress_file.write_text("# Progress Log\nSome content")

        health = parse_progress_file(str(progress_file))
        assert health.exists is True

    def test_parse_progress_file_with_patterns_section(self, tmp_path):
        """Test parsing a file with Codebase Patterns section."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import parse_progress_file

        progress_file = tmp_path / "progress.txt"
        content = """# Progress Log

## Codebase Patterns
- Pattern one
- Pattern two
- Pattern three
---

## Recent History
"""
        progress_file.write_text(content)

        health = parse_progress_file(str(progress_file))
        assert health.has_patterns_section is True
        assert health.patterns_count == 3

    def test_parse_progress_file_without_patterns_section(self, tmp_path):
        """Test parsing a file without Codebase Patterns section."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import parse_progress_file

        progress_file = tmp_path / "progress.txt"
        content = """# Progress Log

## History
- Entry 1
"""
        progress_file.write_text(content)

        health = parse_progress_file(str(progress_file))
        assert health.has_patterns_section is False
        assert health.patterns_count == 0

    def test_parse_progress_file_with_history_entries(self, tmp_path):
        """Test parsing a file with history entries."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import parse_progress_file

        progress_file = tmp_path / "progress.txt"
        content = """# Progress Log

## Codebase Patterns
- Pattern one
---

## 2026-01-28 - US-001
- What was implemented: Feature 1
---

## 2026-01-28 - US-002
- What was implemented: Feature 2
---
"""
        progress_file.write_text(content)

        health = parse_progress_file(str(progress_file))
        assert health.history_count == 2

    def test_parse_progress_file_estimates_tokens(self, tmp_path):
        """Test that parse_progress_file estimates total tokens."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import parse_progress_file

        progress_file = tmp_path / "progress.txt"
        content = "one two three four five"  # 5 words
        progress_file.write_text(content)

        health = parse_progress_file(str(progress_file))
        assert health.total_tokens == 6  # 5 * 1.3 = 6.5 -> 6

    def test_parse_progress_file_estimates_patterns_tokens(self, tmp_path):
        """Test that parse_progress_file estimates patterns section tokens."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import parse_progress_file

        progress_file = tmp_path / "progress.txt"
        content = """## Codebase Patterns
- Pattern one two three
- Pattern four five
---
"""
        progress_file.write_text(content)

        health = parse_progress_file(str(progress_file))
        assert health.patterns_tokens > 0


class TestHealthCommand:
    """Tests for the health command."""

    def test_health_command_file_exists(self, tmp_path):
        """Test health command with existing progress file."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_health

        # Create PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text('{}')

        # Create progress file
        progress_file = tmp_path / "progress.txt"
        progress_file.write_text("""# Progress Log

## Codebase Patterns
- Pattern one
---

## 2026-01-28 - US-001
- What was implemented
---
""")

        args = argparse.Namespace(prd=str(prd_file))
        exit_code = cmd_health(args)
        assert exit_code == 0

    def test_health_command_file_not_exists(self, tmp_path):
        """Test health command with missing progress file."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_health

        # Create PRD file but no progress file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text('{}')

        args = argparse.Namespace(prd=str(prd_file))
        exit_code = cmd_health(args)
        assert exit_code == 1

    def test_health_command_without_patterns_section(self, tmp_path):
        """Test health command warns when patterns section missing."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_health

        # Create PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text('{}')

        # Create progress file without patterns section
        progress_file = tmp_path / "progress.txt"
        progress_file.write_text("""# Progress Log

## 2026-01-28 - US-001
- What was implemented
---
""")

        args = argparse.Namespace(prd=str(prd_file))
        exit_code = cmd_health(args)
        assert exit_code == 1  # Issues found (missing patterns section)

    def test_health_command_many_history_entries(self, tmp_path):
        """Test health command warns with many history entries."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_health, HISTORY_ENTRY_WARNING_THRESHOLD

        # Create PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text('{}')

        # Create progress file with many history entries
        entries = []
        for i in range(HISTORY_ENTRY_WARNING_THRESHOLD + 5):
            entries.append(f"## 2026-01-{(i % 28) + 1:02d} - US-{i:03d}\n- Entry\n---\n")

        progress_file = tmp_path / "progress.txt"
        progress_file.write_text(f"""# Progress Log

## Codebase Patterns
- Pattern one
---

{"".join(entries)}
""")

        args = argparse.Namespace(prd=str(prd_file))
        exit_code = cmd_health(args)
        # Should pass (exit 0) but with warnings
        assert exit_code == 0

    def test_health_command_large_patterns_section(self, tmp_path):
        """Test health command warns with large patterns section."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_health, PATTERNS_TOKEN_WARNING_THRESHOLD

        # Create PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text('{}')

        # Create progress file with large patterns section
        # Need enough words to exceed 2000 tokens (words * 1.3 > 2000)
        # So need > 1539 words
        patterns = [f"- Pattern number {i} with several additional words here" for i in range(300)]

        progress_file = tmp_path / "progress.txt"
        progress_file.write_text(f"""# Progress Log

## Codebase Patterns
{chr(10).join(patterns)}
---

## 2026-01-28 - US-001
- Entry
---
""")

        args = argparse.Namespace(prd=str(prd_file))
        exit_code = cmd_health(args)
        # Should pass (exit 0) but with warnings
        assert exit_code == 0


class TestHealthCommandParsing:
    """Tests for health command argument parsing."""

    def test_health_command_recognized(self):
        """Test that health command is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'health']):
            with patch('v_ralph.cmd_health') as mock_health:
                mock_health.return_value = 0
                main()
                mock_health.assert_called_once()

    def test_health_command_in_help(self):
        """Test that health command appears in help output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_health_command_uses_prd_flag(self):
        """Test that health command uses --prd flag for progress file location."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', '--prd', 'custom/prd.json', 'health']):
            with patch('v_ralph.cmd_health') as mock_health:
                mock_health.return_value = 0
                main()
                args = mock_health.call_args[0][0]
                assert args.prd == 'custom/prd.json'


class TestInteractiveFlag:
    """Tests for the --interactive/-i flag."""

    def test_interactive_flag_long_form_parsed(self):
        """Test that --interactive flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--interactive', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.interactive is True

    def test_interactive_flag_short_form_parsed(self):
        """Test that -i flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '-i', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.interactive is True

    def test_interactive_flag_default_is_false(self):
        """Test that interactive flag defaults to False when not provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.interactive is False

    def test_interactive_flag_in_help_output(self):
        """Test that --interactive/-i appears in run --help output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.stdout.write') as mock_write:
                    main()
            # Help exits with code 0
            assert exc_info.value.code == 0


class TestGetPendingStories:
    """Tests for the get_pending_stories function."""

    def test_get_pending_stories_filters_passed(self):
        """Test that passed stories are filtered out."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_pending_stories

        stories = [
            {"id": "US-001", "passes": True, "priority": 1},
            {"id": "US-002", "passes": False, "priority": 2},
            {"id": "US-003", "passes": True, "priority": 3},
        ]
        pending = get_pending_stories(stories)
        assert len(pending) == 1
        assert pending[0]["id"] == "US-002"

    def test_get_pending_stories_filters_skipped(self):
        """Test that skipped stories are filtered out."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_pending_stories

        stories = [
            {"id": "US-001", "passes": False, "priority": 1, "notes": "Skipped: Reason"},
            {"id": "US-002", "passes": False, "priority": 2, "notes": ""},
        ]
        pending = get_pending_stories(stories)
        assert len(pending) == 1
        assert pending[0]["id"] == "US-002"

    def test_get_pending_stories_sorted_by_priority(self):
        """Test that pending stories are sorted by priority."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_pending_stories

        stories = [
            {"id": "US-001", "passes": False, "priority": 5},
            {"id": "US-002", "passes": False, "priority": 1},
            {"id": "US-003", "passes": False, "priority": 3},
        ]
        pending = get_pending_stories(stories)
        assert len(pending) == 3
        assert pending[0]["id"] == "US-002"  # priority 1
        assert pending[1]["id"] == "US-003"  # priority 3
        assert pending[2]["id"] == "US-001"  # priority 5

    def test_get_pending_stories_empty_list(self):
        """Test with empty stories list."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_pending_stories

        pending = get_pending_stories([])
        assert pending == []

    def test_get_pending_stories_all_complete(self):
        """Test when all stories are complete."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import get_pending_stories

        stories = [
            {"id": "US-001", "passes": True, "priority": 1},
            {"id": "US-002", "passes": True, "priority": 2},
        ]
        pending = get_pending_stories(stories)
        assert pending == []


class TestDisplayInteractiveStories:
    """Tests for the display_interactive_stories function."""

    def test_display_interactive_stories_shows_numbered_list(self):
        """Test that stories are displayed with numbers."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_interactive_stories

        stories = [
            {"id": "US-001", "title": "First Story", "priority": 1},
            {"id": "US-002", "title": "Second Story", "priority": 2},
        ]

        with patch('v_ralph.header') as mock_header:
            with patch('v_ralph.info') as mock_info:
                display_interactive_stories(stories)
                mock_header.assert_called_with("Pending Stories:")
                # Check that info was called multiple times
                assert mock_info.call_count >= 3

    def test_display_interactive_stories_shows_instructions(self):
        """Test that instructions are shown."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_interactive_stories

        stories = [{"id": "US-001", "title": "Story", "priority": 1}]

        with patch('v_ralph.header'):
            with patch('v_ralph.info') as mock_info:
                display_interactive_stories(stories)
                # Last call should be the instructions
                calls = [str(call) for call in mock_info.call_args_list]
                instructions_shown = any("'a'" in str(call) and "'q'" in str(call) for call in calls)
                assert instructions_shown


class TestPromptStorySelection:
    """Tests for the prompt_story_selection function."""

    def test_prompt_story_selection_quit(self):
        """Test that 'q' returns empty list and False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import prompt_story_selection

        stories = [{"id": "US-001", "title": "Story", "priority": 1}]

        with patch('v_ralph.display_interactive_stories'):
            with patch('builtins.input', return_value='q'):
                with patch('v_ralph.info'):
                    selected, should_continue = prompt_story_selection(stories)
                    assert selected == []
                    assert should_continue is False

    def test_prompt_story_selection_all(self):
        """Test that 'a' returns all stories and True."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import prompt_story_selection

        stories = [
            {"id": "US-001", "title": "Story 1", "priority": 1},
            {"id": "US-002", "title": "Story 2", "priority": 2},
        ]

        with patch('v_ralph.display_interactive_stories'):
            with patch('builtins.input', return_value='a'):
                with patch('v_ralph.info'):
                    selected, should_continue = prompt_story_selection(stories)
                    assert len(selected) == 2
                    assert should_continue is True

    def test_prompt_story_selection_valid_number(self):
        """Test that valid number selects correct story."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import prompt_story_selection

        stories = [
            {"id": "US-001", "title": "Story 1", "priority": 1},
            {"id": "US-002", "title": "Story 2", "priority": 2},
        ]

        with patch('v_ralph.display_interactive_stories'):
            with patch('builtins.input', return_value='2'):
                with patch('v_ralph.info'):
                    selected, should_continue = prompt_story_selection(stories)
                    assert len(selected) == 1
                    assert selected[0]["id"] == "US-002"
                    assert should_continue is True

    def test_prompt_story_selection_invalid_number_too_high(self):
        """Test that invalid number (too high) returns empty and False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import prompt_story_selection

        stories = [{"id": "US-001", "title": "Story", "priority": 1}]

        with patch('v_ralph.display_interactive_stories'):
            with patch('builtins.input', return_value='5'):
                with patch('v_ralph.error'):
                    selected, should_continue = prompt_story_selection(stories)
                    assert selected == []
                    assert should_continue is False

    def test_prompt_story_selection_invalid_input(self):
        """Test that invalid input returns empty and False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import prompt_story_selection

        stories = [{"id": "US-001", "title": "Story", "priority": 1}]

        with patch('v_ralph.display_interactive_stories'):
            with patch('builtins.input', return_value='xyz'):
                with patch('v_ralph.error'):
                    selected, should_continue = prompt_story_selection(stories)
                    assert selected == []
                    assert should_continue is False

    def test_prompt_story_selection_eof_error(self):
        """Test that EOFError is handled gracefully."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import prompt_story_selection

        stories = [{"id": "US-001", "title": "Story", "priority": 1}]

        with patch('v_ralph.display_interactive_stories'):
            with patch('builtins.input', side_effect=EOFError):
                with patch('v_ralph.info'):
                    selected, should_continue = prompt_story_selection(stories)
                    assert selected == []
                    assert should_continue is False

    def test_prompt_story_selection_keyboard_interrupt(self):
        """Test that KeyboardInterrupt is handled gracefully."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import prompt_story_selection

        stories = [{"id": "US-001", "title": "Story", "priority": 1}]

        with patch('v_ralph.display_interactive_stories'):
            with patch('builtins.input', side_effect=KeyboardInterrupt):
                with patch('v_ralph.info'):
                    selected, should_continue = prompt_story_selection(stories)
                    assert selected == []
                    assert should_continue is False

    def test_prompt_story_selection_case_insensitive(self):
        """Test that 'Q' and 'A' work (case insensitive)."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import prompt_story_selection

        stories = [{"id": "US-001", "title": "Story", "priority": 1}]

        with patch('v_ralph.display_interactive_stories'):
            with patch('builtins.input', return_value='Q'):
                with patch('v_ralph.info'):
                    selected, should_continue = prompt_story_selection(stories)
                    assert should_continue is False


class TestInteractiveModeIntegration:
    """Integration tests for interactive mode in cmd_run."""

    def test_cmd_run_interactive_no_pending_stories(self, tmp_path):
        """Test interactive mode when all stories are complete."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run

        # Create PRD with all stories passing
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [
                {"id": "US-001", "title": "Story 1", "passes": True},
            ]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=False,
            story=None,
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=True,
            reset_attempts=False,
            skip_validation=False,
            timings=False,
            force=True  # Force flag to bypass git safety checks
        )

        with patch('v_ralph.success') as mock_success:
            exit_code = cmd_run(args)
            mock_success.assert_called_with("All stories are complete!")
            assert exit_code == 0

    def test_cmd_run_interactive_quit(self, tmp_path):
        """Test interactive mode when user quits."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run

        # Create PRD with pending story
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [
                {"id": "US-001", "title": "Story 1", "priority": 1, "passes": False},
            ]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=False,
            story=None,
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=True,
            reset_attempts=False,
            skip_validation=False,
            timings=False,
            force=True  # Force flag to bypass git safety checks
        )

        with patch('v_ralph.display_interactive_stories'):
            with patch('builtins.input', return_value='q'):
                with patch('v_ralph.info'):
                    exit_code = cmd_run(args)
                    assert exit_code == 0


class TestResetAttemptsFlag:
    """Tests for the --reset-attempts flag."""

    def test_reset_attempts_flag_parsed(self):
        """Test that --reset-attempts flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--reset-attempts', '--story', 'US-001', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.reset_attempts is True

    def test_reset_attempts_flag_default_is_false(self):
        """Test that --reset-attempts flag defaults to False when not provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.reset_attempts is False

    def test_reset_attempts_flag_in_help_output(self):
        """Test that --reset-attempts appears in run --help output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.stdout.write') as mock_write:
                    main()
            # Help exits with code 0
            assert exc_info.value.code == 0

    def test_reset_attempts_requires_story_flag(self, tmp_path):
        """Test that --reset-attempts requires --story to be specified."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run

        # Create a valid PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [{"id": "US-001", "title": "Story 1", "passes": False}]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=False,
            story=None,
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=False,
            reset_attempts=True,
            skip_validation=False
        )

        with patch('v_ralph.error') as mock_error:
            with patch('v_ralph.info'):
                exit_code = cmd_run(args)
                assert exit_code == 1
                mock_error.assert_called_once()
                assert "--reset-attempts requires --story" in mock_error.call_args[0][0]

    def test_reset_attempts_works_with_story_flag(self, tmp_path):
        """Test that --reset-attempts works when --story is provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run

        # Create a valid PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [{"id": "US-001", "title": "Story 1", "passes": False}]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=False,
            story="US-001",
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=False,
            reset_attempts=True,
            skip_validation=False,
            timings=False,
            force=True  # Force flag to bypass git safety checks
        )

        # Should not return error for missing --story
        with patch('v_ralph.header'):
            with patch('v_ralph.info'):
                with patch('v_ralph.ExecutionSummary'):
                    with patch('v_ralph.display_post_execution_reminder'):
                        exit_code = cmd_run(args)
                        # Should succeed (0) not error (1) for missing story flag
                        assert exit_code == 0


class TestSkipValidationFlag:
    """Tests for the --skip-validation flag."""

    def test_skip_validation_flag_parsed(self):
        """Test that --skip-validation flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--skip-validation', '--story', 'US-001', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.skip_validation is True

    def test_skip_validation_flag_default_is_false(self):
        """Test that --skip-validation flag defaults to False when not provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.skip_validation is False

    def test_skip_validation_flag_in_help_output(self):
        """Test that --skip-validation appears in run --help output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.stdout.write') as mock_write:
                    main()
            # Help exits with code 0
            assert exc_info.value.code == 0

    def test_skip_validation_requires_story_flag(self, tmp_path):
        """Test that --skip-validation requires --story to be specified."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run

        # Create a valid PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [{"id": "US-001", "title": "Story 1", "passes": False}]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=False,
            story=None,
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=False,
            reset_attempts=False,
            skip_validation=True
        )

        with patch('v_ralph.error') as mock_error:
            with patch('v_ralph.info'):
                exit_code = cmd_run(args)
                assert exit_code == 1
                mock_error.assert_called_once()
                assert "--skip-validation requires --story" in mock_error.call_args[0][0]

    def test_skip_validation_works_with_story_flag(self, tmp_path):
        """Test that --skip-validation works when --story is provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run

        # Create a valid PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [{"id": "US-001", "title": "Story 1", "passes": False}]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=False,
            story="US-001",
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=False,
            reset_attempts=False,
            skip_validation=True,
            timings=False,
            force=True  # Force flag to bypass git safety checks
        )

        # Should not return error for missing --story
        with patch('v_ralph.header'):
            with patch('v_ralph.info'):
                with patch('v_ralph.ExecutionSummary'):
                    with patch('v_ralph.display_post_execution_reminder'):
                        exit_code = cmd_run(args)
                        # Should succeed (0) not error (1) for missing story flag
                        assert exit_code == 0


class TestRetryControlFlagsCombined:
    """Tests for combined use of retry control flags."""

    def test_both_flags_can_be_used_together(self):
        """Test that both --reset-attempts and --skip-validation can be used together."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--reset-attempts', '--skip-validation', '--story', 'US-001', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.reset_attempts is True
                assert args.skip_validation is True

    def test_reset_attempts_error_comes_first(self, tmp_path):
        """Test that --reset-attempts error is reported before --skip-validation."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run

        # Create a valid PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [{"id": "US-001", "title": "Story 1", "passes": False}]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=False,
            story=None,
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=False,
            reset_attempts=True,
            skip_validation=True
        )

        with patch('v_ralph.error') as mock_error:
            with patch('v_ralph.info'):
                exit_code = cmd_run(args)
                assert exit_code == 1
                # Should report reset-attempts error first
                assert "--reset-attempts requires --story" in mock_error.call_args[0][0]

    def test_both_flags_work_with_story(self, tmp_path):
        """Test that both flags work when --story is provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run

        # Create a valid PRD file
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps({
            "project": "Test Project",
            "userStories": [{"id": "US-001", "title": "Story 1", "passes": False}]
        }))

        args = argparse.Namespace(
            prd=str(prd_file),
            dry_run=False,
            story="US-001",
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=False,
            reset_attempts=True,
            skip_validation=True,
            timings=False,
            force=True  # Force flag to bypass git safety checks
        )

        with patch('v_ralph.header'):
            with patch('v_ralph.info'):
                with patch('v_ralph.ExecutionSummary'):
                    with patch('v_ralph.display_post_execution_reminder'):
                        exit_code = cmd_run(args)
                        # Should not fail validation
                        assert exit_code == 0


class TestPhaseTimings:
    """Tests for the PhaseTimings dataclass."""

    def test_phase_timings_default_values(self):
        """Test that PhaseTimings initializes with zero values."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import PhaseTimings

        timings = PhaseTimings()
        assert timings.coder_time == 0.0
        assert timings.validation_time == 0.0
        assert timings.audit_time == 0.0

    def test_phase_timings_total_time(self):
        """Test that total_phase_time sums all phases."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import PhaseTimings

        timings = PhaseTimings(coder_time=10.0, validation_time=5.0, audit_time=3.0)
        assert timings.total_phase_time == 18.0

    def test_phase_timings_format_time_seconds(self):
        """Test formatting time in seconds."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import PhaseTimings

        timings = PhaseTimings()
        assert timings.format_time(30.5) == "30.5s"
        assert timings.format_time(0.0) == "0.0s"

    def test_phase_timings_format_time_minutes(self):
        """Test formatting time in minutes and seconds."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import PhaseTimings

        timings = PhaseTimings()
        assert timings.format_time(90) == "1m 30s"
        assert timings.format_time(3599) == "59m 59s"

    def test_phase_timings_format_time_hours(self):
        """Test formatting time with hours."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import PhaseTimings

        timings = PhaseTimings()
        assert timings.format_time(3600) == "1h 0m 0s"
        assert timings.format_time(3661) == "1h 1m 1s"

    def test_phase_timings_get_breakdown(self):
        """Test that get_breakdown returns correct structure."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import PhaseTimings

        timings = PhaseTimings(coder_time=10.0, validation_time=5.5, audit_time=2.0)
        breakdown = timings.get_breakdown()

        assert len(breakdown) == 3
        assert breakdown[0] == ("Coder invocation", 10.0, "10.0s")
        assert breakdown[1] == ("Validation", 5.5, "5.5s")
        assert breakdown[2] == ("Audit", 2.0, "2.0s")


class TestExecutionSummaryWithTimings:
    """Tests for ExecutionSummary with phase timings integration."""

    def test_execution_summary_has_phase_timings(self):
        """Test that ExecutionSummary includes PhaseTimings."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary, PhaseTimings

        summary = ExecutionSummary()
        assert hasattr(summary, 'phase_timings')
        assert isinstance(summary.phase_timings, PhaseTimings)

    def test_execution_summary_phase_timings_can_be_set(self):
        """Test that phase timings can be modified."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.phase_timings.coder_time = 15.0
        summary.phase_timings.validation_time = 8.0
        summary.phase_timings.audit_time = 3.0

        assert summary.phase_timings.coder_time == 15.0
        assert summary.phase_timings.total_phase_time == 26.0

    def test_execution_summary_display_includes_phase_breakdown(self):
        """Test that display includes phase breakdown when timings present."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.phase_timings.coder_time = 10.0
        summary.phase_timings.validation_time = 5.0
        summary.phase_timings.audit_time = 2.0

        with patch('v_ralph.summary_box') as mock_box:
            summary.display()
            # Check that summary_box was called with lines containing phase breakdown
            call_args = mock_box.call_args[0]
            lines = call_args[1]  # Second argument is the lines list
            assert any("Phase breakdown:" in line for line in lines)
            assert any("Coder invocation:" in line for line in lines)


class TestTimingsFlag:
    """Tests for the --timings flag."""

    def test_timings_flag_parsed(self):
        """Test that --timings flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--timings', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.timings is True

    def test_timings_flag_default_is_false(self):
        """Test that timings flag defaults to False when not provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.timings is False

    def test_timings_flag_in_help_output(self):
        """Test that --timings appears in run --help output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.stdout.write') as mock_write:
                    main()
            # Help exits with code 0
            assert exc_info.value.code == 0


class TestDisplayPhaseTiming:
    """Tests for the display_phase_timing function."""

    def test_display_phase_timing_verbose_enabled(self):
        """Test that display_phase_timing outputs when verbose=True."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_phase_timing

        with patch('v_ralph.info') as mock_info:
            display_phase_timing("Coder invocation", 15.5, True)
            mock_info.assert_called_once()
            call_arg = mock_info.call_args[0][0]
            assert "[TIMING]" in call_arg
            assert "Coder invocation" in call_arg
            assert "15.5s" in call_arg

    def test_display_phase_timing_verbose_disabled(self):
        """Test that display_phase_timing is silent when verbose=False."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_phase_timing

        with patch('v_ralph.info') as mock_info:
            display_phase_timing("Coder invocation", 15.5, False)
            mock_info.assert_not_called()

    def test_display_phase_timing_formats_minutes(self):
        """Test that display_phase_timing formats longer times correctly."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_phase_timing

        with patch('v_ralph.info') as mock_info:
            display_phase_timing("Validation", 125, True)  # 2m 5s
            call_arg = mock_info.call_args[0][0]
            assert "2m 5s" in call_arg


class TestDisplayTimingsOnly:
    """Tests for the display_timings_only function."""

    def test_display_timings_only_calls_header(self):
        """Test that display_timings_only shows header."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_timings_only, PhaseTimings

        timings = PhaseTimings(coder_time=10.0, validation_time=5.0, audit_time=2.0)

        with patch('v_ralph.header') as mock_header:
            with patch('v_ralph.info'):
                display_timings_only(timings, 20.0)
                mock_header.assert_called_once_with("Execution Timings")

    def test_display_timings_only_shows_phases(self):
        """Test that display_timings_only shows all phase timings."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_timings_only, PhaseTimings

        timings = PhaseTimings(coder_time=10.0, validation_time=5.5, audit_time=2.0)

        with patch('v_ralph.header'):
            with patch('v_ralph.info') as mock_info:
                # Force plain text mode
                with patch('shared.console.RICH_AVAILABLE', False):
                    display_timings_only(timings, 20.0)
                    # Should be called multiple times for phases + total
                    assert mock_info.call_count >= 4

    def test_display_timings_only_shows_total(self):
        """Test that display_timings_only shows total time."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_timings_only, PhaseTimings

        timings = PhaseTimings(coder_time=10.0, validation_time=5.0, audit_time=2.0)

        with patch('v_ralph.header'):
            with patch('v_ralph.info') as mock_info:
                display_timings_only(timings, 25.5)
                # Check that total time is shown
                calls = [str(c) for c in mock_info.call_args_list]
                assert any("Total time" in c or "25.5s" in c for c in calls)

    def test_display_timings_only_formats_hours(self):
        """Test that display_timings_only formats hours correctly."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_timings_only, PhaseTimings

        timings = PhaseTimings(coder_time=3600.0, validation_time=0, audit_time=0)

        with patch('v_ralph.header'):
            with patch('v_ralph.info') as mock_info:
                display_timings_only(timings, 3661.0)  # 1h 1m 1s
                calls = [str(c) for c in mock_info.call_args_list]
                assert any("1h" in c for c in calls)


class TestGitSafetyCheckDataclass:
    """Tests for the GitSafetyCheck dataclass."""

    def test_git_safety_check_creation(self):
        """Test that GitSafetyCheck can be created with all fields."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import GitSafetyCheck

        check = GitSafetyCheck(
            check_type="uncommitted_changes",
            is_unsafe=True,
            message="Uncommitted changes detected"
        )
        assert check.check_type == "uncommitted_changes"
        assert check.is_unsafe is True
        assert check.message == "Uncommitted changes detected"

    def test_git_safety_check_safe_state(self):
        """Test GitSafetyCheck for a safe state."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import GitSafetyCheck

        check = GitSafetyCheck(
            check_type="detached_head",
            is_unsafe=False,
            message="On a branch (not detached)"
        )
        assert check.is_unsafe is False


class TestCheckGitUncommittedChanges:
    """Tests for check_git_uncommitted_changes function."""

    def test_uncommitted_changes_clean(self, tmp_path):
        """Test detection of clean working directory."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_git_uncommitted_changes

        # Initialize a git repo with no changes
        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmp_path, capture_output=True)

        result = check_git_uncommitted_changes(str(tmp_path))
        assert result.check_type == "uncommitted_changes"
        assert result.is_unsafe is False
        assert "clean" in result.message.lower()

    def test_uncommitted_changes_dirty(self, tmp_path):
        """Test detection of uncommitted changes."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_git_uncommitted_changes

        # Initialize a git repo and create an uncommitted file
        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True)
        (tmp_path / "test.txt").write_text("test content")

        result = check_git_uncommitted_changes(str(tmp_path))
        assert result.check_type == "uncommitted_changes"
        assert result.is_unsafe is True
        assert "uncommitted" in result.message.lower()

    def test_uncommitted_changes_not_a_repo(self, tmp_path):
        """Test behavior when not in a git repository."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_git_uncommitted_changes

        result = check_git_uncommitted_changes(str(tmp_path))
        assert result.check_type == "uncommitted_changes"
        assert result.is_unsafe is True


class TestCheckGitUnpushedCommits:
    """Tests for check_git_unpushed_commits function."""

    def test_unpushed_commits_no_upstream(self, tmp_path):
        """Test when no upstream branch is configured."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_git_unpushed_commits

        # Initialize a git repo without remote
        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmp_path, capture_output=True)
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(['git', 'add', '.'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'initial'], cwd=tmp_path, capture_output=True)

        result = check_git_unpushed_commits(str(tmp_path))
        assert result.check_type == "unpushed_commits"
        # No upstream is not considered unsafe
        assert result.is_unsafe is False
        assert "upstream" in result.message.lower()

    def test_unpushed_commits_not_a_repo(self, tmp_path):
        """Test behavior when not in a git repository."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_git_unpushed_commits

        result = check_git_unpushed_commits(str(tmp_path))
        assert result.check_type == "unpushed_commits"
        # When not a repo, rev-parse fails which means no upstream - treated as safe
        assert result.is_unsafe is False


class TestCheckGitDetachedHead:
    """Tests for check_git_detached_head function."""

    def test_detached_head_on_branch(self, tmp_path):
        """Test when on a regular branch (not detached)."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_git_detached_head

        # Initialize a git repo on main branch
        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmp_path, capture_output=True)
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(['git', 'add', '.'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'initial'], cwd=tmp_path, capture_output=True)

        result = check_git_detached_head(str(tmp_path))
        assert result.check_type == "detached_head"
        assert result.is_unsafe is False
        assert "branch" in result.message.lower()

    def test_detached_head_actual(self, tmp_path):
        """Test when in detached HEAD state."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_git_detached_head

        # Initialize a git repo and detach HEAD
        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmp_path, capture_output=True)
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(['git', 'add', '.'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'initial'], cwd=tmp_path, capture_output=True)
        # Detach HEAD
        subprocess.run(['git', 'checkout', '--detach', 'HEAD'], cwd=tmp_path, capture_output=True)

        result = check_git_detached_head(str(tmp_path))
        assert result.check_type == "detached_head"
        assert result.is_unsafe is True
        assert "detached" in result.message.lower()

    def test_detached_head_not_a_repo(self, tmp_path):
        """Test behavior when not in a git repository."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import check_git_detached_head

        result = check_git_detached_head(str(tmp_path))
        assert result.check_type == "detached_head"
        assert result.is_unsafe is True


class TestRunGitSafetyChecks:
    """Tests for run_git_safety_checks function."""

    def test_run_safety_checks_all_safe(self, tmp_path):
        """Test when all safety checks pass."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import run_git_safety_checks

        # Initialize a clean git repo
        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmp_path, capture_output=True)
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(['git', 'add', '.'], cwd=tmp_path, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'initial'], cwd=tmp_path, capture_output=True)

        checks, is_unsafe = run_git_safety_checks(str(tmp_path))
        assert len(checks) == 3
        assert is_unsafe is False

    def test_run_safety_checks_some_unsafe(self, tmp_path):
        """Test when some safety checks fail."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import run_git_safety_checks

        # Initialize a git repo with uncommitted changes
        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True)
        (tmp_path / "test.txt").write_text("uncommitted content")

        checks, is_unsafe = run_git_safety_checks(str(tmp_path))
        assert len(checks) == 3
        assert is_unsafe is True

    def test_run_safety_checks_returns_all_check_types(self, tmp_path):
        """Test that all check types are returned."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import run_git_safety_checks

        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True)

        checks, _ = run_git_safety_checks(str(tmp_path))
        check_types = [c.check_type for c in checks]
        assert "uncommitted_changes" in check_types
        assert "unpushed_commits" in check_types
        assert "detached_head" in check_types


class TestDisplayGitSafetyWarning:
    """Tests for display_git_safety_warning function."""

    def test_display_warning_shows_unsafe_checks(self):
        """Test that warnings are displayed for unsafe checks."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_git_safety_warning, GitSafetyCheck

        checks = [
            GitSafetyCheck("uncommitted_changes", True, "Uncommitted changes detected"),
            GitSafetyCheck("detached_head", False, "On a branch"),
        ]

        with patch('v_ralph.warning') as mock_warning:
            with patch('v_ralph.info'):
                display_git_safety_warning(checks)
                # Should only show warnings for unsafe checks
                assert mock_warning.call_count >= 2
                call_args = [str(c) for c in mock_warning.call_args_list]
                assert any("Uncommitted" in c for c in call_args)

    def test_display_warning_no_unsafe_checks(self):
        """Test that no warnings shown when all checks are safe."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_git_safety_warning, GitSafetyCheck

        checks = [
            GitSafetyCheck("uncommitted_changes", False, "Clean"),
            GitSafetyCheck("detached_head", False, "On a branch"),
        ]

        with patch('v_ralph.warning') as mock_warning:
            with patch('v_ralph.info'):
                display_git_safety_warning(checks)
                mock_warning.assert_not_called()

    def test_display_warning_shows_force_suggestion(self):
        """Test that --force suggestion is shown."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_git_safety_warning, GitSafetyCheck

        checks = [
            GitSafetyCheck("uncommitted_changes", True, "Uncommitted changes"),
        ]

        with patch('v_ralph.warning'):
            with patch('v_ralph.info') as mock_info:
                display_git_safety_warning(checks)
                calls = [str(c) for c in mock_info.call_args_list]
                assert any("--force" in c for c in calls)


class TestDisplayPostExecutionReminder:
    """Tests for display_post_execution_reminder function."""

    def test_reminder_shows_git_commands(self):
        """Test that reminder shows git log and diff commands."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_post_execution_reminder

        with patch('v_ralph.info') as mock_info:
            display_post_execution_reminder()
            calls = [str(c) for c in mock_info.call_args_list]
            assert any("git log" in c for c in calls)
            assert any("git diff" in c for c in calls)

    def test_reminder_mentions_review(self):
        """Test that reminder mentions reviewing commits."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import display_post_execution_reminder

        with patch('v_ralph.info') as mock_info:
            display_post_execution_reminder()
            calls = [str(c) for c in mock_info.call_args_list]
            assert any("review" in c.lower() or "Review" in c for c in calls)


class TestForceFlag:
    """Tests for the --force flag."""

    def test_force_flag_parsed(self):
        """Test that --force flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--force', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.force is True

    def test_force_flag_default_is_false(self):
        """Test that force flag defaults to False when not provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.force is False

    def test_force_flag_in_help_output(self):
        """Test that --force appears in run --help output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.stdout.write'):
                    main()
            # Help exits with code 0
            assert exc_info.value.code == 0


class TestGitSafetyIntegration:
    """Integration tests for git safety checks in cmd_run."""

    def test_cmd_run_blocked_by_unsafe_state(self, tmp_path):
        """Test that cmd_run is blocked when git state is unsafe."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run

        # Create a PRD file
        prd_path = tmp_path / "prd.json"
        prd_data = {
            "project": "Test",
            "branchName": "test",
            "userStories": [{"id": "US-001", "title": "Test", "passes": False, "priority": 1}]
        }
        prd_path.write_text(json.dumps(prd_data))

        # Initialize git repo with uncommitted changes
        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True)
        (tmp_path / "dirty.txt").write_text("uncommitted")

        args = argparse.Namespace(
            prd=str(prd_path),
            story=None,
            dry_run=False,
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=False,
            reset_attempts=False,
            skip_validation=False,
            timings=False,
            force=False
        )

        with patch('v_ralph.display_git_safety_warning'):
            result = cmd_run(args)
            # Should return 1 due to unsafe git state
            assert result == 1

    def test_cmd_run_proceeds_with_force_flag(self, tmp_path):
        """Test that cmd_run proceeds when --force is used despite unsafe state."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import cmd_run

        # Create a PRD file
        prd_path = tmp_path / "prd.json"
        prd_data = {
            "project": "Test",
            "branchName": "test",
            "userStories": [{"id": "US-001", "title": "Test", "passes": False, "priority": 1}]
        }
        prd_path.write_text(json.dumps(prd_data))

        # Initialize git repo with uncommitted changes
        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, capture_output=True)
        (tmp_path / "dirty.txt").write_text("uncommitted")

        args = argparse.Namespace(
            prd=str(prd_path),
            story=None,
            dry_run=False,
            max_retries=3,
            verbose=False,
            debug=False,
            interactive=False,
            reset_attempts=False,
            skip_validation=False,
            timings=False,
            force=True  # Force flag enabled
        )

        with patch('v_ralph.header'):
            with patch('v_ralph.info'):
                with patch('v_ralph.summary_box'):
                    with patch('v_ralph.display_post_execution_reminder'):
                        result = cmd_run(args)
                        # Should return 0 (proceed despite unsafe state)
                        assert result == 0


class TestTimeoutFlags:
    """Tests for the --validation-timeout, --coder-timeout, and --audit-timeout flags."""

    def test_validation_timeout_flag_parsed(self):
        """Test that --validation-timeout flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--validation-timeout', '60', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.validation_timeout == 60

    def test_coder_timeout_flag_parsed(self):
        """Test that --coder-timeout flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--coder-timeout', '600', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.coder_timeout == 600

    def test_audit_timeout_flag_parsed(self):
        """Test that --audit-timeout flag is recognized by the parser."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--audit-timeout', '240', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.audit_timeout == 240

    def test_timeout_flags_default_to_none(self):
        """Test that timeout flags default to None when not provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.validation_timeout is None
                assert args.coder_timeout is None
                assert args.audit_timeout is None

    def test_all_timeout_flags_together(self):
        """Test that all timeout flags can be used together."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run',
                               '--validation-timeout', '30',
                               '--coder-timeout', '500',
                               '--audit-timeout', '150',
                               '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.validation_timeout == 30
                assert args.coder_timeout == 500
                assert args.audit_timeout == 150

    def test_timeout_flags_in_help_output(self):
        """Test that timeout flags appear in run --help output."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.stdout.write') as mock_write:
                    main()
            # Help exits with code 0
            assert exc_info.value.code == 0


class TestExecutionTimeouts:
    """Tests for the ExecutionTimeouts dataclass."""

    def test_default_timeouts(self):
        """Test that ExecutionTimeouts has correct default values."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts, DEFAULT_VALIDATION_TIMEOUT, DEFAULT_CODER_TIMEOUT, DEFAULT_AUDIT_TIMEOUT

        timeouts = ExecutionTimeouts()
        assert timeouts.validation == DEFAULT_VALIDATION_TIMEOUT
        assert timeouts.coder == DEFAULT_CODER_TIMEOUT
        assert timeouts.audit == DEFAULT_AUDIT_TIMEOUT

    def test_default_timeout_values(self):
        """Test that default timeout constants have expected values."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import DEFAULT_VALIDATION_TIMEOUT, DEFAULT_CODER_TIMEOUT, DEFAULT_AUDIT_TIMEOUT

        assert DEFAULT_VALIDATION_TIMEOUT == 120
        assert DEFAULT_CODER_TIMEOUT == 300
        assert DEFAULT_AUDIT_TIMEOUT == 180

    def test_custom_timeouts(self):
        """Test that ExecutionTimeouts can be created with custom values."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts

        timeouts = ExecutionTimeouts(validation=60, coder=600, audit=240)
        assert timeouts.validation == 60
        assert timeouts.coder == 600
        assert timeouts.audit == 240


class TestExecutionTimeoutsFromPrdAndArgs:
    """Tests for the ExecutionTimeouts.from_prd_and_args class method."""

    def test_uses_defaults_when_no_prd_or_args(self):
        """Test that defaults are used when no PRD timeouts or CLI args provided."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts, DEFAULT_VALIDATION_TIMEOUT, DEFAULT_CODER_TIMEOUT, DEFAULT_AUDIT_TIMEOUT

        prd_data = {"project": "Test"}
        timeouts = ExecutionTimeouts.from_prd_and_args(prd_data)

        assert timeouts.validation == DEFAULT_VALIDATION_TIMEOUT
        assert timeouts.coder == DEFAULT_CODER_TIMEOUT
        assert timeouts.audit == DEFAULT_AUDIT_TIMEOUT

    def test_uses_prd_timeouts_when_present(self):
        """Test that PRD timeouts override defaults."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts

        prd_data = {
            "project": "Test",
            "timeouts": {
                "validation": 60,
                "coder": 600,
                "audit": 240
            }
        }
        timeouts = ExecutionTimeouts.from_prd_and_args(prd_data)

        assert timeouts.validation == 60
        assert timeouts.coder == 600
        assert timeouts.audit == 240

    def test_cli_args_override_prd_timeouts(self):
        """Test that CLI args override PRD timeouts."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts

        prd_data = {
            "project": "Test",
            "timeouts": {
                "validation": 60,
                "coder": 600,
                "audit": 240
            }
        }
        timeouts = ExecutionTimeouts.from_prd_and_args(
            prd_data,
            validation_timeout=30,
            coder_timeout=500,
            audit_timeout=150
        )

        assert timeouts.validation == 30
        assert timeouts.coder == 500
        assert timeouts.audit == 150

    def test_cli_args_override_defaults_when_no_prd_timeouts(self):
        """Test that CLI args override defaults when no PRD timeouts present."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts

        prd_data = {"project": "Test"}
        timeouts = ExecutionTimeouts.from_prd_and_args(
            prd_data,
            validation_timeout=45,
            coder_timeout=450,
            audit_timeout=200
        )

        assert timeouts.validation == 45
        assert timeouts.coder == 450
        assert timeouts.audit == 200

    def test_partial_prd_timeouts(self):
        """Test that partial PRD timeouts work (only some specified)."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts, DEFAULT_CODER_TIMEOUT, DEFAULT_AUDIT_TIMEOUT

        prd_data = {
            "project": "Test",
            "timeouts": {
                "validation": 90
            }
        }
        timeouts = ExecutionTimeouts.from_prd_and_args(prd_data)

        assert timeouts.validation == 90
        assert timeouts.coder == DEFAULT_CODER_TIMEOUT
        assert timeouts.audit == DEFAULT_AUDIT_TIMEOUT

    def test_partial_cli_override(self):
        """Test that partial CLI override works (only some specified)."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts, DEFAULT_VALIDATION_TIMEOUT, DEFAULT_AUDIT_TIMEOUT

        prd_data = {"project": "Test"}
        timeouts = ExecutionTimeouts.from_prd_and_args(
            prd_data,
            coder_timeout=500
        )

        assert timeouts.validation == DEFAULT_VALIDATION_TIMEOUT
        assert timeouts.coder == 500
        assert timeouts.audit == DEFAULT_AUDIT_TIMEOUT

    def test_mixed_prd_and_cli_override(self):
        """Test that PRD and CLI overrides work together (CLI wins for overlaps)."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts, DEFAULT_AUDIT_TIMEOUT

        prd_data = {
            "project": "Test",
            "timeouts": {
                "validation": 60,
                "coder": 600
            }
        }
        # Only override validation via CLI, coder comes from PRD, audit is default
        timeouts = ExecutionTimeouts.from_prd_and_args(
            prd_data,
            validation_timeout=30
        )

        assert timeouts.validation == 30  # CLI override
        assert timeouts.coder == 600  # From PRD
        assert timeouts.audit == DEFAULT_AUDIT_TIMEOUT  # Default

    def test_empty_prd_timeouts_object(self):
        """Test that empty timeouts object in PRD uses defaults."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts, DEFAULT_VALIDATION_TIMEOUT, DEFAULT_CODER_TIMEOUT, DEFAULT_AUDIT_TIMEOUT

        prd_data = {
            "project": "Test",
            "timeouts": {}
        }
        timeouts = ExecutionTimeouts.from_prd_and_args(prd_data)

        assert timeouts.validation == DEFAULT_VALIDATION_TIMEOUT
        assert timeouts.coder == DEFAULT_CODER_TIMEOUT
        assert timeouts.audit == DEFAULT_AUDIT_TIMEOUT

    def test_non_dict_prd_timeouts_ignored(self):
        """Test that non-dict timeouts value in PRD is ignored."""
        sys.path.insert(0, str(__file__).rsplit('/tests/', 1)[0])
        from v_ralph import ExecutionTimeouts, DEFAULT_VALIDATION_TIMEOUT, DEFAULT_CODER_TIMEOUT, DEFAULT_AUDIT_TIMEOUT

        prd_data = {
            "project": "Test",
            "timeouts": "invalid"
        }
        timeouts = ExecutionTimeouts.from_prd_and_args(prd_data)

        assert timeouts.validation == DEFAULT_VALIDATION_TIMEOUT
        assert timeouts.coder == DEFAULT_CODER_TIMEOUT
        assert timeouts.audit == DEFAULT_AUDIT_TIMEOUT
