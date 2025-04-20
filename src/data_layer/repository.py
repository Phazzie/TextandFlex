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
        """
        return save_json(self.metadata.to_dict(), self._get_metadata_path())
    
    def _load_metadata(self) -> bool:
        """Load repository metadata from disk.
        
        Returns:
            True if successful, False otherwise
        """
        metadata_path = self._get_metadata_path()
        if not metadata_path.exists():
            logger.info("No existing metadata found")
            return False
        
        metadata_dict = load_json(metadata_path)
        if metadata_dict:
            self.metadata = RepositoryMetadata.from_dict(metadata_dict)
            logger.info(f"Loaded metadata with {len(self.metadata.datasets)} datasets")
            return True
        
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
            
            # Add to in-memory collection
            self.datasets[name] = dataset
            
            # Update metadata
            self.metadata.add_dataset(dataset)
            
            # Save dataset to disk
            dataset_path = self._get_dataset_path(name)
            if not save_pickle(dataset, dataset_path):
                logger.error(f"Failed to save dataset {name} to disk")
                return False
            
            # Save updated metadata
            if not self._save_metadata():
                logger.error("Failed to save updated metadata")
                return False
            
            logger.info(f"Added dataset {name} with {len(data)} records")
            return True
            
        except Exception as e:
            error = f"Error adding dataset: {str(e)}"
            self.last_error = error
            logger.error(error)
            return False
    
    def get_dataset(self, name: str) -> Optional[PhoneRecordDataset]:
        """Get a dataset by name.
        
        Args:
            name: Dataset name
            
        Returns:
            PhoneRecordDataset or None if not found
        """
        # Check if dataset is already loaded
        if name in self.datasets:
            return self.datasets[name]
        
        # Check if dataset exists in metadata
        if name not in self.metadata.datasets:
            logger.warning(f"Dataset {name} not found in metadata")
            return None
        
        # Try to load dataset from disk
        dataset_path = self._get_dataset_path(name)
        dataset = load_pickle(dataset_path)
        
        if dataset:
            # Add to in-memory collection
            self.datasets[name] = dataset
            logger.info(f"Loaded dataset {name} from disk")
            return dataset
        
        logger.error(f"Failed to load dataset {name} from disk")
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
                logger.error("Failed to save updated metadata")
                return False
            
            logger.info(f"Removed dataset {name}")
            return True
            
        except Exception as e:
            error = f"Error removing dataset: {str(e)}"
            self.last_error = error
            logger.error(error)
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
    
    def query_dataset(self, name: str, query_func) -> Optional[pd.DataFrame]:
        """Query a dataset using a function.
        
        Args:
            name: Dataset name
            query_func: Function that takes a DataFrame and returns a filtered DataFrame
            
        Returns:
            Filtered DataFrame or None if error
        """
        dataset = self.get_dataset(name)
        if not dataset:
            logger.error(f"Dataset {name} not found")
            return None
        
        try:
            result = query_func(dataset.data)
            return result
        except Exception as e:
            error = f"Error querying dataset: {str(e)}"
            self.last_error = error
            logger.error(error)
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
                logger.error(f"Dataset {name} not found")
                return False
            datasets.append(dataset)
        
        if not datasets:
            logger.error("No datasets to merge")
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
            return self.add_dataset(new_name, merged_data, column_mapping, metadata)
            
        except Exception as e:
            error = f"Error merging datasets: {str(e)}"
            self.last_error = error
            logger.error(error)
            return False
