"""Console output utilities with optional rich text formatting.

Provides colored terminal output when the 'rich' library is available,
with a plain-text fallback when it is not installed.
"""

import sys
import threading
import time
from typing import Optional

# Try to import rich, fall back to plain text if not available
try:
    from rich.console import Console as RichConsole
    from rich.style import Style
    from rich.panel import Panel
    from rich.text import Text
    from rich.spinner import Spinner as RichSpinner
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Create a console instance for output
_console: Optional["RichConsole"] = None

def _get_console() -> Optional["RichConsole"]:
    """Get or create the rich console instance."""
    global _console
    if RICH_AVAILABLE and _console is None:
        _console = RichConsole()
    return _console


def success(message: str) -> None:
    """Print a success message in green.

    Args:
        message: The success message to display
    """
    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            console.print(f"[green]{message}[/green]")
    else:
        print(f"[SUCCESS] {message}")


def error(message: str) -> None:
    """Print an error message in red.

    Args:
        message: The error message to display
    """
    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            console.print(f"[red]{message}[/red]")
    else:
        print(f"[ERROR] {message}")


def warning(message: str) -> None:
    """Print a warning message in yellow.

    Args:
        message: The warning message to display
    """
    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            console.print(f"[yellow]{message}[/yellow]")
    else:
        print(f"[WARNING] {message}")


def info(message: str) -> None:
    """Print an info message in blue.

    Args:
        message: The info message to display
    """
    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            console.print(f"[blue]{message}[/blue]")
    else:
        print(f"[INFO] {message}")


def header(message: str) -> None:
    """Print a header message in bold white.

    Args:
        message: The header message to display
    """
    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            console.print(f"[bold white]{message}[/bold white]")
    else:
        print(f"=== {message} ===")


def debug(message: str) -> None:
    """Print a debug message in dim/gray color.

    Args:
        message: The debug message to display
    """
    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            console.print(f"[dim]{message}[/dim]")
    else:
        print(f"[DEBUG] {message}")


class Spinner:
    """A context manager for showing a spinner during long-running operations.

    When rich is available, displays an animated spinner. When rich is not
    available, prints dots at regular intervals to show progress.

    Usage:
        with Spinner('Loading...'):
            # do something slow
            pass
    """

    def __init__(self, message: str = "Working...", dot_interval: float = 0.5):
        """Initialize the spinner.

        Args:
            message: The message to display alongside the spinner
            dot_interval: Interval in seconds between dots in plain-text mode
        """
        self.message = message
        self.dot_interval = dot_interval
        self._live: Optional["Live"] = None
        self._stop_event: Optional[threading.Event] = None
        self._dot_thread: Optional[threading.Thread] = None

    def __enter__(self) -> "Spinner":
        """Start the spinner when entering the context."""
        if RICH_AVAILABLE:
            console = _get_console()
            if console:
                spinner = RichSpinner("dots", text=self.message)
                self._live = Live(spinner, console=console, refresh_per_second=10)
                self._live.__enter__()
        else:
            # Plain-text mode: print message and start dot printing thread
            sys.stdout.write(self.message)
            sys.stdout.flush()
            self._stop_event = threading.Event()
            self._dot_thread = threading.Thread(target=self._print_dots, daemon=True)
            self._dot_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the spinner when exiting the context."""
        if RICH_AVAILABLE and self._live:
            self._live.__exit__(exc_type, exc_val, exc_tb)
        elif self._stop_event and self._dot_thread:
            # Stop the dot printing thread
            self._stop_event.set()
            self._dot_thread.join(timeout=1.0)
            # Print newline to complete the line
            sys.stdout.write("\n")
            sys.stdout.flush()

    def _print_dots(self) -> None:
        """Print dots at regular intervals in plain-text mode."""
        while self._stop_event and not self._stop_event.is_set():
            self._stop_event.wait(timeout=self.dot_interval)
            if not self._stop_event.is_set():
                sys.stdout.write(".")
                sys.stdout.flush()

    def update(self, message: str) -> None:
        """Update the spinner message.

        Args:
            message: The new message to display
        """
        self.message = message
        if RICH_AVAILABLE and self._live:
            spinner = RichSpinner("dots", text=message)
            self._live.update(spinner)
        # In plain-text mode, we don't update the message mid-spin


def progress_bar(completed: int, total: int, width: int = 30) -> None:
    """Print a progress bar showing completion status.

    Args:
        completed: Number of completed items
        total: Total number of items
        width: Width of the progress bar in characters (default: 30)
    """
    if total == 0:
        percentage = 100.0
    else:
        percentage = (completed / total) * 100

    filled = int(width * completed / total) if total > 0 else width
    empty = width - filled

    bar_text = f"{completed} of {total} stories complete ({percentage:.0f}%)"

    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            # Create a visual progress bar with rich formatting
            filled_char = "█"
            empty_char = "░"
            bar = filled_char * filled + empty_char * empty
            if percentage == 100:
                console.print(f"[green]Progress: [{bar}] {bar_text}[/green]")
            elif percentage >= 50:
                console.print(f"[blue]Progress: [{bar}] {bar_text}[/blue]")
            else:
                console.print(f"[yellow]Progress: [{bar}] {bar_text}[/yellow]")
    else:
        # Plain-text fallback
        filled_char = "#"
        empty_char = "-"
        bar = filled_char * filled + empty_char * empty
        print(f"Progress: [{bar}] {bar_text}")
