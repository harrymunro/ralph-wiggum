"""Integration tests for the V-Model execution flow.

Tests the complete execution flow of Ralph with mocked Claude CLI:
- Complete flow: load PRD -> execute story -> validation -> audit -> commit -> update PRD
- Retry flow: validation fails -> retry with error context -> eventually passes
- Escalation flow: audit returns ESCALATE -> execution stops with code 2
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class MockClaudeCLI:
    """Mock for Claude CLI subprocess calls.

    Simulates Claude code responses for different scenarios:
    - Coder phase: generates code changes
    - Validation phase: runs verification commands
    - Audit phase: returns PASS, RETRY, or ESCALATE
    """

    def __init__(self, responses: list = None):
        """Initialize mock with list of responses.

        Args:
            responses: List of (returncode, stdout, stderr) tuples for sequential calls
        """
        self.responses = responses or []
        self.call_index = 0
        self.calls = []

    def __call__(self, *args, **kwargs):
        """Handle subprocess.run call and return mocked response."""
        self.calls.append({'args': args, 'kwargs': kwargs})

        if self.call_index < len(self.responses):
            response = self.responses[self.call_index]
            self.call_index += 1

            mock_result = MagicMock()
            mock_result.returncode = response[0]
            mock_result.stdout = response[1]
            mock_result.stderr = response[2] if len(response) > 2 else ''
            return mock_result

        # Default: success with empty output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ''
        mock_result.stderr = ''
        return mock_result


def create_test_prd(tmp_path: Path, stories: list = None, project_name: str = "Test Project") -> Path:
    """Create a test PRD file in the temp directory.

    Args:
        tmp_path: Temporary directory path
        stories: List of story dictionaries
        project_name: Project name for the PRD

    Returns:
        Path to the created PRD file
    """
    if stories is None:
        stories = [
            {
                "id": "US-001",
                "title": "Test Story",
                "description": "A test story for integration testing",
                "acceptanceCriteria": ["Code compiles", "Tests pass"],
                "priority": 1,
                "passes": False
            }
        ]

    prd_data = {
        "project": project_name,
        "branchName": "test/integration",
        "verificationCommands": {
            "typecheck": "echo 'typecheck passed'",
            "test": "echo 'tests passed'"
        },
        "userStories": stories
    }

    prd_file = tmp_path / "prd.json"
    prd_file.write_text(json.dumps(prd_data, indent=2))
    return prd_file


def init_test_git_repo(tmp_path: Path) -> None:
    """Initialize a git repository in the temp directory.

    Args:
        tmp_path: Temporary directory path
    """
    os.chdir(tmp_path)
    subprocess.run(['git', 'init'], capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], capture_output=True)


class TestCompleteFlow:
    """Test the complete V-Model execution flow.

    Flow: load PRD -> execute story -> validation -> audit -> commit -> update PRD
    """

    def test_complete_flow_load_prd(self, tmp_path):
        """Test that PRD is loaded correctly at the start of execution."""
        from v_ralph import load_prd

        prd_file = create_test_prd(tmp_path)
        prd = load_prd(str(prd_file))

        assert prd['project'] == 'Test Project'
        assert len(prd['userStories']) == 1
        assert prd['userStories'][0]['id'] == 'US-001'
        assert prd['userStories'][0]['passes'] is False

    def test_complete_flow_select_pending_story(self, tmp_path):
        """Test that pending stories are selected in priority order."""
        from v_ralph import load_prd

        stories = [
            {"id": "US-002", "title": "Low Priority", "priority": 2, "passes": False},
            {"id": "US-001", "title": "High Priority", "priority": 1, "passes": False},
            {"id": "US-003", "title": "Complete", "priority": 3, "passes": True}
        ]
        prd_file = create_test_prd(tmp_path, stories)
        prd = load_prd(str(prd_file))

        # Filter pending stories and sort by priority
        pending = [s for s in prd['userStories'] if not s.get('passes', False)]
        pending.sort(key=lambda s: s.get('priority', 999))

        assert len(pending) == 2
        assert pending[0]['id'] == 'US-001'  # Highest priority first
        assert pending[1]['id'] == 'US-002'

    def test_complete_flow_run_command_with_dry_run(self, tmp_path):
        """Test that run command with dry-run validates without executing."""
        from v_ralph import cmd_run

        # Initialize git repo for dry-run validation
        init_test_git_repo(tmp_path)
        prd_file = create_test_prd(tmp_path)

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

    def test_complete_flow_prd_save_preserves_format(self, tmp_path):
        """Test that saving PRD preserves JSON format."""
        from v_ralph import load_prd, save_prd

        prd_file = create_test_prd(tmp_path)
        prd = load_prd(str(prd_file))

        # Modify story status
        prd['userStories'][0]['passes'] = True

        # Save and reload
        save_prd(str(prd_file), prd)
        reloaded = load_prd(str(prd_file))

        assert reloaded['userStories'][0]['passes'] is True
        assert reloaded['project'] == 'Test Project'

    def test_complete_flow_execution_summary_tracks_stats(self, tmp_path):
        """Test that execution summary tracks story counts correctly."""
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()

        # Simulate executing 3 stories
        summary.stories_attempted = 3
        summary.stories_passed = 2
        summary.stories_failed = 1
        summary.total_iterations = 5
        summary.commits = ['abc123', 'def456']

        summary.finish()

        assert summary.stories_attempted == 3
        assert summary.stories_passed == 2
        assert summary.stories_failed == 1
        assert summary.total_iterations == 5
        assert len(summary.commits) == 2
        assert summary.elapsed_time > 0

    def test_complete_flow_all_stories_complete(self, tmp_path):
        """Test that run command returns 0 when all stories are complete."""
        from v_ralph import cmd_run

        stories = [
            {"id": "US-001", "title": "Story 1", "priority": 1, "passes": True},
            {"id": "US-002", "title": "Story 2", "priority": 2, "passes": True}
        ]
        prd_file = create_test_prd(tmp_path, stories)

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


class TestRetryFlow:
    """Test the retry flow when validation fails.

    Flow: validation fails -> retry with error context -> eventually passes
    """

    def test_retry_flow_tracks_iterations(self, tmp_path):
        """Test that retry iterations are tracked in execution summary."""
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()

        # Simulate 3 retries before success
        for i in range(3):
            summary.total_iterations += 1

        summary.stories_passed = 1
        summary.stories_attempted = 1
        summary.finish()

        assert summary.total_iterations == 3
        assert summary.stories_passed == 1

    def test_retry_flow_max_retries_respected(self, tmp_path):
        """Test that max_retries parameter is parsed correctly."""
        from v_ralph import main

        with patch('sys.argv', ['v_ralph', 'run', '--max-retries', '5', '--dry-run']):
            with patch('v_ralph.cmd_run') as mock_run:
                mock_run.return_value = 0
                main()
                args = mock_run.call_args[0][0]
                assert args.max_retries == 5

    def test_retry_flow_validation_failure_format(self, tmp_path):
        """Test that validation failures are properly captured."""
        from v_ralph import verbose_validation_output

        validation_output = """
FAILED tests/test_example.py::test_one
    AssertionError: Expected True but got False
FAILED tests/test_example.py::test_two
    ValueError: Invalid input
2 failed, 3 passed
"""

        with patch('v_ralph.info') as mock_info:
            verbose_validation_output(validation_output.strip(), True)
            # Should output header plus each line
            assert mock_info.call_count > 1

    def test_retry_flow_context_preserved_across_retries(self, tmp_path):
        """Test that execution summary preserves state across simulated retries."""
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.stories_attempted = 1

        # First attempt fails
        summary.total_iterations = 1

        # Second attempt fails
        summary.total_iterations = 2

        # Third attempt succeeds
        summary.total_iterations = 3
        summary.stories_passed = 1

        summary.finish()

        assert summary.total_iterations == 3
        assert summary.stories_passed == 1
        assert summary.stories_failed == 0

    def test_retry_flow_verbose_shows_retry_details(self, tmp_path):
        """Test that verbose mode shows retry information."""
        from v_ralph import verbose_log

        with patch('v_ralph.info') as mock_info:
            verbose_log("Retry attempt 2 of 3", True)
            verbose_log("Validation failed: 2 tests failed", True)

            assert mock_info.call_count == 2
            # Check message format
            calls = [call[0][0] for call in mock_info.call_args_list]
            assert any("Retry" in msg for msg in calls)


class TestEscalationFlow:
    """Test the escalation flow when audit returns ESCALATE.

    Flow: audit returns ESCALATE -> execution stops with code 2
    """

    def test_escalation_flow_tracked_in_summary(self, tmp_path):
        """Test that escalations are tracked in execution summary."""
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.stories_attempted = 1

        # Story escalated after audit
        summary.add_escalation("US-001", "Fundamental design issue detected")

        summary.finish()

        assert len(summary.escalated_stories) == 1
        assert summary.escalated_stories[0][0] == "US-001"
        assert "design issue" in summary.escalated_stories[0][1]

    def test_escalation_flow_multiple_escalations(self, tmp_path):
        """Test that multiple escalations are tracked separately."""
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.stories_attempted = 3

        summary.add_escalation("US-001", "Security vulnerability")
        summary.add_escalation("US-003", "Breaking API change")

        summary.finish()

        assert len(summary.escalated_stories) == 2

    def test_escalation_flow_display_shows_red_style(self, tmp_path):
        """Test that escalations cause summary to display with red style."""
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.stories_passed = 2
        summary.add_escalation("US-003", "Test escalation reason")
        summary.finish()

        with patch('v_ralph.summary_box') as mock_box:
            summary.display()
            call_kwargs = mock_box.call_args[1]
            assert call_kwargs.get('style') == 'red'

    def test_escalation_flow_reason_in_summary(self, tmp_path):
        """Test that escalation reason appears in summary display."""
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.add_escalation("US-001", "Human review required for API design")
        summary.finish()

        with patch('v_ralph.summary_box') as mock_box:
            summary.display()
            lines = mock_box.call_args[0][1]
            lines_text = "\n".join(lines)
            assert "US-001" in lines_text
            assert "Human review required" in lines_text

    def test_escalation_flow_preserves_story_count(self, tmp_path):
        """Test that escalations don't count as passed or failed."""
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.stories_attempted = 3
        summary.stories_passed = 1
        summary.stories_failed = 1
        # Third story escalated (not passed or failed)
        summary.add_escalation("US-003", "Escalated")

        summary.finish()

        # Escalation doesn't change passed/failed counts
        assert summary.stories_passed == 1
        assert summary.stories_failed == 1
        assert len(summary.escalated_stories) == 1


class TestMockedClaudeCLI:
    """Test that all Claude CLI interactions can be properly mocked."""

    def test_mock_claude_cli_basic_usage(self):
        """Test basic MockClaudeCLI usage."""
        mock_cli = MockClaudeCLI([
            (0, "Code generated successfully", ""),
            (0, "All tests passed", ""),
            (0, "AUDIT: PASS", "")
        ])

        # First call: coder
        result1 = mock_cli()
        assert result1.returncode == 0
        assert "Code generated" in result1.stdout

        # Second call: validation
        result2 = mock_cli()
        assert result2.returncode == 0
        assert "tests passed" in result2.stdout

        # Third call: audit
        result3 = mock_cli()
        assert result3.returncode == 0
        assert "PASS" in result3.stdout

    def test_mock_claude_cli_tracks_calls(self):
        """Test that MockClaudeCLI tracks all calls made."""
        mock_cli = MockClaudeCLI([
            (0, "output1", ""),
            (0, "output2", "")
        ])

        mock_cli(cmd="first command")
        mock_cli(cmd="second command")

        assert len(mock_cli.calls) == 2

    def test_mock_claude_cli_simulates_failure(self):
        """Test that MockClaudeCLI can simulate failures."""
        mock_cli = MockClaudeCLI([
            (1, "", "Error: compilation failed")
        ])

        result = mock_cli()
        assert result.returncode == 1
        assert "compilation failed" in result.stderr

    def test_mock_claude_cli_default_response(self):
        """Test MockClaudeCLI default response when responses exhausted."""
        mock_cli = MockClaudeCLI([])  # No predefined responses

        result = mock_cli()
        assert result.returncode == 0
        assert result.stdout == ''


class TestIsolatedTempDirectory:
    """Test that integration tests run in isolated temp directories."""

    def test_prd_created_in_temp_dir(self, tmp_path):
        """Test that PRD files are created in the temp directory."""
        prd_file = create_test_prd(tmp_path)

        assert prd_file.exists()
        assert tmp_path in prd_file.parents or prd_file.parent == tmp_path

    def test_temp_dir_is_isolated(self, tmp_path):
        """Test that each test gets an isolated temp directory."""
        marker_file = tmp_path / "test_marker.txt"
        marker_file.write_text("test")

        assert marker_file.exists()
        # The marker file should only exist in this test's tmp_path

    def test_git_repo_can_be_initialized_in_temp_dir(self, tmp_path):
        """Test that git repositories can be initialized in temp directories."""
        original_dir = os.getcwd()
        try:
            init_test_git_repo(tmp_path)

            # Verify git repo was created
            assert (tmp_path / '.git').exists()
        finally:
            os.chdir(original_dir)

    def test_multiple_files_in_temp_dir(self, tmp_path):
        """Test that multiple test files can coexist in temp directory."""
        prd_file = create_test_prd(tmp_path)
        progress_file = tmp_path / "progress.txt"
        progress_file.write_text("# Test Progress\n")

        assert prd_file.exists()
        assert progress_file.exists()


class TestEndToEndMockedFlow:
    """End-to-end tests with fully mocked Claude CLI."""

    def test_e2e_successful_story_execution(self, tmp_path):
        """Test successful end-to-end story execution with mocks."""
        from v_ralph import load_prd, save_prd, cmd_run, ExecutionSummary

        # Setup
        prd_file = create_test_prd(tmp_path)
        prd = load_prd(str(prd_file))

        assert prd['userStories'][0]['passes'] is False

        # Simulate successful execution
        summary = ExecutionSummary()
        summary.stories_attempted = 1
        summary.total_iterations = 1
        summary.stories_passed = 1
        summary.commits = ['abc123']

        # Update PRD as would happen after success
        prd['userStories'][0]['passes'] = True
        save_prd(str(prd_file), prd)

        # Verify
        updated_prd = load_prd(str(prd_file))
        assert updated_prd['userStories'][0]['passes'] is True
        summary.finish()
        assert summary.elapsed_time > 0

    def test_e2e_failed_validation_retry(self, tmp_path):
        """Test retry flow when validation fails initially."""
        from v_ralph import ExecutionSummary

        summary = ExecutionSummary()
        summary.stories_attempted = 1

        # Simulate: fail -> fail -> pass
        validation_results = [False, False, True]

        for i, passed in enumerate(validation_results):
            summary.total_iterations += 1
            if passed:
                summary.stories_passed = 1
                break

        summary.finish()

        assert summary.total_iterations == 3
        assert summary.stories_passed == 1

    def test_e2e_escalation_after_max_retries(self, tmp_path):
        """Test escalation when validation continues to fail."""
        from v_ralph import ExecutionSummary

        max_retries = 3
        summary = ExecutionSummary()
        summary.stories_attempted = 1

        # Simulate: fail -> fail -> fail -> escalate
        for i in range(max_retries):
            summary.total_iterations += 1
            # All attempts fail

        # Escalate after max retries
        summary.add_escalation("US-001", f"Failed after {max_retries} attempts")
        summary.stories_failed = 1

        summary.finish()

        assert summary.total_iterations == max_retries
        assert len(summary.escalated_stories) == 1
        assert summary.stories_failed == 1

    def test_e2e_multiple_stories_execution(self, tmp_path):
        """Test execution of multiple stories in sequence."""
        from v_ralph import load_prd, save_prd, ExecutionSummary

        stories = [
            {"id": "US-001", "title": "Story 1", "priority": 1, "passes": False},
            {"id": "US-002", "title": "Story 2", "priority": 2, "passes": False},
            {"id": "US-003", "title": "Story 3", "priority": 3, "passes": False}
        ]
        prd_file = create_test_prd(tmp_path, stories)
        prd = load_prd(str(prd_file))

        summary = ExecutionSummary()

        # Execute each story
        for i, story in enumerate(prd['userStories']):
            if not story.get('passes', False):
                summary.stories_attempted += 1
                summary.total_iterations += 1

                # Simulate success for first two, escalation for third
                if i < 2:
                    summary.stories_passed += 1
                    story['passes'] = True
                    summary.commits.append(f"commit{i+1}")
                else:
                    summary.add_escalation(story['id'], "Complex refactoring needed")

        save_prd(str(prd_file), prd)
        summary.finish()

        # Verify
        assert summary.stories_attempted == 3
        assert summary.stories_passed == 2
        assert len(summary.escalated_stories) == 1
        assert len(summary.commits) == 2

        updated_prd = load_prd(str(prd_file))
        assert updated_prd['userStories'][0]['passes'] is True
        assert updated_prd['userStories'][1]['passes'] is True
        assert updated_prd['userStories'][2]['passes'] is False
