"""
Validation Schema Module
-----------------------
Provides schema validation for dataset metadata, column mappings, and dataset properties.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from ..logger import get_logger
from .exceptions import ValidationError

logger = get_logger("validation_schema")

# Required fields for dataset metadata
REQUIRED_METADATA_FIELDS = ["created_at", "record_count", "columns"]

# Required fields for column mapping
REQUIRED_COLUMN_MAPPING_FIELDS = ["timestamp", "phone_number", "message_type"]

def validate_dataset_metadata(metadata: Dict[str, Any]) -> bool:
    """Validate dataset metadata against the schema.

    Args:
        metadata: Dataset metadata to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    # Check for required fields
    for field in REQUIRED_METADATA_FIELDS:
        if field not in metadata:
            error_msg = f"Missing required metadata field: {field}"
            logger.error(error_msg)
            raise ValidationError(error_msg)

    # Validate field types
    if not isinstance(metadata["created_at"], str):
        error_msg = f"Invalid type for metadata field 'created_at': expected str, got {type(metadata['created_at']).__name__}"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    if not isinstance(metadata["record_count"], int):
        error_msg = f"Invalid type for metadata field 'record_count': expected int, got {type(metadata['record_count']).__name__}"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    if not isinstance(metadata["columns"], list):
        error_msg = f"Invalid type for metadata field 'columns': expected list, got {type(metadata['columns']).__name__}"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    # Validate created_at format
    try:
        datetime.fromisoformat(metadata["created_at"])
    except ValueError:
        error_msg = f"Invalid format for metadata field 'created_at': expected ISO format, got {metadata['created_at']}"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    # Validate record_count
    if metadata["record_count"] < 0:
        error_msg = f"Invalid value for metadata field 'record_count': expected non-negative integer, got {metadata['record_count']}"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    # Validate columns
    if len(metadata["columns"]) == 0:
        error_msg = "Invalid value for metadata field 'columns': expected non-empty list"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    return True

def validate_column_mapping(column_mapping: Dict[str, str]) -> bool:
    """Validate column mapping against the schema.

    Args:
        column_mapping: Column mapping to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    # Check for required fields
    missing_fields = []
    for field in REQUIRED_COLUMN_MAPPING_FIELDS:
        if field not in column_mapping:
            missing_fields.append(field)

    if missing_fields:
        error_msg = f"Missing required column mapping fields: {', '.join(missing_fields)}"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    # Validate field types
    for field, value in column_mapping.items():
        if not isinstance(value, str):
            error_msg = f"Invalid type for column mapping field '{field}': expected str, got {type(value).__name__}"
            logger.error(error_msg)
            raise ValidationError(error_msg)

    return True

def validate_dataset_properties(data: pd.DataFrame, column_mapping: Dict[str, str]) -> bool:
    """Validate dataset properties.

    Args:
        data: DataFrame to validate
        column_mapping: Column mapping to validate against

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    # Check if DataFrame is empty
    if data.empty:
        error_msg = "Dataset is empty"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    # Check if required columns from column mapping are in DataFrame
    missing_columns = []
    for column in REQUIRED_COLUMN_MAPPING_FIELDS:
        if column in column_mapping and column not in data.columns:
            missing_columns.append(column)

    if missing_columns:
        error_msg = f"Required columns not found in dataset: {', '.join(missing_columns)}"
        logger.error(error_msg)
        raise ValidationError(error_msg)


    return True

def validate_dataset(name: str, data: pd.DataFrame, column_mapping: Dict[str, str], metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Validate a complete dataset.

    Args:
        name: Dataset name
        data: DataFrame to validate
        column_mapping: Column mapping to validate
        metadata: Metadata to validate (optional)

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    # Validate name
    if not name or not isinstance(name, str):
        error_msg = f"Invalid dataset name: {name}"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    # Validate column mapping
    validate_column_mapping(column_mapping)

    # Validate dataset properties
    validate_dataset_properties(data, column_mapping)

    # Validate metadata if provided
    if metadata is not None:
        validate_dataset_metadata(metadata)

    return True
