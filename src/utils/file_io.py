"""
File I/O Module
------------
Utilities for file input/output operations.
"""

import os
import json
import pickle
import gzip
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, BinaryIO, TextIO

from ..logger import get_logger

logger = get_logger("file_io")

def ensure_directory_exists(directory: Union[str, Path]) -> bool:
    """Ensure a directory exists, creating it if necessary.

    Args:
        directory: Directory path

    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        path = Path(directory) if isinstance(directory, str) else directory
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {str(e)}")
        return False

def save_json(data: Any, file_path: Union[str, Path]) -> bool:
    """Save data to a JSON file.

    Args:
        data: Data to save
        file_path: Path to save to

    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path) if isinstance(file_path, str) else file_path

        # Ensure directory exists
        ensure_directory_exists(path.parent)

        # Convert datetime objects to ISO format strings
        def json_serial(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(path, 'w') as f:
            json.dump(data, f, default=json_serial, indent=2)

        logger.info(f"Saved JSON to {path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {str(e)}")
        return False

def load_json(file_path: Union[str, Path]) -> Optional[Any]:
    """Load data from a JSON file.

    Args:
        file_path: Path to load from

    Returns:
        Loaded data or None if error
    """
    try:
        path = Path(file_path) if isinstance(file_path, str) else file_path

        if not path.exists():
            logger.warning(f"JSON file does not exist: {path}")
            return None

        with open(path, 'r') as f:
            data = json.load(f)

        logger.info(f"Loaded JSON from {path}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {str(e)}")
        return None

def save_pickle(data: Any, file_path: Union[str, Path]) -> bool:
    """Save data to a pickle file.

    Args:
        data: Data to save
        file_path: Path to save to

    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path) if isinstance(file_path, str) else file_path

        # Ensure directory exists
        ensure_directory_exists(path.parent)

        with open(path, 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"Saved pickle to {path}")
        return True
    except Exception as e:
        logger.error(f"Error saving pickle to {file_path}: {str(e)}")
        return False

def load_pickle(file_path: Union[str, Path]) -> Optional[Any]:
    """Load data from a pickle file.

    Args:
        file_path: Path to load from

    Returns:
        Loaded data or None if error
    """
    try:
        path = Path(file_path) if isinstance(file_path, str) else file_path

        if not path.exists():
            logger.warning(f"Pickle file does not exist: {path}")
            return None

        with open(path, 'rb') as f:
            data = pickle.load(f)

        logger.info(f"Loaded pickle from {path}")
        return data
    except Exception as e:
        logger.error(f"Error loading pickle from {file_path}: {str(e)}")
        return None


def save_compressed_pickle(data: Any, file_path: Union[str, Path]) -> bool:
    """Save data to a compressed pickle file.

    Args:
        data: Data to save
        file_path: Path to save to

    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path) if isinstance(file_path, str) else file_path

        # Ensure directory exists
        ensure_directory_exists(path.parent)

        with gzip.open(path, 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"Saved compressed pickle to {path}")
        return True
    except Exception as e:
        logger.error(f"Error saving compressed pickle to {file_path}: {str(e)}")
        return False


def load_compressed_pickle(file_path: Union[str, Path]) -> Optional[Any]:
    """Load data from a compressed pickle file.

    Args:
        file_path: Path to load from

    Returns:
        Loaded data or None if error
    """
    try:
        path = Path(file_path) if isinstance(file_path, str) else file_path

        if not path.exists():
            logger.warning(f"Compressed pickle file does not exist: {path}")
            return None

        with gzip.open(path, 'rb') as f:
            data = pickle.load(f)

        logger.info(f"Loaded compressed pickle from {path}")
        return data
    except Exception as e:
        logger.error(f"Error loading compressed pickle from {file_path}: {str(e)}")
        return None
