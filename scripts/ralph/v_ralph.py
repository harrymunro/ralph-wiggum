#!/usr/bin/env python3
"""V-Ralph: Python CLI for the Ralph autonomous agent system.

A command-line interface for managing and executing user stories
defined in PRD (Product Requirements Document) files.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from shared.console import success, error, warning, info, header, progress_bar
from shared.errors import PRDNotFoundError, StoryNotFoundError, RalphError


def display_error(err: RalphError) -> None:
    """Display an error with its suggestion in a consistent format.

    Args:
        err: A RalphError instance with message and suggestion
    """
    error(f"Error: {err}")
    if err.suggestion:
        info(f"Suggestion: {err.suggestion}")


def load_prd(prd_path: str) -> Dict[str, Any]:
    """Load and parse a PRD JSON file.

    Args:
        prd_path: Path to the PRD file

    Returns:
        Parsed PRD dictionary

    Raises:
        PRDNotFoundError: If the PRD file is not found
        ValueError: If the PRD file contains invalid JSON
    """
    try:
        with open(prd_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise PRDNotFoundError(prd_path)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in PRD file: {e}")


def save_prd(prd_path: str, prd_data: Dict[str, Any]) -> bool:
    """Save PRD data to a JSON file.

    Args:
        prd_path: Path to the PRD file
        prd_data: PRD data to save

    Returns:
        True if save was successful, False otherwise
    """
    try:
        with open(prd_path, 'w') as f:
            json.dump(prd_data, f, indent=2)
            f.write('\n')
        return True
    except Exception as e:
        error(f"Failed to save PRD: {e}")
        return False


def get_story_badge(story: Dict[str, Any]) -> str:
    """Get a colored badge string for a story's status.

    Args:
        story: Story dictionary with 'passes' field

    Returns:
        Colored badge string for the story status
    """
    if story.get('passes', False):
        return "[green]✓ PASS[/green]"
    elif story.get('notes', '').startswith('Skipped:'):
        return "[yellow]⊘ SKIP[/yellow]"
    else:
        return "[red]✗ FAIL[/red]"


def get_story_badge_plain(story: Dict[str, Any]) -> str:
    """Get a plain text badge for a story's status (when rich not available).

    Args:
        story: Story dictionary with 'passes' field

    Returns:
        Plain text badge string for the story status
    """
    if story.get('passes', False):
        return "[PASS]"
    elif story.get('notes', '').startswith('Skipped:'):
        return "[SKIP]"
    else:
        return "[FAIL]"


def cmd_status(args: argparse.Namespace) -> int:
    """Execute the status command to show PRD status.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    prd_path = args.prd
    try:
        prd = load_prd(prd_path)
    except PRDNotFoundError as e:
        display_error(e)
        return 1
    except ValueError as e:
        error(f"Error: {e}")
        info("Suggestion: Check your PRD file for valid JSON syntax. Use a JSON validator tool.")
        return 1

    # Print header
    project_name = prd.get('project', 'Unknown Project')
    header(f"Project: {project_name}")
    info(f"Branch: {prd.get('branchName', 'N/A')}")

    # Get stories
    stories = prd.get('userStories', [])
    if not stories:
        warning("No user stories found in PRD")
        return 0

    # Count stats
    total = len(stories)
    passed = sum(1 for s in stories if s.get('passes', False))
    skipped = sum(1 for s in stories if s.get('notes', '').startswith('Skipped:'))
    pending = total - passed - skipped

    # Sort stories: pending first (passes=false, not skipped), then by priority
    def story_sort_key(s: Dict[str, Any]) -> tuple:
        is_pending = not s.get('passes', False) and not s.get('notes', '').startswith('Skipped:')
        priority = s.get('priority', 999)
        return (not is_pending, priority)

    sorted_stories = sorted(stories, key=story_sort_key)

    # Print stories
    info("")
    header("User Stories:")
    info("")

    # Try to use rich for colored output
    try:
        from shared.console import RICH_AVAILABLE, _get_console
        if RICH_AVAILABLE:
            console = _get_console()
            for story in sorted_stories:
                story_id = story.get('id', 'N/A')
                title = story.get('title', 'Untitled')
                priority = story.get('priority', 'N/A')
                badge = get_story_badge(story)
                console.print(f"  {badge} [{story_id}] P{priority}: {title}")
        else:
            raise ImportError("Using plain text mode")
    except Exception:
        # Plain text fallback
        for story in sorted_stories:
            story_id = story.get('id', 'N/A')
            title = story.get('title', 'Untitled')
            priority = story.get('priority', 'N/A')
            badge = get_story_badge_plain(story)
            info(f"  {badge} [{story_id}] P{priority}: {title}")

    # Print summary
    info("")
    header("Summary:")
    if passed == total:
        success(f"  All {total} stories complete!")
    else:
        info(f"  Total: {total} | Passed: {passed} | Pending: {pending} | Skipped: {skipped}")

    # Print progress bar
    info("")
    progress_bar(passed, total)

    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Execute the run command to process stories.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error, 2 for escalation)
    """
    prd_path = args.prd
    try:
        prd = load_prd(prd_path)
    except PRDNotFoundError as e:
        display_error(e)
        return 1
    except ValueError as e:
        error(f"Error: {e}")
        info("Suggestion: Check your PRD file for valid JSON syntax. Use a JSON validator tool.")
        return 1

    if args.dry_run:
        header("Dry-run mode: validating configuration...")
        info(f"  PRD file: {prd_path}")
        info(f"  Project: {prd.get('project', 'Unknown')}")
        info(f"  Branch: {prd.get('branchName', 'N/A')}")

        stories = prd.get('userStories', [])
        pending = [s for s in stories if not s.get('passes', False)]
        info(f"  Pending stories: {len(pending)}")

        success("Dry-run validation complete")
        return 0

    # Find story to run
    stories = prd.get('userStories', [])
    target_story = None

    if args.story:
        # Run specific story
        for story in stories:
            if story.get('id') == args.story:
                target_story = story
                break
        if target_story is None:
            available_ids = [s.get('id', '') for s in stories if s.get('id')]
            err = StoryNotFoundError(args.story, available_ids)
            display_error(err)
            return 1
    else:
        # Find next pending story by priority
        pending = [s for s in stories if not s.get('passes', False) and not s.get('notes', '').startswith('Skipped:')]
        pending.sort(key=lambda s: s.get('priority', 999))
        if pending:
            target_story = pending[0]

    if target_story is None:
        success("All stories are complete!")
        return 0

    story_id = target_story.get('id', 'N/A')
    story_title = target_story.get('title', 'Untitled')

    header(f"Running story: [{story_id}] {story_title}")
    info("(Execution would happen here - this is a placeholder)")

    return 0


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        prog='v_ralph',
        description='V-Ralph: Python CLI for the Ralph autonomous agent system'
    )
    parser.add_argument(
        '--prd',
        default='prd.json',
        help='Path to PRD file (default: prd.json)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show PRD status')
    status_parser.set_defaults(func=cmd_status)

    # Run command
    run_parser = subparsers.add_parser('run', help='Run stories')
    run_parser.add_argument(
        '--story',
        help='Specific story ID to run'
    )
    run_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration without executing'
    )
    run_parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts per story (default: 3)'
    )
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
