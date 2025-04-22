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

from .validation_schema import validate_dataset_metadata, validate_column_mapping, validate_dataset_properties
from .exceptions import ValidationError
from ..logger import get_logger

logger = get_logger("models")

@dataclass
class PhoneRecordDataset:
    """Dataset containing phone records."""
    name: str
    data: pd.DataFrame
    column_mapping: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    version_info: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize metadata if not provided and validate the dataset."""
        # Initialize metadata if not provided
        if not self.metadata:
            self.metadata = {
                "created_at": datetime.now().isoformat(),
                "record_count": len(self.data),
                "columns": list(self.data.columns)
            }

        # Initialize version info if not provided
        if self.version_info is None:
            self.version_info = {
                "is_versioned": False,
                "version_number": None,
                "version_timestamp": None
            }

        # Validate the dataset
        try:
            # Validate column mapping
            validate_column_mapping(self.column_mapping)

            # Validate dataset properties
            validate_dataset_properties(self.data, self.column_mapping)

            # Validate metadata
            validate_dataset_metadata(self.metadata)
        except ValidationError as e:
            logger.error(f"Dataset validation failed: {str(e)}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding DataFrame).

        Returns:
            Dictionary representation of metadata
        """
        return {
            "name": self.name,
            "column_mapping": self.column_mapping,
            "metadata": self.metadata,
            "version_info": self.version_info
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the dataset.

        Returns:
            Dictionary with summary information
        """
        summary = {
            "name": self.name,
            "record_count": len(self.data),
            "columns": list(self.data.columns),
            "column_mapping": self.column_mapping,
            "created_at": self.metadata.get("created_at")
        }

        # Add version info if available
        if self.version_info and self.version_info.get("is_versioned"):
            summary["is_versioned"] = True
            summary["version_number"] = self.version_info.get("version_number")
            summary["version_timestamp"] = self.version_info.get("version_timestamp")
        else:
            summary["is_versioned"] = False

        return summary

@dataclass
class RepositoryMetadata:
    """Metadata for the repository."""
    datasets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Validate the repository metadata."""
        # Validate created_at and last_updated
        try:
            datetime.fromisoformat(self.created_at)
            datetime.fromisoformat(self.last_updated)
        except ValueError as e:
            logger.error(f"Repository metadata validation failed: {str(e)}")
            raise ValidationError(f"Invalid datetime format: {str(e)}")

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
        # Validate the dataset
        try:
            validate_dataset_metadata(dataset.metadata)
            validate_column_mapping(dataset.column_mapping)
        except ValidationError as e:
            logger.error(f"Dataset validation failed: {str(e)}")
            raise

        self.datasets[dataset.name] = dataset.to_dict()
        self.update_last_updated()

    def add_dataset_metadata(self, name: str, dataset_dict: Dict[str, Any]):
        """Add dataset metadata directly.

        Args:
            name: Dataset name
            dataset_dict: Dictionary containing dataset metadata

        Raises:
            ValidationError: If validation fails
        """
        # Validate the dataset dictionary
        if "column_mapping" not in dataset_dict:
            raise ValidationError("Missing column_mapping in dataset metadata")

        if "metadata" not in dataset_dict:
            raise ValidationError("Missing metadata in dataset metadata")

        try:
            validate_column_mapping(dataset_dict["column_mapping"])
            validate_dataset_metadata(dataset_dict["metadata"])
        except ValidationError as e:
            logger.error(f"Dataset metadata validation failed: {str(e)}")
            raise

        self.datasets[name] = dataset_dict
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


@dataclass
class Message:
    """Individual message record."""
    timestamp: str
    phone_number: str
    message_type: str  # 'sent' or 'received'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "timestamp": self.timestamp,
            "phone_number": self.phone_number,
            "message_type": self.message_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Message instance
        """
        return cls(
            timestamp=data.get("timestamp", ""),
            phone_number=data.get("phone_number", ""),
            message_type=data.get("message_type", "")
        )


@dataclass
class Contact:
    """Contact with associated messages."""
    phone_number: str
    messages: List[Message] = field(default_factory=list)

    def add_message(self, message: Message):
        """Add a message to this contact.

        Args:
            message: Message to add
        """
        self.messages.append(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "phone_number": self.phone_number,
            "messages": [message.to_dict() for message in self.messages]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contact':
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Contact instance
        """
        contact = cls(
            phone_number=data.get("phone_number", "")
        )

        # Add messages
        for message_data in data.get("messages", []):
            contact.add_message(Message.from_dict(message_data))

        return contact
