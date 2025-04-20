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

from .models import PhoneRecordDataset, RepositoryMetadata
from .exceptions import (DatasetNotFoundError, DatasetSaveError, DatasetLoadError,
                        MetadataSaveError, MetadataLoadError, QueryError)
from ..utils.file_io import save_json, load_json, save_pickle, load_pickle
from ..logger import get_logger
from ..config import DATA_DIR

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
        self.last_error = None

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
            Sets self.last_error to a MetadataSaveError if saving fails
        """
        try:
            result = save_json(self.metadata.to_dict(), self._get_metadata_path())
            if not result:
                error = MetadataSaveError("Failed to save metadata to disk")
                self.last_error = error
                logger.error(str(error))
            return result
        except Exception as e:
            error = MetadataSaveError(e)
            self.last_error = error
            logger.error(str(error))
            return False

    def _load_metadata(self) -> bool:
        """Load repository metadata from disk.

        Returns:
            True if successful, False otherwise

        Note:
            Sets self.last_error to a MetadataLoadError if loading fails
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
            self.last_error = error
            logger.error(str(error))
            return False
        except Exception as e:
            error = MetadataLoadError(e)
            self.last_error = error
            logger.error(str(error))
            return False

    def add_dataset(self, name: str, data: pd.DataFrame, column_mapping: Dict[str, str],
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a dataset to the repository.

        Args:
            name: Dataset name
            data: DataFrame containing phone records
            column_mapping: Dictionary mapping logical column names to actual column names
            metadata: Optional additional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create dataset
            dataset = PhoneRecordDataset(
                name=name,
                data=data,
                column_mapping=column_mapping,
                metadata=metadata or {}
            )

            # Save dataset to disk
            dataset_path = self._get_dataset_path(name)
            if not save_pickle(dataset, dataset_path):
                error = DatasetSaveError(name, "Failed to save dataset to disk")
                self.last_error = error
                logger.error(str(error))
                # Remove from in-memory collection and metadata
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
                error = MetadataSaveError("Failed to save updated metadata")
                self.last_error = error
                logger.error(str(error))
                return False

            logger.info(f"Added dataset {name} with {len(data)} records")
            return True

        except Exception as e:
            error = DatasetError(f"Error adding dataset {name}: {str(e)}")
            self.last_error = error
            logger.error(str(error))
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
            self.last_error = error
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
            self.last_error = error
            logger.error(str(error))
            return None
        except Exception as e:
            error = DatasetLoadError(name, e)
            self.last_error = error
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
                self.last_error = error
                logger.error(str(error))
                return False

            logger.info(f"Removed dataset {name}")
            return True

        except Exception as e:
            error = DatasetError(f"Error removing dataset {name}: {str(e)}")
            self.last_error = error
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
                # self.last_error already set by get_dataset
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
                self.last_error = error
                logger.error(str(error))
                return False

            # Update metadata
            self.metadata.add_dataset(dataset)

            # Save updated metadata
            if not self._save_metadata():
                error = MetadataSaveError("Failed to save updated metadata")
                self.last_error = error
                logger.error(str(error))
                return False

            logger.info(f"Updated dataset {name} with {len(dataset.data)} records")
            return True

        except Exception as e:
            error = DatasetError(f"Error updating dataset {name}: {str(e)}")
            self.last_error = error
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
            This method sets self.last_error if an error occurs during query execution
        """
        dataset = self.get_dataset(name)
        if not dataset:
            # self.last_error already set by get_dataset
            return None

        try:
            result = query_func(dataset.data)
            return result
        except Exception as e:
            error = QueryError(f"Error querying dataset {name}: {str(e)}")
            self.last_error = error
            logger.error(str(error))
            return None

    def merge_datasets(self, names: List[str], new_name: str) -> bool:
        """Merge multiple datasets into a new dataset.

        Args:
            names: List of dataset names to merge
            new_name: Name for the merged dataset

        Returns:
            True if successful, False otherwise
        """
        # Load all datasets
        datasets = []
        for name in names:
            dataset = self.get_dataset(name)
            if not dataset:
                # self.last_error already set by get_dataset
                return False
            datasets.append(dataset)

        if not datasets:
            error = DatasetError("No datasets to merge")
            self.last_error = error
            logger.error(str(error))
            return False

        try:
            # Concatenate DataFrames
            merged_data = pd.concat([d.data for d in datasets], ignore_index=True)

            # Use column mapping from first dataset
            column_mapping = datasets[0].column_mapping

            # Create metadata
            metadata = {
                "source_datasets": names,
                "created_at": self.metadata.last_updated,
                "record_count": len(merged_data),
                "columns": list(merged_data.columns)
            }

            # Add merged dataset
            result = self.add_dataset(new_name, merged_data, column_mapping, metadata)
            if not result:
                # self.last_error already set by add_dataset
                return False

            return True

        except Exception as e:
            error = DatasetError(f"Error merging datasets: {str(e)}")
            self.last_error = error
            logger.error(str(error))
            return False
