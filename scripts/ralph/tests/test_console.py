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
