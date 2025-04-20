"""
Validators Module
--------------
Input validation functions for phone records data processing.

This module provides functions to validate file formats, data structures,
and content of phone records data.
"""

import os
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Set, Any

from ..logger import get_logger

logger = get_logger("validators")


def validate_file_exists(file_path: Union[str, Path]) -> None:
    """Validate that a file exists.

    Args:
        file_path: Path to the file to validate

    Raises:
        FileNotFoundError: If the file does not exist
    """
    # Convert to string for os.path functions
    path_str = str(file_path)

    # Check if file exists using os.path.isfile for better mock support
    if not os.path.isfile(path_str):
        logger.error(f"File does not exist: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")


def validate_file_extension(file_path: Union[str, Path], valid_extensions: List[str]) -> None:
    """Validate that a file has one of the specified extensions.

    Args:
        file_path: Path to the file to validate
        valid_extensions: List of valid file extensions (e.g., ['.xlsx', '.xls'])

    Raises:
        ValueError: If the file does not have a valid extension
    """
    # Extract extension from file path string for better mock support
    if isinstance(file_path, str):
        _, ext = os.path.splitext(file_path)
    else:
        ext = file_path.suffix

    # Convert to lowercase for case-insensitive comparison
    ext = ext.lower()

    if ext not in [e.lower() for e in valid_extensions]:
        logger.error(f"Invalid file extension: {ext}. Expected one of: {', '.join(valid_extensions)}")
        raise ValueError(
            f"Invalid file extension: {ext}. Expected one of: {', '.join(valid_extensions)}"
        )


def validate_excel_file(file_path: Union[str, Path]) -> None:
    """Validate that a file exists and is an Excel file.

    Args:
        file_path: Path to the file to validate

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is not an Excel file
    """
    validate_file_exists(file_path)
    validate_file_extension(file_path, ['.xlsx', '.xls'])


def validate_dataframe_columns(df: pd.DataFrame, required_columns: List[str]) -> None:
    """Validate that a DataFrame contains all required columns.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names

    Raises:
        ValueError: If the DataFrame does not contain all required columns
    """
    if df.empty:
        logger.error("DataFrame is empty")
        raise ValueError("DataFrame is empty")

    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        logger.error(f"DataFrame is missing required columns: {', '.join(missing_columns)}")
        raise ValueError(
            f"DataFrame is missing required columns: {', '.join(missing_columns)}"
        )


def validate_phone_number_format(phone_number: str) -> bool:
    """Validate that a string is a valid phone number.

    Args:
        phone_number: Phone number to validate

    Returns:
        True if the phone number is valid, False otherwise
    """
    if not phone_number:
        return False

    # Remove all non-numeric characters
    digits_only = re.sub(r'\D', '', phone_number)

    # Check if we have a reasonable number of digits
    # Most phone numbers have between 7 and 15 digits
    return 7 <= len(digits_only) <= 15


def validate_timestamp_format(timestamp: str, date_format: str) -> bool:
    """Validate that a string is a valid timestamp in the specified format.

    Args:
        timestamp: Timestamp to validate
        date_format: Expected date format (e.g., '%Y-%m-%d %H:%M:%S')

    Returns:
        True if the timestamp is valid, False otherwise
    """
    if not timestamp:
        return False

    try:
        datetime.strptime(timestamp, date_format)
        return True
    except ValueError:
        return False


def validate_message_type(message_type: str, valid_types: List[str]) -> bool:
    """Validate that a string is a valid message type.

    Args:
        message_type: Message type to validate
        valid_types: List of valid message types

    Returns:
        True if the message type is valid, False otherwise
    """
    if not message_type:
        return False

    return message_type.lower() in [t.lower() for t in valid_types]


def validate_dataframe_values(
    df: pd.DataFrame,
    timestamp_format: str,
    valid_message_types: List[str]
) -> pd.DataFrame:
    """Validate the values in a DataFrame and return a DataFrame of validation errors.

    Args:
        df: DataFrame to validate
        timestamp_format: Expected timestamp format
        valid_message_types: List of valid message types

    Returns:
        DataFrame containing rows with validation errors and a 'validation_error' column
    """
    # Create a copy of the DataFrame to avoid modifying the original
    validation_df = df.copy()

    # Add a column to track validation errors
    validation_df['validation_error'] = ''

    # Validate phone numbers
    mask = validation_df['phone_number'].apply(
        lambda x: not validate_phone_number_format(str(x)) if pd.notna(x) else True
    )
    validation_df.loc[mask, 'validation_error'] += 'Invalid phone number; '

    # Validate timestamps
    mask = validation_df['timestamp'].apply(
        lambda x: not validate_timestamp_format(str(x), timestamp_format) if pd.notna(x) else True
    )
    validation_df.loc[mask, 'validation_error'] += 'Invalid timestamp format; '

    # Validate message types
    mask = validation_df['message_type'].apply(
        lambda x: not validate_message_type(str(x), valid_message_types) if pd.notna(x) else True
    )
    validation_df.loc[mask, 'validation_error'] += 'Invalid message type; '

    # Return only rows with validation errors
    return validation_df[validation_df['validation_error'] != '']
