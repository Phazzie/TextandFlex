"""
Tests for the logging service.
"""
import pytest
import logging
from unittest.mock import MagicMock, patch
import os

from src.presentation_layer.services.logging_service import LoggingService


class TestLoggingService:
    """Tests for the LoggingService class."""

    def test_init(self):
        """Test initializing the logging service."""
        # Act
        service = LoggingService(logger_name="test_logger")

        # Assert
        assert service.logger.name == "test_logger"
        assert service.context == {}

    def test_set_context(self):
        """Test setting context information."""
        # Arrange
        service = LoggingService(logger_name="test_logger")

        # Act
        service.set_context(component="test_component", user="test_user")

        # Assert
        assert service.context == {"component": "test_component", "user": "test_user"}

    def test_clear_context(self):
        """Test clearing context information."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.set_context(component="test_component")

        # Act
        service.clear_context()

        # Assert
        assert service.context == {}

    def test_format_context_empty(self):
        """Test formatting empty context."""
        # Arrange
        service = LoggingService(logger_name="test_logger")

        # Act
        result = service._format_context()

        # Assert
        assert result == "-"

    def test_format_context_with_global(self):
        """Test formatting context with global context."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.set_context(component="test_component")

        # Act
        result = service._format_context()

        # Assert
        assert result == "component=test_component"

    def test_format_context_with_additional(self):
        """Test formatting context with additional context."""
        # Arrange
        service = LoggingService(logger_name="test_logger")

        # Act
        result = service._format_context({"method": "test_method"})

        # Assert
        assert result == "method=test_method"

    def test_format_context_with_both(self):
        """Test formatting context with both global and additional context."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.set_context(component="test_component")

        # Act
        result = service._format_context({"method": "test_method"})

        # Assert
        assert "component=test_component" in result
        assert "method=test_method" in result

    def test_debug(self):
        """Test logging a debug message."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.logger.debug = MagicMock()

        # Act
        service.debug("Debug message", method="test_method")

        # Assert
        service.logger.debug.assert_called_once()
        args, kwargs = service.logger.debug.call_args
        assert args[0] == "Debug message"
        assert kwargs["extra"]["context"] == "method=test_method"

    def test_info(self):
        """Test logging an info message."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.logger.info = MagicMock()

        # Act
        service.info("Info message", method="test_method")

        # Assert
        service.logger.info.assert_called_once()
        args, kwargs = service.logger.info.call_args
        assert args[0] == "Info message"
        assert kwargs["extra"]["context"] == "method=test_method"

    def test_warning(self):
        """Test logging a warning message."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.logger.warning = MagicMock()

        # Act
        service.warning("Warning message", method="test_method")

        # Assert
        service.logger.warning.assert_called_once()
        args, kwargs = service.logger.warning.call_args
        assert args[0] == "Warning message"
        assert kwargs["extra"]["context"] == "method=test_method"

    def test_error(self):
        """Test logging an error message."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.logger.error = MagicMock()

        # Act
        service.error("Error message", method="test_method")

        # Assert
        service.logger.error.assert_called_once()
        args, kwargs = service.logger.error.call_args
        assert args[0] == "Error message"
        assert kwargs["extra"]["context"] == "method=test_method"

    def test_critical(self):
        """Test logging a critical message."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.logger.critical = MagicMock()

        # Act
        service.critical("Critical message", method="test_method")

        # Assert
        service.logger.critical.assert_called_once()
        args, kwargs = service.logger.critical.call_args
        assert args[0] == "Critical message"
        assert kwargs["extra"]["context"] == "method=test_method"

    def test_exception(self):
        """Test logging an exception message."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.logger.exception = MagicMock()
        exc = ValueError("Test exception")

        # Act
        service.exception("Exception message", exc, method="test_method")

        # Assert
        service.logger.exception.assert_called_once()
        args, kwargs = service.logger.exception.call_args
        assert args[0] == "Exception message"
        assert "exception_type=ValueError" in kwargs["extra"]["context"]
        assert "exception_message=Test exception" in kwargs["extra"]["context"]
        assert "method=test_method" in kwargs["extra"]["context"]

    def test_log_method_call(self):
        """Test logging a method call."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.debug = MagicMock()

        # Act
        service.log_method_call("test_method", param1="value1", param2="value2")

        # Assert
        service.debug.assert_called_once()
        args, kwargs = service.debug.call_args
        assert args[0] == "Calling test_method"
        assert kwargs["method"] == "test_method"
        # Check that params contains the expected values
        assert "param1" in str(kwargs["params"])
        assert "value1" in str(kwargs["params"])
        assert "param2" in str(kwargs["params"])
        assert "value2" in str(kwargs["params"])

    def test_log_method_return(self):
        """Test logging a method return value."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.debug = MagicMock()

        # Act
        service.log_method_return("test_method", "test_result")

        # Assert
        service.debug.assert_called_once()
        args, kwargs = service.debug.call_args
        assert args[0] == "Returning from test_method"
        assert kwargs["method"] == "test_method"
        assert kwargs["result"] == "test_result"

    def test_log_method_return_truncate(self):
        """Test logging a method return value with truncation."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.debug = MagicMock()
        long_result = "x" * 200

        # Act
        service.log_method_return("test_method", long_result)

        # Assert
        service.debug.assert_called_once()
        args, kwargs = service.debug.call_args
        assert args[0] == "Returning from test_method"
        assert kwargs["method"] == "test_method"
        assert len(kwargs["result"]) == 103  # 100 chars + "..."
        assert kwargs["result"].endswith("...")

    def test_log_method_error(self):
        """Test logging a method error."""
        # Arrange
        service = LoggingService(logger_name="test_logger")
        service.error = MagicMock()
        exc = ValueError("Test exception")

        # Act
        service.log_method_error("test_method", exc)

        # Assert
        service.error.assert_called_once()
        args, kwargs = service.error.call_args
        assert args[0] == "Error in test_method: Test exception"
        assert kwargs["method"] == "test_method"
        assert kwargs["error_type"] == "ValueError"
        assert kwargs["error_message"] == "Test exception"

    def test_log_file(self):
        """Test logging to a file."""
        # Arrange
        log_file = "test_log.log"

        # Act
        with patch('logging.FileHandler') as mock_file_handler:
            with patch('os.makedirs') as mock_makedirs:
                service = LoggingService(logger_name="test_logger", log_file=log_file)

                # Assert
                mock_file_handler.assert_called_once_with(log_file)
                mock_makedirs.assert_called_once()

                # Clean up
                if os.path.exists(log_file):
                    os.remove(log_file)
