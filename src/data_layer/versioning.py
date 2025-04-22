"""
Versioning Module
-------------
Functionality for dataset versioning.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import pandas as pd
import json
import shutil
from datetime import datetime

from .version_metadata import DatasetVersion, VersionHistory
from .models import PhoneRecordDataset
from .exceptions import (
    ValidationError, VersioningError, DatasetNotFoundError,
    VersionNotFoundError, DatasetLoadError, DatasetSaveError
)
from ..utils.file_io import save_json, load_json, save_pickle, load_pickle
from ..logger import get_logger

# Constants
INITIAL_VERSION = 1
VERSION_FILE_PREFIX = "v"
VERSION_HISTORY_SUFFIX = "_version_history.json"
VERSION_DATA_SUFFIX = "_{prefix}{number}.pkl"

logger = get_logger("versioning")

class VersionManager:
    """Manager for dataset versions."""

    def __init__(self, storage_dir: Optional[Union[str, Path]] = None):
        """Initialize the version manager.

        Args:
            storage_dir: Directory for storing version data (default: None, uses repository storage)
        """
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self.version_histories: Dict[str, VersionHistory] = {}
        self.last_error = None

    def _get_version_history_path(self, dataset_name: str) -> Path:
        """Get the path to the version history file.

        Args:
            dataset_name: Dataset name

        Returns:
            Path to version history file
        """
        if not self.storage_dir:
            raise VersioningError("Storage directory not set")

        return self.storage_dir / f"{dataset_name}{VERSION_HISTORY_SUFFIX}"

    def _get_version_data_path(self, dataset_name: str, version_number: int) -> Path:
        """Get the path to a version data file.

        Args:
            dataset_name: Dataset name
            version_number: Version number

        Returns:
            Path to version data file
        """
        if not self.storage_dir:
            raise VersioningError("Storage directory not set")

        return self.storage_dir / f"{dataset_name}{VERSION_DATA_SUFFIX.format(prefix=VERSION_FILE_PREFIX, number=version_number)}"

    def _load_version_history(self, dataset_name: str) -> Optional[VersionHistory]:
        """Load version history from disk.

        Args:
            dataset_name: Dataset name

        Returns:
            VersionHistory or None if not found
        """
        try:
            history_path = self._get_version_history_path(dataset_name)
            if not history_path.exists():
                logger.info(f"No version history found for dataset {dataset_name}")
                return None

            history_dict = load_json(history_path)
            if not history_dict:
                logger.warning(f"Failed to load version history for dataset {dataset_name}")
                return None

            history = VersionHistory.from_dict(history_dict)
            self.version_histories[dataset_name] = history
            logger.info(f"Loaded version history for dataset {dataset_name} with {len(history.versions)} versions")
            return history

        except Exception as e:
            error_msg = f"Error loading version history for dataset {dataset_name}: {str(e)}"
            self.last_error = VersioningError(error_msg)
            logger.error(error_msg)
            return None

    def _save_version_history(self, history: VersionHistory) -> bool:
        """Save version history to disk.

        Args:
            history: Version history to save

        Returns:
            True if successful, False otherwise
        """
        try:
            history_path = self._get_version_history_path(history.dataset_name)
            result = save_json(history.to_dict(), history_path)

            if not result:
                error_msg = f"Failed to save version history for dataset {history.dataset_name}"
                self.last_error = VersioningError(error_msg)
                logger.error(error_msg)
                return False

            logger.info(f"Saved version history for dataset {history.dataset_name}")
            return True

        except Exception as e:
            error_msg = f"Error saving version history for dataset {history.dataset_name}: {str(e)}"
            self.last_error = VersioningError(error_msg)
            logger.error(error_msg)
            return False

    def initialize_versioning(self, dataset: PhoneRecordDataset, author: Optional[str] = None) -> bool:
        """Initialize versioning for a dataset.

        Args:
            dataset: Dataset to initialize versioning for
            author: Optional author name

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create initial version
            initial_version = DatasetVersion(
                version_number=INITIAL_VERSION,
                author=author,
                description="Initial version",
                changes={"type": "initial", "record_count": len(dataset.data)}
            )

            # Create version history
            history = VersionHistory(
                dataset_name=dataset.name,
                versions={INITIAL_VERSION: initial_version},
                current_version=INITIAL_VERSION
            )

            # Save version history
            if not self._save_version_history(history):
                return False

            # Save version data
            version_path = self._get_version_data_path(dataset.name, INITIAL_VERSION)
            if not save_pickle(dataset, version_path):
                error_msg = f"Failed to save initial version data for dataset {dataset.name}"
                self.last_error = VersioningError(error_msg)
                logger.error(error_msg)
                return False

            # Store in memory
            self.version_histories[dataset.name] = history

            logger.info(f"Initialized versioning for dataset {dataset.name}")
            return True

        except Exception as e:
            error_msg = f"Error initializing versioning for dataset {dataset.name}: {str(e)}"
            self.last_error = VersioningError(error_msg)
            logger.error(error_msg)
            return False

    def create_version(self, dataset: PhoneRecordDataset, description: str = "",
                      author: Optional[str] = None, changes: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """Create a new version of a dataset.

        Args:
            dataset: Dataset to create a version for
            description: Description of the changes
            author: Optional author name
            changes: Optional dictionary of changes

        Returns:
            New version number or None if failed
        """
        try:
            # Get version history
            history = self.get_version_history(dataset.name)
            if not history:
                # Initialize versioning if not already done
                if not self.initialize_versioning(dataset, author):
                    return None
                return INITIAL_VERSION

            # Get current version
            current_version = history.get_current_version()
            if not current_version:
                error_msg = f"No current version found for dataset {dataset.name}"
                self.last_error = VersioningError(error_msg)
                logger.error(error_msg)
                return None

            # Create new version
            new_version_number = max(history.get_version_numbers()) + 1
            new_version = DatasetVersion(
                version_number=new_version_number,
                author=author,
                description=description,
                changes=changes or {"type": "update", "record_count": len(dataset.data)},
                parent_version=current_version.version_number
            )

            # Add to history
            history.add_version(new_version)

            # Save version history
            if not self._save_version_history(history):
                return None

            # Save version data
            version_path = self._get_version_data_path(dataset.name, new_version_number)
            if not save_pickle(dataset, version_path):
                error_msg = f"Failed to save version {new_version_number} data for dataset {dataset.name}"
                self.last_error = VersioningError(error_msg)
                logger.error(error_msg)
                return None

            logger.info(f"Created version {new_version_number} for dataset {dataset.name}")
            return new_version_number

        except Exception as e:
            error_msg = f"Error creating version for dataset {dataset.name}: {str(e)}"
            self.last_error = VersioningError(error_msg)
            logger.error(error_msg)
            return None

    def get_version_history(self, dataset_name: str) -> Optional[VersionHistory]:
        """Get version history for a dataset.

        Args:
            dataset_name: Dataset name

        Returns:
            VersionHistory or None if not found
        """
        # Check if already loaded
        if dataset_name in self.version_histories:
            return self.version_histories[dataset_name]

        # Try to load from disk
        return self._load_version_history(dataset_name)

    def get_version(self, dataset_name: str, version_number: int) -> Optional[PhoneRecordDataset]:
        """Get a specific version of a dataset.

        Args:
            dataset_name: Dataset name
            version_number: Version number

        Returns:
            Dataset version or None if not found
        """
        try:
            # Get version history
            history = self.get_version_history(dataset_name)
            if not history:
                error_msg = f"No version history found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return None

            # Check if version exists
            if version_number not in history.versions:
                error_msg = f"Version {version_number} not found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return None

            # Load version data
            version_path = self._get_version_data_path(dataset_name, version_number)
            if not version_path.exists():
                error_msg = f"Version {version_number} data not found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return None

            dataset = load_pickle(version_path)
            if not dataset:
                error_msg = f"Failed to load version {version_number} data for dataset {dataset_name}"
                self.last_error = DatasetLoadError(dataset_name, error_msg)
                logger.error(error_msg)
                return None

            logger.info(f"Loaded version {version_number} for dataset {dataset_name}")
            return dataset

        except Exception as e:
            error_msg = f"Error getting version {version_number} for dataset {dataset_name}: {str(e)}"
            self.last_error = VersioningError(error_msg)
            logger.error(error_msg)
            return None

    def get_current_version(self, dataset_name: str) -> Optional[PhoneRecordDataset]:
        """Get the current version of a dataset.

        Args:
            dataset_name: Dataset name

        Returns:
            Current dataset version or None if not found
        """
        try:
            # Get version history
            history = self.get_version_history(dataset_name)
            if not history:
                error_msg = f"No version history found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return None

            # Get current version number
            current_version = history.current_version

            # Load current version
            return self.get_version(dataset_name, current_version)

        except Exception as e:
            error_msg = f"Error getting current version for dataset {dataset_name}: {str(e)}"
            self.last_error = VersioningError(error_msg)
            logger.error(error_msg)
            return None

    def set_current_version(self, dataset_name: str, version_number: int) -> bool:
        """Set the current version of a dataset.

        Args:
            dataset_name: Dataset name
            version_number: Version number to set as current

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get version history
            history = self.get_version_history(dataset_name)
            if not history:
                error_msg = f"No version history found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return False

            # Check if version exists
            if version_number not in history.versions:
                error_msg = f"Version {version_number} not found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return False

            # Set current version
            history.current_version = version_number

            # Save version history
            if not self._save_version_history(history):
                return False

            logger.info(f"Set current version to {version_number} for dataset {dataset_name}")
            return True

        except Exception as e:
            error_msg = f"Error setting current version for dataset {dataset_name}: {str(e)}"
            self.last_error = VersioningError(error_msg)
            logger.error(error_msg)
            return False

    def _compare_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, Any]:
        """Compare two DataFrames and return detailed differences.

        Args:
            df1: First DataFrame
            df2: Second DataFrame

        Returns:
            Dictionary with detailed comparison results
        """
        # Get common columns
        common_columns = set(df1.columns).intersection(set(df2.columns))

        # Calculate added and removed columns
        added_columns = list(set(df2.columns) - set(df1.columns))
        removed_columns = list(set(df1.columns) - set(df2.columns))

        # Calculate added and removed rows (based on index)
        if df1.index.name and df2.index.name and df1.index.name == df2.index.name:
            # If both DataFrames have named indices, use them for comparison
            added_indices = list(set(df2.index) - set(df1.index))
            removed_indices = list(set(df1.index) - set(df2.index))
            common_indices = list(set(df1.index).intersection(set(df2.index)))

            # For common indices, find modified values
            modified_cells = []
            for idx in common_indices:
                for col in common_columns:
                    if df1.loc[idx, col] != df2.loc[idx, col]:
                        modified_cells.append({
                            "index": idx,
                            "column": col,
                            "old_value": df1.loc[idx, col],
                            "new_value": df2.loc[idx, col]
                        })
        else:
            # If indices are not comparable, use row-by-row comparison
            # This is less accurate but provides a reasonable approximation
            added_indices = []
            removed_indices = []
            modified_cells = []

            # Check for modified values in common columns
            if len(df1) == len(df2):
                for i in range(min(len(df1), len(df2))):
                    for col in common_columns:
                        if df1.iloc[i][col] != df2.iloc[i][col]:
                            modified_cells.append({
                                "row": i,
                                "column": col,
                                "old_value": df1.iloc[i][col],
                                "new_value": df2.iloc[i][col]
                            })

        # Calculate statistical differences for numeric columns
        stat_diffs = {}
        for col in common_columns:
            if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col]):
                stat_diffs[col] = {
                    "mean_diff": df2[col].mean() - df1[col].mean(),
                    "std_diff": df2[col].std() - df1[col].std(),
                    "min_diff": df2[col].min() - df1[col].min(),
                    "max_diff": df2[col].max() - df1[col].max()
                }

        return {
            "added_columns": added_columns,
            "removed_columns": removed_columns,
            "added_indices": added_indices[:100] if len(added_indices) > 100 else added_indices,  # Limit to 100 items
            "removed_indices": removed_indices[:100] if len(removed_indices) > 100 else removed_indices,
            "modified_cells": modified_cells[:100] if len(modified_cells) > 100 else modified_cells,
            "statistical_differences": stat_diffs
        }

    def _get_version_metadata_diff(self, metadata1: DatasetVersion, metadata2: DatasetVersion) -> Dict[str, Any]:
        """Compare metadata between two versions and return differences.

        Args:
            metadata1: First version metadata
            metadata2: Second version metadata

        Returns:
            Dictionary with metadata differences
        """
        # Compare authors
        author_diff = metadata1.author != metadata2.author

        # Compare timestamps
        time_diff = (metadata2.timestamp - metadata1.timestamp).total_seconds()

        # Compare descriptions
        desc_diff = metadata1.description != metadata2.description

        # Compare changes dictionaries
        changes_diff = {}
        for k, v in metadata2.changes.items():
            if k not in metadata1.changes:
                changes_diff[k] = {"type": "added", "value": v}
            elif metadata1.changes[k] != v:
                changes_diff[k] = {
                    "type": "modified",
                    "old_value": metadata1.changes[k],
                    "new_value": v
                }

        for k, v in metadata1.changes.items():
            if k not in metadata2.changes:
                changes_diff[k] = {"type": "removed", "value": v}

        return {
            "author_changed": author_diff,
            "time_difference_seconds": time_diff,
            "description_changed": desc_diff,
            "changes_diff": changes_diff
        }

    def compare_versions(self, dataset_name: str, version1: int, version2: int) -> Optional[Dict[str, Any]]:
        """Compare two versions of a dataset with enhanced detail.

        Args:
            dataset_name: Dataset name
            version1: First version number
            version2: Second version number

        Returns:
            Dictionary with detailed comparison results or None if failed
        """
        try:
            # Load both versions
            dataset1 = self.get_version(dataset_name, version1)
            dataset2 = self.get_version(dataset_name, version2)

            if not dataset1 or not dataset2:
                return None

            # Get version metadata
            history = self.get_version_history(dataset_name)
            if not history:
                error_msg = f"No version history found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return None

            metadata1 = history.get_version(version1)
            metadata2 = history.get_version(version2)

            if not metadata1 or not metadata2:
                error_msg = f"Version metadata not found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return None

            # Compare basic properties
            comparison = {
                "dataset_name": dataset_name,
                "version1": version1,
                "version2": version2,
                "timestamp1": metadata1.timestamp,
                "timestamp2": metadata2.timestamp,
                "record_count1": len(dataset1.data),
                "record_count2": len(dataset2.data),
                "record_count_diff": len(dataset2.data) - len(dataset1.data),
                "column_count1": len(dataset1.data.columns),
                "column_count2": len(dataset2.data.columns)
            }

            # Add enhanced data comparisons
            comparison["data_diff"] = self._compare_dataframes(dataset1.data, dataset2.data)

            # Add enhanced metadata comparisons
            comparison["metadata_diff"] = self._get_version_metadata_diff(metadata1, metadata2)

            # Add lineage information
            comparison["lineage"] = {
                "version1_parent": metadata1.parent_version,
                "version2_parent": metadata2.parent_version,
                "direct_relationship": (
                    metadata1.parent_version == version2 or
                    metadata2.parent_version == version1
                )
            }

            logger.info(f"Compared versions {version1} and {version2} for dataset {dataset_name} with enhanced detail")
            return comparison

        except Exception as e:
            error_msg = f"Error comparing versions for dataset {dataset_name}: {str(e)}"
            self.last_error = VersioningError(error_msg)
            logger.error(error_msg)
            return None

    def delete_version(self, dataset_name: str, version_number: int) -> bool:
        """Delete a version of a dataset.

        Args:
            dataset_name: Dataset name
            version_number: Version number to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get version history
            history = self.get_version_history(dataset_name)
            if not history:
                error_msg = f"No version history found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return False

            # Check if version exists
            if version_number not in history.versions:
                error_msg = f"Version {version_number} not found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return False

            # Check if it's the current version
            if version_number == history.current_version:
                error_msg = f"Cannot delete current version {version_number} for dataset {dataset_name}"
                self.last_error = VersioningError(error_msg)
                logger.error(error_msg)
                return False

            # Check if it's the only version
            if len(history.versions) == 1:
                error_msg = f"Cannot delete the only version for dataset {dataset_name}"
                self.last_error = VersioningError(error_msg)
                logger.error(error_msg)
                return False

            # Delete version data file
            version_path = self._get_version_data_path(dataset_name, version_number)
            if version_path.exists():
                version_path.unlink()

            # Remove from history
            del history.versions[version_number]

            # Update parent references
            for v in history.versions.values():
                if v.parent_version == version_number:
                    # Find the nearest ancestor
                    deleted_version = history.get_version(version_number)
                    if deleted_version and deleted_version.parent_version:
                        v.parent_version = deleted_version.parent_version
                    else:
                        v.parent_version = None

            # Save version history
            if not self._save_version_history(history):
                return False

            logger.info(f"Deleted version {version_number} for dataset {dataset_name}")
            return True

        except Exception as e:
            error_msg = f"Error deleting version {version_number} for dataset {dataset_name}: {str(e)}"
            self.last_error = VersioningError(error_msg)
            logger.error(error_msg)
            return False

    def get_version_lineage(self, dataset_name: str) -> Optional[Dict[int, List[int]]]:
        """Get the version lineage (parent-child relationships) for a dataset.

        Args:
            dataset_name: Dataset name

        Returns:
            Dictionary mapping version numbers to lists of child version numbers, or None if failed
        """
        try:
            # Get version history
            history = self.get_version_history(dataset_name)
            if not history:
                error_msg = f"No version history found for dataset {dataset_name}"
                self.last_error = VersionNotFoundError(dataset_name, error_msg)
                logger.error(error_msg)
                return None

            # Build lineage
            lineage = {}
            for version_number, version in history.versions.items():
                lineage[version_number] = []

            for version_number, version in history.versions.items():
                if version.parent_version:
                    if version.parent_version in lineage:
                        lineage[version.parent_version].append(version_number)

            logger.info(f"Generated version lineage for dataset {dataset_name}")
            return lineage

        except Exception as e:
            error_msg = f"Error getting version lineage for dataset {dataset_name}: {str(e)}"
            self.last_error = VersioningError(error_msg)
            logger.error(error_msg)
            return None
