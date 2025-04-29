"""
Repository Module
-------------
Data storage and management for phone records.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any
import uuid
from datetime import datetime, date

from .models import PhoneRecordDataset, RepositoryMetadata
from .exceptions import (DatasetNotFoundError, DatasetSaveError, DatasetLoadError,
                        MetadataSaveError, MetadataLoadError, QueryError, ValidationError, DatasetError,
                        VersioningError, VersionNotFoundError)
from .validation_schema import validate_dataset, validate_dataset_metadata, validate_column_mapping, validate_dataset_properties
from .complex_query import JoinOperation, ComplexFilter, QueryBuilder
from .versioning import VersionManager, INITIAL_VERSION
from ..utils.file_io import save_json, load_json, save_pickle, load_pickle
from ..logger import get_logger
from ..config import DATA_DIR

# Constants
MIN_DATASET_COUNT = 1
FIRST_DATASET_INDEX = 0

logger = get_logger("repository")

class PhoneRecordRepository:
    """Repository for storing and managing phone record datasets."""

    def __init__(self, storage_dir: Optional[Union[str, Path]] = None):
        """Initialize the repository.

        Args:
            storage_dir: Directory for storing datasets (default: project data directory)
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent.parent.parent / DATA_DIR
        self.datasets: Dict[str, PhoneRecordDataset] = {}
        self.metadata = RepositoryMetadata()
        self._last_error = None
        self.version_manager = VersionManager(storage_dir=self.storage_dir)

        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Try to load existing metadata
        self._load_metadata()

    def _get_metadata_path(self) -> Path:
        """Get the path to the metadata file.

        Returns:
            Path to metadata file
        """
        return self.storage_dir / "repository_metadata.json"

    def _get_dataset_path(self, name: str) -> Path:
        """Get the path to a dataset file.

        Args:
            name: Dataset name

        Returns:
            Path to dataset file
        """
        return self.storage_dir / f"{name}.pkl"

    def _save_metadata(self) -> bool:
        """Save repository metadata to disk.

        Returns:
            True if successful, False otherwise

        Note:
            Sets self._last_error to a MetadataSaveError if saving fails
        """
        try:
            result = save_json(self.metadata.to_dict(), self._get_metadata_path())
            if not result:
                error = MetadataSaveError("Failed to save metadata to disk")
                self._last_error = error
                logger.error(str(error))
            return result
        except Exception as e:
            error = MetadataSaveError(e)
            self._last_error = error
            logger.error(str(error))
            return False

    def _load_metadata(self) -> bool:
        """Load repository metadata from disk.

        Returns:
            True if successful, False otherwise

        Note:
            Sets self._last_error to a MetadataLoadError if loading fails
        """
        try:
            metadata_path = self._get_metadata_path()
            if not metadata_path.exists():
                logger.info("No existing metadata found")
                return False

            metadata_dict = load_json(metadata_path)
            if metadata_dict:
                self.metadata = RepositoryMetadata.from_dict(metadata_dict)
                logger.info(f"Loaded metadata with {len(self.metadata.datasets)} datasets")
                return True

            error = MetadataLoadError("Failed to parse metadata file")
            self._last_error = error
            logger.error(str(error))
            return False
        except Exception as e:
            error = MetadataLoadError(e)
            self._last_error = error
            logger.error(str(error))
            return False

    def _validate_dataset_inputs(self, name: str, data: pd.DataFrame,
                              column_mapping: Dict[str, str],
                              metadata: Optional[Dict[str, Any]] = None) -> Optional[DatasetError]:
        """Validate inputs for dataset operations.

        Args:
            name: Dataset name
            data: DataFrame containing phone records
            column_mapping: Dictionary mapping logical column names to actual column names
            metadata: Optional additional metadata

        Returns:
            DatasetError if validation fails, None if validation succeeds
        """
        try:
            # Validate dataset name
            if not name or not isinstance(name, str):
                raise ValidationError(f"Invalid dataset name: {name}")

            # Check for Excel-specific format (Date and Time columns)
            excel_format = all(field in data.columns for field in ['Date', 'Time', 'To/From', 'Message Type'])

            if not excel_format:
                # For standard format, validate column mapping and dataset properties
                validate_column_mapping(column_mapping)
                validate_dataset_properties(data, column_mapping)
            else:
                # For Excel-specific format, we'll handle it differently
                logger.info(f"Detected Excel-specific format for dataset {name}")
                # We don't need to validate further as the format is recognized

            # Validate metadata if provided
            if metadata is not None:
                validate_dataset_metadata(metadata)

            return None
        except ValidationError as validation_error:
            return DatasetError(f"Validation failed for dataset {name}: {str(validation_error)}")

    def _create_dataset_object(self, name: str, data: pd.DataFrame,
                             column_mapping: Dict[str, str],
                             metadata: Optional[Dict[str, Any]] = None) -> PhoneRecordDataset:
        """Create a dataset object.

        Args:
            name: Dataset name
            data: DataFrame containing phone records
            column_mapping: Dictionary mapping logical column names to actual column names
            metadata: Optional additional metadata

        Returns:
            PhoneRecordDataset object
        """
        return PhoneRecordDataset(
            name=name,
            data=data,
            column_mapping=column_mapping,
            metadata=metadata or {}
        )

    def _save_dataset_to_disk(self, dataset: PhoneRecordDataset) -> bool:
        """Save a dataset to disk.

        Args:
            dataset: Dataset to save

        Returns:
            True if successful, False otherwise
        """
        dataset_path = self._get_dataset_path(dataset.name)
        if not save_pickle(dataset, dataset_path):
            self._last_error = DatasetSaveError(dataset.name, "Failed to save dataset to disk")
            logger.error(str(self._last_error))
            return False
        return True

    def _initialize_dataset_versioning(self, dataset: PhoneRecordDataset,
                                     version_author: Optional[str] = None) -> bool:
        """Initialize versioning for a dataset.

        Args:
            dataset: Dataset to initialize versioning for
            version_author: Optional author name for the initial version

        Returns:
            True if successful, False otherwise
        """
        if not self.version_manager.initialize_versioning(dataset, author=version_author):
            # Versioning initialization failed
            logger.warning(f"Failed to initialize versioning for dataset '{dataset.name}'")
            return False

        # Update dataset with version info
        dataset.version_info = {
            "is_versioned": True,
            "version_number": INITIAL_VERSION,
            "version_timestamp": datetime.now().isoformat()
        }

        # Save dataset again with version info
        dataset_path = self._get_dataset_path(dataset.name)
        if not save_pickle(dataset, dataset_path):
            logger.warning(f"Failed to update dataset '{dataset.name}' with version info")
            return False

        return True

    def add_dataset(self, name: str, data: pd.DataFrame, column_mapping: Dict[str, str],
                   metadata: Optional[Dict[str, Any]] = None, enable_versioning: bool = False,
                   version_author: Optional[str] = None) -> bool:
        """Add a dataset to the repository.

        Args:
            name: Dataset name
            data: DataFrame containing phone records
            column_mapping: Dictionary mapping logical column names to actual column names
            metadata: Optional additional metadata
            enable_versioning: Whether to enable versioning for this dataset
            version_author: Optional author name for the initial version

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate inputs
            validation_error = self._validate_dataset_inputs(name, data, column_mapping, metadata)
            if validation_error:
                self._last_error = validation_error
                logger.error(str(validation_error))
                return False

            # Create dataset object
            dataset = self._create_dataset_object(name, data, column_mapping, metadata)

            # Save dataset to disk
            if not self._save_dataset_to_disk(dataset):
                # Remove from in-memory collection and metadata if it exists
                if name in self.datasets:
                    del self.datasets[name]
                self.metadata.remove_dataset(name)
                return False

            # Add to in-memory collection
            self.datasets[name] = dataset

            # Update metadata
            self.metadata.add_dataset(dataset)

            # Save updated metadata
            if not self._save_metadata():
                self._last_error = MetadataSaveError("Failed to save updated metadata")
                logger.error(str(self._last_error))
                return False

            # Initialize versioning if requested
            if enable_versioning:
                self._initialize_dataset_versioning(dataset, version_author)

            logger.info(f"Added dataset {name} with {len(data)} records")
            return True

        except Exception as e:
            self._last_error = DatasetError(f"Error adding dataset {name}: {str(e)}")
            logger.error(str(self._last_error))
            return False

    def get_dataset(self, name: str) -> Optional[PhoneRecordDataset]:
        """Get a dataset by name.

        Args:
            name: Dataset name

        Returns:
            PhoneRecordDataset or None if not found

        Raises:
            DatasetLoadError: If there's an error loading the dataset from disk

        Note:
            This method returns None instead of raising DatasetNotFoundError when the dataset
            is not found, to maintain backward compatibility with existing code.
        """
        # Check if dataset is already loaded
        if name in self.datasets:
            return self.datasets[name]

        # Check if dataset exists in metadata
        if name not in self.metadata.datasets:
            error = DatasetNotFoundError(name, "Dataset not found in metadata")
            self._last_error = error
            logger.warning(str(error))
            return None

        # Try to load dataset from disk
        dataset_path = self._get_dataset_path(name)
        try:
            dataset = load_pickle(dataset_path)

            if dataset:
                # Add to in-memory collection
                self.datasets[name] = dataset
                logger.info(f"Loaded dataset {name} from disk")
                return dataset

            error = DatasetLoadError(name, "Failed to deserialize dataset")
            self._last_error = error
            logger.error(str(error))
            return None
        except Exception as e:
            error = DatasetLoadError(name, e)
            self._last_error = error
            logger.error(str(error))
            return None

    def remove_dataset(self, name: str) -> bool:
        """Remove a dataset from the repository.

        Args:
            name: Dataset name

        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from in-memory collection
            if name in self.datasets:
                del self.datasets[name]

            # Remove from metadata
            self.metadata.remove_dataset(name)

            # Remove from disk
            dataset_path = self._get_dataset_path(name)
            if dataset_path.exists():
                dataset_path.unlink()

            # Save updated metadata
            if not self._save_metadata():
                error = MetadataSaveError("Failed to save metadata after removing dataset")
                self._last_error = error
                logger.error(str(error))
                return False

            logger.info(f"Removed dataset {name}")
            return True

        except Exception as e:
            error = DatasetError(f"Error removing dataset {name}: {str(e)}")
            self._last_error = error
            logger.error(str(error))
            return False

    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all datasets in the repository.

        Returns:
            List of dataset summaries
        """
        summaries = []

        for name, metadata in self.metadata.datasets.items():
            # Get dataset if loaded, otherwise use metadata
            dataset = self.datasets.get(name)

            if dataset:
                summaries.append(dataset.get_summary())
            else:
                summaries.append({
                    "name": name,
                    "record_count": metadata.get("metadata", {}).get("record_count", "Unknown"),
                    "columns": metadata.get("metadata", {}).get("columns", []),
                    "column_mapping": metadata.get("column_mapping", {}),
                    "created_at": metadata.get("metadata", {}).get("created_at")
                })

        return summaries

    def update_dataset(self, name: str, data: Optional[pd.DataFrame] = None,
                     column_mapping: Optional[Dict[str, str]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update an existing dataset in the repository.

        Args:
            name: Dataset name
            data: New DataFrame (if None, keeps existing data)
            column_mapping: New column mapping (if None, keeps existing mapping)
            metadata: New metadata to merge with existing metadata (if None, keeps existing metadata)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing dataset
            dataset = self.get_dataset(name)
            if not dataset:
                # self._last_error already set by get_dataset
                return False

            # Validate inputs before updating
            try:
                # Validate new data if provided
                if data is not None:
                    # If column mapping is also being updated, use that for validation
                    mapping_for_validation = column_mapping if column_mapping is not None else dataset.column_mapping
                    validate_dataset_properties(data, mapping_for_validation)

                # Validate new column mapping if provided
                if column_mapping is not None:
                    validate_column_mapping(column_mapping)
                    # If data is not being updated, validate that the new mapping works with existing data
                    if data is None:
                        validate_dataset_properties(dataset.data, column_mapping)

                # Validate new metadata if provided
                if metadata is not None:
                    # Create a copy of the existing metadata and update it with the new metadata
                    merged_metadata = dataset.metadata.copy()
                    merged_metadata.update(metadata)
                    validate_dataset_metadata(merged_metadata)
            except ValidationError as validation_error:
                error = DatasetError(f"Validation failed for dataset update {name}: {str(validation_error)}")
                self._last_error = error
                logger.error(str(error))
                return False

            # Update dataset properties
            if data is not None:
                dataset.data = data

            if column_mapping is not None:
                dataset.column_mapping = column_mapping

            if metadata is not None:
                # Merge new metadata with existing metadata
                dataset.metadata.update(metadata)

            # Update record count and timestamp
            dataset.metadata["record_count"] = len(dataset.data)
            dataset.metadata["last_updated"] = self.metadata.last_updated

            # Save dataset to disk
            dataset_path = self._get_dataset_path(name)
            if not save_pickle(dataset, dataset_path):
                error = DatasetSaveError(name, "Failed to save updated dataset to disk")
                self._last_error = error
                logger.error(str(error))
                return False

            # Update metadata
            self.metadata.add_dataset(dataset)

            # Save updated metadata
            if not self._save_metadata():
                error = MetadataSaveError("Failed to save updated metadata")
                self._last_error = error
                logger.error(str(error))
                return False

            logger.info(f"Updated dataset {name} with {len(dataset.data)} records")
            return True

        except Exception as e:
            error = DatasetError(f"Error updating dataset {name}: {str(e)}")
            self._last_error = error
            logger.error(str(error))
            return False

    def query_dataset(self, name: str, query_func) -> Optional[pd.DataFrame]:
        """Query a dataset using a function.

        Args:
            name: Dataset name
            query_func: Function that takes a DataFrame and returns a filtered DataFrame or other result
                       The function should handle its own errors and return appropriate values

        Returns:
            Result of query_func applied to the dataset, or None if dataset not found or error occurs

        Note:
            This method sets self._last_error if an error occurs during query execution
        """
        dataset = self.get_dataset(name)
        if not dataset:
            # self._last_error already set by get_dataset
            return None

        try:
            result = query_func(dataset.data)
            return result
        except Exception as e:
            error = QueryError(f"Error querying dataset {name}: {str(e)}")
            self._last_error = error
            logger.error(str(error))
            return None

    def complex_filter(self, name: str, conditions: List[Tuple[str, str, Any]],
                      combine: str = "and") -> Optional[pd.DataFrame]:
        """Apply complex filtering to a dataset.

        Args:
            name: Dataset name
            conditions: List of conditions as (column, operator, value) tuples
            combine: How to combine conditions ('and' or 'or')

        Returns:
            Filtered DataFrame, or None if dataset not found or error occurs
        """
        dataset = self.get_dataset(name)
        if not dataset:
            # self._last_error already set by get_dataset
            return None

        try:
            complex_filter = ComplexFilter(dataset.data)
            result = complex_filter.filter(conditions, combine)
            logger.info(f"Applied complex filter to dataset {name}, returned {len(result)} rows")
            return result
        except Exception as e:
            error = QueryError(f"Error applying complex filter to dataset {name}: {str(e)}")
            self._last_error = error
            logger.error(str(error))
            return None

    def filter_by_date_range(self, name: str, column: str, start_date: Union[str, datetime, date],
                           end_date: Union[str, datetime, date]) -> Optional[pd.DataFrame]:
        """Filter a dataset by date range.

        Args:
            name: Dataset name
            column: Date column to filter on
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Filtered DataFrame, or None if dataset not found or error occurs
        """
        dataset = self.get_dataset(name)
        if not dataset:
            # self._last_error already set by get_dataset
            return None

        try:
            complex_filter = ComplexFilter(dataset.data)
            result = complex_filter.filter_date_range(column, start_date, end_date)
            logger.info(f"Applied date range filter to dataset {name}, returned {len(result)} rows")
            return result
        except Exception as e:
            error = QueryError(f"Error applying date range filter to dataset {name}: {str(e)}")
            self._last_error = error
            logger.error(str(error))
            return None

    def filter_by_values(self, name: str, filters: Dict[str, List[Any]]) -> Optional[pd.DataFrame]:
        """Filter a dataset by multiple column values.

        Args:
            name: Dataset name
            filters: Dictionary mapping columns to lists of allowed values

        Returns:
            Filtered DataFrame, or None if dataset not found or error occurs
        """
        dataset = self.get_dataset(name)
        if not dataset:
            # self._last_error already set by get_dataset
            return None

        try:
            complex_filter = ComplexFilter(dataset.data)
            result = complex_filter.filter_by_values(filters)
            logger.info(f"Applied multi-column filter to dataset {name}, returned {len(result)} rows")
            return result
        except Exception as e:
            error = QueryError(f"Error applying multi-column filter to dataset {name}: {str(e)}")
            self._last_error = error
            logger.error(str(error))
            return None

    def join_datasets(self, left_name: str, right_name: str, join_columns: Union[str, List[str]],
                     join_type: str = "inner", suffixes: Tuple[str, str] = ("_x", "_y")) -> Optional[pd.DataFrame]:
        """Join two datasets.

        Args:
            left_name: Name of the left dataset
            right_name: Name of the right dataset
            join_columns: Column(s) to join on
            join_type: Type of join (inner, left, right, outer)
            suffixes: Suffixes for overlapping columns

        Returns:
            Joined DataFrame, or None if datasets not found or error occurs
        """
        # Get datasets
        left_dataset = self.get_dataset(left_name)
        if not left_dataset:
            # self._last_error already set by get_dataset
            return None

        right_dataset = self.get_dataset(right_name)
        if not right_dataset:
            # self._last_error already set by get_dataset
            return None

        # Convert join_columns to list if it's a string
        if isinstance(join_columns, str):
            join_columns = [join_columns]

        try:
            # Create join operation
            join_op = JoinOperation(
                left_df=left_dataset.data,
                right_df=right_dataset.data,
                join_type=join_type,
                join_columns=join_columns,
                suffixes=suffixes
            )

            # Execute join
            result = join_op.execute()
            logger.info(f"Joined datasets {left_name} and {right_name}, returned {len(result)} rows")
            return result
        except Exception as e:
            error = QueryError(f"Error joining datasets {left_name} and {right_name}: {str(e)}")
            self._last_error = error
            logger.error(str(error))
            return None

    def execute_complex_query(self, query: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Execute a complex query.

        Args:
            query: Query dictionary with dataset, conditions, etc.

        Returns:
            Result DataFrame, or None if error occurs
        """

    # Version Management Methods

    def create_dataset_version(self, name: str, description: str = "",
                             author: Optional[str] = None) -> Optional[int]:
        """Create a new version of a dataset.

        Args:
            name: Dataset name
            description: Description of the changes
            author: Optional author name

        Returns:
            New version number or None if failed
        """
        # Get dataset
        dataset = self.get_dataset(name)
        if not dataset:
            # self._last_error already set by get_dataset
            return None

        # Check if versioning is enabled
        if not dataset.version_info or not dataset.version_info.get("is_versioned"):
            # Initialize versioning
            if not self.version_manager.initialize_versioning(dataset, author=author):
                error = VersioningError(f"Failed to initialize versioning for dataset {name}")
                self._last_error = error
                logger.error(str(error))
                return None

            # Update dataset with version info
            dataset.version_info = {
                "is_versioned": True,
                "version_number": 1,
                "version_timestamp": datetime.now().isoformat()
            }

            # Save dataset with version info
            dataset_path = self._get_dataset_path(name)
            if not save_pickle(dataset, dataset_path):
                logger.warning(f"Failed to update dataset '{name}' with version info")

            return INITIAL_VERSION

        # Create new version
        version_number = self.version_manager.create_version(
            dataset,
            description=description,
            author=author
        )

        if version_number:
            # Update dataset with version info
            dataset.version_info["version_number"] = version_number
            dataset.version_info["version_timestamp"] = datetime.now().isoformat()

            # Save dataset with updated version info
            dataset_path = self._get_dataset_path(name)
            if not save_pickle(dataset, dataset_path):
                logger.warning(f"Failed to update dataset '{name}' with version info")

        return version_number

    def get_dataset_version(self, name: str, version_number: int) -> Optional[PhoneRecordDataset]:
        """Get a specific version of a dataset.

        Args:
            name: Dataset name
            version_number: Version number

        Returns:
            Dataset version or None if not found
        """
        # Check if dataset exists
        if not self.metadata.datasets.get(name):
            error = DatasetNotFoundError(name)
            self._last_error = error
            logger.error(str(error))
            return None

        # Get version
        return self.version_manager.get_version(name, version_number)

    def get_dataset_version_history(self, name: str) -> Optional[Dict[str, Any]]:
        """Get version history for a dataset.

        Args:
            name: Dataset name

        Returns:
            Dictionary with version history or None if not found
        """
        # Check if dataset exists
        if not self.metadata.datasets.get(name):
            error = DatasetNotFoundError(name)
            self._last_error = error
            logger.error(str(error))
            return None

        # Get version history
        history = self.version_manager.get_version_history(name)
        if not history:
            error = VersionNotFoundError(name, f"No version history found for dataset {name}")
            self._last_error = error
            logger.error(str(error))
            return None

        # Convert to dictionary
        return history.to_dict()

    def revert_to_version(self, name: str, version_number: int) -> bool:
        """Revert a dataset to a specific version.

        Args:
            name: Dataset name
            version_number: Version number to revert to

        Returns:
            True if successful, False otherwise
        """
        # Check if dataset exists
        if not self.metadata.datasets.get(name):
            error = DatasetNotFoundError(name)
            self._last_error = error
            logger.error(str(error))
            return False

        # Get version
        version_dataset = self.version_manager.get_version(name, version_number)
        if not version_dataset:
            # self._last_error already set by get_version
            return False

        # Set as current version in version manager
        if not self.version_manager.set_current_version(name, version_number):
            # self._last_error already set by set_current_version
            return False

        # Update in-memory dataset
        self.datasets[name] = version_dataset

        # Update version info
        version_dataset.version_info["version_number"] = version_number
        version_dataset.version_info["version_timestamp"] = datetime.now().isoformat()

        # Save dataset
        dataset_path = self._get_dataset_path(name)
        if not save_pickle(version_dataset, dataset_path):
            error = DatasetSaveError(name, "Failed to save reverted dataset to disk")
            self._last_error = error
            logger.error(str(error))
            return False

        logger.info(f"Reverted dataset {name} to version {version_number}")
        return True

    def compare_dataset_versions(self, dataset_name: str, first_version: int,
                                 second_version: int) -> Optional[Dict[str, Any]]:
        """Compare two versions of a dataset.

        Args:
            dataset_name: Dataset name
            first_version: First version number
            second_version: Second version number

        Returns:
            Dictionary with comparison results or None if failed
        """
        # Check if dataset exists
        if not self.metadata.datasets.get(dataset_name):
            dataset_error = DatasetNotFoundError(dataset_name)
            self._last_error = dataset_error
            logger.error(str(dataset_error))
            return None

        # Compare versions
        return self.version_manager.compare_versions(dataset_name, first_version, second_version)

    def _validate_complex_query(self, query: Dict[str, Any]) -> Optional[QueryError]:
        """Validate a complex query.

        Args:
            query: Query dictionary with dataset, conditions, etc.

        Returns:
            QueryError if validation fails, None if validation succeeds
        """
        if not isinstance(query, dict):
            return QueryError("Invalid query: must be a dictionary")

        if "dataset" not in query:
            return QueryError("Invalid query: must include 'dataset' key")

        return None

    def _execute_query_on_dataset(self, query: Dict[str, Any], dataset: PhoneRecordDataset) -> \
            Tuple[Optional[pd.DataFrame], Optional[QueryError]]:
        """Execute a query on a dataset.

        Args:
            query: Query dictionary with dataset, conditions, etc.
            dataset: Dataset to query

        Returns:
            Tuple of (result DataFrame, error) where one is None
        """
        try:
            # Import here to avoid circular imports
            from ..utils.query_utils import execute_query

            # Execute query
            result = execute_query(query, dataset.data)
            return result, None
        except Exception as e:
            error_message = f"Error executing complex query on dataset {dataset.name}: {str(e)}"
            return None, QueryError(error_message)

    def execute_complex_query(self, query: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Execute a complex query.

        Args:
            query: Query dictionary with dataset, conditions, etc.

        Returns:
            Result DataFrame, or None if error occurs
        """
        # Validate query
        validation_error = self._validate_complex_query(query)
        if validation_error:
            self._last_error = validation_error
            logger.error(str(validation_error))
            return None

        # Get dataset
        dataset_name = query["dataset"]
        dataset = self.get_dataset(dataset_name)
        if not dataset:
            # self._last_error already set by get_dataset
            return None

        # Execute query
        result, query_error = self._execute_query_on_dataset(query, dataset)
        if query_error:
            self._last_error = query_error
            logger.error(str(query_error))
            return None

        logger.info(
            f"Executed complex query on dataset {dataset_name}, returned {len(result)} rows"
        )
        return result

    def _validate_merge_inputs(self, names: List[str], new_name: str) -> Optional[DatasetError]:
        """Validate inputs for dataset merge operation.

        Args:
            names: List of dataset names to merge
            new_name: Name for the merged dataset

        Returns:
            DatasetError if validation fails, None if validation succeeds
        """
        try:
            # Validate new dataset name
            if not new_name or not isinstance(new_name, str):
                raise ValidationError(f"Invalid dataset name: {new_name}")

            # Check if new_name already exists
            if new_name in self.datasets or new_name in self.metadata.datasets:
                raise ValidationError(f"Dataset with name '{new_name}' already exists")

            # Validate names list
            if not names or not isinstance(names, list) or len(names) < MIN_DATASET_COUNT:
                raise ValidationError("At least one dataset name must be provided for merging")

            return None
        except ValidationError as validation_error:
            return DatasetError(f"Validation failed for dataset merge: {str(validation_error)}")

    def _load_datasets_for_merge(self, dataset_names: List[str]) -> \
            Tuple[List[PhoneRecordDataset], Optional[DatasetError]]:
        """Load datasets for merging.

        Args:
            dataset_names: List of dataset names to load

        Returns:
            Tuple of (list of datasets, error) where one is None
        """
        datasets = []
        for name in dataset_names:
            dataset = self.get_dataset(name)
            if not dataset:
                # self._last_error already set by get_dataset
                return [], None
            datasets.append(dataset)

        if not datasets:
            return [], DatasetError("No datasets to merge")

        return datasets, None

    def _create_merged_dataset(self, datasets: List[PhoneRecordDataset],
                             dataset_names: List[str], new_name: str) -> bool:
        """Create a merged dataset from multiple datasets.

        Args:
            datasets: List of datasets to merge
            dataset_names: Original names of the datasets
            new_name: Name for the merged dataset

        Returns:
            True if successful, False otherwise
        """
        try:
            # Concatenate DataFrames
            merged_data = pd.concat([dataset.data for dataset in datasets], ignore_index=True)

            # Use column mapping from first dataset
            column_mapping = datasets[FIRST_DATASET_INDEX].column_mapping

            # Create metadata
            metadata = {
                "source_datasets": dataset_names,
                "created_at": self.metadata.last_updated,
                "record_count": len(merged_data),
                "columns": list(merged_data.columns)
            }

            # Add merged dataset
            result = self.add_dataset(new_name, merged_data, column_mapping, metadata)
            if not result:
                # self._last_error already set by add_dataset
                return False

            return True

        except Exception as exception:
            error_message = f"Error merging datasets: {str(exception)}"
            self._last_error = DatasetError(error_message)
            logger.error(error_message)
            return False

    def merge_datasets(self, names: List[str], new_name: str) -> bool:
        """Merge multiple datasets into a new dataset.

        Args:
            names: List of dataset names to merge
            new_name: Name for the merged dataset

        Returns:
            True if successful, False otherwise
        """
        # Validate inputs
        validation_error = self._validate_merge_inputs(names, new_name)
        if validation_error:
            self._last_error = validation_error
            logger.error(str(validation_error))
            return False

        # Load datasets
        datasets, load_error = self._load_datasets_for_merge(names)
        if load_error:
            self._last_error = load_error
            logger.error(str(load_error))
            return False

        # Create merged dataset
        return self._create_merged_dataset(datasets, names, new_name)
