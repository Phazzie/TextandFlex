"""
Version Metadata Module
-------------------
Models for dataset version metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..logger import get_logger
from .exceptions import ValidationError

logger = get_logger("version_metadata")

@dataclass
class DatasetVersion:
    """Metadata for a dataset version."""
    version_number: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    author: Optional[str] = None
    description: str = ""
    changes: Dict[str, Any] = field(default_factory=dict)
    parent_version: Optional[int] = None
    
    def __post_init__(self):
        """Validate the version metadata."""
        # Validate version number
        if not isinstance(self.version_number, int) or self.version_number < 1:
            raise ValidationError("Version number must be a positive integer")
        
        # Validate timestamp
        try:
            datetime.fromisoformat(self.timestamp)
        except ValueError:
            raise ValidationError(f"Invalid timestamp format: {self.timestamp}")
        
        # Validate description
        if not isinstance(self.description, str):
            raise ValidationError("Description must be a string")
        
        # Validate changes
        if not isinstance(self.changes, dict):
            raise ValidationError("Changes must be a dictionary")
        
        # Validate parent version
        if self.parent_version is not None and (not isinstance(self.parent_version, int) or self.parent_version < 1):
            raise ValidationError("Parent version must be a positive integer")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the version metadata
        """
        return {
            "version_number": self.version_number,
            "timestamp": self.timestamp,
            "author": self.author,
            "description": self.description,
            "changes": self.changes,
            "parent_version": self.parent_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetVersion':
        """Create from dictionary.
        
        Args:
            data: Dictionary representation of version metadata
            
        Returns:
            DatasetVersion instance
        """
        return cls(
            version_number=data.get("version_number", 1),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            author=data.get("author"),
            description=data.get("description", ""),
            changes=data.get("changes", {}),
            parent_version=data.get("parent_version")
        )
    
    def __str__(self) -> str:
        """String representation of the version metadata.
        
        Returns:
            String representation
        """
        return f"Version {self.version_number} ({self.timestamp}): {self.description}"


@dataclass
class VersionHistory:
    """History of dataset versions."""
    dataset_name: str
    versions: Dict[int, DatasetVersion] = field(default_factory=dict)
    current_version: int = 1
    
    def __post_init__(self):
        """Validate the version history."""
        # Validate dataset name
        if not isinstance(self.dataset_name, str) or not self.dataset_name:
            raise ValidationError("Dataset name must be a non-empty string")
        
        # Validate versions
        if not isinstance(self.versions, dict):
            raise ValidationError("Versions must be a dictionary")
        
        for version_number, version in self.versions.items():
            if not isinstance(version_number, int) or version_number < 1:
                raise ValidationError(f"Invalid version number: {version_number}")
            
            if not isinstance(version, DatasetVersion):
                raise ValidationError(f"Invalid version metadata for version {version_number}")
        
        # Validate current version
        if not isinstance(self.current_version, int) or self.current_version < 1:
            raise ValidationError("Current version must be a positive integer")
        
        if self.versions and self.current_version not in self.versions:
            raise ValidationError(f"Current version {self.current_version} not found in versions")
    
    def add_version(self, version: DatasetVersion) -> None:
        """Add a version to the history.
        
        Args:
            version: Version metadata to add
        """
        if version.version_number in self.versions:
            raise ValidationError(f"Version {version.version_number} already exists")
        
        self.versions[version.version_number] = version
        self.current_version = version.version_number
    
    def get_version(self, version_number: int) -> Optional[DatasetVersion]:
        """Get a specific version.
        
        Args:
            version_number: Version number to get
            
        Returns:
            Version metadata or None if not found
        """
        return self.versions.get(version_number)
    
    def get_current_version(self) -> Optional[DatasetVersion]:
        """Get the current version.
        
        Returns:
            Current version metadata or None if no versions exist
        """
        return self.versions.get(self.current_version)
    
    def get_version_numbers(self) -> List[int]:
        """Get all version numbers.
        
        Returns:
            List of version numbers
        """
        return sorted(self.versions.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the version history
        """
        return {
            "dataset_name": self.dataset_name,
            "versions": {str(k): v.to_dict() for k, v in self.versions.items()},
            "current_version": self.current_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VersionHistory':
        """Create from dictionary.
        
        Args:
            data: Dictionary representation of version history
            
        Returns:
            VersionHistory instance
        """
        versions_dict = {}
        for k, v in data.get("versions", {}).items():
            try:
                version_number = int(k)
                versions_dict[version_number] = DatasetVersion.from_dict(v)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid version number {k}: {str(e)}")
        
        return cls(
            dataset_name=data.get("dataset_name", ""),
            versions=versions_dict,
            current_version=data.get("current_version", 1)
        )
    
    def __str__(self) -> str:
        """String representation of the version history.
        
        Returns:
            String representation
        """
        versions_str = ", ".join(str(v) for v in self.get_version_numbers())
        return f"Version history for {self.dataset_name} (current: {self.current_version}): [{versions_str}]"
