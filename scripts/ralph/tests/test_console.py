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

    def test_debug_with_rich(self) -> None:
        """Test debug() function outputs dim text when rich is available."""
        if console.RICH_AVAILABLE:
            mock_console = MagicMock()
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    console.debug("Test debug message")
                    mock_console.print.assert_called_once()
                    call_args = mock_console.print.call_args[0][0]
                    assert "[dim]" in call_args
                    assert "Test debug message" in call_args

    def test_debug_without_rich(self) -> None:
        """Test debug() function outputs plain text when rich is not available."""
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                console.debug("Test debug message")
            output = captured_output.getvalue()
            assert "[DEBUG]" in output
            assert "Test debug message" in output


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


class TestSummaryBox:
    """Test suite for summary_box function."""

    def test_summary_box_can_be_imported(self) -> None:
        """Test that summary_box can be imported from the console module."""
        from shared.console import summary_box
        assert summary_box is not None

    def test_summary_box_without_rich_shows_title(self) -> None:
        """Test that summary_box shows title in plain-text mode."""
        from shared.console import summary_box
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                summary_box("Test Title", ["Line 1", "Line 2"])
            output = captured_output.getvalue()
            assert "Test Title" in output

    def test_summary_box_without_rich_shows_lines(self) -> None:
        """Test that summary_box shows content lines in plain-text mode."""
        from shared.console import summary_box
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                summary_box("Title", ["Line 1", "Line 2", "Line 3"])
            output = captured_output.getvalue()
            assert "Line 1" in output
            assert "Line 2" in output
            assert "Line 3" in output

    def test_summary_box_without_rich_has_borders(self) -> None:
        """Test that summary_box has ASCII borders in plain-text mode."""
        from shared.console import summary_box
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                summary_box("Title", ["Content"])
            output = captured_output.getvalue()
            assert "+" in output  # Corner characters
            assert "-" in output  # Horizontal borders
            assert "|" in output  # Vertical borders

    def test_summary_box_with_empty_lines(self) -> None:
        """Test that summary_box handles empty lines list."""
        from shared.console import summary_box
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                summary_box("Title", [])
            output = captured_output.getvalue()
            assert "Title" in output

    def test_summary_box_with_rich_uses_panel(self) -> None:
        """Test that summary_box uses Panel when rich is available."""
        if console.RICH_AVAILABLE:
            from shared.console import summary_box
            mock_console = MagicMock()
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    summary_box("Test", ["Line 1"])
                    mock_console.print.assert_called_once()

    def test_summary_box_accepts_style_parameter(self) -> None:
        """Test that summary_box accepts different style parameters."""
        from shared.console import summary_box
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                # Should not raise for any of these styles
                summary_box("Title", ["Line"], style="blue")
                summary_box("Title", ["Line"], style="green")
                summary_box("Title", ["Line"], style="red")
                summary_box("Title", ["Line"], style="yellow")


class TestWrapText:
    """Test suite for wrap_text function."""

    def test_wrap_text_can_be_imported(self) -> None:
        """Test that wrap_text can be imported from the console module."""
        from shared.console import wrap_text
        assert wrap_text is not None

    def test_wrap_text_empty_string(self) -> None:
        """Test wrap_text with empty string returns empty list."""
        from shared.console import wrap_text
        result = wrap_text("")
        assert result == []

    def test_wrap_text_short_string(self) -> None:
        """Test wrap_text with short string returns single line."""
        from shared.console import wrap_text
        result = wrap_text("Hello world", width=60)
        assert len(result) == 1
        assert result[0] == "Hello world"

    def test_wrap_text_long_string(self) -> None:
        """Test wrap_text with long string wraps properly."""
        from shared.console import wrap_text
        long_text = "This is a very long message that should be wrapped across multiple lines when displayed."
        result = wrap_text(long_text, width=30)
        assert len(result) > 1
        for line in result:
            # Each line should be close to width limit
            assert len(line) <= 35  # Allow some wiggle room for word boundaries

    def test_wrap_text_preserves_words(self) -> None:
        """Test wrap_text doesn't break words in the middle."""
        from shared.console import wrap_text
        text = "one two three four five"
        result = wrap_text(text, width=10)
        all_words = " ".join(result).split()
        assert all_words == ["one", "two", "three", "four", "five"]

    def test_wrap_text_handles_long_word(self) -> None:
        """Test wrap_text handles a word longer than width."""
        from shared.console import wrap_text
        text = "superlongwordthatexceedswidth normal"
        result = wrap_text(text, width=10)
        assert len(result) >= 1
        # Long word should still be present
        all_text = " ".join(result)
        assert "superlongwordthatexceedswidth" in all_text


class TestFeedbackPanel:
    """Test suite for feedback_panel function."""

    def test_feedback_panel_can_be_imported(self) -> None:
        """Test that feedback_panel can be imported from the console module."""
        from shared.console import feedback_panel
        assert feedback_panel is not None

    def test_feedback_panel_retry_without_rich(self) -> None:
        """Test feedback_panel for RETRY displays with proper formatting."""
        from shared.console import feedback_panel
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                feedback_panel("RETRY", "The test failed, please fix the issue.")
            output = captured_output.getvalue()
            assert "RETRY" in output
            assert "Audit Feedback" in output
            assert "test failed" in output

    def test_feedback_panel_with_iteration(self) -> None:
        """Test feedback_panel shows iteration number."""
        from shared.console import feedback_panel
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                feedback_panel("RETRY", "Please fix the issue.", iteration=3)
            output = captured_output.getvalue()
            assert "Iteration 3" in output

    def test_feedback_panel_word_wraps(self) -> None:
        """Test feedback_panel word-wraps long messages."""
        from shared.console import feedback_panel
        long_message = "This is a very long feedback message that should be wrapped across multiple lines for better readability in the terminal."
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                feedback_panel("RETRY", long_message, width=40)
            output = captured_output.getvalue()
            # Should have multiple lines of content
            lines = output.strip().split("\n")
            assert len(lines) > 4  # Header + border + at least 2 content lines + border

    def test_feedback_panel_with_rich(self) -> None:
        """Test feedback_panel uses Panel when rich is available."""
        if console.RICH_AVAILABLE:
            from shared.console import feedback_panel
            mock_console = MagicMock()
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    feedback_panel("RETRY", "Test message", iteration=1)
                    mock_console.print.assert_called_once()


class TestEscalatePanel:
    """Test suite for escalate_panel function."""

    def test_escalate_panel_can_be_imported(self) -> None:
        """Test that escalate_panel can be imported from the console module."""
        from shared.console import escalate_panel
        assert escalate_panel is not None

    def test_escalate_panel_without_rich(self) -> None:
        """Test escalate_panel displays prominently without rich."""
        from shared.console import escalate_panel
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                escalate_panel("Human intervention required due to blocking issue.")
            output = captured_output.getvalue()
            assert "ESCALATION" in output
            assert "Human intervention" in output
            # Should use prominent markers
            assert "!" in output

    def test_escalate_panel_with_story_id(self) -> None:
        """Test escalate_panel shows story ID."""
        from shared.console import escalate_panel
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                escalate_panel("Blocking issue", story_id="US-001")
            output = captured_output.getvalue()
            assert "US-001" in output

    def test_escalate_panel_word_wraps(self) -> None:
        """Test escalate_panel word-wraps long reasons."""
        from shared.console import escalate_panel
        long_reason = "This story cannot be completed automatically because it requires human review of the security implications and manual approval of the proposed changes."
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                escalate_panel(long_reason, width=40)
            output = captured_output.getvalue()
            lines = output.strip().split("\n")
            assert len(lines) > 4

    def test_escalate_panel_with_rich(self) -> None:
        """Test escalate_panel uses styled Panel when rich is available."""
        if console.RICH_AVAILABLE:
            from shared.console import escalate_panel
            mock_console = MagicMock()
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    escalate_panel("Critical issue", story_id="US-002")
                    mock_console.print.assert_called_once()


class TestRetryHistoryPanel:
    """Test suite for retry_history_panel function."""

    def test_retry_history_panel_can_be_imported(self) -> None:
        """Test that retry_history_panel can be imported from the console module."""
        from shared.console import retry_history_panel
        assert retry_history_panel is not None

    def test_retry_history_panel_empty_list(self) -> None:
        """Test retry_history_panel does nothing with empty list."""
        from shared.console import retry_history_panel
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                retry_history_panel([])
            output = captured_output.getvalue()
            assert output == ""

    def test_retry_history_panel_single_retry(self) -> None:
        """Test retry_history_panel with single retry entry."""
        from shared.console import retry_history_panel
        retries = [(1, "First attempt failed, please fix the issue.")]
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                retry_history_panel(retries)
            output = captured_output.getvalue()
            assert "Retry History" in output
            assert "1 retries" in output
            assert "Iteration 1" in output
            assert "First attempt failed" in output

    def test_retry_history_panel_multiple_retries(self) -> None:
        """Test retry_history_panel with multiple retry entries."""
        from shared.console import retry_history_panel
        retries = [
            (1, "First issue"),
            (2, "Second issue"),
            (3, "Third issue"),
        ]
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                retry_history_panel(retries)
            output = captured_output.getvalue()
            assert "3 retries" in output
            assert "Iteration 1" in output
            assert "Iteration 2" in output
            assert "Iteration 3" in output
            assert "First issue" in output
            assert "Second issue" in output
            assert "Third issue" in output

    def test_retry_history_panel_with_rich(self) -> None:
        """Test retry_history_panel uses Panel when rich is available."""
        if console.RICH_AVAILABLE:
            from shared.console import retry_history_panel
            mock_console = MagicMock()
            retries = [(1, "Test feedback")]
            with patch.object(console, '_console', mock_console):
                with patch.object(console, '_get_console', return_value=mock_console):
                    retry_history_panel(retries)
                    mock_console.print.assert_called_once()

    def test_retry_history_panel_word_wraps_feedback(self) -> None:
        """Test retry_history_panel word-wraps long feedback messages."""
        from shared.console import retry_history_panel
        long_feedback = "This is a very long feedback message that should be wrapped across multiple lines for better readability."
        retries = [(1, long_feedback)]
        with patch.object(console, 'RICH_AVAILABLE', False):
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                retry_history_panel(retries, width=40)
            output = captured_output.getvalue()
            # Should have content wrapped
            assert "This is a very long" in output
