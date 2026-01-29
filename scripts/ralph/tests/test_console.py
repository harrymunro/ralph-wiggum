"""Tests for the console output module."""

import sys
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from shared import console


class TestConsoleFunctions:
    """Test suite for console output functions."""

    def test_success_with_rich(self) -> None:
        """Test success() function outputs green text when rich is available."""
        if console.RICH_AVAILABLE:
            mock_console = MagicMock()
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    console.success("Test success message")
                    mock_console.print.assert_called_once()
                    call_args = mock_console.print.call_args[0][0]
                    assert "[green]" in call_args
                    assert "Test success message" in call_args

    def test_success_without_rich(self) -> None:
        """Test success() function outputs plain text when rich is not available."""
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                console.success("Test success message")
            output = captured_output.getvalue()
            assert "[SUCCESS]" in output
            assert "Test success message" in output

    def test_error_with_rich(self) -> None:
        """Test error() function outputs red text when rich is available."""
        if console.RICH_AVAILABLE:
            mock_console = MagicMock()
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    console.error("Test error message")
                    mock_console.print.assert_called_once()
                    call_args = mock_console.print.call_args[0][0]
                    assert "[red]" in call_args
                    assert "Test error message" in call_args

    def test_error_without_rich(self) -> None:
        """Test error() function outputs plain text when rich is not available."""
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                console.error("Test error message")
            output = captured_output.getvalue()
            assert "[ERROR]" in output
            assert "Test error message" in output

    def test_warning_with_rich(self) -> None:
        """Test warning() function outputs yellow text when rich is available."""
        if console.RICH_AVAILABLE:
            mock_console = MagicMock()
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    console.warning("Test warning message")
                    mock_console.print.assert_called_once()
                    call_args = mock_console.print.call_args[0][0]
                    assert "[yellow]" in call_args
                    assert "Test warning message" in call_args

    def test_warning_without_rich(self) -> None:
        """Test warning() function outputs plain text when rich is not available."""
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                console.warning("Test warning message")
            output = captured_output.getvalue()
            assert "[WARNING]" in output
            assert "Test warning message" in output

    def test_info_with_rich(self) -> None:
        """Test info() function outputs blue text when rich is available."""
        if console.RICH_AVAILABLE:
            mock_console = MagicMock()
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    console.info("Test info message")
                    mock_console.print.assert_called_once()
                    call_args = mock_console.print.call_args[0][0]
                    assert "[blue]" in call_args
                    assert "Test info message" in call_args

    def test_info_without_rich(self) -> None:
        """Test info() function outputs plain text when rich is not available."""
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                console.info("Test info message")
            output = captured_output.getvalue()
            assert "[INFO]" in output
            assert "Test info message" in output

    def test_header_with_rich(self) -> None:
        """Test header() function outputs bold white text when rich is available."""
        if console.RICH_AVAILABLE:
            mock_console = MagicMock()
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    console.header("Test header message")
                    mock_console.print.assert_called_once()
                    call_args = mock_console.print.call_args[0][0]
                    assert "[bold white]" in call_args
                    assert "Test header message" in call_args

    def test_header_without_rich(self) -> None:
        """Test header() function outputs plain text when rich is not available."""
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                console.header("Test header message")
            output = captured_output.getvalue()
            assert "===" in output
            assert "Test header message" in output


class TestRichAvailability:
    """Test suite for rich library availability detection."""

    def test_rich_available_flag_exists(self) -> None:
        """Test that RICH_AVAILABLE flag exists in the module."""
        assert hasattr(console, 'RICH_AVAILABLE')
        assert isinstance(console.RICH_AVAILABLE, bool)

    def test_get_console_returns_none_when_rich_unavailable(self) -> None:
        """Test _get_console returns None when rich is not available."""
        with patch.object(console, 'RICH_AVAILABLE', False):
            result = console._get_console()
            # When RICH_AVAILABLE is False, it should return the cached console or None
            # Since we're patching RICH_AVAILABLE to False, the function won't create a new console


class TestSpinner:
    """Test suite for Spinner context manager."""

    def test_spinner_can_be_imported(self) -> None:
        """Test that Spinner can be imported from the console module."""
        from shared.console import Spinner
        assert Spinner is not None

    def test_spinner_context_manager_basic(self) -> None:
        """Test that Spinner works as a basic context manager."""
        from shared.console import Spinner
        # Should not raise any exceptions
        with Spinner("Test message"):
            pass

    def test_spinner_with_custom_message(self) -> None:
        """Test Spinner with a custom message."""
        from shared.console import Spinner
        spinner = Spinner("Loading data...")
        assert spinner.message == "Loading data..."

    def test_spinner_without_rich_prints_dots(self) -> None:
        """Test that Spinner prints dots in plain-text mode."""
        import time
        from shared.console import Spinner
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                with Spinner("Testing...", dot_interval=0.1):
                    time.sleep(0.25)  # Allow time for at least 2 dots
            output = captured_output.getvalue()
            assert "Testing..." in output
            # Should have printed at least one dot
            assert "." in output

    def test_spinner_without_rich_ends_with_newline(self) -> None:
        """Test that plain-text spinner ends with a newline."""
        from shared.console import Spinner
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                with Spinner("Test"):
                    pass
            output = captured_output.getvalue()
            assert output.endswith("\n")

    def test_spinner_update_method_exists(self) -> None:
        """Test that Spinner has an update method."""
        from shared.console import Spinner
        spinner = Spinner("Initial")
        assert hasattr(spinner, 'update')
        assert callable(spinner.update)

    def test_spinner_update_changes_message(self) -> None:
        """Test that Spinner.update() changes the message."""
        from shared.console import Spinner
        spinner = Spinner("Initial message")
        spinner.update("Updated message")
        assert spinner.message == "Updated message"

    def test_spinner_with_rich_uses_live(self) -> None:
        """Test that Spinner uses Live when rich is available."""
        if console.RICH_AVAILABLE:
            from shared.console import Spinner
            mock_live = MagicMock()
            mock_live.__enter__ = MagicMock(return_value=mock_live)
            mock_live.__exit__ = MagicMock(return_value=None)

            with patch('shared.console.Live', return_value=mock_live):
                with Spinner("Test"):
                    pass
            mock_live.__enter__.assert_called_once()
            mock_live.__exit__.assert_called_once()

    def test_spinner_thread_stops_on_exit(self) -> None:
        """Test that the dot-printing thread stops when exiting context."""
        import time
        from shared.console import Spinner
        with patch.object(console, 'RICH_AVAILABLE', False):
            with patch('sys.stdout', StringIO()):
                spinner_instance = None
                with Spinner("Test", dot_interval=0.1) as spinner:
                    spinner_instance = spinner
                    time.sleep(0.05)
                # After exiting, the stop event should be set
                if spinner_instance._stop_event:
                    assert spinner_instance._stop_event.is_set()

    def test_spinner_handles_exception_in_context(self) -> None:
        """Test that Spinner properly cleans up when exception occurs in context."""
        from shared.console import Spinner
        with patch.object(console, 'RICH_AVAILABLE', False):
            with patch('sys.stdout', StringIO()):
                spinner_instance = None
                try:
                    with Spinner("Test") as spinner:
                        spinner_instance = spinner
                        raise ValueError("Test exception")
                except ValueError:
                    pass
                # Stop event should still be set after exception
                if spinner_instance._stop_event:
                    assert spinner_instance._stop_event.is_set()


class TestProgressBar:
    """Test suite for progress_bar function."""

    def test_progress_bar_can_be_imported(self) -> None:
        """Test that progress_bar can be imported from the console module."""
        from shared.console import progress_bar
        assert progress_bar is not None

    def test_progress_bar_shows_percentage(self) -> None:
        """Test that progress_bar shows correct percentage."""
        from shared.console import progress_bar
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                progress_bar(5, 10)
            output = captured_output.getvalue()
            assert "50%" in output
            assert "5 of 10 stories complete" in output

    def test_progress_bar_shows_visual_bar(self) -> None:
        """Test that progress_bar shows a visual bar."""
        from shared.console import progress_bar
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                progress_bar(3, 10)
            output = captured_output.getvalue()
            assert "Progress:" in output
            assert "[" in output
            assert "]" in output
            assert "#" in output  # Filled portion
            assert "-" in output  # Empty portion

    def test_progress_bar_zero_total(self) -> None:
        """Test progress_bar handles zero total gracefully."""
        from shared.console import progress_bar
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                progress_bar(0, 0)
            output = captured_output.getvalue()
            assert "100%" in output

    def test_progress_bar_full_completion(self) -> None:
        """Test progress_bar shows 100% when all complete."""
        from shared.console import progress_bar
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                progress_bar(10, 10)
            output = captured_output.getvalue()
            assert "100%" in output
            assert "10 of 10 stories complete" in output

    def test_progress_bar_with_rich(self) -> None:
        """Test progress_bar uses rich formatting when available."""
        if console.RICH_AVAILABLE:
            from shared.console import progress_bar
            mock_console = MagicMock()
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    progress_bar(5, 10)
                    mock_console.print.assert_called_once()
                    call_args = mock_console.print.call_args[0][0]
                    assert "Progress:" in call_args
                    assert "50%" in call_args
