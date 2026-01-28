"""Micro-V executor loop module for V-Ralph.

Implements the core retry loop that writes code and runs validation.
This version does not include the semantic auditor (added in US-008/009).
"""

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from shared.claude import invoke_claude
from shared.prd import UserStory


class ExecutionResult(Enum):
    """Possible outcomes of story execution."""

    SUCCESS = "success"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class ExecutorConfig:
    """Configuration for the executor."""

    max_retries: int = 5
    validation_command: str = ""
    working_dir: str = "."
    coder_prompt_path: str = "micro_v/prompts/coder.md"
    learnings: str = ""
    files_whitelist: list[str] | None = None
    claude_timeout: int = 300


@dataclass
class ExecutionOutput:
    """Result from executing a story."""

    result: ExecutionResult
    story_id: str
    iterations: int
    last_error: str = ""
    escalation_reason: str = ""


def _log(message: str) -> None:
    """Log a message to the terminal."""
    print(f"[executor] {message}")


def _load_coder_prompt(path: str) -> str:
    """Load the coder prompt template from file.

    Args:
        path: Path to the coder.md prompt file.

    Returns:
        The prompt template string.

    Raises:
        FileNotFoundError: If the prompt file doesn't exist.
    """
    prompt_path = Path(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Coder prompt not found: {path}")
    return prompt_path.read_text()


def _format_prompt(
    template: str,
    story: UserStory,
    learnings: str,
    files_whitelist: list[str] | None,
    error_context: str = "",
) -> str:
    """Format the coder prompt with story details.

    Args:
        template: The prompt template string.
        story: The user story to implement.
        learnings: Previous learnings from progress.txt.
        files_whitelist: List of files the coder may edit.
        error_context: Optional error from previous iteration.

    Returns:
        The formatted prompt string.
    """
    # Build goal
    goal = f"{story.id}: {story.title}\n\n{story.description}"
    if error_context:
        goal += f"\n\n## Previous Iteration Failed\n\nThe previous attempt failed validation with the following error:\n\n```\n{error_context}\n```\n\nPlease fix the issues and try again."

    # Build criteria
    criteria = "\n".join(f"- {c}" for c in story.acceptanceCriteria)

    # Build files whitelist
    files = "(No whitelist specified - use judgment)" if files_whitelist is None else "\n".join(f"- {f}" for f in files_whitelist)

    # Build learnings
    learnings_text = learnings if learnings else "(No previous learnings available)"

    # Replace placeholders
    result = template.replace("{{goal}}", goal)
    result = result.replace("{{criteria}}", criteria)
    result = result.replace("{{files}}", files)
    result = result.replace("{{learnings}}", learnings_text)

    return result


def _run_validation(command: str, working_dir: str) -> tuple[bool, str]:
    """Run the validation command.

    Args:
        command: The shell command to run.
        working_dir: Working directory for the command.

    Returns:
        Tuple of (success, output_or_error).
    """
    if not command:
        _log("No validation command specified, skipping validation")
        return True, ""

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout for validation
        )

        output = result.stdout + result.stderr

        if result.returncode == 0:
            return True, output
        else:
            return False, output

    except subprocess.TimeoutExpired:
        return False, "Validation command timed out after 120s"
    except Exception as e:
        return False, f"Validation command failed: {str(e)}"


def execute_story(
    story: UserStory,
    config: ExecutorConfig,
) -> ExecutionOutput:
    """Execute a user story with the retry loop.

    Implements the core micro-V loop:
    1. Invoke coder via claude -p
    2. Run validation_command
    3. Check result
    4. On failure: retry with error context
    5. Stop after max_retries (circuit breaker)

    Args:
        story: The user story to implement.
        config: Executor configuration.

    Returns:
        ExecutionOutput with result status and metadata.
    """
    _log(f"Starting execution of {story.id}: {story.title}")
    _log(f"Max retries: {config.max_retries}")

    # Load the coder prompt template
    try:
        template = _load_coder_prompt(config.coder_prompt_path)
    except FileNotFoundError as e:
        _log(f"Error: {e}")
        return ExecutionOutput(
            result=ExecutionResult.FAILED,
            story_id=story.id,
            iterations=0,
            last_error=str(e),
        )

    error_context = ""
    iterations = 0

    for attempt in range(1, config.max_retries + 1):
        iterations = attempt
        _log(f"--- Iteration {attempt}/{config.max_retries} ---")

        # Format the prompt with any error context from previous iteration
        prompt = _format_prompt(
            template=template,
            story=story,
            learnings=config.learnings,
            files_whitelist=config.files_whitelist,
            error_context=error_context,
        )

        # Invoke Claude coder
        _log("Invoking coder...")
        stdout, stderr, exit_code = invoke_claude(
            prompt=prompt,
            timeout=config.claude_timeout,
            working_dir=config.working_dir,
        )

        if exit_code != 0:
            _log(f"Coder invocation failed (exit code {exit_code})")
            error_context = stderr if stderr else "Claude invocation failed"
            _log(f"Error: {error_context}")
            continue

        _log("Coder completed successfully")

        # Run validation
        _log(f"Running validation: {config.validation_command}")
        validation_passed, validation_output = _run_validation(
            config.validation_command,
            config.working_dir,
        )

        if validation_passed:
            _log("Validation PASSED")
            return ExecutionOutput(
                result=ExecutionResult.SUCCESS,
                story_id=story.id,
                iterations=iterations,
            )
        else:
            _log("Validation FAILED")
            _log(f"Output: {validation_output[:500]}...")  # Truncate for logging
            error_context = validation_output

    # Circuit breaker triggered
    _log(f"Circuit breaker: max retries ({config.max_retries}) exceeded")
    return ExecutionOutput(
        result=ExecutionResult.FAILED,
        story_id=story.id,
        iterations=iterations,
        last_error=error_context,
    )
