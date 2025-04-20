"""
Basic Statistics Module
-------------------
Core statistical functions for analyzing phone records.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime

from .analysis_models import BasicStatistics, DateRangeStats, ContactStats, DurationStats, TypeStats
from .statistical_utils import (
    calculate_time_distribution,
    calculate_message_frequency,
    calculate_response_times,
    calculate_conversation_gaps,
    calculate_contact_activity_periods,
    calculate_word_frequency,
    get_cached_result,
    cache_result
)
from ..logger import get_logger
from ..config import MAX_TOP_CONTACTS

logger = get_logger("basic_statistics")

class BasicStatisticsAnalyzer:
    """Analyzer for basic statistics of phone records."""

    def __init__(self):
        """Initialize the basic statistics analyzer."""
        self.last_error = None

    def analyze(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> Tuple[Optional[BasicStatistics], str]:
        """Analyze phone records to generate basic statistics.

        Args:
            df: DataFrame containing phone records
            column_mapping: Dictionary mapping logical column names to actual column names

        Returns:
            Tuple of (BasicStatistics or None, error message)
        """
        if df is None or df.empty:
            error = "Cannot analyze empty DataFrame"
            self.last_error = error
            logger.error(error)
            return None, error

        try:
            stats = BasicStatistics(total_records=len(df))

            # Analyze date range if date column exists
            if 'date' in column_mapping and column_mapping['date'] in df.columns:
                stats.date_range = self._analyze_date_range(df, column_mapping['date'])

            # Analyze top contacts if number column exists
            if 'number' in column_mapping and column_mapping['number'] in df.columns:
                stats.top_contacts = self._analyze_top_contacts(df, column_mapping)

            # Analyze durations if duration column exists
            if 'duration' in column_mapping and column_mapping['duration'] in df.columns:
                stats.duration_stats = self._analyze_durations(df, column_mapping['duration'])

            # Analyze types if type column exists
            if 'type' in column_mapping and column_mapping['type'] in df.columns:
                stats.type_stats = self._analyze_types(df, column_mapping['type'])

            logger.info("Successfully analyzed basic statistics")
            return stats, ""

        except Exception as e:
            error = f"Error analyzing basic statistics: {str(e)}"
            self.last_error = error
            logger.error(error)
            return None, error

    def _analyze_date_range(self, df: pd.DataFrame, date_column: str) -> DateRangeStats:
        """Analyze date range statistics.

        Args:
            df: DataFrame containing phone records
            date_column: Column name containing dates

        Returns:
            DateRangeStats object
        """
        min_date = df[date_column].min()
        max_date = df[date_column].max()

        days = None
        if isinstance(min_date, pd.Timestamp) and isinstance(max_date, pd.Timestamp):
            days = (max_date - min_date).days

        return DateRangeStats(
            start=min_date,
            end=max_date,
            days=days,
            total_records=len(df)
        )

    def _analyze_top_contacts(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> List[ContactStats]:
        """Analyze top contacts statistics.

        Args:
            df: DataFrame containing phone records
            column_mapping: Dictionary mapping logical column names to actual column names

        Returns:
            List of ContactStats objects
        """
        number_column = column_mapping['number']
        contact_counts = df[number_column].value_counts().head(MAX_TOP_CONTACTS)
        total_records = len(df)

        top_contacts = []
        for number, count in contact_counts.items():
            contact_df = df[df[number_column] == number]

            first_contact = None
            last_contact = None
            if 'date' in column_mapping and column_mapping['date'] in df.columns:
                date_column = column_mapping['date']
                first_contact = contact_df[date_column].min()
                last_contact = contact_df[date_column].max()

            contact_stats = ContactStats(
                number=number,
                count=count,
                percentage=(count / total_records) * 100,
                first_contact=first_contact,
                last_contact=last_contact
            )

            top_contacts.append(contact_stats)

        return top_contacts

    def _analyze_durations(self, df: pd.DataFrame, duration_column: str) -> DurationStats:
        """Analyze duration statistics.

        Args:
            df: DataFrame containing phone records
            duration_column: Column name containing durations

        Returns:
            DurationStats object
        """
        return DurationStats(
            total=df[duration_column].sum(),
            average=df[duration_column].mean(),
            median=df[duration_column].median(),
            max=df[duration_column].max(),
            min=df[duration_column].min()
        )

    def _analyze_types(self, df: pd.DataFrame, type_column: str) -> TypeStats:
        """Analyze type statistics.

        Args:
            df: DataFrame containing phone records
            type_column: Column name containing types

        Returns:
            TypeStats object
        """
        type_counts = df[type_column].value_counts().to_dict()
        return TypeStats(types=type_counts)

    def analyze_time_distribution(self, df: pd.DataFrame, date_column: str) -> Dict[str, Dict[str, int]]:
        """Analyze time distribution of messages.

        Args:
            df: DataFrame containing phone records
            date_column: Column name containing dates/times

        Returns:
            Dictionary with hourly, daily, and monthly distributions
        """
        try:
            # Create cache key
            cache_key = f"time_distribution_{id(df)}_{date_column}"

            # Check cache first
            cached_result = get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result

            # Calculate distributions
            hourly = calculate_time_distribution(df, date_column, 'hour')
            daily = calculate_time_distribution(df, date_column, 'day')
            monthly = calculate_time_distribution(df, date_column, 'month')

            # Combine results
            result = {
                'hourly': hourly,
                'daily': daily,
                'monthly': monthly
            }

            # Cache result
            cache_result(cache_key, result)

            return result

        except Exception as e:
            error = f"Error analyzing time distribution: {str(e)}"
            self.last_error = error
            logger.error(error)
            return {}

    def analyze_message_frequency(self, df: pd.DataFrame, date_column: str) -> Dict[str, float]:
        """Analyze message frequency.

        Args:
            df: DataFrame containing phone records
            date_column: Column name containing dates/times

        Returns:
            Dictionary with daily, weekly, and monthly frequencies
        """
        try:
            # Create cache key
            cache_key = f"message_frequency_{id(df)}_{date_column}"

            # Check cache first
            cached_result = get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result

            # Calculate frequencies
            daily = calculate_message_frequency(df, date_column, 'day')
            weekly = calculate_message_frequency(df, date_column, 'week')
            monthly = calculate_message_frequency(df, date_column, 'month')

            # Combine results
            result = {
                'daily': daily,
                'weekly': weekly,
                'monthly': monthly
            }

            # Cache result
            cache_result(cache_key, result)

            return result

        except Exception as e:
            error = f"Error analyzing message frequency: {str(e)}"
            self.last_error = error
            logger.error(error)
            return {}
