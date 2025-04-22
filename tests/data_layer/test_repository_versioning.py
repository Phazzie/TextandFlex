"""
Tests for repository versioning functionality.
"""
import pytest
import pandas as pd
from pathlib import Path
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.data_layer.repository import Repository
from src.data_layer.models import PhoneRecordDataset
from src.data_layer.exceptions import (
    DatasetNotFoundError, ValidationError, VersioningError, VersionNotFoundError
)


@pytest.fixture
def temp_repo_dir(tmpdir):
    """Create a temporary directory for repository data."""
    repo_dir = Path(tmpdir) / "repo_data"
    repo_dir.mkdir(exist_ok=True)
    yield repo_dir
    # Clean up
    shutil.rmtree(repo_dir, ignore_errors=True)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "timestamp": ["2023-01-01 12:00:00", "2023-01-01 12:30:00", "2023-01-01 13:00:00"],
        "phone_number": ["1234567890", "9876543210", "5555555555"],
        "message_type": ["sent", "received", "sent"],
        "message_content": ["Hello, world!", "Hi there!", "Testing..."]
    })


@pytest.fixture
def sample_column_mapping():
    """Create a sample column mapping for testing."""
    return {
        "timestamp": "timestamp",
        "phone_number": "phone_number",
        "message_type": "message_type",
        "message_content": "message_content"
    }


@pytest.fixture
def repository(temp_repo_dir):
    """Create a repository for testing."""
    return Repository(storage_dir=temp_repo_dir)


@pytest.mark.unit
def test_add_dataset_with_versioning(repository, sample_dataframe, sample_column_mapping):
    """Test adding a dataset with versioning enabled."""
    # Add dataset with versioning
    result = repository.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping,
        enable_versioning=True,
        version_author="test_user"
    )
    
    # Verify the result
    assert result is True
    
    # Verify the dataset was added
    dataset = repository.get_dataset("test_dataset")
    assert dataset is not None
    assert dataset.name == "test_dataset"
    assert len(dataset.data) == len(sample_dataframe)
    
    # Verify versioning was enabled
    assert dataset.version_info is not None
    assert dataset.version_info["is_versioned"] is True
    assert dataset.version_info["version_number"] == 1


@pytest.mark.unit
def test_create_dataset_version(repository, sample_dataframe, sample_column_mapping):
    """Test creating a new version of a dataset."""
    # Add dataset with versioning
    repository.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping,
        enable_versioning=True,
        version_author="test_user"
    )
    
    # Get the dataset
    dataset = repository.get_dataset("test_dataset")
    
    # Modify the dataset
    modified_data = dataset.data.copy()
    modified_data.loc[0, "message_content"] = "Modified message"
    dataset.data = modified_data
    
    # Create a new version
    version_number = repository.create_dataset_version(
        name="test_dataset",
        description="Modified version",
        author="test_user"
    )
    
    # Verify the result
    assert version_number == 2
    
    # Verify the dataset was updated
    updated_dataset = repository.get_dataset("test_dataset")
    assert updated_dataset is not None
    assert updated_dataset.version_info["version_number"] == 2
    assert updated_dataset.data.loc[0, "message_content"] == "Modified message"


@pytest.mark.unit
def test_get_dataset_version(repository, sample_dataframe, sample_column_mapping):
    """Test getting a specific version of a dataset."""
    # Add dataset with versioning
    repository.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping,
        enable_versioning=True,
        version_author="test_user"
    )
    
    # Get the dataset
    dataset = repository.get_dataset("test_dataset")
    
    # Modify the dataset
    modified_data = dataset.data.copy()
    modified_data.loc[0, "message_content"] = "Modified message"
    dataset.data = modified_data
    
    # Create a new version
    repository.create_dataset_version(
        name="test_dataset",
        description="Modified version",
        author="test_user"
    )
    
    # Get version 1
    dataset_v1 = repository.get_dataset_version("test_dataset", 1)
    
    # Verify the result
    assert dataset_v1 is not None
    assert dataset_v1.version_info["version_number"] == 1
    assert dataset_v1.data.loc[0, "message_content"] == "Hello, world!"
    
    # Get version 2
    dataset_v2 = repository.get_dataset_version("test_dataset", 2)
    
    # Verify the result
    assert dataset_v2 is not None
    assert dataset_v2.version_info["version_number"] == 2
    assert dataset_v2.data.loc[0, "message_content"] == "Modified message"
    
    # Try to get non-existent version
    dataset_v3 = repository.get_dataset_version("test_dataset", 3)
    
    # Verify the result
    assert dataset_v3 is None
    assert isinstance(repository.last_error, VersionNotFoundError)


@pytest.mark.unit
def test_revert_to_version(repository, sample_dataframe, sample_column_mapping):
    """Test reverting a dataset to a specific version."""
    # Add dataset with versioning
    repository.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping,
        enable_versioning=True,
        version_author="test_user"
    )
    
    # Get the dataset
    dataset = repository.get_dataset("test_dataset")
    
    # Modify the dataset
    modified_data = dataset.data.copy()
    modified_data.loc[0, "message_content"] = "Modified message"
    dataset.data = modified_data
    
    # Create a new version
    repository.create_dataset_version(
        name="test_dataset",
        description="Modified version",
        author="test_user"
    )
    
    # Verify current version is 2
    current_dataset = repository.get_dataset("test_dataset")
    assert current_dataset.version_info["version_number"] == 2
    
    # Revert to version 1
    result = repository.revert_to_version("test_dataset", 1)
    
    # Verify the result
    assert result is True
    
    # Verify the dataset was reverted
    reverted_dataset = repository.get_dataset("test_dataset")
    assert reverted_dataset is not None
    assert reverted_dataset.version_info["version_number"] == 1
    assert reverted_dataset.data.loc[0, "message_content"] == "Hello, world!"


@pytest.mark.unit
def test_compare_dataset_versions(repository, sample_dataframe, sample_column_mapping):
    """Test comparing two versions of a dataset."""
    # Add dataset with versioning
    repository.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping,
        enable_versioning=True,
        version_author="test_user"
    )
    
    # Get the dataset
    dataset = repository.get_dataset("test_dataset")
    
    # Modify the dataset
    modified_data = dataset.data.copy()
    modified_data.loc[0, "message_content"] = "Modified message"
    dataset.data = modified_data
    
    # Create a new version
    repository.create_dataset_version(
        name="test_dataset",
        description="Modified version",
        author="test_user"
    )
    
    # Compare versions
    comparison = repository.compare_dataset_versions("test_dataset", 1, 2)
    
    # Verify the comparison
    assert comparison is not None
    assert comparison["dataset_name"] == "test_dataset"
    assert comparison["version1"] == 1
    assert comparison["version2"] == 2
    assert comparison["record_count1"] == len(sample_dataframe)
    assert comparison["record_count2"] == len(sample_dataframe)
    assert comparison["record_count_diff"] == 0  # Same number of records


@pytest.mark.unit
def test_get_dataset_version_history(repository, sample_dataframe, sample_column_mapping):
    """Test getting version history for a dataset."""
    # Add dataset with versioning
    repository.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping,
        enable_versioning=True,
        version_author="test_user"
    )
    
    # Get the dataset
    dataset = repository.get_dataset("test_dataset")
    
    # Modify the dataset
    modified_data = dataset.data.copy()
    modified_data.loc[0, "message_content"] = "Modified message"
    dataset.data = modified_data
    
    # Create a new version
    repository.create_dataset_version(
        name="test_dataset",
        description="Modified version",
        author="test_user"
    )
    
    # Get version history
    history = repository.get_dataset_version_history("test_dataset")
    
    # Verify the history
    assert history is not None
    assert history["dataset_name"] == "test_dataset"
    assert "versions" in history
    assert "1" in history["versions"]
    assert "2" in history["versions"]
    assert history["current_version"] == 2


@pytest.mark.unit
def test_create_version_for_unversioned_dataset(repository, sample_dataframe, sample_column_mapping):
    """Test creating a version for a dataset that wasn't initially versioned."""
    # Add dataset without versioning
    repository.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping
    )
    
    # Get the dataset
    dataset = repository.get_dataset("test_dataset")
    
    # Verify versioning is not enabled
    assert dataset.version_info["is_versioned"] is False
    
    # Create a version
    version_number = repository.create_dataset_version(
        name="test_dataset",
        description="Initial version",
        author="test_user"
    )
    
    # Verify the result
    assert version_number == 1
    
    # Verify versioning is now enabled
    updated_dataset = repository.get_dataset("test_dataset")
    assert updated_dataset.version_info["is_versioned"] is True
    assert updated_dataset.version_info["version_number"] == 1


@pytest.mark.unit
def test_error_handling_for_nonexistent_dataset(repository):
    """Test error handling when trying to version a non-existent dataset."""
    # Try to create a version for a non-existent dataset
    version_number = repository.create_dataset_version(
        name="nonexistent_dataset",
        description="Initial version",
        author="test_user"
    )
    
    # Verify the result
    assert version_number is None
    assert isinstance(repository.last_error, DatasetNotFoundError)
    
    # Try to get a version for a non-existent dataset
    dataset = repository.get_dataset_version("nonexistent_dataset", 1)
    
    # Verify the result
    assert dataset is None
    assert isinstance(repository.last_error, DatasetNotFoundError)
    
    # Try to revert a non-existent dataset
    result = repository.revert_to_version("nonexistent_dataset", 1)
    
    # Verify the result
    assert result is False
    assert isinstance(repository.last_error, DatasetNotFoundError)
    
    # Try to compare versions for a non-existent dataset
    comparison = repository.compare_dataset_versions("nonexistent_dataset", 1, 2)
    
    # Verify the result
    assert comparison is None
    assert isinstance(repository.last_error, DatasetNotFoundError)
    
    # Try to get version history for a non-existent dataset
    history = repository.get_dataset_version_history("nonexistent_dataset")
    
    # Verify the result
    assert history is None
    assert isinstance(repository.last_error, DatasetNotFoundError)
