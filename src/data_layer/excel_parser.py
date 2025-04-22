"""
Excel Parser Module
----------------
Module for parsing Excel files containing phone records.

This module provides functionality to parse Excel files containing phone records,
validate their structure and content, and convert them into structured data for analysis.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from ..logger import get_logger
from ..utils.data_cleaner import (
    clean_message_content,
    normalize_message_types,
    normalize_phone_numbers,
    standardize_timestamps,
)
from ..utils.validators import (
    validate_dataframe_columns,
    validate_dataframe_values,
    validate_file_exists,
    validate_file_extension,
)
from .parser_exceptions import MappingError, ParserError, ValidationError

logger = get_logger("excel_parser")

# Default column name patterns for auto-mapping
DEFAULT_COLUMN_PATTERNS = {
    'timestamp': ['timestamp', 'date', 'time', 'datetime'],
    'phone_number': ['phone', 'number', 'contact', 'phonenumber', 'to/from', 'to', 'from'],
    'message_type': ['type', 'direction', 'message_type', 'messagetype', 'message type'],
    'message_content': ['content', 'message', 'text', 'body']
}

class ExcelParser:
    """Parser for Excel files containing phone records."""

    def __init__(self,
                 required_columns: Optional[List[str]] = None,
                 date_format: str = '%Y-%m-%d %H:%M:%S',
                 valid_message_types: Optional[List[str]] = None,
                 column_mapping: Optional[Dict[str, str]] = None,
                 auto_map_columns: bool = False,
                 validate_data: bool = True):
        """Initialize the Excel parser with configuration options.

        Args:
            required_columns: List of required column names (default: timestamp, phone_number, message_type)
            date_format: Format string for parsing dates (default: %Y-%m-%d %H:%M:%S)
            valid_message_types: List of valid message types (default: sent, received)
            column_mapping: Dictionary mapping standard column names to file column names
            auto_map_columns: Whether to attempt automatic column mapping
            validate_data: Whether to validate data values after parsing
        """
        self.required_columns = required_columns or ['timestamp', 'phone_number', 'message_type']
        self.date_format = date_format
        self.valid_message_types = valid_message_types or ['sent', 'received']
        self.column_mapping = column_mapping or {}
        self.auto_map_columns = auto_map_columns
        self.validate_data = validate_data
        self.last_error = None

    def parse(self, file_path: Union[str, Path], sheet_name: Any = 0) -> pd.DataFrame:
        """Parse an Excel file into a pandas DataFrame.

        Args:
            file_path: Path to the Excel file
            sheet_name: Name or index of the sheet to parse (default: 0)

        Returns:
            DataFrame containing parsed data

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file has an invalid extension
            ParserError: If there is an error parsing the file
            ValidationError: If the data fails validation
            MappingError: If column mapping fails
        """
        # Convert Path to string if necessary
        if isinstance(file_path, Path):
            file_path = str(file_path)

        # Validate file exists and has valid extension
        validate_file_exists(file_path)
        validate_file_extension(file_path, ['.xlsx', '.xls'])

        try:
            # Read the Excel file
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Apply column mapping if provided
            if self.column_mapping:
                df = self._apply_column_mapping(df, self.column_mapping)
            # Auto-map columns if enabled
            elif self.auto_map_columns:
                df = self._auto_map_columns(df)

            # Validate required columns exist
            validate_dataframe_columns(df, self.required_columns)

            # Clean and normalize data
            df = self._clean_data(df)

            # Validate data values if enabled
            if self.validate_data:
                self._validate_data(df)

            logger.info(f"Successfully parsed Excel file: {file_path}")
            return df

        except (FileNotFoundError, ValueError):
            # Re-raise these exceptions as they are already handled
            raise
        except Exception as e:
            # Wrap other exceptions in ParserError
            error_msg = f"Error parsing Excel file: {str(e)}"
            logger.error(error_msg)
            raise ParserError(error_msg) from e

    def _apply_column_mapping(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """Apply column mapping to rename DataFrame columns.

        Args:
            df: DataFrame to rename columns in
            mapping: Dictionary mapping standard column names to file column names

        Returns:
            DataFrame with renamed columns

        Raises:
            MappingError: If any mapped columns don't exist in the DataFrame
        """
        # Check if all mapped columns exist
        missing_columns = [col for col in mapping.values() if col not in df.columns]
        if missing_columns:
            error_msg = f"Column mapping references missing columns: {', '.join(missing_columns)}"
            logger.error(error_msg)
            raise MappingError(error_msg, missing_columns)

        # Create reverse mapping (file columns to standard columns)
        reverse_mapping = {v: k for k, v in mapping.items()}

        # Rename columns
        return df.rename(columns=reverse_mapping)

    def _auto_map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Automatically map columns based on common patterns.

        Args:
            df: DataFrame to map columns in

        Returns:
            DataFrame with renamed columns

        Raises:
            MappingError: If required columns can't be mapped
        """
        mapping = {}
        columns_lower = {col.lower(): col for col in df.columns}

        # Try to match columns based on patterns
        for std_col, patterns in DEFAULT_COLUMN_PATTERNS.items():
            for pattern in patterns:
                for col_lower, col_actual in columns_lower.items():
                    if pattern in col_lower:
                        mapping[std_col] = col_actual
                        break
                if std_col in mapping:
                    break

        # Check if all required columns were mapped
        missing_mappings = [col for col in self.required_columns if col not in mapping]
        if missing_mappings:
            error_msg = f"Could not automatically map required columns: {', '.join(missing_mappings)}"
            logger.error(error_msg)
            raise MappingError(error_msg, missing_mappings)

        logger.info(f"Auto-mapped columns: {mapping}")

        # Apply the mapping
        return self._apply_column_mapping(df, mapping)

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize data in the DataFrame.

        Args:
            df: DataFrame to clean

        Returns:
            Cleaned DataFrame
        """
        # Create a copy to avoid modifying the original
        result = df.copy()

        # Normalize phone numbers
        result = normalize_phone_numbers(result)

        # Standardize timestamps
        result = standardize_timestamps(result, self.date_format)

        # Normalize message types
        result = normalize_message_types(result)

        # Clean message content
        result = clean_message_content(result)

        return result

    def _validate_data(self, df: pd.DataFrame) -> None:
        """Validate data values in the DataFrame.

        Args:
            df: DataFrame to validate

        Raises:
            ValidationError: If the data fails validation
        """
        # Validate data values
        validation_errors = validate_dataframe_values(
            df,
            self.date_format,
            self.valid_message_types
        )

        # Raise exception if there are validation errors
        if not validation_errors.empty:
            error_msg = f"Found {len(validation_errors)} validation errors in data"
            logger.error(error_msg)
            raise ValidationError(error_msg, validation_errors)

    def parse_and_detect(self, file_path: Union[str, Path], sheet_name: Any = 0) -> tuple:
        """Parse an Excel file and detect column mappings.

        This method attempts to parse the file and automatically detect column mappings.
        It's more flexible than the parse method and returns additional information.

        Args:
            file_path: Path to the Excel file
            sheet_name: Name or index of the sheet to parse (default: 0)

        Returns:
            Tuple of (DataFrame, column_mapping, error_message)
            If successful, error_message will be None
            If failed, DataFrame will be None and error_message will contain the error
        """
        try:
            # Try to parse with auto-mapping
            auto_map_parser = ExcelParser(
                required_columns=self.required_columns,
                date_format=self.date_format,
                valid_message_types=self.valid_message_types,
                auto_map_columns=True
            )

            # First try with the provided column mapping
            if self.column_mapping:
                try:
                    df = self.parse(file_path, sheet_name)
                    return df, self.column_mapping, None
                except Exception as e:
                    logger.warning(f"Failed to parse with provided mapping: {str(e)}")
                    # Fall back to auto-mapping

            # Try auto-mapping
            try:
                df = auto_map_parser.parse(file_path, sheet_name)
                return df, auto_map_parser.column_mapping, None
            except Exception as e:
                logger.warning(f"Failed to auto-map columns: {str(e)}")

            # If we get here, try a more flexible approach with minimal validation
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Create a mapping based on best guesses
            mapping = {}

            # Look for date/time columns
            date_col = None
            time_col = None
            for col in df.columns:
                if col.lower() in ['date', 'datetime', 'timestamp']:
                    date_col = col
                elif col.lower() == 'time':
                    time_col = col

            # If we have separate date and time columns, combine them
            if date_col and time_col:
                # Create a new timestamp column by combining date and time
                try:
                    df['timestamp'] = df.apply(
                        lambda row: f"{row[date_col]} {row[time_col]}", axis=1
                    )
                    mapping['timestamp'] = 'timestamp'
                except Exception as e:
                    logger.error(f"Failed to combine date and time columns: {str(e)}")
            elif date_col:
                mapping['timestamp'] = date_col

            # Look for phone number column
            for col in df.columns:
                if any(pattern in col.lower() for pattern in ['phone', 'number', 'contact', 'to/from', 'to', 'from']):
                    mapping['phone_number'] = col
                    break

            # Look for message type column
            for col in df.columns:
                if any(pattern in col.lower() for pattern in ['type', 'direction', 'message']):
                    mapping['message_type'] = col
                    break

            # Check if we found the minimum required columns
            missing = [col for col in self.required_columns if col not in mapping]
            if missing:
                return None, None, f"Could not identify required columns: {', '.join(missing)}"

            # Apply the mapping and basic cleaning
            result = df.copy()

            # Add empty message_content column if needed and not present
            if 'message_content' not in result.columns and 'message_content' in self.required_columns:
                result['message_content'] = ''
                mapping['message_content'] = 'message_content'

            return result, mapping, None

        except Exception as e:
            error_msg = f"Error parsing Excel file: {str(e)}"
            logger.error(error_msg)
            return None, None, error_msg
