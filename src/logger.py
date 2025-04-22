"""
Logging Module
------------
Configures application-wide logging with context-aware capabilities.
"""

import logging
import sys
import threading
from pathlib import Path
from typing import Optional

# Thread-local storage for context data
_context_storage = threading.local()

# Default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(context)s - %(message)s'

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)


class ContextFilter(logging.Filter):
    """Filter that adds context data to log records."""

    def filter(self, record):
        # Add context data to the record
        context_data = getattr(_context_storage, 'context_data', {})
        context_str = ' '.join(f'{k}={v}' for k, v in context_data.items()) if context_data else '-'
        record.context = context_str
        return True


class LoggerContext:
    """Context manager for adding context data to logs.

    Example:
        with LoggerContext(user='john', action='login'):
            logger.info('User logged in')
    """

    def __init__(self, **kwargs):
        """Initialize with context data.

        Args:
            **kwargs: Context data as keyword arguments
        """
        self.context_data = kwargs
        self.previous_context = {}

    def __enter__(self):
        # Save previous context
        self.previous_context = getattr(_context_storage, 'context_data', {}).copy()

        # Initialize context_data if it doesn't exist
        if not hasattr(_context_storage, 'context_data'):
            _context_storage.context_data = {}

        # Update with new context data
        _context_storage.context_data.update(self.context_data)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        _context_storage.context_data = self.previous_context


def setup_logger(level: str = 'INFO', log_format: str = DEFAULT_LOG_FORMAT,
                log_file: Optional[str] = None) -> None:
    """Set up the root logger with the specified configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format string for log messages
        log_file: Path to log file (None for no file logging)
    """
    # Convert level string to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Add context filter
    context_filter = ContextFilter()
    for handler in root_logger.handlers:
        handler.addFilter(context_filter)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # Inherit level from root logger if not set
    if logger.level == 0:  # NOTSET
        root_level = logging.getLogger().level
        logger.setLevel(root_level)

    # Ensure the logger has our context filter
    has_context_filter = any(isinstance(f, ContextFilter) for f in logger.filters)
    if not has_context_filter:
        logger.addFilter(ContextFilter())

    return logger


# Initialize the root logger
setup_logger()

# Create an application-wide logger instance
app_logger = get_logger('app')
