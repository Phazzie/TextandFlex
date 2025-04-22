"""
Complex Query Module
------------------
Provides advanced query capabilities for phone record datasets.
"""

import pandas as pd
from typing import List, Dict, Tuple, Any, Optional, Union, Callable
import operator
from datetime import datetime, date

from ..logger import get_logger
from .exceptions import QueryError

logger = get_logger("complex_query")

# Define operators for conditions
OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda x, y: x.isin(y),
    "not in": lambda x, y: ~x.isin(y),
    "contains": lambda x, y: x.str.contains(y, na=False),
    "startswith": lambda x, y: x.str.startswith(y, na=False),
    "endswith": lambda x, y: x.str.endswith(y, na=False)
}

class JoinOperation:
    """Class for joining two datasets."""

    def __init__(self, left_df: pd.DataFrame, right_df: pd.DataFrame,
                 join_type: str = "inner", join_columns: List[str] = None,
                 suffixes: Tuple[str, str] = ("_x", "_y")):
        """Initialize the join operation.

        Args:
            left_df: Left DataFrame
            right_df: Right DataFrame
            join_type: Type of join (inner, left, right, outer)
            join_columns: Columns to join on
            suffixes: Suffixes for overlapping columns
        """
        self.left_df = left_df
        self.right_df = right_df
        self.join_type = join_type
        self.join_columns = join_columns or []
        self.suffixes = suffixes

        # Validate inputs
        self._validate_inputs()

    def _validate_inputs(self):
        """Validate the inputs for the join operation."""
        # Validate join type
        valid_join_types = ["inner", "left", "right", "outer"]
        if self.join_type not in valid_join_types:
            raise ValueError(f"Invalid join type: {self.join_type}. Must be one of {valid_join_types}")

        # Validate join columns
        if not self.join_columns:
            raise ValueError("Join columns must be specified")

        for col in self.join_columns:
            if col not in self.left_df.columns:
                raise ValueError(f"Join column '{col}' not found in left DataFrame")
            if col not in self.right_df.columns:
                raise ValueError(f"Join column '{col}' not found in right DataFrame")

    def execute(self) -> pd.DataFrame:
        """Execute the join operation.

        Returns:
            Joined DataFrame
        """
        try:
            result = pd.merge(
                self.left_df,
                self.right_df,
                on=self.join_columns,
                how=self.join_type,
                suffixes=self.suffixes
            )

            logger.info(f"Joined DataFrames with {len(result)} resulting rows")
            return result

        except Exception as e:
            error_msg = f"Error executing join operation: {str(e)}"
            logger.error(error_msg)
            raise QueryError(error_msg)


class ComplexFilter:
    """Class for complex filtering operations."""

    def __init__(self, df: pd.DataFrame):
        """Initialize the complex filter.

        Args:
            df: DataFrame to filter
        """
        self.df = df

    def filter(self, conditions: List[Tuple[str, str, Any]], combine: str = "and") -> pd.DataFrame:
        """Filter the DataFrame based on conditions.

        Args:
            conditions: List of conditions as (column, operator, value) tuples
            combine: How to combine conditions ('and' or 'or')

        Returns:
            Filtered DataFrame
        """
        if not conditions:
            return self.df

        try:
            # Initialize mask based on combine method
            if combine.lower() == "and":
                mask = pd.Series(True, index=self.df.index)
                for column, op, value in conditions:
                    if op in OPERATORS:
                        mask = mask & OPERATORS[op](self.df[column], value)
                    else:
                        raise ValueError(f"Invalid operator: {op}")

            elif combine.lower() == "or":
                mask = pd.Series(False, index=self.df.index)
                for column, op, value in conditions:
                    if op in OPERATORS:
                        mask = mask | OPERATORS[op](self.df[column], value)
                    else:
                        raise ValueError(f"Invalid operator: {op}")

            else:
                raise ValueError(f"Invalid combine method: {combine}. Must be 'and' or 'or'")

            result = self.df[mask]
            logger.info(f"Filtered DataFrame from {len(self.df)} to {len(result)} rows")
            return result

        except Exception as e:
            error_msg = f"Error filtering DataFrame: {str(e)}"
            logger.error(error_msg)
            raise QueryError(error_msg)

    def filter_date_range(self, column: str, start_date: Union[str, datetime, date],
                         end_date: Union[str, datetime, date]) -> pd.DataFrame:
        """Filter the DataFrame based on a date range.

        Args:
            column: Date column to filter on
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Filtered DataFrame
        """
        try:
            # Convert column to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(self.df[column]):
                df_copy = self.df.copy()
                df_copy[column] = pd.to_datetime(df_copy[column])
            else:
                df_copy = self.df

            # Convert start_date and end_date to pandas Timestamp
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)

            # Filter the DataFrame
            result = df_copy[(df_copy[column] >= start) & (df_copy[column] <= end)]
            logger.info(f"Date range filter from {len(self.df)} to {len(result)} rows")
            return result

        except Exception as e:
            error_msg = f"Error filtering by date range: {str(e)}"
            logger.error(error_msg)
            raise QueryError(error_msg)

    def filter_by_values(self, filters: Dict[str, List[Any]]) -> pd.DataFrame:
        """Filter the DataFrame based on multiple column values.

        Args:
            filters: Dictionary mapping columns to lists of allowed values

        Returns:
            Filtered DataFrame
        """
        try:
            result = self.df.copy()

            for column, values in filters.items():
                if column in result.columns:
                    result = result[result[column].isin(values)]
                else:
                    raise ValueError(f"Column '{column}' not found in DataFrame")

            logger.info(f"Multi-column filter from {len(self.df)} to {len(result)} rows")
            return result

        except Exception as e:
            error_msg = f"Error filtering by values: {str(e)}"
            logger.error(error_msg)
            raise QueryError(error_msg)


class QueryBuilder:
    """Builder class for constructing and executing complex queries."""

    def __init__(self, df: pd.DataFrame):
        """Initialize the query builder.

        Args:
            df: DataFrame to query
        """
        self.df = df
        self.reset()

    def reset(self):
        """Reset the query builder to its initial state."""
        self.conditions = []
        self.combine_method = "and"
        self.columns = None
        self.group_columns = None
        self.aggregations = None
        self.sort_column = None
        self.sort_ascending = True
        self.row_limit = None
        return self

    def where(self, column: str, op: str, value: Any):
        """Add a where condition to the query.

        Args:
            column: Column to filter on
            op: Operator to use
            value: Value to compare against

        Returns:
            Self for method chaining
        """
        if op not in OPERATORS:
            raise ValueError(f"Invalid operator: {op}")

        self.conditions.append((column, op, value))
        return self

    def and_where(self, column: str, op: str, value: Any):
        """Add an AND where condition to the query.

        Args:
            column: Column to filter on
            op: Operator to use
            value: Value to compare against

        Returns:
            Self for method chaining
        """
        self.combine_method = "and"
        return self.where(column, op, value)

    def or_where(self, column: str, op: str, value: Any):
        """Add an OR where condition to the query.

        Args:
            column: Column to filter on
            op: Operator to use
            value: Value to compare against

        Returns:
            Self for method chaining
        """
        self.combine_method = "or"
        return self.where(column, op, value)

    def select(self, columns: List[str]):
        """Select columns to include in the result.

        Args:
            columns: List of column names to include

        Returns:
            Self for method chaining
        """
        self.columns = columns
        return self

    def group_by(self, columns: Union[str, List[str]]):
        """Group the result by columns.

        Args:
            columns: Column or list of columns to group by

        Returns:
            Self for method chaining
        """
        if isinstance(columns, str):
            self.group_columns = [columns]
        else:
            self.group_columns = columns
        return self

    def aggregate(self, aggregations: Dict[str, Union[str, List[str]]]):
        """Add aggregations to the query.

        Args:
            aggregations: Dictionary mapping columns to aggregation functions

        Returns:
            Self for method chaining
        """
        self.aggregations = aggregations
        return self

    def order_by(self, column: str, ascending: bool = True):
        """Order the result by a column.

        Args:
            column: Column to order by
            ascending: Whether to sort in ascending order

        Returns:
            Self for method chaining
        """
        self.sort_column = column
        self.sort_ascending = ascending
        return self

    def limit(self, n: int):
        """Limit the number of rows in the result.

        Args:
            n: Maximum number of rows to return

        Returns:
            Self for method chaining
        """
        if n < 0:
            raise ValueError("Limit must be a non-negative integer")

        self.row_limit = n
        return self

    def execute(self) -> pd.DataFrame:
        """Execute the query and return the result.

        Returns:
            Result DataFrame
        """
        try:
            result = self.df.copy()

            # Apply filters
            if self.conditions:
                complex_filter = ComplexFilter(result)
                result = complex_filter.filter(self.conditions, self.combine_method)

            # Apply grouping and aggregation
            if self.group_columns and self.aggregations:
                result = result.groupby(self.group_columns).agg(self.aggregations)
                # Flatten column names if MultiIndex
                if isinstance(result.columns, pd.MultiIndex):
                    result.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col for col in result.columns]
                result = result.reset_index()

            # Select columns
            if self.columns and not self.group_columns:
                result = result[self.columns]

            # Apply sorting
            if self.sort_column:
                result = result.sort_values(by=self.sort_column, ascending=self.sort_ascending)

            # Apply limit
            if self.row_limit is not None:
                result = result.head(self.row_limit)

            logger.info(f"Query executed successfully, returning {len(result)} rows")
            return result

        except Exception as e:
            error_msg = f"Error executing query: {str(e)}"
            logger.error(error_msg)
            raise QueryError(error_msg)
