"""Progress tracking module for V-Ralph.

Implements two-tier progress structure:
- Patterns section: Reusable learnings that persist across iterations
- Recent History: Last N entries for context (older entries remain but aren't loaded)
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class ProgressError(Exception):
    """Exception raised for progress-related errors."""

    pass


@dataclass
class ProgressContext:
    """Context loaded from progress file for iteration use.

    Only contains the Patterns section and last N history entries
    to avoid bloating the context window.
    """

    patterns: list[str]
    recent_history: list[str]


# Template for new progress files
PROGRESS_TEMPLATE = """# Ralph Progress Log
Started: {timestamp}

## Codebase Patterns
---

## Recent History
---
"""


def load_learnings(path: str | Path, max_history: int = 5) -> ProgressContext:
    """Load learnings from progress file with two-tier structure.

    Loads only the Patterns section and the last N Recent History entries.
    This keeps context compact while preserving important learnings.

    Args:
        path: Path to the progress.txt file.
        max_history: Maximum number of recent history entries to load (default 5).

    Returns:
        ProgressContext with patterns and recent history.

    Note:
        If file doesn't exist, creates it with template structure.
    """
    path = Path(path)

    if not path.exists():
        # Create file with template structure
        timestamp = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        content = PROGRESS_TEMPLATE.format(timestamp=timestamp)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return ProgressContext(patterns=[], recent_history=[])

    content = path.read_text()

    # Extract Patterns section
    patterns = _extract_patterns(content)

    # Extract Recent History entries (last N)
    history_entries = _extract_history_entries(content)
    recent_history = history_entries[-max_history:] if history_entries else []

    return ProgressContext(patterns=patterns, recent_history=recent_history)


def append_progress(path: str | Path, entry: str) -> None:
    """Append a new entry to the Recent History section.

    Args:
        path: Path to the progress.txt file.
        entry: The progress entry to append (should include ## header).

    Note:
        If file doesn't exist, creates it with template structure first.
    """
    path = Path(path)

    if not path.exists():
        # Create file with template structure
        timestamp = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        content = PROGRESS_TEMPLATE.format(timestamp=timestamp)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    content = path.read_text()

    # Ensure entry ends with separator
    entry = entry.strip()
    if not entry.endswith("---"):
        entry = entry + "\n---"

    # Append to file
    if not content.endswith("\n"):
        content += "\n"
    content += "\n" + entry + "\n"

    path.write_text(content)


def _extract_patterns(content: str) -> list[str]:
    """Extract patterns from the Codebase Patterns section.

    Args:
        content: Full content of progress file.

    Returns:
        List of pattern strings (lines starting with '- ').
    """
    patterns = []

    # Find Codebase Patterns section (ends at --- or next ## section)
    patterns_match = re.search(
        r"## Codebase Patterns\s*\n(.*?)(?=\n---|\n## |\Z)",
        content,
        re.DOTALL,
    )

    if patterns_match:
        section = patterns_match.group(1)
        # Extract lines starting with '- ' (bullet points, not separators like ---)
        for line in section.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                patterns.append(line)

    return patterns


def _extract_history_entries(content: str) -> list[str]:
    """Extract individual history entries from the file.

    History entries are sections starting with ## followed by a date/story ID.
    Each entry ends with '---' separator.

    Args:
        content: Full content of progress file.

    Returns:
        List of complete history entry strings.
    """
    entries = []

    # Pattern to match history entries: ## date - story_id followed by content until ---
    # Skip the Codebase Patterns section header
    entry_pattern = re.compile(
        r"(## \d{4}-\d{2}-\d{2}.*?(?=\n---|\Z))",
        re.DOTALL,
    )

    matches = entry_pattern.findall(content)
    for match in matches:
        entry = match.strip()
        if entry:
            entries.append(entry)

    return entries
