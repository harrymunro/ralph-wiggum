#!/usr/bin/env python3
"""V-Ralph: V-Lifecycle Agent for autonomous code execution with semantic validation."""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from shared.prd import load_prd, save_prd, get_pending_stories, mark_story_passed, increment_attempts, PRDError, UserStory
from shared.progress import load_learnings, append_progress
from shared.git import commit_story
from micro_v.executor import execute_story, ExecutorConfig, ExecutionResult

__version__ = "0.1.0"

# Default PRD file location
DEFAULT_PRD_PATH = Path(__file__).parent / "prd.json"
DEFAULT_PROGRESS_PATH = Path(__file__).parent / "progress.txt"


def _format_progress_entry(story: UserStory, iterations: int) -> str:
    """Format a progress entry for completed story.

    Args:
        story: The completed user story.
        iterations: Number of iterations it took.

    Returns:
        Formatted progress entry string.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""## {timestamp} - {story.id}
- What was implemented: {story.title}
- Iterations: {iterations}
- **Learnings for future iterations:**
  - (Add learnings here)"""


def cmd_run(args: argparse.Namespace) -> int:
    """Execute pending stories from prd.yml.

    Returns:
        0: All requested stories completed successfully
        1: Error (file not found, etc.)
        2: Story escalated (requires human input)
    """
    # Determine paths
    prd_path = Path(args.prd) if args.prd else DEFAULT_PRD_PATH
    progress_path = Path(args.progress) if args.progress else DEFAULT_PROGRESS_PATH

    # Also try prd.yml if prd.json doesn't exist
    if not prd_path.exists() and prd_path.suffix == ".json":
        yml_path = prd_path.with_suffix(".yml")
        if yml_path.exists():
            prd_path = yml_path

    # Load PRD
    try:
        prd = load_prd(prd_path)
    except PRDError as e:
        print(f"Error: {e}")
        print(f"\nMake sure you have a prd.json or prd.yml file in the current directory,")
        print(f"or specify a path with: python v_ralph.py run --prd PATH")
        return 1

    print(f"\nProject: {prd.project}")
    print(f"Branch: {prd.branchName}")
    print()

    # Get pending stories
    pending = get_pending_stories(prd)

    # Filter to single story if --story specified
    if args.story:
        pending = [s for s in pending if s.id == args.story]
        if not pending:
            # Check if story exists but already passed
            all_stories = {s.id: s for s in prd.userStories}
            if args.story in all_stories:
                story = all_stories[args.story]
                if story.passes:
                    print(f"Story {args.story} has already passed.")
                    return 0
            print(f"Error: Story {args.story} not found in PRD")
            return 1

    if not pending:
        print("All stories have passed! Nothing to run.")
        return 0

    print(f"Found {len(pending)} pending stories:")
    for story in pending:
        print(f"  - {story.id}: {story.title}")
    print()

    # Dry run mode
    if args.dry_run:
        print("[DRY RUN] Would execute the following stories:")
        for story in pending:
            print(f"  {story.id}: {story.title}")
            print(f"    Criteria: {len(story.acceptanceCriteria)} items")
            print(f"    Attempts so far: {story.attempts}")
        return 0

    # Load learnings for context
    try:
        context = load_learnings(progress_path)
        learnings = "\n".join(context.patterns + context.recent_history)
    except Exception as e:
        print(f"Warning: Could not load learnings: {e}")
        learnings = ""

    # Build validation command
    validation_commands = []
    if prd.verificationCommands.typecheck:
        validation_commands.append(prd.verificationCommands.typecheck)
    if prd.verificationCommands.test:
        validation_commands.append(prd.verificationCommands.test)
    validation_command = " && ".join(validation_commands) if validation_commands else ""

    # Get working directory (directory containing PRD)
    working_dir = str(prd_path.parent.absolute())

    # Execute stories
    for story in pending:
        print(f"\n{'='*60}")
        print(f"Executing: {story.id} - {story.title}")
        print(f"{'='*60}")

        # Increment attempts
        increment_attempts(prd, story.id)
        save_prd(prd, prd_path)

        # Build executor config
        config = ExecutorConfig(
            max_retries=args.max_retries,
            validation_command=validation_command,
            working_dir=working_dir,
            learnings=learnings,
        )

        # Execute the story
        output = execute_story(story, config)

        if output.result == ExecutionResult.SUCCESS:
            print(f"\n[SUCCESS] {story.id} completed in {output.iterations} iterations")

            # Commit changes
            # Get list of files that may have changed (use broad pattern for now)
            files_to_commit = _get_modified_files(working_dir)
            if files_to_commit:
                commit_result = commit_story(
                    story_id=story.id,
                    title=story.title,
                    files=files_to_commit,
                    working_dir=working_dir,
                )
                if commit_result.success:
                    print(f"Committed: {commit_result.sha[:8]}")
                else:
                    print(f"Warning: Commit failed: {commit_result.error}")

            # Update PRD
            mark_story_passed(prd, story.id)
            save_prd(prd, prd_path)
            print(f"Updated PRD: {story.id} marked as passed")

            # Append progress
            entry = _format_progress_entry(story, output.iterations)
            try:
                append_progress(progress_path, entry)
                print(f"Appended progress entry")
            except Exception as e:
                print(f"Warning: Could not append progress: {e}")

        elif output.result == ExecutionResult.ESCALATED:
            print(f"\n[ESCALATED] {story.id}")
            print(f"Reason: {output.escalation_reason}")
            print(f"\nStopping execution - human input required.")
            return 2

        elif output.result == ExecutionResult.FAILED:
            print(f"\n[CIRCUIT BREAKER] {story.id} failed after {output.iterations} iterations")
            print(f"Last error: {output.last_error[:500]}..." if len(output.last_error) > 500 else f"Last error: {output.last_error}")

            # Mark as escalated (circuit breaker triggered)
            # Note: UserStory doesn't have escalated field, so we just leave passes=False
            # and continue to next story
            print(f"Moving to next story...")
            continue

    # Check if all stories passed
    remaining = get_pending_stories(prd)
    if remaining:
        print(f"\n{len(remaining)} stories still pending")
        return 0
    else:
        print(f"\nAll stories complete!")
        return 0


def _get_modified_files(working_dir: str) -> list[str]:
    """Get list of modified files in the working directory.

    Args:
        working_dir: Working directory to check.

    Returns:
        List of file paths relative to working_dir.
    """
    import subprocess

    files = []

    # Get modified tracked files
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            files.extend(f for f in result.stdout.strip().split("\n") if f)
    except Exception:
        pass

    # Get untracked files
    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            files.extend(f for f in result.stdout.strip().split("\n") if f)
    except Exception:
        pass

    return list(set(files))


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
    run_parser.add_argument(
        "--prd",
        help="Path to prd.json or prd.yml file (default: prd.json in current directory)",
    )
    run_parser.add_argument(
        "--progress",
        help="Path to progress.txt file (default: progress.txt in current directory)",
    )
    run_parser.add_argument(
        "--max-retries",
        type=int,
        default=5,
        help="Maximum retry attempts per story (default: 5)",
    )
    run_parser.add_argument(
        "--story",
        metavar="US-XXX",
        help="Run only the specified story ID",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would run without executing",
    )
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
