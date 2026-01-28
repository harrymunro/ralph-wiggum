"""PRD (Product Requirements Document) module for V-Ralph.

Handles reading, writing, and manipulating prd.yml/prd.json files.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


class PRDError(Exception):
    """Exception raised for PRD-related errors."""

    pass


@dataclass
class UserStory:
    """Represents a single user story in the PRD."""

    id: str
    title: str
    description: str
    acceptanceCriteria: list[str]
    priority: int
    passes: bool = False
    notes: str = ""
    attempts: int = 0


@dataclass
class VerificationCommands:
    """Commands used to verify the project."""

    typecheck: str = ""
    test: str = ""


@dataclass
class PRD:
    """Represents the complete PRD structure."""

    project: str
    branchName: str
    description: str
    verificationCommands: VerificationCommands
    userStories: list[UserStory] = field(default_factory=list)


def load_prd(path: str | Path) -> PRD:
    """Load and parse a PRD file (JSON or YAML).

    Args:
        path: Path to the prd.json or prd.yml file.

    Returns:
        Parsed PRD dataclass.

    Raises:
        PRDError: If file doesn't exist or is invalid.
    """
    path = Path(path)

    if not path.exists():
        raise PRDError(f"PRD file not found: {path}")

    try:
        content = path.read_text()

        # Support both JSON and YAML (JSON for now, YAML can be added later)
        if path.suffix == ".json":
            data = json.loads(content)
        elif path.suffix in (".yml", ".yaml"):
            # For YAML support, we'd need PyYAML
            # For now, try JSON parsing as fallback
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                raise PRDError(
                    f"YAML parsing not yet implemented. Use JSON format for: {path}"
                )
        else:
            # Try JSON as default
            data = json.loads(content)

        # Parse verification commands
        vc_data = data.get("verificationCommands", {})
        verification_commands = VerificationCommands(
            typecheck=vc_data.get("typecheck", ""),
            test=vc_data.get("test", ""),
        )

        # Parse user stories
        stories = []
        for story_data in data.get("userStories", []):
            story = UserStory(
                id=story_data["id"],
                title=story_data["title"],
                description=story_data["description"],
                acceptanceCriteria=story_data.get("acceptanceCriteria", []),
                priority=story_data.get("priority", 0),
                passes=story_data.get("passes", False),
                notes=story_data.get("notes", ""),
                attempts=story_data.get("attempts", 0),
            )
            stories.append(story)

        return PRD(
            project=data.get("project", ""),
            branchName=data.get("branchName", ""),
            description=data.get("description", ""),
            verificationCommands=verification_commands,
            userStories=stories,
        )

    except json.JSONDecodeError as e:
        raise PRDError(f"Invalid JSON in PRD file {path}: {e}")
    except KeyError as e:
        raise PRDError(f"Missing required field in PRD file {path}: {e}")


def save_prd(prd: PRD, path: str | Path) -> None:
    """Save a PRD to file, preserving structure.

    Args:
        prd: The PRD dataclass to save.
        path: Path to write the file to.
    """
    path = Path(path)

    # Convert to dict structure
    data = {
        "project": prd.project,
        "branchName": prd.branchName,
        "description": prd.description,
        "verificationCommands": asdict(prd.verificationCommands),
        "userStories": [asdict(story) for story in prd.userStories],
    }

    # Write with proper formatting
    content = json.dumps(data, indent=2) + "\n"
    path.write_text(content)


def get_pending_stories(prd: PRD) -> list[UserStory]:
    """Get all stories where passes is False, sorted by priority.

    Args:
        prd: The PRD to query.

    Returns:
        List of UserStory objects that haven't passed yet.
    """
    return sorted(
        [story for story in prd.userStories if not story.passes],
        key=lambda s: s.priority,
    )


def mark_story_passed(prd: PRD, story_id: str) -> bool:
    """Mark a story as passed.

    Args:
        prd: The PRD to modify.
        story_id: The ID of the story to mark as passed.

    Returns:
        True if story was found and marked, False otherwise.
    """
    for story in prd.userStories:
        if story.id == story_id:
            story.passes = True
            return True
    return False


def increment_attempts(prd: PRD, story_id: str) -> int:
    """Increment the attempt counter for a story.

    Args:
        prd: The PRD to modify.
        story_id: The ID of the story to increment.

    Returns:
        The new attempt count, or -1 if story not found.
    """
    for story in prd.userStories:
        if story.id == story_id:
            story.attempts += 1
            return story.attempts
    return -1
