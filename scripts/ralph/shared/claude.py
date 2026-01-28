"""Claude CLI wrapper module for V-Ralph.

Provides a clean interface to spawn stateless Claude instances for the retry loop.
"""

import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class ClaudeResult:
    """Result from a Claude CLI invocation."""

    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False


class ClaudeError(Exception):
    """Exception raised for Claude CLI-related errors."""

    pass


def invoke_claude(
    prompt: str,
    timeout: int = 300,
    working_dir: Optional[str] = None,
) -> tuple[str, str, int]:
    """Spawn a stateless Claude CLI instance with the given prompt.

    Args:
        prompt: The prompt to send to Claude via the -p flag.
        timeout: Maximum time in seconds to wait for completion (default 300).
        working_dir: Optional working directory for the subprocess.

    Returns:
        Tuple of (stdout, stderr, exit_code).
        On timeout, returns ("", "Timeout: Process killed after {timeout}s", -1).

    Note:
        The process is fully terminated after this call returns.
        No zombie processes will be left behind.
    """
    process = None
    try:
        # Spawn claude -p with the prompt
        process = subprocess.Popen(
            ["claude", "-p", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_dir,
            text=True,
        )

        # Wait for completion with timeout
        stdout, stderr = process.communicate(timeout=timeout)

        return (stdout, stderr, process.returncode)

    except subprocess.TimeoutExpired:
        # Timeout occurred - kill the process tree
        if process is not None:
            _kill_process_tree(process)

        return ("", f"Timeout: Process killed after {timeout}s", -1)

    except FileNotFoundError:
        # Claude CLI not found
        return ("", "Error: 'claude' command not found in PATH", -1)

    except Exception as e:
        # Ensure cleanup on any other error
        if process is not None:
            _kill_process_tree(process)

        return ("", f"Error: {str(e)}", -1)


def _kill_process_tree(process: subprocess.Popen) -> None:
    """Kill a process and ensure it's fully terminated.

    Uses terminate() first for graceful shutdown, then kill() if needed.

    Args:
        process: The subprocess.Popen instance to kill.
    """
    try:
        # First try graceful termination
        process.terminate()

        try:
            # Give it a moment to terminate gracefully
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate gracefully
            process.kill()
            process.wait()  # Reap the zombie process

    except ProcessLookupError:
        # Process already terminated
        pass
    except Exception:
        # Best effort - try to kill anyway
        try:
            process.kill()
        except Exception:
            pass
