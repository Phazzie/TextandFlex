"""
Data Utilities Module
----------------
Utilities for working with data in the application.
"""

import pandas as pd
from typing import Any, Optional, Union, List, Dict

def safe_get_column(df: pd.DataFrame, column_name: str, default_value: Any = None) -> pd.Series:
    """Safely access a column in a DataFrame.
    
    Args:
        df: DataFrame to access
        column_name: Name of the column to access
        default_value: Value to return if column doesn't exist
        
    Returns:
        Column series if exists, otherwise a series filled with default_value
    """
    if column_name in df.columns:
        return df[column_name]
    else:
        # Return a series of default values with the same index as the DataFrame
        return pd.Series([default_value] * len(df), index=df.index)

def safe_get_value(data: Dict[str, Any], key: str, default_value: Any = None) -> Any:
    """Safely access a value in a dictionary.
    
    Args:
        data: Dictionary to access
        key: Key to access
        default_value: Value to return if key doesn't exist
        
    Returns:
        Value if key exists, otherwise default_value
    """
    return data.get(key, default_value)

def combine_date_time(df: pd.DataFrame, date_column: str = 'date', 
                     time_column: str = 'time', 
                     format: str = '%m/%d/%Y %I:%M %p') -> pd.Series:
    """Combine date and time columns into a timestamp.
    
    Args:
        df: DataFrame containing date and time columns
        date_column: Name of the date column
        time_column: Name of the time column
        format: Format string for parsing the combined date and time
        
    Returns:
        Series of timestamps
        
    Note:
        Returns a series of NaT (Not a Time) values if either column is missing
    """
    if date_column in df.columns and time_column in df.columns:
        try:
            # Combine date and time columns
            combined = df[date_column].astype(str) + ' ' + df[time_column].astype(str)
            # Parse as datetime
            return pd.to_datetime(combined, format=format, errors='coerce')
        except Exception as e:
            # Return NaT values on error
            return pd.Series([pd.NaT] * len(df), index=df.index)
    else:
        # Return NaT values if columns don't exist
        return pd.Series([pd.NaT] * len(df), index=df.index)

def detect_excel_format(df: pd.DataFrame) -> bool:
    """Detect if the DataFrame has the Excel-specific format.
    
    Args:
        df: DataFrame to check
        
    Returns:
        True if the DataFrame has the Excel-specific format, False otherwise
    """
    return all(field in df.columns for field in ['Date', 'Time', 'To/From', 'Message Type'])

def map_excel_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map Excel-specific columns to standard column names.
    
    Args:
        df: DataFrame with Excel-specific columns
        
    Returns:
        DataFrame with standard column names
    """
    if not detect_excel_format(df):
        return df
        
    # Create a copy to avoid modifying the original
    result = df.copy()
    
    # Create timestamp column by combining Date and Time
    result['timestamp'] = combine_date_time(result, 'Date', 'Time')
    
    # Map columns to standard names
    column_mapping = {
        'Line': 'line',
        'Date': 'date',
        'Time': 'time',
        'Direction': 'direction',
        'To/From': 'phone_number',
        'Message Type': 'message_type'
    }
    
    # Rename columns
    return result.rename(columns=column_mapping)
