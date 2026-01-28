#!/usr/bin/env python3
"""V-Ralph: V-Lifecycle Agent for autonomous code execution with semantic validation."""

import argparse
import sys
from pathlib import Path

from shared.prd import load_prd, PRDError

__version__ = "0.1.0"

# Default PRD file location
DEFAULT_PRD_PATH = Path(__file__).parent / "prd.json"


def cmd_run(args: argparse.Namespace) -> int:
    """Execute pending stories from prd.yml."""
    print("Run command not yet implemented")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Display status of all stories in a formatted table.

    Reads prd.json/prd.yml and shows:
    - Branch name from PRD
    - Table with ID, Title, Status, Attempts for each story
    - Progress summary (X/Y complete)
    """
    # Determine PRD path
    prd_path = Path(args.prd) if hasattr(args, 'prd') and args.prd else DEFAULT_PRD_PATH

    # Also try prd.yml if prd.json doesn't exist
    if not prd_path.exists() and prd_path.suffix == ".json":
        yml_path = prd_path.with_suffix(".yml")
        if yml_path.exists():
            prd_path = yml_path

    try:
        prd = load_prd(prd_path)
    except PRDError as e:
        print(f"Error: {e}")
        print(f"\nMake sure you have a prd.json or prd.yml file in the current directory,")
        print(f"or specify a path with: python v_ralph.py status --prd PATH")
        return 1

    # Display branch name
    print(f"\nProject: {prd.project}")
    print(f"Branch: {prd.branchName}")
    print()

    # Calculate column widths
    id_width = max(4, max(len(s.id) for s in prd.userStories) if prd.userStories else 4)
    title_width = min(50, max(5, max(len(s.title) for s in prd.userStories) if prd.userStories else 5))
    status_width = 9  # "escalated" is longest
    attempts_width = 8

    # Print table header
    header = f"{'ID':<{id_width}}  {'Title':<{title_width}}  {'Status':<{status_width}}  {'Attempts':<{attempts_width}}"
    print(header)
    print("-" * len(header))

    # Print each story
    passed_count = 0
    for story in prd.userStories:
        # Determine status string
        if story.passes:
            status = "pass"
            passed_count += 1
        elif hasattr(story, 'escalated') and story.escalated:
            status = "escalated"
        else:
            status = "fail"

        # Truncate title if too long
        title = story.title
        if len(title) > title_width:
            title = title[:title_width - 3] + "..."

        print(f"{story.id:<{id_width}}  {title:<{title_width}}  {status:<{status_width}}  {story.attempts:<{attempts_width}}")

    # Print summary
    total = len(prd.userStories)
    print()
    print(f"Progress: {passed_count}/{total} stories complete")

    return 0


def main() -> int:
    """Main entry point for V-Ralph CLI."""
    parser = argparse.ArgumentParser(
        prog="v_ralph",
        description="V-Ralph: V-Lifecycle Agent for autonomous code execution with semantic validation",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Execute pending stories from prd.yml")
    run_parser.set_defaults(func=cmd_run)

    # status command
    status_parser = subparsers.add_parser("status", help="Display status of all stories")
    status_parser.add_argument(
        "--prd",
        help="Path to prd.json or prd.yml file (default: prd.json in current directory)",
    )
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
