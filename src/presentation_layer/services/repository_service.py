"""
Repository Service Module
------------------------
Service for abstracting repository operations for GUI controllers.
"""
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from pathlib import Path

from src.data_layer.repository import PhoneRecordRepository
from src.data_layer.exceptions import DatasetNotFoundError, ValidationError, DatasetError


class RepositoryService:
    """
    Service for abstracting repository operations.
    
    This class provides a simplified interface for GUI controllers to interact
    with the repository, handling exceptions and data transformations.
    """
    
    def __init__(self, repository: Optional[PhoneRecordRepository] = None):
        """
        Initialize the repository service.
        
        Args:
            repository: Optional repository instance (for testing)
        """
        self.repository = repository or PhoneRecordRepository()
    
    def get_dataset_names(self) -> List[str]:
        """
        Get a list of all dataset names in the repository.
        
        Returns:
            List of dataset names
        """
        try:
            # Get dataset names from repository metadata
            if hasattr(self.repository, 'metadata') and hasattr(self.repository.metadata, 'datasets'):
                return list(self.repository.metadata.datasets.keys())
            # Fallback to direct method if available
            elif hasattr(self.repository, 'get_dataset_names'):
                return self.repository.get_dataset_names()
            else:
                return []
        except Exception as e:
            # Log error and return empty list
            print(f"Error getting dataset names: {str(e)}")
            return []
    
    def get_dataset(self, name: str) -> Dict[str, Any]:
        """
        Get a dataset by name, transformed into a dictionary format.
        
        Args:
            name: Name of the dataset to retrieve
            
        Returns:
            Dictionary containing dataset information
            
        Raises:
            ValueError: If the dataset is not found or other error occurs
        """
        try:
            dataset = self.repository.get_dataset(name)
            if not dataset:
                raise ValueError(f"Dataset '{name}' not found")
            
            # Transform to dictionary format for GUI
            return {
                "name": dataset.name,
                "data": dataset.data.copy(),
                "column_mapping": dataset.column_mapping,
                "metadata": dataset.metadata,
                "version_info": getattr(dataset, "version_info", None)
            }
        except DatasetNotFoundError as e:
            raise ValueError(f"Dataset not found: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error retrieving dataset: {str(e)}")
    
    def add_dataset(self, name: str, data: pd.DataFrame, 
                   column_mapping: Dict[str, str], 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a new dataset to the repository.
        
        Args:
            name: Name for the new dataset
            data: DataFrame containing the dataset
            column_mapping: Mapping of standard column names to actual column names
            metadata: Optional metadata for the dataset
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If validation fails or other error occurs
        """
        try:
            # Ensure data is a copy to prevent modification of original
            data_copy = data.copy()
            
            # Add dataset to repository
            success = self.repository.add_dataset(
                name, 
                data_copy, 
                column_mapping, 
                metadata or {}
            )
            
            if not success:
                error_msg = "Failed to add dataset"
                if hasattr(self.repository, 'get_last_error'):
                    error_msg = self.repository.get_last_error() or error_msg
                raise ValueError(error_msg)
                
            return success
        except ValidationError as e:
            raise ValueError(f"Invalid dataset: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error adding dataset: {str(e)}")
    
    def remove_dataset(self, name: str) -> bool:
        """
        Remove a dataset from the repository.
        
        Args:
            name: Name of the dataset to remove
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If the dataset is not found or other error occurs
        """
        try:
            success = self.repository.remove_dataset(name)
            
            if not success:
                error_msg = f"Failed to remove dataset '{name}'"
                if hasattr(self.repository, 'get_last_error'):
                    error_msg = self.repository.get_last_error() or error_msg
                raise ValueError(error_msg)
                
            return success
        except DatasetNotFoundError as e:
            raise ValueError(f"Dataset not found: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error removing dataset: {str(e)}")
    
    def get_dataset_metadata(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a dataset.
        
        Args:
            name: Name of the dataset
            
        Returns:
            Dictionary of metadata
            
        Raises:
            ValueError: If the dataset is not found or other error occurs
        """
        try:
            dataset = self.repository.get_dataset(name)
            if not dataset:
                raise ValueError(f"Dataset '{name}' not found")
            
            return dataset.metadata.copy() if dataset.metadata else {}
        except DatasetNotFoundError as e:
            raise ValueError(f"Dataset not found: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error retrieving dataset metadata: {str(e)}")
    
    def get_dataset_version_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get version information for a dataset.
        
        Args:
            name: Name of the dataset
            
        Returns:
            Dictionary of version information or None if not available
            
        Raises:
            ValueError: If the dataset is not found or other error occurs
        """
        try:
            dataset = self.repository.get_dataset(name)
            if not dataset:
                raise ValueError(f"Dataset '{name}' not found")
            
            return getattr(dataset, "version_info", None)
        except DatasetNotFoundError as e:
            raise ValueError(f"Dataset not found: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error retrieving dataset version info: {str(e)}")
    
    def create_dataset_version(self, name: str, description: str = "", 
                              author: Optional[str] = None) -> Optional[int]:
        """
        Create a new version of a dataset.
        
        Args:
            name: Name of the dataset
            description: Description of the changes
            author: Optional author name
            
        Returns:
            New version number or None if failed
            
        Raises:
            ValueError: If the dataset is not found or other error occurs
        """
        try:
            if not hasattr(self.repository, 'create_dataset_version'):
                raise ValueError("Version management not supported by repository")
                
            version = self.repository.create_dataset_version(name, description, author)
            
            if version is None:
                error_msg = f"Failed to create version for dataset '{name}'"
                if hasattr(self.repository, 'get_last_error'):
                    error_msg = self.repository.get_last_error() or error_msg
                raise ValueError(error_msg)
                
            return version
        except DatasetNotFoundError as e:
            raise ValueError(f"Dataset not found: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error creating dataset version: {str(e)}")
