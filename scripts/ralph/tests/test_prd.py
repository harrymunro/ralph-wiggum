"""Unit tests for shared/prd.py module."""

import json
import tempfile
from pathlib import Path

import pytest

from shared.prd import (
    PRD,
    PRDError,
    UserStory,
    VerificationCommands,
    get_pending_stories,
    increment_attempts,
    load_prd,
    mark_story_passed,
    save_prd,
)


@pytest.fixture
def sample_prd_data() -> dict:
    """Return sample PRD data for testing."""
    return {
        "project": "Test Project",
        "branchName": "feature/test",
        "description": "A test project",
        "verificationCommands": {
            "typecheck": "python -m py_compile main.py",
            "test": "python -m pytest tests/ -v",
        },
        "userStories": [
            {
                "id": "US-001",
                "title": "First Story",
                "description": "First story description",
                "acceptanceCriteria": ["Criterion 1", "Criterion 2"],
                "priority": 1,
                "passes": True,
                "notes": "Some notes",
                "attempts": 1,
            },
            {
                "id": "US-002",
                "title": "Second Story",
                "description": "Second story description",
                "acceptanceCriteria": ["Criterion A"],
                "priority": 2,
                "passes": False,
                "notes": "",
                "attempts": 0,
            },
            {
                "id": "US-003",
                "title": "Third Story",
                "description": "Third story description",
                "acceptanceCriteria": [],
                "priority": 3,
                "passes": False,
                "notes": "",
                "attempts": 2,
            },
        ],
    }


@pytest.fixture
def sample_prd_file(sample_prd_data: dict) -> Path:
    """Create a temporary PRD file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(sample_prd_data, f)
        return Path(f.name)


class TestLoadPRD:
    """Tests for load_prd function."""

    def test_load_valid_json(self, sample_prd_file: Path) -> None:
        """Test loading a valid JSON PRD file."""
        prd = load_prd(sample_prd_file)

        assert prd.project == "Test Project"
        assert prd.branchName == "feature/test"
        assert prd.description == "A test project"
        assert prd.verificationCommands.typecheck == "python -m py_compile main.py"
        assert prd.verificationCommands.test == "python -m pytest tests/ -v"
        assert len(prd.userStories) == 3

    def test_load_parses_stories_correctly(self, sample_prd_file: Path) -> None:
        """Test that user stories are parsed with all fields."""
        prd = load_prd(sample_prd_file)

        story = prd.userStories[0]
        assert story.id == "US-001"
        assert story.title == "First Story"
        assert story.description == "First story description"
        assert story.acceptanceCriteria == ["Criterion 1", "Criterion 2"]
        assert story.priority == 1
        assert story.passes is True
        assert story.notes == "Some notes"
        assert story.attempts == 1

    def test_load_missing_file_raises_error(self) -> None:
        """Test that loading a non-existent file raises PRDError."""
        with pytest.raises(PRDError) as exc_info:
            load_prd("/nonexistent/path/prd.json")

        assert "PRD file not found" in str(exc_info.value)

    def test_load_invalid_json_raises_error(self) -> None:
        """Test that loading invalid JSON raises PRDError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("{ invalid json }")
            path = Path(f.name)

        with pytest.raises(PRDError) as exc_info:
            load_prd(path)

        assert "Invalid JSON" in str(exc_info.value)

    def test_load_handles_missing_optional_fields(self) -> None:
        """Test loading PRD with missing optional fields uses defaults."""
        minimal_data = {
            "project": "Minimal",
            "branchName": "main",
            "description": "Minimal project",
            "userStories": [
                {
                    "id": "US-001",
                    "title": "Story",
                    "description": "Desc",
                }
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(minimal_data, f)
            path = Path(f.name)

        prd = load_prd(path)

        assert prd.verificationCommands.typecheck == ""
        assert prd.verificationCommands.test == ""
        assert prd.userStories[0].passes is False
        assert prd.userStories[0].attempts == 0
        assert prd.userStories[0].acceptanceCriteria == []

    def test_load_accepts_path_string(self, sample_prd_file: Path) -> None:
        """Test that load_prd accepts both Path and str."""
        prd = load_prd(str(sample_prd_file))
        assert prd.project == "Test Project"


class TestSavePRD:
    """Tests for save_prd function."""

    def test_save_creates_valid_json(self) -> None:
        """Test that save_prd creates valid JSON."""
        prd = PRD(
            project="Saved Project",
            branchName="save/test",
            description="A saved project",
            verificationCommands=VerificationCommands(
                typecheck="check", test="test"
            ),
            userStories=[
                UserStory(
                    id="US-001",
                    title="Story",
                    description="Desc",
                    acceptanceCriteria=["Crit 1"],
                    priority=1,
                    passes=True,
                    notes="Notes",
                    attempts=3,
                )
            ],
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            path = Path(f.name)

        save_prd(prd, path)

        # Verify file is valid JSON
        content = path.read_text()
        data = json.loads(content)

        assert data["project"] == "Saved Project"
        assert data["branchName"] == "save/test"
        assert data["userStories"][0]["passes"] is True
        assert data["userStories"][0]["attempts"] == 3

    def test_save_round_trip(self, sample_prd_file: Path) -> None:
        """Test that load -> save -> load preserves data."""
        original = load_prd(sample_prd_file)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            new_path = Path(f.name)

        save_prd(original, new_path)
        reloaded = load_prd(new_path)

        assert reloaded.project == original.project
        assert reloaded.branchName == original.branchName
        assert len(reloaded.userStories) == len(original.userStories)

        for orig, new in zip(original.userStories, reloaded.userStories):
            assert orig.id == new.id
            assert orig.passes == new.passes
            assert orig.attempts == new.attempts


class TestGetPendingStories:
    """Tests for get_pending_stories function."""

    def test_returns_only_failing_stories(self, sample_prd_file: Path) -> None:
        """Test that only stories with passes=False are returned."""
        prd = load_prd(sample_prd_file)
        pending = get_pending_stories(prd)

        assert len(pending) == 2
        assert all(not s.passes for s in pending)

    def test_returns_sorted_by_priority(self, sample_prd_file: Path) -> None:
        """Test that pending stories are sorted by priority."""
        prd = load_prd(sample_prd_file)
        pending = get_pending_stories(prd)

        priorities = [s.priority for s in pending]
        assert priorities == sorted(priorities)

    def test_returns_empty_when_all_pass(self) -> None:
        """Test returns empty list when all stories pass."""
        prd = PRD(
            project="Done",
            branchName="main",
            description="All done",
            verificationCommands=VerificationCommands(),
            userStories=[
                UserStory(
                    id="US-001",
                    title="Done",
                    description="Done",
                    acceptanceCriteria=[],
                    priority=1,
                    passes=True,
                )
            ],
        )

        pending = get_pending_stories(prd)
        assert pending == []


class TestMarkStoryPassed:
    """Tests for mark_story_passed function."""

    def test_marks_story_as_passed(self, sample_prd_file: Path) -> None:
        """Test that a story can be marked as passed."""
        prd = load_prd(sample_prd_file)

        assert prd.userStories[1].passes is False

        result = mark_story_passed(prd, "US-002")

        assert result is True
        assert prd.userStories[1].passes is True

    def test_returns_false_for_unknown_story(
        self, sample_prd_file: Path
    ) -> None:
        """Test returns False when story ID not found."""
        prd = load_prd(sample_prd_file)

        result = mark_story_passed(prd, "US-999")

        assert result is False


class TestIncrementAttempts:
    """Tests for increment_attempts function."""

    def test_increments_attempt_counter(self, sample_prd_file: Path) -> None:
        """Test that attempt counter is incremented."""
        prd = load_prd(sample_prd_file)

        original_attempts = prd.userStories[1].attempts
        new_count = increment_attempts(prd, "US-002")

        assert new_count == original_attempts + 1
        assert prd.userStories[1].attempts == new_count

    def test_returns_new_count(self, sample_prd_file: Path) -> None:
        """Test that the new count is returned."""
        prd = load_prd(sample_prd_file)

        # US-003 has attempts=2
        new_count = increment_attempts(prd, "US-003")
        assert new_count == 3

    def test_returns_negative_for_unknown_story(
        self, sample_prd_file: Path
    ) -> None:
        """Test returns -1 when story ID not found."""
        prd = load_prd(sample_prd_file)

        result = increment_attempts(prd, "US-999")

        assert result == -1
