"""
Test fixtures and utilities for the Phone Records Analyzer project.
"""
import os
import tempfile
import shutil
import pytest
import logging


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    yield temp_dir

    # Clean up after test with error handling for Windows
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except (PermissionError, OSError):
        # On Windows, sometimes directories can't be deleted immediately
        pass


@pytest.fixture
def temp_file():
    """Create a temporary file for tests."""
    # Create a temporary file path without creating the file
    fd, file_path = tempfile.mkstemp()
    os.close(fd)  # Close the file descriptor immediately

    yield file_path

    # Clean up after test with error handling for Windows
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except (PermissionError, OSError):
        # On Windows, sometimes files can't be deleted immediately
        pass


@pytest.fixture
def sample_config_dict():
    """Return a sample configuration dictionary for testing."""
    return {
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": None
        },        "data": {
            "excel": {
                "required_columns": ["timestamp", "phone_number", "message_type"],
                "date_format": "%Y-%m-%d %H:%M:%S"
            },
            "repository": {
                "storage_path": "./data",
                "max_datasets": 10
            }
        },
        "analysis": {
            "cache_results": True,
            "cache_expiry_seconds": 3600
        }
    }


@pytest.fixture
def null_logger():
    """Return a logger that doesn't output anything."""
    logger = logging.getLogger("null_logger")
    logger.setLevel(logging.CRITICAL + 1)  # Set to a level higher than CRITICAL
    return logger
