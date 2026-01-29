"""Console output utilities with optional rich text formatting.

Provides colored terminal output when the 'rich' library is available,
with a plain-text fallback when it is not installed.
"""

from typing import Optional

# Try to import rich, fall back to plain text if not available
try:
    from rich.console import Console as RichConsole
    from rich.style import Style
    from rich.panel import Panel
    from rich.text import Text
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
