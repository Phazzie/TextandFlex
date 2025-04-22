"""
Data Cleaner Module
----------------
Functions for cleaning and normalizing phone records data.

This module provides functions to clean and normalize data from Excel files,
including phone numbers, timestamps, message types, and message content.
"""

import re

import pandas as pd

from ..logger import get_logger

logger = get_logger("data_cleaner")


def normalize_phone_numbers(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize phone numbers in the DataFrame.

    Args:
        df: DataFrame containing phone numbers in 'phone_number' column

    Returns:
        DataFrame with normalized phone numbers
    """
    if 'phone_number' not in df.columns:
        logger.warning("Column 'phone_number' not found in DataFrame")
        return df

    # Create a copy to avoid modifying the original
    result = df.copy()

    # Function to normalize a single phone number
    def normalize_number(number):
        if pd.isna(number):
            return number

        # Convert to string if not already
        number = str(number)

        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', number)

        # If it's a valid phone number, return the digits only
        if len(digits_only) >= 7:
            return digits_only
        else:
            # Return as is if we can't normalize
            return number

    # Apply normalization to the column
    result['phone_number'] = result['phone_number'].apply(normalize_number)

    return result


def standardize_timestamps(df: pd.DataFrame, date_format: str = '%Y-%m-%d %H:%M:%S') -> pd.DataFrame:
    """Standardize timestamps in the DataFrame.

    Args:
        df: DataFrame containing timestamps in 'timestamp' column
        date_format: Format string for output timestamps

    Returns:
        DataFrame with standardized timestamps
    """
    if 'timestamp' not in df.columns:
        logger.warning("Column 'timestamp' not found in DataFrame")
        return df

    # Create a copy to avoid modifying the original
    result = df.copy()

    # Function to standardize a single timestamp
    def standardize_timestamp(timestamp):
        if pd.isna(timestamp):
            return timestamp

        try:
            # Convert to datetime using pandas' flexible parser
            dt = pd.to_datetime(timestamp)
            # Format according to the specified format
            return dt.strftime(date_format)
        except:
            # Return as is if we can't standardize
            return timestamp

    # Apply standardization to the column
    result['timestamp'] = result['timestamp'].apply(standardize_timestamp)

    return result


def normalize_message_types(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize message types in the DataFrame.

    Args:
        df: DataFrame containing message types in 'message_type' column

    Returns:
        DataFrame with normalized message types
    """
    if 'message_type' not in df.columns:
        logger.warning("Column 'message_type' not found in DataFrame")
        return df

    # Create a copy to avoid modifying the original
    result = df.copy()

    # Function to normalize a single message type
    def normalize_type(msg_type):
        if pd.isna(msg_type):
            return msg_type

        # Convert to string and lowercase
        msg_type = str(msg_type).lower()

        # Map common variations
        if msg_type in ['sent', 'outgoing', 'outbound', 'out']:
            return 'sent'
        elif msg_type in ['received', 'incoming', 'inbound', 'in']:
            return 'received'
        else:
            return msg_type

    # Apply normalization to the column
    result['message_type'] = result['message_type'].apply(normalize_type)

    return result





def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize all relevant columns in the DataFrame.

    Args:
        df: DataFrame to clean

    Returns:
        Cleaned DataFrame
    """
    result = df.copy()

    # Apply all cleaning functions
    result = normalize_phone_numbers(result)
    result = standardize_timestamps(result)
    result = normalize_message_types(result)

    # Remove rows with all NaN values
    result = result.dropna(how='all')

    # Reset index
    result = result.reset_index(drop=True)

    return result


def remove_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with invalid data.

    Args:
        df: DataFrame to clean

    Returns:
        DataFrame with invalid rows removed
    """
    result = df.copy()

    # Remove rows with invalid phone numbers (non-numeric)
    if 'phone_number' in result.columns:
        result = result[result['phone_number'].apply(
            lambda x: bool(re.match(r'^\d+$', str(x))) if pd.notna(x) else False
        )]

    # Remove rows with invalid timestamps
    if 'timestamp' in result.columns:
        result = result[result['timestamp'].apply(
            lambda x: bool(pd.to_datetime(x, errors='coerce')) if pd.notna(x) else False
        )]

    # Remove rows with invalid message types
    if 'message_type' in result.columns:
        result = result[result['message_type'].apply(
            lambda x: x.lower() in ['sent', 'received'] if pd.notna(x) else False
        )]

    # Reset index
    result = result.reset_index(drop=True)

    return result
