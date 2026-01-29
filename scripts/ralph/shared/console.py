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


def summary_box(title: str, lines: list[str], style: str = "blue") -> None:
    """Print a summary box with a title and content lines.

    Args:
        title: The title for the summary box
        lines: List of content lines to display inside the box
        style: Color style for the box (default: blue). Options: blue, green, red, yellow
    """
    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            # Join lines with newlines for the panel content
            content = "\n".join(lines)
            panel = Panel(content, title=title, border_style=style, padding=(0, 1))
            console.print(panel)
    else:
        # Plain-text fallback with ASCII box
        max_width = max(len(title) + 4, max((len(line) for line in lines), default=0) + 4)
        border = "+" + "-" * (max_width - 2) + "+"

        print(border)
        # Center the title
        title_line = f"| {title.center(max_width - 4)} |"
        print(title_line)
        print(border)
        for line in lines:
            padded_line = f"| {line.ljust(max_width - 4)} |"
            print(padded_line)
        print(border)


def wrap_text(text: str, width: int = 60) -> list[str]:
    """Wrap text to a specified width for readability.

    Args:
        text: The text to wrap
        width: Maximum line width (default: 60)

    Returns:
        List of wrapped lines
    """
    if not text:
        return []

    words = text.split()
    lines = []
    current_line: list[str] = []
    current_length = 0

    for word in words:
        word_length = len(word)
        # Check if adding this word would exceed the width
        if current_length + word_length + (1 if current_line else 0) > width:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                # Word is longer than width, add it anyway
                lines.append(word)
                current_length = 0
        else:
            current_line.append(word)
            current_length += word_length + (1 if len(current_line) > 1 else 0)

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def feedback_panel(
    feedback_type: str,
    message: str,
    iteration: int | None = None,
    width: int = 60
) -> None:
    """Display audit feedback in a distinct bordered panel.

    For RETRY feedback, displays in a yellow bordered panel.
    For other feedback types, uses blue styling.

    Args:
        feedback_type: Type of feedback (e.g., "RETRY", "INFO")
        message: The feedback message to display
        iteration: Optional iteration number for context
        width: Width for word-wrapping (default: 60)
    """
    # Word-wrap the message for readability
    wrapped_lines = wrap_text(message, width)

    # Build title with iteration if provided
    if iteration is not None:
        title = f"Audit Feedback - {feedback_type} (Iteration {iteration})"
    else:
        title = f"Audit Feedback - {feedback_type}"

    # Choose style based on feedback type
    if feedback_type.upper() == "RETRY":
        style = "yellow"
    else:
        style = "blue"

    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            content = "\n".join(wrapped_lines)
            panel = Panel(
                content,
                title=title,
                border_style=style,
                padding=(1, 2)
            )
            console.print(panel)
    else:
        # Plain-text fallback with ASCII box
        max_line_len = max(len(title) + 4, max((len(line) for line in wrapped_lines), default=0) + 4)
        border = "+" + "-" * (max_line_len - 2) + "+"

        print(border)
        print(f"| {title.center(max_line_len - 4)} |")
        print(border)
        for line in wrapped_lines:
            print(f"| {line.ljust(max_line_len - 4)} |")
        print(border)


def escalate_panel(reason: str, story_id: str | None = None, width: int = 60) -> None:
    """Display an ESCALATE reason prominently with red background styling.

    The escalation reason is displayed in a panel with red background
    to make it highly visible and indicate a critical issue.

    Args:
        reason: The reason for escalation
        story_id: Optional story ID for context
        width: Width for word-wrapping (default: 60)
    """
    # Word-wrap the reason for readability
    wrapped_lines = wrap_text(reason, width)

    # Build title
    if story_id:
        title = f"⚠ ESCALATION REQUIRED - {story_id} ⚠"
    else:
        title = "⚠ ESCALATION REQUIRED ⚠"

    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            content = "\n".join(wrapped_lines)
            # Use red background with white text for prominence
            text = Text(content, style="white on red")
            panel = Panel(
                text,
                title=f"[bold white on red]{title}[/bold white on red]",
                border_style="bold red",
                padding=(1, 2)
            )
            console.print(panel)
    else:
        # Plain-text fallback with prominent markers
        max_line_len = max(len(title) + 4, max((len(line) for line in wrapped_lines), default=0) + 4)
        border = "!" + "=" * (max_line_len - 2) + "!"

        print(border)
        print(f"! {title.center(max_line_len - 4)} !")
        print(border)
        for line in wrapped_lines:
            print(f"! {line.ljust(max_line_len - 4)} !")
        print(border)


def retry_history_panel(
    retries: list[tuple[int, str]],
    width: int = 60
) -> None:
    """Display the history of all retries in verbose mode.

    Args:
        retries: List of (iteration_number, feedback_message) tuples
        width: Width for word-wrapping (default: 60)
    """
    if not retries:
        return

    title = f"Retry History ({len(retries)} retries)"

    if RICH_AVAILABLE:
        console = _get_console()
        if console:
            # Build content with each retry entry
            content_parts = []
            for iteration, feedback in retries:
                content_parts.append(f"[bold]Iteration {iteration}:[/bold]")
                wrapped = wrap_text(feedback, width - 4)  # Account for indentation
                for line in wrapped:
                    content_parts.append(f"  {line}")
                content_parts.append("")  # Empty line between entries

            # Remove trailing empty line
            if content_parts and content_parts[-1] == "":
                content_parts.pop()

            content = "\n".join(content_parts)
            panel = Panel(
                content,
                title=title,
                border_style="dim",
                padding=(1, 2)
            )
            console.print(panel)
    else:
        # Plain-text fallback
        lines = []
        for iteration, feedback in retries:
            lines.append(f"Iteration {iteration}:")
            wrapped = wrap_text(feedback, width - 4)
            for line in wrapped:
                lines.append(f"  {line}")
            lines.append("")

        # Remove trailing empty line
        if lines and lines[-1] == "":
            lines.pop()

        max_line_len = max(len(title) + 4, max((len(line) for line in lines), default=0) + 4)
        border = "+" + "-" * (max_line_len - 2) + "+"

        print(border)
        print(f"| {title.center(max_line_len - 4)} |")
        print(border)
        for line in lines:
            print(f"| {line.ljust(max_line_len - 4)} |")
        print(border)
