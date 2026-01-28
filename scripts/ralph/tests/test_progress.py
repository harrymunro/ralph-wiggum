"""Unit tests for shared/progress.py module."""

import tempfile
from pathlib import Path

import pytest

from shared.progress import (
    ProgressContext,
    ProgressError,
    append_progress,
    load_learnings,
    _extract_patterns,
    _extract_history_entries,
)


@pytest.fixture
def sample_progress_content() -> str:
    """Return sample progress file content for testing."""
    return """# Ralph Progress Log
Started: Wed Jan 28 15:58:34 AST 2026

## Codebase Patterns
- Use `python3` not `python` for all CLI commands on macOS
- Directory structure: macro_v/, micro_v/, shared/, tests/ with __init__.py in each
- CLI uses argparse with subparsers for run/status commands
---

## 2026-01-28 16:00 - US-001
- What was implemented: Basic project scaffolding and CLI entry point
- Files changed:
  - v_ralph.py (main CLI)
- **Learnings for future iterations:**
  - Use `python3` command not `python` on macOS
---

## 2026-01-28 16:15 - US-002
- What was implemented: PRD read/write module with typed dataclasses
- Files changed:
  - shared/prd.py
  - tests/test_prd.py
- **Learnings for future iterations:**
  - pytest must be installed
---

## 2026-01-28 16:30 - US-003
- What was implemented: Claude CLI wrapper module
- Files changed:
  - shared/claude.py
  - tests/test_claude.py
- **Learnings for future iterations:**
  - Use subprocess.Popen with communicate() for timeout support
---

## 2026-01-28 16:45 - US-004
- What was implemented: Fourth story
- **Learnings:** Something
---

## 2026-01-28 17:00 - US-005
- What was implemented: Fifth story
- **Learnings:** Something else
---

## 2026-01-28 17:15 - US-006
- What was implemented: Sixth story
- **Learnings:** More learnings
---
"""


@pytest.fixture
def sample_progress_file(sample_progress_content: str) -> Path:
    """Create a temporary progress file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as f:
        f.write(sample_progress_content)
        return Path(f.name)


class TestLoadLearnings:
    """Tests for load_learnings function."""

    def test_loads_patterns_section(self, sample_progress_file: Path) -> None:
        """Test that patterns are loaded correctly."""
        context = load_learnings(sample_progress_file)

        assert len(context.patterns) == 3
        assert "- Use `python3` not `python`" in context.patterns[0]
        assert "- Directory structure:" in context.patterns[1]
        assert "- CLI uses argparse" in context.patterns[2]

    def test_loads_only_last_n_history_entries(
        self, sample_progress_file: Path
    ) -> None:
        """Test that only the last N history entries are loaded."""
        context = load_learnings(sample_progress_file, max_history=5)

        # Should have last 5 entries (US-002 through US-006)
        assert len(context.recent_history) == 5

        # Verify we have the most recent entries
        history_text = "\n".join(context.recent_history)
        assert "US-002" in history_text
        assert "US-003" in history_text
        assert "US-004" in history_text
        assert "US-005" in history_text
        assert "US-006" in history_text

        # US-001 should not be in the last 5
        assert "US-001" not in history_text

    def test_respects_max_history_parameter(
        self, sample_progress_file: Path
    ) -> None:
        """Test that max_history parameter limits entries."""
        context = load_learnings(sample_progress_file, max_history=2)

        assert len(context.recent_history) == 2

        # Should have only the last 2 entries
        history_text = "\n".join(context.recent_history)
        assert "US-005" in history_text
        assert "US-006" in history_text

    def test_creates_file_if_missing(self) -> None:
        """Test that missing file is created with template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "new_progress.txt"

            assert not path.exists()

            context = load_learnings(path)

            assert path.exists()
            assert context.patterns == []
            assert context.recent_history == []

            # Verify template structure
            content = path.read_text()
            assert "# Ralph Progress Log" in content
            assert "## Codebase Patterns" in content

    def test_creates_parent_directories_if_missing(self) -> None:
        """Test that parent directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "nested" / "progress.txt"

            assert not path.parent.exists()

            context = load_learnings(path)

            assert path.exists()
            assert context.patterns == []

    def test_returns_empty_lists_for_empty_sections(self) -> None:
        """Test handling of file with empty sections."""
        content = """# Ralph Progress Log
Started: Wed Jan 28 15:58:34 AST 2026

## Codebase Patterns
---
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write(content)
            path = Path(f.name)

        context = load_learnings(path)

        assert context.patterns == []
        assert context.recent_history == []

    def test_accepts_path_string(self, sample_progress_file: Path) -> None:
        """Test that load_learnings accepts both Path and str."""
        context = load_learnings(str(sample_progress_file))
        assert len(context.patterns) == 3


class TestAppendProgress:
    """Tests for append_progress function."""

    def test_appends_entry_to_file(self, sample_progress_file: Path) -> None:
        """Test that entry is appended to file."""
        new_entry = """## 2026-01-28 18:00 - US-007
- What was implemented: New story
- **Learnings:** New learnings"""

        append_progress(sample_progress_file, new_entry)

        content = sample_progress_file.read_text()
        assert "US-007" in content
        assert "New story" in content
        assert "New learnings" in content

    def test_adds_separator_if_missing(
        self, sample_progress_file: Path
    ) -> None:
        """Test that --- separator is added if not present."""
        new_entry = """## 2026-01-28 18:00 - US-007
- What was implemented: New story"""

        append_progress(sample_progress_file, new_entry)

        content = sample_progress_file.read_text()
        # Entry should end with ---
        assert content.strip().endswith("---")

    def test_preserves_existing_separator(
        self, sample_progress_file: Path
    ) -> None:
        """Test that existing separator is preserved."""
        new_entry = """## 2026-01-28 18:00 - US-007
- What was implemented: New story
---"""

        append_progress(sample_progress_file, new_entry)

        content = sample_progress_file.read_text()
        # Should not have double separators
        assert "---\n---" not in content

    def test_creates_file_if_missing(self) -> None:
        """Test that missing file is created before appending."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "new_progress.txt"

            new_entry = """## 2026-01-28 18:00 - US-001
- What was implemented: First story"""

            append_progress(path, new_entry)

            assert path.exists()
            content = path.read_text()
            assert "# Ralph Progress Log" in content
            assert "## Codebase Patterns" in content
            assert "US-001" in content

    def test_creates_parent_directories_if_missing(self) -> None:
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "progress.txt"

            new_entry = """## 2026-01-28 18:00 - US-001
- What was implemented: First story"""

            append_progress(path, new_entry)

            assert path.exists()

    def test_accepts_path_string(self) -> None:
        """Test that append_progress accepts both Path and str."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "progress.txt"
            path.write_text("# Progress\n")

            append_progress(str(path), "## 2026-01-28 - Entry")

            content = path.read_text()
            assert "Entry" in content


class TestExtractPatterns:
    """Tests for _extract_patterns helper function."""

    def test_extracts_bullet_points(self) -> None:
        """Test extracting patterns from bullet points."""
        content = """## Codebase Patterns
- Pattern one
- Pattern two
- Pattern three
---"""

        patterns = _extract_patterns(content)

        assert len(patterns) == 3
        assert "- Pattern one" in patterns
        assert "- Pattern two" in patterns
        assert "- Pattern three" in patterns

    def test_handles_empty_section(self) -> None:
        """Test handling empty patterns section."""
        content = """## Codebase Patterns
---"""

        patterns = _extract_patterns(content)

        assert patterns == []

    def test_ignores_non_bullet_lines(self) -> None:
        """Test that non-bullet lines are ignored."""
        content = """## Codebase Patterns
- Valid pattern
Some other text
- Another valid pattern
---"""

        patterns = _extract_patterns(content)

        # Should have 2 patterns (ignoring "Some other text" and "---")
        assert len(patterns) == 2
        assert "- Valid pattern" in patterns
        assert "- Another valid pattern" in patterns

    def test_handles_missing_section(self) -> None:
        """Test handling file without patterns section."""
        content = """# Progress Log
Some content here
"""

        patterns = _extract_patterns(content)

        assert patterns == []


class TestExtractHistoryEntries:
    """Tests for _extract_history_entries helper function."""

    def test_extracts_all_entries(self, sample_progress_content: str) -> None:
        """Test extracting all history entries."""
        entries = _extract_history_entries(sample_progress_content)

        assert len(entries) == 6  # US-001 through US-006

    def test_preserves_entry_content(
        self, sample_progress_content: str
    ) -> None:
        """Test that entry content is preserved."""
        entries = _extract_history_entries(sample_progress_content)

        first_entry = entries[0]
        assert "## 2026-01-28 16:00 - US-001" in first_entry
        assert "What was implemented" in first_entry
        assert "Files changed" in first_entry

    def test_handles_empty_file(self) -> None:
        """Test handling file with no history entries."""
        content = """# Progress Log
## Codebase Patterns
- Pattern one
---
"""

        entries = _extract_history_entries(content)

        assert entries == []

    def test_handles_single_entry(self) -> None:
        """Test handling file with single entry."""
        content = """## 2026-01-28 16:00 - US-001
- What was implemented: Something
---
"""

        entries = _extract_history_entries(content)

        assert len(entries) == 1
        assert "US-001" in entries[0]


class TestTwoTierIntegration:
    """Integration tests verifying two-tier loading and appending."""

    def test_older_entries_remain_in_file_but_not_loaded(self) -> None:
        """Test that older entries remain in file but aren't loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "progress.txt"

            # Create file with many entries
            content = """# Progress Log
Started: Today

## Codebase Patterns
- Pattern one
---

## 2026-01-28 10:00 - US-001
- Entry 1
---

## 2026-01-28 11:00 - US-002
- Entry 2
---

## 2026-01-28 12:00 - US-003
- Entry 3
---
"""
            path.write_text(content)

            # Load with max_history=2
            context = load_learnings(path, max_history=2)

            # Only last 2 entries loaded
            assert len(context.recent_history) == 2
            history_text = "\n".join(context.recent_history)
            assert "US-002" in history_text
            assert "US-003" in history_text
            assert "US-001" not in history_text

            # But all entries still in file
            file_content = path.read_text()
            assert "US-001" in file_content
            assert "US-002" in file_content
            assert "US-003" in file_content

    def test_append_then_load_shows_new_entry(self) -> None:
        """Test that appended entries appear in subsequent loads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "progress.txt"

            # Create initial file
            content = """# Progress Log

## Codebase Patterns
---

## 2026-01-28 10:00 - US-001
- Entry 1
---
"""
            path.write_text(content)

            # Append new entry
            new_entry = """## 2026-01-28 11:00 - US-002
- Entry 2"""
            append_progress(path, new_entry)

            # Load and verify
            context = load_learnings(path)

            history_text = "\n".join(context.recent_history)
            assert "US-001" in history_text
            assert "US-002" in history_text

    def test_full_workflow_with_patterns_and_history(self) -> None:
        """Test complete workflow with patterns and history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "progress.txt"

            # Start fresh - creates template
            context = load_learnings(path)
            assert context.patterns == []
            assert context.recent_history == []

            # Manually add patterns (simulating edit)
            content = path.read_text()
            content = content.replace(
                "## Codebase Patterns\n---",
                "## Codebase Patterns\n- Use python3\n- Test everything\n---",
            )
            path.write_text(content)

            # Append history entry
            append_progress(
                path,
                """## 2026-01-28 10:00 - US-001
- Implemented feature X""",
            )

            # Load and verify
            context = load_learnings(path)

            assert len(context.patterns) == 2
            assert "- Use python3" in context.patterns[0]
            assert len(context.recent_history) == 1
            assert "US-001" in context.recent_history[0]
