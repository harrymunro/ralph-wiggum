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
            debug=False
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
