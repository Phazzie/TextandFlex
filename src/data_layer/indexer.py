"""
Indexer Module
-----------
Provides indexing capabilities for faster querying of phone record datasets.
"""

import pandas as pd
from typing import Dict, List, Optional, Union, Any, Set
from collections import defaultdict

from ..logger import get_logger
from .repository import PhoneRecordRepository

logger = get_logger("indexer")

class DatasetIndexer:
    """Indexer for phone record datasets."""
    
    def __init__(self, repository: PhoneRecordRepository):
        """Initialize the indexer.
        
        Args:
            repository: Repository to index
        """
        self.repository = repository
        self.indices: Dict[str, Dict[str, Dict[Any, List[int]]]] = {}
    
    def create_index(self, dataset_name: str, column_name: str) -> bool:
        """Create an index for a dataset column.
        
        Args:
            dataset_name: Name of the dataset to index
            column_name: Name of the column to index
            
        Returns:
            True if successful, False otherwise
        """
        # Get the dataset
        dataset = self.repository.get_dataset(dataset_name)
        if dataset is None:
            logger.error(f"Dataset {dataset_name} not found")
            return False
        
        # Check if the column exists
        if column_name not in dataset.data.columns:
            logger.error(f"Column {column_name} not found in dataset {dataset_name}")
            return False
        
        try:
            # Create the index
            index = defaultdict(list)
            
            # Build the index
            for i, value in enumerate(dataset.data[column_name]):
                if pd.notna(value):  # Skip NaN values
                    index[value].append(i)
            
            # Store the index
            if dataset_name not in self.indices:
                self.indices[dataset_name] = {}
            
            self.indices[dataset_name][column_name] = dict(index)
            
            logger.info(f"Created index for {dataset_name}.{column_name} with {len(index)} unique values")
            return True
            
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            return False
    
    def get_index(self, dataset_name: str, column_name: str) -> Optional[Dict[Any, List[int]]]:
        """Get an index.
        
        Args:
            dataset_name: Name of the dataset
            column_name: Name of the column
            
        Returns:
            Index dictionary or None if not found
        """
        if dataset_name not in self.indices or column_name not in self.indices[dataset_name]:
            logger.warning(f"Index for {dataset_name}.{column_name} not found")
            return None
        
        return self.indices[dataset_name][column_name]
    
    def query_by_index(self, dataset_name: str, column_name: str, value: Any) -> Optional[pd.DataFrame]:
        """Query a dataset using an index.
        
        Args:
            dataset_name: Name of the dataset to query
            column_name: Name of the column to query
            value: Value to search for
            
        Returns:
            Filtered DataFrame or None if error
        """
        # Get the index
        index = self.get_index(dataset_name, column_name)
        if index is None:
            logger.warning(f"Index for {dataset_name}.{column_name} not found")
            return None
        
        # Get the dataset
        dataset = self.repository.get_dataset(dataset_name)
        if dataset is None:
            logger.error(f"Dataset {dataset_name} not found")
            return None
        
        # Get the row indices for the value
        row_indices = index.get(value, [])
        
        # Return the filtered DataFrame
        return dataset.data.iloc[row_indices]
    
    def remove_index(self, dataset_name: str, column_name: str) -> bool:
        """Remove an index.
        
        Args:
            dataset_name: Name of the dataset
            column_name: Name of the column
            
        Returns:
            True if successful, False otherwise
        """
        if dataset_name not in self.indices or column_name not in self.indices[dataset_name]:
            logger.warning(f"Index for {dataset_name}.{column_name} not found")
            return False
        
        try:
            # Remove the index
            del self.indices[dataset_name][column_name]
            
            # Remove the dataset entry if it's empty
            if not self.indices[dataset_name]:
                del self.indices[dataset_name]
            
            logger.info(f"Removed index for {dataset_name}.{column_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing index: {str(e)}")
            return False
    
    def create_indices_for_dataset(self, dataset_name: str, columns: List[str]) -> bool:
        """Create indices for multiple columns in a dataset.
        
        Args:
            dataset_name: Name of the dataset to index
            columns: List of column names to index
            
        Returns:
            True if all indices were created successfully, False otherwise
        """
        success = True
        
        for column in columns:
            if not self.create_index(dataset_name, column):
                success = False
        
        return success
    
    def query_by_multiple_indices(self, dataset_name: str, criteria: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Query a dataset using multiple indices.
        
        Args:
            dataset_name: Name of the dataset to query
            criteria: Dictionary mapping column names to values
            
        Returns:
            Filtered DataFrame or None if error
        """
        # Get the dataset
        dataset = self.repository.get_dataset(dataset_name)
        if dataset is None:
            logger.error(f"Dataset {dataset_name} not found")
            return None
        
        # Start with all row indices
        all_indices: Optional[Set[int]] = None
        
        # Process each criterion
        for column, value in criteria.items():
            # Get the index
            index = self.get_index(dataset_name, column)
            if index is None:
                logger.warning(f"Index for {dataset_name}.{column} not found")
                continue
            
            # Get the row indices for the value
            row_indices = set(index.get(value, []))
            
            # Intersect with previous indices
            if all_indices is None:
                all_indices = row_indices
            else:
                all_indices &= row_indices
            
            # If no rows match, we can stop early
            if not all_indices:
                break
        
        # If no indices were found, return an empty DataFrame
        if all_indices is None or not all_indices:
            return dataset.data.iloc[0:0]  # Empty DataFrame with same columns
        
        # Return the filtered DataFrame
        return dataset.data.iloc[list(all_indices)]
