"""
Query Engine Module
---------------
Provides querying capabilities for phone record datasets.
"""

import pandas as pd
from typing import Dict, List, Optional, Union, Any, Callable
from datetime import datetime, date
import re

from ..logger import get_logger
from .repository import PhoneRecordRepository
from .exceptions import DateParseError, ColumnNotFoundError, QueryError

logger = get_logger("query_engine")

class QueryBuilder:
    """Builder for constructing complex queries."""

    def __init__(self):
        """Initialize the query builder."""
        self.filters = []
        self.sorters = []

    def filter_by_phone_number(self, phone_number: str):
        """Filter by phone number.

        Args:
            phone_number: Phone number to filter by

        Returns:
            Self for method chaining
        """
        self.filters.append(lambda df: df[df['phone_number'] == phone_number])
        return self

    def filter_by_date_range(self, start_date: str, end_date: Optional[str] = None):
        """Filter by date range.

        Args:
            start_date: Start date (inclusive) in format YYYY-MM-DD or any format parseable by pandas
            end_date: End date (inclusive, defaults to start_date if None) in format YYYY-MM-DD

        Returns:
            Self for method chaining

        Note:
            This method handles date conversion errors gracefully and will return an empty
            DataFrame if the dates cannot be parsed or if the timestamp column doesn't exist.
        """
        if end_date is None:
            end_date = start_date

        def date_filter(df):
            try:
                # Check if timestamp column exists
                if 'timestamp' not in df.columns:
                    error = ColumnNotFoundError('timestamp')
                    logger.error(str(error))
                    return df.iloc[0:0]  # Return empty DataFrame with same columns

                # Convert timestamp column to datetime if it's not already
                if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                    df_copy = df.copy()
                    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'], errors='coerce')
                else:
                    df_copy = df

                # Check for NaT values after conversion
                if df_copy['timestamp'].isna().any():
                    logger.warning("Some timestamp values could not be converted to datetime")

                # Extract date component
                dates = df_copy['timestamp'].dt.date

                # Convert start_date and end_date to date objects if they're strings
                try:
                    start = pd.to_datetime(start_date).date() if isinstance(start_date, str) else start_date
                except Exception as e:
                    error = DateParseError(start_date, e)
                    logger.error(str(error))
                    return df.iloc[0:0]  # Return empty DataFrame with same columns

                try:
                    end = pd.to_datetime(end_date).date() if isinstance(end_date, str) else end_date
                except Exception as e:
                    error = DateParseError(end_date, e)
                    logger.error(str(error))
                    return df.iloc[0:0]  # Return empty DataFrame with same columns

                # Filter by date range
                mask = (dates >= start) & (dates <= end)
                return df[mask]
            except Exception as e:
                error = QueryError(f"Error filtering by date range: {str(e)}")
                logger.error(str(error))
                return df.iloc[0:0]  # Return empty DataFrame with same columns

        self.filters.append(date_filter)
        return self

    def filter_by_message_type(self, message_type: str):
        """Filter by message type.

        Args:
            message_type: Message type to filter by

        Returns:
            Self for method chaining
        """
        self.filters.append(lambda df: df[df['message_type'] == message_type])
        return self

    def filter_by_content(self, content: str, case_sensitive: bool = False):
        """Filter by message content.

        Args:
            content: Content to search for
            case_sensitive: Whether to perform case-sensitive search

        Returns:
            Self for method chaining
        """
        if case_sensitive:
            self.filters.append(lambda df: df[df['message_content'].str.contains(content, na=False)])
        else:
            self.filters.append(lambda df: df[df['message_content'].str.contains(content, case=False, na=False)])
        return self

    def sort_by_timestamp(self, ascending: bool = True):
        """Sort by timestamp.

        Args:
            ascending: Whether to sort in ascending order

        Returns:
            Self for method chaining
        """
        self.sorters.append(lambda df: df.sort_values('timestamp', ascending=ascending))
        return self

    def execute(self, dataset_name: str, repository: Optional[PhoneRecordRepository] = None) -> pd.DataFrame:
        """Execute the query.

        Args:
            dataset_name: Name of the dataset to query
            repository: Repository to use (required if not provided to QueryEngine)

        Returns:
            Filtered and sorted DataFrame
        """
        if repository is None:
            raise QueryError("Repository must be provided for query execution")

        # Get the dataset
        dataset = repository.get_dataset(dataset_name)
        if dataset is None:
            # repository.last_error already contains the appropriate error
            logger.error(f"Dataset {dataset_name} not found for query execution")
            return pd.DataFrame()

        # Start with the full dataset
        result = dataset.data

        # Apply filters
        for filter_func in self.filters:
            result = filter_func(result)

        # Apply sorters
        for sorter_func in self.sorters:
            result = sorter_func(result)

        return result


class QueryEngine:
    """Engine for querying phone record datasets."""

    def __init__(self, repository: PhoneRecordRepository):
        """Initialize the query engine.

        Args:
            repository: Repository to query
        """
        self.repository = repository

    def filter_by_phone_number(self, dataset_name: str, phone_number: str) -> pd.DataFrame:
        """Filter a dataset by phone number.

        Args:
            dataset_name: Name of the dataset to query
            phone_number: Phone number to filter by

        Returns:
            Filtered DataFrame
        """
        return self.repository.query_dataset(
            dataset_name,
            lambda df: df[df['phone_number'] == phone_number]
        )

    def filter_by_date_range(self, dataset_name: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """Filter a dataset by date range.

        Args:
            dataset_name: Name of the dataset to query
            start_date: Start date (inclusive) in format YYYY-MM-DD or any format parseable by pandas
            end_date: End date (inclusive, defaults to start_date if None) in format YYYY-MM-DD

        Returns:
            Filtered DataFrame or empty DataFrame if error occurs

        Note:
            This method handles date conversion errors gracefully and will return an empty
            DataFrame if the dates cannot be parsed or if the timestamp column doesn't exist.
        """
        if end_date is None:
            end_date = start_date

        def date_filter(df):
            try:
                # Check if timestamp column exists
                if 'timestamp' not in df.columns:
                    error = ColumnNotFoundError('timestamp')
                    logger.error(str(error))
                    return df.iloc[0:0]  # Return empty DataFrame with same columns

                # Convert timestamp column to datetime if it's not already
                if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                    df_copy = df.copy()
                    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'], errors='coerce')
                else:
                    df_copy = df

                # Check for NaT values after conversion
                if df_copy['timestamp'].isna().any():
                    logger.warning("Some timestamp values could not be converted to datetime")

                # Extract date component
                dates = df_copy['timestamp'].dt.date

                # Convert start_date and end_date to date objects if they're strings
                try:
                    start = pd.to_datetime(start_date).date() if isinstance(start_date, str) else start_date
                except Exception as e:
                    error = DateParseError(start_date, e)
                    logger.error(str(error))
                    return df.iloc[0:0]  # Return empty DataFrame with same columns

                try:
                    end = pd.to_datetime(end_date).date() if isinstance(end_date, str) else end_date
                except Exception as e:
                    error = DateParseError(end_date, e)
                    logger.error(str(error))
                    return df.iloc[0:0]  # Return empty DataFrame with same columns

                # Filter by date range
                mask = (dates >= start) & (dates <= end)
                return df[mask]
            except Exception as e:
                error = QueryError(f"Error filtering by date range: {str(e)}")
                logger.error(str(error))
                return df.iloc[0:0]  # Return empty DataFrame with same columns

        return self.repository.query_dataset(dataset_name, date_filter)

    def filter_by_message_type(self, dataset_name: str, message_type: str) -> pd.DataFrame:
        """Filter a dataset by message type.

        Args:
            dataset_name: Name of the dataset to query
            message_type: Message type to filter by

        Returns:
            Filtered DataFrame
        """
        return self.repository.query_dataset(
            dataset_name,
            lambda df: df[df['message_type'] == message_type]
        )

    def filter_by_content(self, dataset_name: str, content: str, case_sensitive: bool = False) -> pd.DataFrame:
        """Filter a dataset by message content.

        Args:
            dataset_name: Name of the dataset to query
            content: Content to search for
            case_sensitive: Whether to perform case-sensitive search

        Returns:
            Filtered DataFrame
        """
        if case_sensitive:
            filter_func = lambda df: df[df['message_content'].str.contains(content, na=False)]
        else:
            filter_func = lambda df: df[df['message_content'].str.contains(content, case=False, na=False)]

        return self.repository.query_dataset(dataset_name, filter_func)

    def sort_by_timestamp(self, dataset_name: str, ascending: bool = True) -> pd.DataFrame:
        """Sort a dataset by timestamp.

        Args:
            dataset_name: Name of the dataset to query
            ascending: Whether to sort in ascending order

        Returns:
            Sorted DataFrame
        """
        return self.repository.query_dataset(
            dataset_name,
            lambda df: df.sort_values('timestamp', ascending=ascending)
        )

    def get_unique_phone_numbers(self, dataset_name: str) -> List[str]:
        """Get unique phone numbers in a dataset.

        Args:
            dataset_name: Name of the dataset to query

        Returns:
            List of unique phone numbers
        """
        result = self.repository.query_dataset(
            dataset_name,
            lambda df: df['phone_number'].unique()
        )

        if result is None:
            return []

        return result.tolist()

    def count_by_message_type(self, dataset_name: str) -> Dict[str, int]:
        """Count messages by type.

        Args:
            dataset_name: Name of the dataset to query

        Returns:
            Dictionary mapping message types to counts
        """
        result = self.repository.query_dataset(
            dataset_name,
            lambda df: df['message_type'].value_counts().to_dict()
        )

        if result is None:
            return {}

        return result

    def count_by_phone_number(self, dataset_name: str) -> Dict[str, int]:
        """Count messages by phone number.

        Args:
            dataset_name: Name of the dataset to query

        Returns:
            Dictionary mapping phone numbers to counts
        """
        result = self.repository.query_dataset(
            dataset_name,
            lambda df: df['phone_number'].value_counts().to_dict()
        )

        if result is None:
            return {}

        return result

    def count_by_date(self, dataset_name: str) -> Dict[str, int]:
        """Count messages by date.

        Args:
            dataset_name: Name of the dataset to query

        Returns:
            Dictionary mapping dates (as strings in YYYY-MM-DD format) to counts (as integers)
            Returns empty dictionary if dataset not found or on error

        Note:
            This method handles date conversion errors gracefully and will exclude any
            timestamp values that cannot be parsed as valid dates.
        """
        def count_func(df):
            try:
                # Check if timestamp column exists
                if 'timestamp' not in df.columns:
                    error = ColumnNotFoundError('timestamp')
                    logger.error(str(error))
                    return {}

                # Convert timestamp column to datetime if it's not already
                if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                    df_copy = df.copy()
                    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'], errors='coerce')
                else:
                    df_copy = df

                # Check for NaT values after conversion
                if df_copy['timestamp'].isna().any():
                    logger.warning("Some timestamp values could not be converted to datetime")
                    # Drop NaT values
                    df_copy = df_copy.dropna(subset=['timestamp'])

                # If all values were NaT, return empty dict
                if len(df_copy) == 0:
                    return {}

                # Extract date component and count
                date_counts = df_copy['timestamp'].dt.date.value_counts()

                # Convert date objects to strings
                return {str(d): int(c) for d, c in date_counts.items()}
            except Exception as e:
                error = QueryError(f"Error counting by date: {str(e)}")
                logger.error(str(error))
                return {}

        result = self.repository.query_dataset(dataset_name, count_func)

        if result is None:
            return {}

        return result

    def build_query(self) -> QueryBuilder:
        """Create a new query builder.

        Returns:
            QueryBuilder instance
        """
        builder = QueryBuilder()
        # Inject repository reference
        builder.execute = lambda dataset_name: QueryBuilder.execute(builder, dataset_name, self.repository)
        return builder
