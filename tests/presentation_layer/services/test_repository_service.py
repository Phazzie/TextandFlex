"""
Tests for the repository service.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.presentation_layer.services.repository_service import RepositoryService
from src.data_layer.models import PhoneRecordDataset
from src.data_layer.exceptions import DatasetNotFoundError, ValidationError


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    mock_repo = MagicMock()
    mock_repo.get_dataset_names.return_value = ["dataset1", "dataset2"]
    
    # Create a mock dataset
    mock_dataset = MagicMock(spec=PhoneRecordDataset)
    mock_dataset.name = "dataset1"
    mock_dataset.data = pd.DataFrame({
        "timestamp": ["2023-01-01 12:00:00", "2023-01-02 13:00:00"],
        "phone_number": ["123456789", "987654321"],
        "message_type": ["sent", "received"],
        "content": ["Hello", "Hi there"]
    })
    mock_dataset.column_mapping = {
        "timestamp": "timestamp",
        "phone_number": "phone_number",
        "message_type": "message_type",
        "content": "content"
    }
    mock_dataset.metadata = {
        "created_at": "2023-01-01T12:00:00",
        "record_count": 2
    }
    
    mock_repo.get_dataset.return_value = mock_dataset
    return mock_repo


@pytest.fixture
def repository_service(mock_repository):
    """Create a repository service with a mock repository."""
    return RepositoryService(repository=mock_repository)


class TestRepositoryService:
    """Tests for the RepositoryService class."""

    def test_get_dataset_names(self, repository_service, mock_repository):
        """Test getting dataset names."""
        # Act
        result = repository_service.get_dataset_names()
        
        # Assert
        assert result == ["dataset1", "dataset2"]
        mock_repository.get_dataset_names.assert_called_once()

    def test_get_dataset(self, repository_service, mock_repository):
        """Test getting a dataset."""
        # Act
        result = repository_service.get_dataset("dataset1")
        
        # Assert
        assert isinstance(result, dict)
        assert "data" in result
        assert "metadata" in result
        assert "column_mapping" in result
        assert isinstance(result["data"], pd.DataFrame)
        mock_repository.get_dataset.assert_called_once_with("dataset1")

    def test_get_dataset_not_found(self, repository_service, mock_repository):
        """Test getting a dataset that doesn't exist."""
        # Arrange
        mock_repository.get_dataset.side_effect = DatasetNotFoundError("Dataset not found")
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            repository_service.get_dataset("nonexistent")
        
        assert "Dataset not found" in str(exc_info.value)
        mock_repository.get_dataset.assert_called_once_with("nonexistent")

    def test_add_dataset(self, repository_service, mock_repository):
        """Test adding a dataset."""
        # Arrange
        mock_repository.add_dataset.return_value = True
        df = pd.DataFrame({
            "timestamp": ["2023-01-01 12:00:00"],
            "phone_number": ["123456789"],
            "message_type": ["sent"],
            "content": ["Hello"]
        })
        column_mapping = {
            "timestamp": "timestamp",
            "phone_number": "phone_number",
            "message_type": "message_type",
            "content": "content"
        }
        
        # Act
        result = repository_service.add_dataset("new_dataset", df, column_mapping)
        
        # Assert
        assert result is True
        mock_repository.add_dataset.assert_called_once_with(
            "new_dataset", df, column_mapping, {}
        )

    def test_add_dataset_validation_error(self, repository_service, mock_repository):
        """Test adding a dataset with validation error."""
        # Arrange
        mock_repository.add_dataset.side_effect = ValidationError("Invalid dataset")
        df = pd.DataFrame({"invalid_column": [1, 2, 3]})
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            repository_service.add_dataset("new_dataset", df, {})
        
        assert "Invalid dataset" in str(exc_info.value)

    def test_remove_dataset(self, repository_service, mock_repository):
        """Test removing a dataset."""
        # Arrange
        mock_repository.remove_dataset.return_value = True
        
        # Act
        result = repository_service.remove_dataset("dataset1")
        
        # Assert
        assert result is True
        mock_repository.remove_dataset.assert_called_once_with("dataset1")

    def test_get_dataset_metadata(self, repository_service, mock_repository):
        """Test getting dataset metadata."""
        # Act
        result = repository_service.get_dataset_metadata("dataset1")
        
        # Assert
        assert isinstance(result, dict)
        assert "created_at" in result
        assert "record_count" in result
        mock_repository.get_dataset.assert_called_once_with("dataset1")
