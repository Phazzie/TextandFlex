"""
Statistical Utilities Module
-----------------------
Common statistical functions and utilities for analyzing phone records.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta
import time
from collections import Counter
import re

from ..logger import get_logger

logger = get_logger("statistical_utils")

# Cache for storing computed results
_result_cache = {}
_cache_expiry_seconds = 3600  # Default: 1 hour

def calculate_time_distribution(df: pd.DataFrame, date_column: str, period: str) -> Dict[str, int]:
    """Calculate the distribution of messages over a time period.

    Args:
        df: DataFrame containing phone records
        date_column: Column name containing dates/times
        period: Time period to analyze ('hour', 'day', 'month')

    Returns:
        Dictionary mapping time periods to message counts

    Raises:
        ValueError: If an invalid period is provided
    """
    if period not in ['hour', 'day', 'month']:
        raise ValueError(f"Invalid period: {period}. Must be 'hour', 'day', or 'month'")

    try:
        # Ensure date column is datetime type
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column])

        if period == 'hour':
            # Extract hour (0-23)
            distribution = df[date_column].dt.hour.value_counts().sort_index().to_dict()

            # Ensure all hours are represented
            return {hour: distribution.get(hour, 0) for hour in range(24)}

        elif period == 'day':
            # Extract day of week (0=Monday, 6=Sunday)
            distribution = df[date_column].dt.dayofweek.value_counts().sort_index().to_dict()

            # Convert to named days and ensure all days are represented
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            return {day_names[day]: distribution.get(day, 0) for day in range(7)}

        elif period == 'month':
            # Extract month (1-12)
            distribution = df[date_column].dt.month.value_counts().sort_index().to_dict()

            # Convert to named months and ensure all months are represented
            month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            return {month_names[month-1]: distribution.get(month, 0) for month in range(1, 13)}

    except Exception as e:
        logger.error(f"Error calculating time distribution: {str(e)}")
        if period == 'hour':
            return {hour: 0 for hour in range(24)}
        elif period == 'day':
            return {day: 0 for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
        elif period == 'month':
            return {month: 0 for month in ['January', 'February', 'March', 'April', 'May', 'June',
                                          'July', 'August', 'September', 'October', 'November', 'December']}

def calculate_message_frequency(df: pd.DataFrame, date_column: str, period: str) -> float:
    """Calculate the average number of messages per time period.

    Args:
        df: DataFrame containing phone records
        date_column: Column name containing dates/times
        period: Time period to analyze ('day', 'week', 'month')

    Returns:
        Average number of messages per time period

    Raises:
        ValueError: If an invalid period is provided
    """
    if period not in ['day', 'week', 'month']:
        raise ValueError(f"Invalid period: {period}. Must be 'day', 'week', or 'month'")

    try:
        # Ensure date column is datetime type
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column])

        # Get date range
        min_date = df[date_column].min()
        max_date = df[date_column].max()

        if pd.isna(min_date) or pd.isna(max_date):
            return 0.0

        # Calculate total number of periods
        if period == 'day':
            total_periods = (max_date - min_date).days + 1
        elif period == 'week':
            total_periods = ((max_date - min_date).days + 1) / 7
        elif period == 'month':
            # Calculate months between dates
            total_periods = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month + 1

        # Calculate frequency
        if total_periods > 0:
            return len(df) / total_periods
        else:
            return 0.0

    except Exception as e:
        logger.error(f"Error calculating message frequency: {str(e)}")
        return 0.0

def calculate_response_times(df: pd.DataFrame, date_column: str, type_column: str, number_column: str) -> Dict[str, float]:
    """Calculate response time statistics for conversations.

    Args:
        df: DataFrame containing phone records
        date_column: Column name containing dates/times
        type_column: Column name containing message types ('sent' or 'received')
        number_column: Column name containing phone numbers

    Returns:
        Dictionary with response time statistics
    """
    try:
        # Ensure date column is datetime type
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column])

        # Sort by date
        sorted_df = df.sort_values(by=date_column)

        # Initialize response times list
        response_times = []

        # Group by phone number
        for number, group in sorted_df.groupby(number_column):
            # Process each conversation
            prev_row = None
            for _, row in group.iterrows():
                if prev_row is not None:
                    # If previous message was sent and current is received, or vice versa
                    if (prev_row[type_column] == 'sent' and row[type_column] == 'received') or \
                       (prev_row[type_column] == 'received' and row[type_column] == 'sent'):
                        # Calculate response time in minutes
                        response_time = (row[date_column] - prev_row[date_column]).total_seconds() / 60
                        response_times.append(response_time)
                prev_row = row

        # Calculate statistics
        if response_times:
            return {
                'average_response_time': np.mean(response_times),
                'median_response_time': np.median(response_times),
                'max_response_time': np.max(response_times),
                'min_response_time': np.min(response_times)
            }
        else:
            return {
                'average_response_time': 0,
                'median_response_time': 0,
                'max_response_time': 0,
                'min_response_time': 0
            }

    except Exception as e:
        logger.error(f"Error calculating response times: {str(e)}")
        return {
            'average_response_time': 0,
            'median_response_time': 0,
            'max_response_time': 0,
            'min_response_time': 0
        }

def calculate_conversation_gaps(df: pd.DataFrame, date_column: str, number_column: str = None, gap_threshold: int = 3600) -> Dict[str, Any]:
    """Calculate gaps in conversations.

    Args:
        df: DataFrame containing phone records
        date_column: Column name containing dates/times
        number_column: Column name containing phone numbers (optional)
        gap_threshold: Minimum gap duration in seconds to be considered a gap

    Returns:
        Dictionary with gap information including indices and durations
    """
    try:
        # Ensure date column is datetime type
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column])

        # Sort by date
        sorted_df = df.sort_values(by=date_column).reset_index()

        # Initialize results
        gap_indices = []
        gap_durations = []

        # If number_column is provided, group by number
        if number_column is not None:
            # Process each contact separately
            for number, group in sorted_df.groupby(number_column):
                if len(group) <= 1:
                    continue

                # Reset index for this group
                group = group.reset_index()

                # Find gaps within this contact's messages
                for i in range(len(group) - 1):
                    time_diff = (group[date_column].iloc[i+1] - group[date_column].iloc[i]).total_seconds()
                    if time_diff >= gap_threshold:
                        gap_indices.append(group['index'].iloc[i])
                        gap_durations.append(time_diff)
        else:
            # Process the entire dataset
            for i in range(len(sorted_df) - 1):
                time_diff = (sorted_df[date_column].iloc[i+1] - sorted_df[date_column].iloc[i]).total_seconds()
                if time_diff >= gap_threshold:
                    gap_indices.append(sorted_df.index[i])
                    gap_durations.append(time_diff)

        return {
            'gap_indices': gap_indices,
            'gap_durations': gap_durations,
            'avg_gap_duration': np.mean(gap_durations) if gap_durations else 0,
            'max_gap_duration': np.max(gap_durations) if gap_durations else 0,
            'gap_count': len(gap_indices)
        }

    except Exception as e:
        logger.error(f"Error calculating conversation gaps: {str(e)}")
        return {
            'gap_indices': [],
            'gap_durations': [],
            'avg_gap_duration': 0,
            'max_gap_duration': 0,
            'gap_count': 0
        }

def calculate_contact_activity_periods(df: pd.DataFrame, date_column: str, number_column: str) -> Dict[str, Dict[str, int]]:
    """Calculate when contacts are most active.

    Args:
        df: DataFrame containing phone records
        date_column: Column name containing dates/times
        number_column: Column name containing phone numbers

    Returns:
        Dictionary mapping phone numbers to activity period counts
    """
    try:
        # Ensure date column is datetime type
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column])

        # Define time periods
        def get_period(hour):
            if 6 <= hour < 12:
                return 'morning'
            elif 12 <= hour < 18:
                return 'afternoon'
            elif 18 <= hour < 22:
                return 'evening'
            else:
                return 'night'

        # Extract hour and determine period
        df = df.copy()
        df['hour'] = df[date_column].dt.hour
        df['period'] = df['hour'].apply(get_period)

        # Group by number and period
        result = {}
        for number, group in df.groupby(number_column):
            period_counts = group['period'].value_counts().to_dict()
            # Ensure all periods are represented
            result[number] = {
                'morning': period_counts.get('morning', 0),
                'afternoon': period_counts.get('afternoon', 0),
                'evening': period_counts.get('evening', 0),
                'night': period_counts.get('night', 0)
            }

        return result

    except Exception as e:
        logger.error(f"Error calculating contact activity periods: {str(e)}")
        return {}

def calculate_word_frequency(df: pd.DataFrame, content_column: str, remove_stopwords: bool = False) -> Dict[str, int]:
    """Calculate word frequency in message content.

    Args:
        df: DataFrame containing phone records
        content_column: Column name containing message content
        remove_stopwords: Whether to remove common stopwords

    Returns:
        Dictionary mapping words to frequencies
    """
    try:
        # Combine all message content
        all_content = ' '.join(df[content_column].astype(str))

        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', all_content.lower())

        # Remove stopwords if requested
        if remove_stopwords:
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                        'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'of', 'from'}
            words = [word for word in words if word not in stopwords]

        # Count word frequencies
        word_counts = Counter(words)

        return dict(word_counts)

    except Exception as e:
        logger.error(f"Error calculating word frequency: {str(e)}")
        return {}

def get_cached_result(cache_key: str) -> Optional[Any]:
    """Get a cached result if it exists and is not expired.

    Args:
        cache_key: Key to look up in the cache

    Returns:
        Cached result or None if not found or expired
    """
    if cache_key in _result_cache:
        timestamp, result = _result_cache[cache_key]
        if time.time() - timestamp < _cache_expiry_seconds:
            return result
    return None

def cache_result(cache_key: str, result: Any) -> None:
    """Cache a result with the current timestamp.

    Args:
        cache_key: Key to store in the cache
        result: Result to cache
    """
    _result_cache[cache_key] = (time.time(), result)

def set_cache_expiry(seconds: int) -> None:
    """Set the cache expiry time.

    Args:
        seconds: Number of seconds before cache entries expire
    """
    global _cache_expiry_seconds
    _cache_expiry_seconds = seconds

def clear_cache() -> None:
    """Clear the result cache."""
    _result_cache.clear()
