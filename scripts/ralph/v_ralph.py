#!/usr/bin/env python3
"""V-Ralph: Python CLI for the Ralph autonomous agent system.

A command-line interface for managing and executing user stories
defined in PRD (Product Requirements Document) files.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

from shared.console import (
    success, error, warning, info, header, progress_bar, debug, summary_box,
    feedback_panel, escalate_panel, retry_history_panel
)
from shared.errors import PRDNotFoundError, StoryNotFoundError, RalphError


@dataclass
class ExecutionSummary:
    """Summary statistics for a Ralph execution run.

    Tracks metrics about the execution including story counts,
    timing information, and commit details.
    """

    stories_attempted: int = 0
    stories_passed: int = 0
    stories_failed: int = 0
    total_iterations: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    files_changed: int = 0
    commits: list[str] = field(default_factory=list)
    escalated_stories: list[tuple[str, str]] = field(default_factory=list)  # (story_id, reason)

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    @property
    def elapsed_time_formatted(self) -> str:
        """Format elapsed time as human-readable string."""
        elapsed = self.elapsed_time
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        if minutes < 60:
            return f"{minutes}m {seconds}s"
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}h {minutes}m {seconds}s"

    def finish(self) -> None:
        """Mark the execution as finished."""
        self.end_time = time.time()

    def add_escalation(self, story_id: str, reason: str) -> None:
        """Record an escalated story.

        Args:
            story_id: The ID of the escalated story
            reason: The reason for escalation
        """
        self.escalated_stories.append((story_id, reason))

    def display(self) -> None:
        """Display the execution summary using console module."""
        lines = []

        # Story counts
        lines.append(f"Stories attempted: {self.stories_attempted}")
        lines.append(f"Stories passed:    {self.stories_passed}")
        lines.append(f"Stories failed:    {self.stories_failed}")
        lines.append("")

        # Timing and iterations
        lines.append(f"Total iterations:  {self.total_iterations}")
        lines.append(f"Time elapsed:      {self.elapsed_time_formatted}")
        lines.append("")

        # Files and commits
        lines.append(f"Files changed:     {self.files_changed}")
        if self.commits:
            lines.append(f"Commits made:      {len(self.commits)}")
            for sha in self.commits:
                lines.append(f"  - {sha}")
        else:
            lines.append("Commits made:      0")

        # Escalated stories
        if self.escalated_stories:
            lines.append("")
            lines.append("Escalated stories:")
            for story_id, reason in self.escalated_stories:
                lines.append(f"  - {story_id}: {reason}")

        # Determine box style based on results
        if self.stories_failed > 0 or self.escalated_stories:
            style = "red"
        elif self.stories_passed > 0:
            style = "green"
        else:
            style = "blue"

        summary_box("Execution Summary", lines, style=style)


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to a maximum length, adding ellipsis if truncated.

    Args:
        text: Text to truncate
        max_length: Maximum length (default: 500)

    Returns:
        Truncated text with ellipsis if original was longer
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def verbose_log(message: str, verbose: bool) -> None:
    """Log a message only if verbose mode is enabled.

    Args:
        message: Message to log
        verbose: Whether verbose mode is enabled
    """
    if verbose:
        info(f"[VERBOSE] {message}")


def verbose_prompt(prompt: str, verbose: bool) -> None:
    """Log a prompt in verbose mode, truncated to 500 chars.

    Args:
        prompt: The prompt text to log
        verbose: Whether verbose mode is enabled
    """
    if verbose:
        truncated = truncate_text(prompt, 500)
        info(f"[VERBOSE] Prompt ({len(prompt)} chars, showing first 500):")
        info(f"  {truncated}")


def verbose_validation_output(output: str, verbose: bool) -> None:
    """Log full validation command output in verbose mode.

    Args:
        output: The validation command output
        verbose: Whether verbose mode is enabled
    """
    if verbose:
        info("[VERBOSE] Validation output:")
        for line in output.split('\n'):
            info(f"  {line}")


def debug_log(message: str, debug_enabled: bool) -> None:
    """Log a message only if debug mode is enabled.

    Args:
        message: Message to log
        debug_enabled: Whether debug mode is enabled
    """
    if debug_enabled:
        debug(f"[DEBUG] {message}")


def debug_prompt(prompt: str, debug_enabled: bool) -> None:
    """Log a full prompt in debug mode (not truncated).

    Args:
        prompt: The prompt text to log
        debug_enabled: Whether debug mode is enabled
    """
    if debug_enabled:
        debug(f"[DEBUG] Full prompt ({len(prompt)} chars):")
        for line in prompt.split('\n'):
            debug(f"  {line}")


def debug_file_path(path: str, description: str, debug_enabled: bool) -> None:
    """Log a file path in debug mode.

    Args:
        path: The file path to log
        description: Description of what the file is
        debug_enabled: Whether debug mode is enabled
    """
    if debug_enabled:
        debug(f"[DEBUG] {description}: {path}")


def debug_environment(debug_enabled: bool) -> None:
    """Log environment information in debug mode.

    Args:
        debug_enabled: Whether debug mode is enabled
    """
    if debug_enabled:
        import platform
        debug("[DEBUG] Environment info:")
        debug(f"  Python: {sys.version}")
        debug(f"  Platform: {platform.platform()}")
        debug(f"  Working directory: {os.getcwd()}")


def display_retry_feedback(
    feedback_message: str,
    iteration: int,
    verbose: bool = False
) -> None:
    """Display RETRY audit feedback in a styled panel.

    Args:
        feedback_message: The feedback message from the auditor
        iteration: Current iteration number
        verbose: Whether verbose mode is enabled (for logging)
    """
    feedback_panel("RETRY", feedback_message, iteration=iteration)
    if verbose:
        verbose_log(f"Retry feedback received at iteration {iteration}", True)


def display_escalate_feedback(
    reason: str,
    story_id: str,
    verbose: bool = False
) -> None:
    """Display ESCALATE audit feedback prominently.

    Args:
        reason: The reason for escalation
        story_id: The ID of the story being escalated
        verbose: Whether verbose mode is enabled (for logging)
    """
    escalate_panel(reason, story_id=story_id)
    if verbose:
        verbose_log(f"Story {story_id} escalated: {reason}", True)


def display_verbose_retry_history(
    retry_history: list[tuple[int, str]],
    verbose: bool
) -> None:
    """Display the history of all retries when verbose mode is enabled.

    Args:
        retry_history: List of (iteration_number, feedback_message) tuples
        verbose: Whether verbose mode is enabled
    """
    if verbose and retry_history:
        info("")
        retry_history_panel(retry_history)


def display_error(err: RalphError) -> None:
    """Display an error with its suggestion in a consistent format.

    Args:
        err: A RalphError instance with message and suggestion
    """
    error(f"Error: {err}")
    if err.suggestion:
        info(f"Suggestion: {err.suggestion}")


@dataclass
class ValidationCheck:
    """Result of a single validation check.

    Attributes:
        name: Short name of the check
        passed: Whether the check passed
        message: Detailed message about the result
    """
    name: str
    passed: bool
    message: str


def check_prd_exists(prd_path: str) -> ValidationCheck:
    """Check if PRD file exists.

    Args:
        prd_path: Path to the PRD file

    Returns:
        ValidationCheck with result
    """
    exists = os.path.isfile(prd_path)
    if exists:
        return ValidationCheck(
            name="PRD file exists",
            passed=True,
            message=f"Found PRD at {prd_path}"
        )
    return ValidationCheck(
        name="PRD file exists",
        passed=False,
        message=f"PRD file not found at {prd_path}"
    )


def check_prd_valid_json(prd_path: str) -> Tuple[ValidationCheck, Dict[str, Any] | None]:
    """Check if PRD file contains valid JSON.

    Args:
        prd_path: Path to the PRD file

    Returns:
        Tuple of (ValidationCheck with result, parsed PRD data or None)
    """
    if not os.path.isfile(prd_path):
        return ValidationCheck(
            name="PRD is valid JSON",
            passed=False,
            message="Cannot check JSON - file does not exist"
        ), None

    try:
        with open(prd_path, 'r') as f:
            prd_data = json.load(f)
        return ValidationCheck(
            name="PRD is valid JSON",
            passed=True,
            message="PRD contains valid JSON"
        ), prd_data
    except json.JSONDecodeError as e:
        return ValidationCheck(
            name="PRD is valid JSON",
            passed=False,
            message=f"Invalid JSON: {e}"
        ), None
    except Exception as e:
        return ValidationCheck(
            name="PRD is valid JSON",
            passed=False,
            message=f"Error reading file: {e}"
        ), None


def check_git_repo_exists(prd_path: str) -> ValidationCheck:
    """Check if a git repository exists in the PRD directory or parent.

    Args:
        prd_path: Path to the PRD file (used to determine working directory)

    Returns:
        ValidationCheck with result
    """
    # Get directory containing the PRD
    prd_dir = os.path.dirname(os.path.abspath(prd_path)) or '.'

    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=prd_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return ValidationCheck(
                name="Git repository exists",
                passed=True,
                message="Git repository found"
            )
        return ValidationCheck(
            name="Git repository exists",
            passed=False,
            message="Not a git repository (or any parent)"
        )
    except FileNotFoundError:
        return ValidationCheck(
            name="Git repository exists",
            passed=False,
            message="Git command not found"
        )
    except Exception as e:
        return ValidationCheck(
            name="Git repository exists",
            passed=False,
            message=f"Error checking git: {e}"
        )


def check_verification_commands(prd_data: Dict[str, Any] | None) -> ValidationCheck:
    """Check if verification commands are set in the PRD.

    Args:
        prd_data: Parsed PRD data dictionary, or None if PRD couldn't be parsed

    Returns:
        ValidationCheck with result
    """
    if prd_data is None:
        return ValidationCheck(
            name="Verification commands set",
            passed=False,
            message="Cannot check - PRD not loaded"
        )

    verification = prd_data.get('verificationCommands', {})
    if not verification:
        return ValidationCheck(
            name="Verification commands set",
            passed=False,
            message="No verificationCommands object in PRD"
        )

    # Check for common verification commands
    expected = ['typecheck', 'test']
    found = [cmd for cmd in expected if cmd in verification]
    missing = [cmd for cmd in expected if cmd not in verification]

    if missing:
        return ValidationCheck(
            name="Verification commands set",
            passed=False,
            message=f"Missing verification commands: {', '.join(missing)}"
        )

    return ValidationCheck(
        name="Verification commands set",
        passed=True,
        message=f"Found commands: {', '.join(found)}"
    )


def display_validation_check(check: ValidationCheck) -> None:
    """Display a validation check result with checkmark or X.

    Args:
        check: The validation check to display
    """
    try:
        from shared.console import RICH_AVAILABLE, _get_console
        if RICH_AVAILABLE:
            console = _get_console()
            if check.passed:
                console.print(f"  [green]✓[/green] {check.name}: {check.message}")
            else:
                console.print(f"  [red]✗[/red] {check.name}: {check.message}")
            return
    except Exception:
        pass

    # Plain text fallback
    mark = "[OK]" if check.passed else "[FAIL]"
    info(f"  {mark} {check.name}: {check.message}")


def run_dry_run_validation(prd_path: str) -> int:
    """Run all dry-run validation checks.

    Performs comprehensive validation:
    - PRD file exists
    - PRD is valid JSON
    - Git repository exists
    - Verification commands are set

    Args:
        prd_path: Path to the PRD file

    Returns:
        Exit code: 0 if all checks pass, 1 if any fail
    """
    header("Dry-run validation")
    info("")

    checks: List[ValidationCheck] = []
    prd_data: Dict[str, Any] | None = None

    # Check 1: PRD file exists
    check1 = check_prd_exists(prd_path)
    checks.append(check1)
    display_validation_check(check1)

    # Check 2: PRD is valid JSON
    check2, prd_data = check_prd_valid_json(prd_path)
    checks.append(check2)
    display_validation_check(check2)

    # Check 3: Git repository exists
    check3 = check_git_repo_exists(prd_path)
    checks.append(check3)
    display_validation_check(check3)

    # Check 4: Verification commands are set
    check4 = check_verification_commands(prd_data)
    checks.append(check4)
    display_validation_check(check4)

    # Display summary
    info("")
    passed_count = sum(1 for c in checks if c.passed)
    total_count = len(checks)

    if passed_count == total_count:
        success(f"All {total_count} checks passed")
        return 0
    else:
        failed_count = total_count - passed_count
        error(f"{failed_count} of {total_count} checks failed")
        return 1


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


# Token estimation constants
# Approximate context window size for Claude (conservative estimate)
CONTEXT_WINDOW_TOKENS = 100000
TOKEN_WARNING_THRESHOLD = 0.50  # 50% of context window
TOKEN_ERROR_THRESHOLD = 0.80  # 80% of context window


def estimate_story_tokens(story: Dict[str, Any]) -> int:
    """Estimate the token count for a story.

    Uses a simple heuristic of word count * 1.3 to estimate tokens.
    This accounts for the fact that tokens are often smaller than words
    due to subword tokenization.

    Token count is estimated from: title + description + acceptance criteria + files whitelist

    Args:
        story: Story dictionary with title, description, acceptanceCriteria, and optionally filesWhitelist

    Returns:
        Estimated token count
    """
    text_parts = []

    # Add title
    title = story.get('title', '')
    if title:
        text_parts.append(title)

    # Add description
    description = story.get('description', '')
    if description:
        text_parts.append(description)

    # Add acceptance criteria
    criteria = story.get('acceptanceCriteria', [])
    for criterion in criteria:
        if criterion:
            text_parts.append(criterion)

    # Add files whitelist if present
    files_whitelist = story.get('filesWhitelist', [])
    for file_path in files_whitelist:
        if file_path:
            text_parts.append(file_path)

    # Combine all text
    combined_text = ' '.join(text_parts)

    # Count words and apply multiplier
    word_count = len(combined_text.split())
    estimated_tokens = int(word_count * 1.3)

    return estimated_tokens


def get_token_indicator(tokens: int) -> tuple[str, str]:
    """Get a token indicator based on percentage of context window.

    Args:
        tokens: Estimated token count

    Returns:
        Tuple of (rich_indicator, plain_indicator) strings
        - Empty strings if under warning threshold
        - Warning indicator if >= 50% of context window
        - Error indicator if >= 80% of context window
    """
    percentage = tokens / CONTEXT_WINDOW_TOKENS

    if percentage >= TOKEN_ERROR_THRESHOLD:
        return ("[red]⚠ TOO LARGE[/red]", "[!!!]")
    elif percentage >= TOKEN_WARNING_THRESHOLD:
        return ("[yellow]⚠ LARGE[/yellow]", "[!]")
    else:
        return ("", "")


# Health check constants
PATTERNS_TOKEN_WARNING_THRESHOLD = 2000
HISTORY_ENTRY_WARNING_THRESHOLD = 20


@dataclass
class ProgressFileHealth:
    """Health status of a progress.txt file.

    Attributes:
        exists: Whether the file exists
        has_patterns_section: Whether the Codebase Patterns section exists
        patterns_count: Number of patterns in the Codebase Patterns section
        patterns_tokens: Estimated token count for patterns section
        history_count: Number of history entries (## Date - StoryID sections)
        history_parseable: Whether all history entries could be parsed
        parse_errors: List of any parse errors encountered
        total_tokens: Estimated total token count for the file
    """
    exists: bool = False
    has_patterns_section: bool = False
    patterns_count: int = 0
    patterns_tokens: int = 0
    history_count: int = 0
    history_parseable: bool = True
    parse_errors: list[str] = field(default_factory=list)
    total_tokens: int = 0


def estimate_text_tokens(text: str) -> int:
    """Estimate token count for a text string.

    Uses word count * 1.3 heuristic (same as story estimation).

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    word_count = len(text.split())
    return int(word_count * 1.3)


def parse_progress_file(file_path: str) -> ProgressFileHealth:
    """Parse a progress.txt file and return health information.

    Args:
        file_path: Path to the progress.txt file

    Returns:
        ProgressFileHealth with parsed information
    """
    health = ProgressFileHealth()

    # Check if file exists
    if not os.path.isfile(file_path):
        return health

    health.exists = True

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        health.parse_errors.append(f"Could not read file: {e}")
        health.history_parseable = False
        return health

    # Estimate total tokens
    health.total_tokens = estimate_text_tokens(content)

    lines = content.split('\n')

    # Parse Codebase Patterns section
    in_patterns_section = False
    patterns_text = []
    for line in lines:
        if line.strip() == '## Codebase Patterns':
            health.has_patterns_section = True
            in_patterns_section = True
            continue
        if in_patterns_section:
            # Section ends at next ## heading or ---
            if line.startswith('## ') or line.strip() == '---':
                in_patterns_section = False
                continue
            # Count pattern lines (starting with -)
            if line.strip().startswith('- '):
                health.patterns_count += 1
            if line.strip():
                patterns_text.append(line)

    # Estimate patterns section tokens
    if patterns_text:
        health.patterns_tokens = estimate_text_tokens('\n'.join(patterns_text))

    # Parse history entries (## Date - StoryID format)
    import re
    # Match patterns like: ## 2026-01-28 - US-001
    history_pattern = re.compile(r'^## \d{4}-\d{2}-\d{2} - [A-Z]+-\d+')
    for line in lines:
        if history_pattern.match(line.strip()):
            health.history_count += 1

    return health


def display_health_check(check_name: str, passed: bool, message: str) -> None:
    """Display a health check result with checkmark or X.

    Args:
        check_name: Name of the check
        passed: Whether the check passed
        message: Message describing the result
    """
    try:
        from shared.console import RICH_AVAILABLE, _get_console
        if RICH_AVAILABLE:
            console = _get_console()
            if passed:
                console.print(f"  [green]✓[/green] {check_name}: {message}")
            else:
                console.print(f"  [red]✗[/red] {check_name}: {message}")
            return
    except Exception:
        pass

    # Plain text fallback
    mark = "[OK]" if passed else "[FAIL]"
    info(f"  {mark} {check_name}: {message}")


def display_health_warning(message: str) -> None:
    """Display a health warning.

    Args:
        message: Warning message
    """
    try:
        from shared.console import RICH_AVAILABLE, _get_console
        if RICH_AVAILABLE:
            console = _get_console()
            console.print(f"  [yellow]⚠[/yellow] {message}")
            return
    except Exception:
        pass

    # Plain text fallback
    warning(f"  [WARN] {message}")


def display_health_stat(label: str, value: str | int) -> None:
    """Display a health statistic.

    Args:
        label: Statistic label
        value: Statistic value
    """
    info(f"  {label}: {value}")


def cmd_health(args: argparse.Namespace) -> int:
    """Execute the health command to check progress.txt health.

    Checks:
    - progress.txt exists
    - Codebase Patterns section present
    - History entries parseable

    Reports:
    - Total entry count
    - Patterns count
    - Estimated token size

    Warns if:
    - Patterns section exceeds 2000 tokens
    - History has more than 20 entries

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for healthy, 1 for issues found)
    """
    # Determine progress file path (relative to PRD location)
    prd_path = args.prd
    prd_dir = os.path.dirname(os.path.abspath(prd_path)) or '.'
    progress_path = os.path.join(prd_dir, 'progress.txt')

    header("Progress File Health Check")
    info("")

    # Parse the progress file
    health = parse_progress_file(progress_path)

    issues_found = False

    # Check 1: File exists
    if health.exists:
        display_health_check("File exists", True, f"Found at {progress_path}")
    else:
        display_health_check("File exists", False, f"Not found at {progress_path}")
        issues_found = True
        # Cannot continue checks if file doesn't exist
        info("")
        error("Cannot perform further checks - file does not exist")
        return 1

    # Check 2: Patterns section present
    if health.has_patterns_section:
        display_health_check("Patterns section present", True, "Codebase Patterns section found")
    else:
        display_health_check("Patterns section present", False, "No Codebase Patterns section")
        issues_found = True

    # Check 3: History entries parseable
    if health.history_parseable:
        display_health_check("History parseable", True, f"Found {health.history_count} history entries")
    else:
        display_health_check("History parseable", False, "Parse errors encountered")
        for err in health.parse_errors:
            info(f"    - {err}")
        issues_found = True

    # Display statistics
    info("")
    header("Statistics:")
    display_health_stat("Total history entries", health.history_count)
    display_health_stat("Patterns count", health.patterns_count)
    display_health_stat("Patterns tokens (estimated)", health.patterns_tokens)
    display_health_stat("Total tokens (estimated)", health.total_tokens)

    # Check for warnings
    info("")
    header("Warnings:")
    warnings_found = False

    if health.patterns_tokens > PATTERNS_TOKEN_WARNING_THRESHOLD:
        display_health_warning(
            f"Patterns section has {health.patterns_tokens} tokens "
            f"(threshold: {PATTERNS_TOKEN_WARNING_THRESHOLD})"
        )
        warnings_found = True

    if health.history_count > HISTORY_ENTRY_WARNING_THRESHOLD:
        display_health_warning(
            f"History has {health.history_count} entries "
            f"(threshold: {HISTORY_ENTRY_WARNING_THRESHOLD})"
        )
        warnings_found = True

    if not warnings_found:
        success("  No warnings")

    # Summary
    info("")
    if issues_found:
        error("Health check found issues")
        return 1
    elif warnings_found:
        warning("Health check passed with warnings")
        return 0
    else:
        success("Health check passed")
        return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Execute the status command to show PRD status.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    prd_path = args.prd
    show_estimate = getattr(args, 'estimate', False)

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

                # Add token estimate if requested
                if show_estimate:
                    tokens = estimate_story_tokens(story)
                    rich_indicator, _ = get_token_indicator(tokens)
                    token_info = f" (~{tokens} tokens)"
                    if rich_indicator:
                        token_info = f" (~{tokens} tokens) {rich_indicator}"
                    console.print(f"  {badge} [{story_id}] P{priority}: {title}{token_info}")
                else:
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

            # Add token estimate if requested
            if show_estimate:
                tokens = estimate_story_tokens(story)
                _, plain_indicator = get_token_indicator(tokens)
                token_info = f" (~{tokens} tokens)"
                if plain_indicator:
                    token_info = f" (~{tokens} tokens) {plain_indicator}"
                info(f"  {badge} [{story_id}] P{priority}: {title}{token_info}")
            else:
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

    # Dry-run mode performs comprehensive validation and exits
    if args.dry_run:
        return run_dry_run_validation(prd_path)

    try:
        prd = load_prd(prd_path)
    except PRDNotFoundError as e:
        display_error(e)
        return 1
    except ValueError as e:
        error(f"Error: {e}")
        info("Suggestion: Check your PRD file for valid JSON syntax. Use a JSON validator tool.")
        return 1

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
    debug_enabled = getattr(args, 'debug', False)
    # Debug mode includes verbose mode
    verbose = getattr(args, 'verbose', False) or debug_enabled

    header(f"Running story: [{story_id}] {story_title}")

    # Debug mode shows environment info
    debug_environment(debug_enabled)
    debug_file_path(prd_path, "PRD file", debug_enabled)

    # Verbose mode shows additional details
    verbose_log(f"Story priority: {target_story.get('priority', 'N/A')}", verbose)
    verbose_log(f"Max retries: {args.max_retries}", verbose)

    # Debug mode shows full story details
    debug_log(f"Story description: {target_story.get('description', 'N/A')}", debug_enabled)
    if target_story.get('acceptanceCriteria'):
        debug_log("Acceptance criteria:", debug_enabled)
        for criterion in target_story.get('acceptanceCriteria', []):
            debug_log(f"  - {criterion}", debug_enabled)

    # Create execution summary to track stats
    summary = ExecutionSummary()
    summary.stories_attempted = 1

    # Placeholder for execution - in full implementation, these would be used:
    # verbose_prompt(executor_prompt, verbose) - to show truncated prompts
    # debug_prompt(executor_prompt, debug_enabled) - to show full prompts
    # verbose_validation_output(validation_result, verbose) - to show full validation output
    info("(Execution would happen here - this is a placeholder)")

    # In a real execution, these would be updated based on actual results:
    # summary.stories_passed += 1  # if story passed
    # summary.stories_failed += 1  # if story failed
    # summary.total_iterations += iteration_count
    # summary.files_changed = get_files_changed_count()
    # summary.commits.append(commit_sha)
    # summary.add_escalation(story_id, reason)  # if escalated

    # Finish and display the summary
    summary.finish()
    info("")
    summary.display()

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
    status_parser.add_argument(
        '--estimate',
        action='store_true',
        help='Show token estimates per story'
    )
    status_parser.set_defaults(func=cmd_status)

    # Health command
    health_parser = subparsers.add_parser('health', help='Check progress.txt health')
    health_parser.set_defaults(func=cmd_health)

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
    run_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output with truncated prompts and full validation output'
    )
    run_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output with full prompts, file paths, and environment info (includes verbose)'
    )
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
