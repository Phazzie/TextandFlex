"""
Data Models Module
--------------
Data structures for phone records.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import pandas as pd
import json

@dataclass
class PhoneRecordDataset:
    """Dataset containing phone records."""
    name: str
    data: pd.DataFrame
    column_mapping: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if not self.metadata:
            self.metadata = {
                "created_at": datetime.now().isoformat(),
                "record_count": len(self.data),
                "columns": list(self.data.columns)
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding DataFrame).
        
        Returns:
            Dictionary representation of metadata
        """
        return {
            "name": self.name,
            "column_mapping": self.column_mapping,
            "metadata": self.metadata
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the dataset.
        
        Returns:
            Dictionary with summary information
        """
        return {
            "name": self.name,
            "record_count": len(self.data),
            "columns": list(self.data.columns),
            "column_mapping": self.column_mapping,
            "created_at": self.metadata.get("created_at")
        }

@dataclass
class RepositoryMetadata:
    """Metadata for the repository."""
    datasets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "datasets": self.datasets,
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }
    
    def update_last_updated(self):
        """Update the last_updated timestamp."""
        self.last_updated = datetime.now().isoformat()
    
    def add_dataset(self, dataset: PhoneRecordDataset):
        """Add a dataset to the metadata.
        
        Args:
            dataset: Dataset to add
        """
        self.datasets[dataset.name] = dataset.to_dict()
        self.update_last_updated()
    
    def remove_dataset(self, name: str):
        """Remove a dataset from the metadata.
        
        Args:
            name: Name of the dataset to remove
        """
        if name in self.datasets:
            del self.datasets[name]
            self.update_last_updated()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RepositoryMetadata':
        """Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            RepositoryMetadata instance
        """
        return cls(
            datasets=data.get("datasets", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_updated=data.get("last_updated", datetime.now().isoformat())
        )
