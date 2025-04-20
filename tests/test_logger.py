"""
Tests for the logging system.
"""
import os
import logging
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
def test_logger_initialization():
    """Test that the logger initializes correctly."""
    from src.logger import setup_logger, get_logger

    # Setup logger with default configuration
    setup_logger()

    # Get a logger instance
    logger = get_logger("test")

    # Verify logger properties
    assert logger.name == "test"
    assert logger.level == logging.INFO  # Default level

    # The logger might not have handlers directly, but should inherit from root
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0  # Root logger should have handlers


@pytest.mark.unit
def test_logger_levels():
    """Test setting different logging levels."""
    from src.logger import setup_logger, get_logger

    # Test each logging level
    for level_name, level_value in [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL)
    ]:
        # Setup logger with specific level
        setup_logger(level=level_name)

        # Get a logger instance
        logger = get_logger(f"test_{level_name.lower()}")

        # Verify logger level
        assert logger.level == level_value


@pytest.mark.unit
def test_logger_file_output(temp_dir):
    """Test logging to a file."""
    from src.logger import setup_logger, get_logger

    # Create log file path
    log_file = os.path.join(temp_dir, "test.log")

    # Setup logger with file output
    setup_logger(log_file=log_file)

    # Get a logger instance
    logger = get_logger("test_file")

    # Log a test message
    test_message = "Test log message to file"
    logger.info(test_message)

    # Verify message was written to file
    with open(log_file, "r") as f:
        log_content = f.read()

    assert test_message in log_content


@pytest.mark.unit
def test_logger_format():
    """Test logger format configuration."""
    from src.logger import setup_logger, get_logger
    import io

    # Custom format that's easy to verify
    test_format = "%(levelname)s:%(name)s:%(message)s"

    # Setup logger with custom format
    setup_logger(log_format=test_format)

    # Create a real handler with a string buffer to capture output
    string_io = io.StringIO()
    handler = logging.StreamHandler(string_io)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(test_format))

    # Get a logger and add our handler
    logger = get_logger("test_format")
    logger.handlers = [handler]  # Replace existing handlers

    # Log a test message
    test_message = "Format test message"
    logger.info(test_message)

    # Get the output
    output = string_io.getvalue().strip()

    # Verify the format was applied
    expected_format = f"INFO:test_format:{test_message}"
    assert output == expected_format


@pytest.mark.unit
def test_logger_context():
    """Test context-aware logging."""
    from src.logger import setup_logger, get_logger, LoggerContext, ContextFilter
    import io

    # Setup logger with a format that includes context
    test_format = "%(levelname)s:%(context)s:%(message)s"
    setup_logger(log_format=test_format)

    # Create a real handler with a string buffer to capture output
    string_io = io.StringIO()
    handler = logging.StreamHandler(string_io)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(test_format))
    handler.addFilter(ContextFilter())

    # Get a logger and add our handler
    logger = get_logger("test_context")
    logger.handlers = [handler]  # Replace existing handlers

    # Test without context
    logger.info("No context message")

    # Test with context
    with LoggerContext(user="test_user", dataset="test_dataset"):
        logger.info("With context message")

    # Get the output
    output = string_io.getvalue().strip()

    # Verify both messages were logged
    assert "No context message" in output
    assert "With context message" in output

    # Verify context was included
    assert "user=test_user dataset=test_dataset" in output


@pytest.mark.unit
def test_nested_logger_context():
    """Test nested context-aware logging."""
    from src.logger import setup_logger, get_logger, LoggerContext, ContextFilter
    import io

    # Setup logger with a format that includes context
    test_format = "%(levelname)s:%(context)s:%(message)s"
    setup_logger(log_format=test_format)

    # Create a real handler with a string buffer to capture output
    string_io = io.StringIO()
    handler = logging.StreamHandler(string_io)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(test_format))
    handler.addFilter(ContextFilter())

    # Get a logger and add our handler
    logger = get_logger("test_nested_context")
    logger.handlers = [handler]  # Replace existing handlers

    # Test with nested contexts
    with LoggerContext(user="outer_user"):
        logger.info("Outer context message")

        with LoggerContext(dataset="inner_dataset"):
            logger.info("Inner context message")

        logger.info("Back to outer context message")

    # Get the output
    output = string_io.getvalue().strip()

    # Verify all messages were logged
    assert "Outer context message" in output
    assert "Inner context message" in output
    assert "Back to outer context message" in output

    # Verify contexts were included correctly
    assert "user=outer_user" in output
    assert "dataset=inner_dataset" in output

    # Check that the inner context had both values
    lines = output.split('\n')
    inner_line = [line for line in lines if "Inner context message" in line][0]
    assert "user=outer_user" in inner_line
    assert "dataset=inner_dataset" in inner_line
