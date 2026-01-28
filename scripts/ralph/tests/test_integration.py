"""End-to-end integration tests for V-Ralph.

Tests the full V-model flow with mocked Claude calls:
1. Story executed
2. Validation passed
3. Audit passed
4. prd.json updated with passes=true
5. progress.txt has new entry

All tests use deterministic mocked responses suitable for CI.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from shared.prd import load_prd, save_prd, PRD, UserStory, VerificationCommands
from shared.progress import load_learnings, append_progress
from micro_v.executor import execute_story, ExecutorConfig, ExecutionResult
from micro_v.auditor import AuditVerdict, AuditResult


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def test_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary test project directory with fixture files.

    Copies all fixtures to a temp directory for isolation.

    Yields:
        Path to the temporary project directory.
    """
    # Copy fixtures to temp directory
    project_dir = tmp_path / "test_project"
    shutil.copytree(FIXTURES_DIR, project_dir)

    yield project_dir


@pytest.fixture
def sample_story() -> UserStory:
    """Create a sample user story for direct executor testing."""
    return UserStory(
        id="TEST-001",
        title="Simple function implementation",
        description="As a developer, I need a simple add function for testing.",
        acceptanceCriteria=[
            "sample.py exists with add function",
            "add(1, 2) returns 3",
            "test_sample.py has passing test for add function",
        ],
        priority=1,
        passes=False,
        notes="",
        attempts=0,
    )


class TestFixturesExist:
    """Verify test fixtures are properly set up."""

    def test_fixtures_directory_exists(self) -> None:
        """Verify fixtures directory exists."""
        assert FIXTURES_DIR.exists(), f"Fixtures dir not found: {FIXTURES_DIR}"

    def test_prd_json_exists(self) -> None:
        """Verify prd.json fixture exists."""
        prd_path = FIXTURES_DIR / "prd.json"
        assert prd_path.exists(), f"prd.json not found: {prd_path}"

    def test_progress_txt_exists(self) -> None:
        """Verify progress.txt fixture exists."""
        progress_path = FIXTURES_DIR / "progress.txt"
        assert progress_path.exists(), f"progress.txt not found: {progress_path}"

    def test_sample_py_exists(self) -> None:
        """Verify sample.py fixture exists."""
        sample_path = FIXTURES_DIR / "sample.py"
        assert sample_path.exists(), f"sample.py not found: {sample_path}"

    def test_prd_json_is_valid(self) -> None:
        """Verify prd.json fixture has valid structure."""
        prd = load_prd(FIXTURES_DIR / "prd.json")
        assert prd.project == "Test Project"
        assert len(prd.userStories) > 0
        assert prd.userStories[0].id == "TEST-001"


class TestExecutorIntegration:
    """Integration tests for the executor with mocked Claude calls."""

    @patch("micro_v.executor._get_git_diff")
    @patch("micro_v.executor.audit_implementation")
    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_full_execution_flow_success(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        mock_audit: MagicMock,
        mock_diff: MagicMock,
        sample_story: UserStory,
        test_project_dir: Path,
    ) -> None:
        """Test complete execution flow: coder -> validation -> audit -> success."""
        # Setup mocks for deterministic behavior
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Implementation complete", "", 0)
        mock_validate.return_value = (True, "All tests passed")
        mock_diff.return_value = "diff --git a/sample.py\n+def add(a, b): return a + b"
        mock_audit.return_value = AuditResult(verdict=AuditVerdict.PASS)

        config = ExecutorConfig(
            max_retries=5,
            validation_command="python -m pytest",
            working_dir=str(test_project_dir),
            learnings="Use pytest for testing",
            enable_audit=True,
        )

        result = execute_story(sample_story, config)

        # Verify success
        assert result.result == ExecutionResult.SUCCESS
        assert result.story_id == "TEST-001"
        assert result.iterations == 1

        # Verify flow order: coder called, then validation, then audit
        mock_claude.assert_called_once()
        mock_validate.assert_called_once()
        mock_audit.assert_called_once()

    @patch("micro_v.executor._get_git_diff")
    @patch("micro_v.executor.audit_implementation")
    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_validation_retry_then_success(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        mock_audit: MagicMock,
        mock_diff: MagicMock,
        sample_story: UserStory,
        test_project_dir: Path,
    ) -> None:
        """Test validation failure triggers retry with error context."""
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Code written", "", 0)
        mock_diff.return_value = "diff content"
        mock_audit.return_value = AuditResult(verdict=AuditVerdict.PASS)

        # First validation fails, second passes
        mock_validate.side_effect = [
            (False, "NameError: name 'add' is not defined"),
            (True, "All tests passed"),
        ]

        config = ExecutorConfig(
            max_retries=5,
            validation_command="python -m pytest",
            working_dir=str(test_project_dir),
            enable_audit=True,
        )

        result = execute_story(sample_story, config)

        assert result.result == ExecutionResult.SUCCESS
        assert result.iterations == 2
        assert mock_claude.call_count == 2

        # Second call should include error context
        second_call_prompt = mock_claude.call_args_list[1][1]["prompt"]
        assert "NameError" in second_call_prompt

    @patch("micro_v.executor._get_git_diff")
    @patch("micro_v.executor.audit_implementation")
    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_audit_retry_then_success(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        mock_audit: MagicMock,
        mock_diff: MagicMock,
        sample_story: UserStory,
        test_project_dir: Path,
    ) -> None:
        """Test audit RETRY verdict triggers coder retry with feedback."""
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Code written", "", 0)
        mock_validate.return_value = (True, "Tests passed")
        mock_diff.return_value = "diff content"

        # First audit: RETRY, second: PASS
        mock_audit.side_effect = [
            AuditResult(
                verdict=AuditVerdict.RETRY,
                feedback="Function lacks docstring and type hints",
            ),
            AuditResult(verdict=AuditVerdict.PASS),
        ]

        config = ExecutorConfig(
            max_retries=5,
            validation_command="python -m pytest",
            working_dir=str(test_project_dir),
            enable_audit=True,
        )

        result = execute_story(sample_story, config)

        assert result.result == ExecutionResult.SUCCESS
        assert result.iterations == 2
        assert mock_audit.call_count == 2

        # Second coder call should include audit feedback
        second_call_prompt = mock_claude.call_args_list[1][1]["prompt"]
        assert "Semantic audit requested changes" in second_call_prompt
        assert "docstring" in second_call_prompt

    @patch("micro_v.executor._get_git_diff")
    @patch("micro_v.executor.audit_implementation")
    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_escalation_stops_execution(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        mock_audit: MagicMock,
        mock_diff: MagicMock,
        sample_story: UserStory,
        test_project_dir: Path,
    ) -> None:
        """Test ESCALATE verdict returns escalated result."""
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Code written", "", 0)
        mock_validate.return_value = (True, "Tests passed")
        mock_diff.return_value = "diff content"
        mock_audit.return_value = AuditResult(
            verdict=AuditVerdict.ESCALATE,
            reason="Spec is ambiguous: should add() handle None inputs?",
        )

        config = ExecutorConfig(
            max_retries=5,
            validation_command="python -m pytest",
            working_dir=str(test_project_dir),
            enable_audit=True,
        )

        result = execute_story(sample_story, config)

        assert result.result == ExecutionResult.ESCALATED
        assert result.iterations == 1
        assert "ambiguous" in result.escalation_reason.lower()


class TestPRDIntegration:
    """Integration tests for PRD read/write with execution."""

    def test_load_fixture_prd(self, test_project_dir: Path) -> None:
        """Test loading PRD from fixture."""
        prd = load_prd(test_project_dir / "prd.json")

        assert prd.project == "Test Project"
        assert prd.branchName == "test/integration"
        assert len(prd.userStories) == 1
        assert prd.userStories[0].passes is False

    def test_update_prd_marks_story_passed(self, test_project_dir: Path) -> None:
        """Test that updating PRD persists passed status."""
        prd_path = test_project_dir / "prd.json"
        prd = load_prd(prd_path)

        # Mark story as passed
        prd.userStories[0].passes = True
        save_prd(prd, prd_path)

        # Reload and verify
        reloaded = load_prd(prd_path)
        assert reloaded.userStories[0].passes is True

    @patch("micro_v.executor._get_git_diff")
    @patch("micro_v.executor.audit_implementation")
    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_execution_and_prd_update_flow(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        mock_audit: MagicMock,
        mock_diff: MagicMock,
        test_project_dir: Path,
    ) -> None:
        """Test full flow: execute story, verify PRD updated."""
        # Setup mocks
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Implementation complete", "", 0)
        mock_validate.return_value = (True, "Tests passed")
        mock_diff.return_value = "diff content"
        mock_audit.return_value = AuditResult(verdict=AuditVerdict.PASS)

        prd_path = test_project_dir / "prd.json"
        prd = load_prd(prd_path)
        story = prd.userStories[0]

        # Verify initial state
        assert story.passes is False

        config = ExecutorConfig(
            max_retries=5,
            validation_command="python -m pytest",
            working_dir=str(test_project_dir),
            enable_audit=True,
        )

        result = execute_story(story, config)

        # Execution should succeed
        assert result.result == ExecutionResult.SUCCESS

        # Simulate what run command does: update PRD
        story.passes = True
        save_prd(prd, prd_path)

        # Verify PRD was updated
        reloaded = load_prd(prd_path)
        assert reloaded.userStories[0].passes is True


class TestProgressIntegration:
    """Integration tests for progress tracking with execution."""

    def test_load_fixture_progress(self, test_project_dir: Path) -> None:
        """Test loading progress from fixture."""
        context = load_learnings(test_project_dir / "progress.txt")

        assert len(context.patterns) >= 1
        assert any("pytest" in p for p in context.patterns)

    def test_append_progress_entry(self, test_project_dir: Path) -> None:
        """Test appending progress entry persists to file."""
        progress_path = test_project_dir / "progress.txt"

        entry = """## 2026-01-28 12:00 - TEST-001
- What was implemented: Simple add function
- Iterations: 1
- **Learnings:** Tests should cover edge cases"""

        append_progress(progress_path, entry)

        # Verify entry was appended
        content = progress_path.read_text()
        assert "TEST-001" in content
        assert "Simple add function" in content
        assert "edge cases" in content

    @patch("micro_v.executor._get_git_diff")
    @patch("micro_v.executor.audit_implementation")
    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_execution_and_progress_update_flow(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        mock_audit: MagicMock,
        mock_diff: MagicMock,
        test_project_dir: Path,
    ) -> None:
        """Test full flow: execute story, verify progress updated."""
        # Setup mocks
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Implementation complete", "", 0)
        mock_validate.return_value = (True, "Tests passed")
        mock_diff.return_value = "diff content"
        mock_audit.return_value = AuditResult(verdict=AuditVerdict.PASS)

        prd_path = test_project_dir / "prd.json"
        progress_path = test_project_dir / "progress.txt"

        prd = load_prd(prd_path)
        story = prd.userStories[0]

        config = ExecutorConfig(
            max_retries=5,
            validation_command="python -m pytest",
            working_dir=str(test_project_dir),
            enable_audit=True,
        )

        result = execute_story(story, config)

        # Execution should succeed
        assert result.result == ExecutionResult.SUCCESS

        # Simulate what run command does: append progress
        entry = f"""## 2026-01-28 12:00 - {story.id}
- What was implemented: {story.title}
- Iterations: {result.iterations}
- **Learnings:** Mocked execution for integration test"""

        append_progress(progress_path, entry)

        # Verify progress was updated
        content = progress_path.read_text()
        assert story.id in content
        assert "Simple function implementation" in content


class TestFullVModelFlow:
    """End-to-end tests verifying the complete V-model flow."""

    @patch("micro_v.executor._get_git_diff")
    @patch("micro_v.executor.audit_implementation")
    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_complete_v_model_cycle(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        mock_audit: MagicMock,
        mock_diff: MagicMock,
        test_project_dir: Path,
    ) -> None:
        """Test complete V-model cycle with all components integrated.

        Verifies:
        1. Story executed with mocked Claude
        2. Validation passed
        3. Audit passed
        4. prd.json updated with passes=true
        5. progress.txt has new entry
        """
        # Setup deterministic mocked responses
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Implementation complete", "", 0)
        mock_validate.return_value = (True, "All tests passed")
        mock_diff.return_value = "diff --git a/sample.py\n+def add(a, b): return a + b"
        mock_audit.return_value = AuditResult(verdict=AuditVerdict.PASS)

        prd_path = test_project_dir / "prd.json"
        progress_path = test_project_dir / "progress.txt"

        # 1. Load initial state
        prd = load_prd(prd_path)
        story = prd.userStories[0]
        assert story.passes is False, "Story should start as not passed"

        # 2. Execute story
        config = ExecutorConfig(
            max_retries=5,
            validation_command="python -m pytest test_sample.py -v",
            working_dir=str(test_project_dir),
            learnings="Use pytest for testing",
            enable_audit=True,
        )

        result = execute_story(story, config)

        # 3. Verify execution succeeded
        assert result.result == ExecutionResult.SUCCESS, "Execution should succeed"
        assert result.story_id == "TEST-001"

        # 4. Simulate run command: update PRD
        story.passes = True
        save_prd(prd, prd_path)

        # 5. Verify prd.json updated
        reloaded_prd = load_prd(prd_path)
        assert reloaded_prd.userStories[0].passes is True, "PRD should show passes=true"

        # 6. Simulate run command: append progress
        entry = f"""## 2026-01-28 15:00 - {story.id}
- What was implemented: {story.title}
- Iterations: {result.iterations}
- **Learnings for future iterations:**
  - Integration test completed successfully"""

        append_progress(progress_path, entry)

        # 7. Verify progress.txt has new entry
        progress_content = progress_path.read_text()
        assert story.id in progress_content, "Progress should contain story ID"
        assert "Integration test completed" in progress_content

        # 8. Verify all mocks were called in correct order
        mock_load.assert_called_once()  # Coder prompt loaded
        mock_claude.assert_called_once()  # Coder invoked
        mock_validate.assert_called_once()  # Validation ran
        mock_audit.assert_called_once()  # Audit ran

    @patch("micro_v.executor._get_git_diff")
    @patch("micro_v.executor.audit_implementation")
    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_retry_flow_updates_correctly(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        mock_audit: MagicMock,
        mock_diff: MagicMock,
        test_project_dir: Path,
    ) -> None:
        """Test that retry flow correctly updates PRD and progress.

        Simulates:
        - First attempt: validation fails
        - Second attempt: validation passes, audit RETRYs
        - Third attempt: all pass
        """
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Code written", "", 0)
        mock_diff.return_value = "diff content"

        # Validation: fail, pass, pass
        mock_validate.side_effect = [
            (False, "SyntaxError: invalid syntax"),
            (True, "Tests passed"),
            (True, "Tests passed"),
        ]

        # Audit: RETRY, PASS
        mock_audit.side_effect = [
            AuditResult(verdict=AuditVerdict.RETRY, feedback="Missing edge case test"),
            AuditResult(verdict=AuditVerdict.PASS),
        ]

        prd_path = test_project_dir / "prd.json"
        progress_path = test_project_dir / "progress.txt"

        prd = load_prd(prd_path)
        story = prd.userStories[0]

        config = ExecutorConfig(
            max_retries=5,
            validation_command="python -m pytest",
            working_dir=str(test_project_dir),
            enable_audit=True,
        )

        result = execute_story(story, config)

        # Should succeed after 3 iterations
        assert result.result == ExecutionResult.SUCCESS
        assert result.iterations == 3

        # Update PRD and progress as run command would
        story.passes = True
        save_prd(prd, prd_path)

        entry = f"""## 2026-01-28 15:30 - {story.id}
- What was implemented: {story.title}
- Iterations: {result.iterations}
- **Learnings:** Needed 3 attempts due to validation and audit retries"""

        append_progress(progress_path, entry)

        # Verify final state
        reloaded_prd = load_prd(prd_path)
        assert reloaded_prd.userStories[0].passes is True

        progress_content = progress_path.read_text()
        assert "3 attempts" in progress_content


class TestDeterministicMocking:
    """Tests verifying mocks produce deterministic results for CI."""

    @patch("micro_v.executor._get_git_diff")
    @patch("micro_v.executor.audit_implementation")
    @patch("micro_v.executor._run_validation")
    @patch("micro_v.executor.invoke_claude")
    @patch("micro_v.executor._load_coder_prompt")
    def test_same_inputs_produce_same_outputs(
        self,
        mock_load: MagicMock,
        mock_claude: MagicMock,
        mock_validate: MagicMock,
        mock_audit: MagicMock,
        mock_diff: MagicMock,
        sample_story: UserStory,
    ) -> None:
        """Verify deterministic behavior with mocked dependencies."""
        # Fixed mocked responses
        mock_load.return_value = "{{goal}}{{files}}{{criteria}}{{learnings}}"
        mock_claude.return_value = ("Implementation", "", 0)
        mock_validate.return_value = (True, "Passed")
        mock_diff.return_value = "diff"
        mock_audit.return_value = AuditResult(verdict=AuditVerdict.PASS)

        config = ExecutorConfig(
            max_retries=5,
            validation_command="test",
            working_dir="/test",
            enable_audit=True,
        )

        # Run multiple times
        results = []
        for _ in range(3):
            # Reset mock call counts but keep return values
            mock_load.reset_mock()
            mock_claude.reset_mock()
            mock_validate.reset_mock()
            mock_audit.reset_mock()
            mock_diff.reset_mock()

            result = execute_story(sample_story, config)
            results.append(result)

        # All results should be identical
        for r in results:
            assert r.result == ExecutionResult.SUCCESS
            assert r.iterations == 1
            assert r.story_id == "TEST-001"

    def test_fixture_loading_is_deterministic(self) -> None:
        """Verify fixtures produce same data each load."""
        prd1 = load_prd(FIXTURES_DIR / "prd.json")
        prd2 = load_prd(FIXTURES_DIR / "prd.json")

        assert prd1.project == prd2.project
        assert prd1.branchName == prd2.branchName
        assert len(prd1.userStories) == len(prd2.userStories)
        assert prd1.userStories[0].id == prd2.userStories[0].id
