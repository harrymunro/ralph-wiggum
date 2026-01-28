"""Git integration module for V-Ralph.

Handles committing completed work to version control.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class GitError(Exception):
    """Exception raised for git-related errors."""

    pass


@dataclass
class CommitResult:
    """Result from a git commit operation."""

    success: bool
    sha: str = ""
    error: str = ""


def commit_story(
    story_id: str,
    title: str,
    files: list[str],
    working_dir: Optional[str] = None,
) -> CommitResult:
    """Stage whitelisted files and commit with formatted message.

    Args:
        story_id: The story ID (e.g., "US-001").
        title: The story title for the commit message.
        files: Whitelist of files to stage and commit.
        working_dir: Optional working directory for git commands.

    Returns:
        CommitResult with success status and commit SHA or error.

    Note:
        Only files in the whitelist will be staged. Unrelated dirty files
        are left unstaged and uncommitted.
    """
    cwd = working_dir or "."

    # Validate files list
    if not files:
        return CommitResult(
            success=False,
            error="No files provided to commit",
        )

    # Check which whitelisted files exist and have changes
    staged_files = []
    for file_path in files:
        # Check if file exists
        full_path = Path(cwd) / file_path
        if not full_path.exists():
            continue

        # Check if file has changes (staged or unstaged)
        result = _run_git(
            ["diff", "--name-only", "HEAD", "--", file_path],
            cwd=cwd,
        )
        if result.returncode == 0 and result.stdout.strip():
            staged_files.append(file_path)
            continue

        # Also check for untracked files
        result = _run_git(
            ["ls-files", "--others", "--exclude-standard", "--", file_path],
            cwd=cwd,
        )
        if result.returncode == 0 and result.stdout.strip():
            staged_files.append(file_path)

    if not staged_files:
        return CommitResult(
            success=False,
            error="No whitelisted files have changes to commit",
        )

    # Stage only whitelisted files
    for file_path in staged_files:
        result = _run_git(["add", file_path], cwd=cwd)
        if result.returncode != 0:
            return CommitResult(
                success=False,
                error=f"Failed to stage {file_path}: {result.stderr}",
            )

    # Create commit with formatted message
    commit_message = f"feat: {story_id} - {title}"
    result = _run_git(["commit", "-m", commit_message], cwd=cwd)

    if result.returncode != 0:
        # Check if it's a "nothing to commit" situation
        if "nothing to commit" in result.stdout.lower() or "nothing to commit" in result.stderr.lower():
            return CommitResult(
                success=False,
                error="Nothing to commit - files may already be committed",
            )
        return CommitResult(
            success=False,
            error=f"Commit failed: {result.stderr or result.stdout}",
        )

    # Get the commit SHA
    sha_result = _run_git(["rev-parse", "HEAD"], cwd=cwd)
    if sha_result.returncode != 0:
        # Commit succeeded but couldn't get SHA
        return CommitResult(
            success=True,
            sha="unknown",
        )

    return CommitResult(
        success=True,
        sha=sha_result.stdout.strip(),
    )


@dataclass
class _GitResult:
    """Internal result from git command execution."""

    returncode: int
    stdout: str
    stderr: str


def _run_git(
    args: list[str],
    cwd: Optional[str] = None,
) -> _GitResult:
    """Run a git command and return the result.

    Args:
        args: Arguments to pass to git command.
        cwd: Working directory for the command.

    Returns:
        _GitResult with returncode, stdout, and stderr.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return _GitResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except subprocess.TimeoutExpired:
        return _GitResult(
            returncode=-1,
            stdout="",
            stderr="Git command timed out after 30s",
        )
    except FileNotFoundError:
        return _GitResult(
            returncode=-1,
            stdout="",
            stderr="'git' command not found in PATH",
        )
    except Exception as e:
        return _GitResult(
            returncode=-1,
            stdout="",
            stderr=f"Git error: {str(e)}",
        )


def get_staged_files(working_dir: Optional[str] = None) -> list[str]:
    """Get list of currently staged files.

    Args:
        working_dir: Optional working directory for git commands.

    Returns:
        List of staged file paths.
    """
    result = _run_git(["diff", "--cached", "--name-only"], cwd=working_dir)
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().split("\n") if f]


def get_dirty_files(working_dir: Optional[str] = None) -> list[str]:
    """Get list of modified (dirty) files in working directory.

    Args:
        working_dir: Optional working directory for git commands.

    Returns:
        List of modified file paths (both staged and unstaged).
    """
    # Get modified tracked files
    result = _run_git(["diff", "--name-only", "HEAD"], cwd=working_dir)
    files = set()
    if result.returncode == 0 and result.stdout.strip():
        files.update(f for f in result.stdout.strip().split("\n") if f)

    # Get untracked files
    result = _run_git(
        ["ls-files", "--others", "--exclude-standard"],
        cwd=working_dir,
    )
    if result.returncode == 0 and result.stdout.strip():
        files.update(f for f in result.stdout.strip().split("\n") if f)

    return list(files)


def reset_staged(working_dir: Optional[str] = None) -> bool:
    """Unstage all staged files.

    Args:
        working_dir: Optional working directory for git commands.

    Returns:
        True if reset succeeded, False otherwise.
    """
    result = _run_git(["reset", "HEAD"], cwd=working_dir)
    return result.returncode == 0
