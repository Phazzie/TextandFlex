"""
Integration tests for the versioning functionality.
"""
import pytest
import pandas as pd
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from src.data_layer.repository import PhoneRecordRepository
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
        "timestamp": [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        ],
        "phone_number": ["1234567890", "9876543210", "5555555555"],
        "message_type": ["sent", "received", "sent"],
        "duration": [60, 120, 30]
    })


@pytest.fixture
def sample_column_mapping():
    """Create a sample column mapping for testing."""
    return {
        "timestamp": "timestamp",
        "phone_number": "phone_number",
        "message_type": "message_type",
        "duration": "duration"
    }


@pytest.fixture
def repository(temp_repo_dir):
    """Create a repository for testing."""
    return PhoneRecordRepository(storage_dir=temp_repo_dir)


@pytest.mark.integration
def test_versioning_workflow(repository, sample_dataframe, sample_column_mapping):
    """Test the complete versioning workflow."""
    # Step 1: Add a dataset with versioning enabled
    result = repository.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping,
        enable_versioning=True,
        version_author="test_user"
    )
    assert result is True
    
    # Verify the dataset was added with versioning
    dataset = repository.get_dataset("test_dataset")
    assert dataset is not None
    assert dataset.version_info is not None
    assert dataset.version_info["is_versioned"] is True
    assert dataset.version_info["version_number"] == 1
    
    # Step 2: Modify the dataset
    modified_data = dataset.data.copy()
    modified_data.loc[0, "duration"] = 90
    
    # Update the dataset
    result = repository.update_dataset(
        name="test_dataset",
        data=modified_data
    )
    assert result is True
    
    # Step 3: Create a new version
    version_number = repository.create_dataset_version(
        name="test_dataset",
        description="Modified duration",
        author="test_user"
    )
    assert version_number == 2
    
    # Verify the dataset was updated
    updated_dataset = repository.get_dataset("test_dataset")
    assert updated_dataset is not None
    assert updated_dataset.version_info["version_number"] == 2
    assert updated_dataset.data.loc[0, "duration"] == 90
    
    # Step 4: Get version history
    history = repository.get_dataset_version_history("test_dataset")
    assert history is not None
    assert history["dataset_name"] == "test_dataset"
    assert "versions" in history
    assert "1" in history["versions"]
    assert "2" in history["versions"]
    assert history["current_version"] == 2
    
    # Step 5: Compare versions
    comparison = repository.compare_dataset_versions("test_dataset", 1, 2)
    assert comparison is not None
    assert comparison["dataset_name"] == "test_dataset"
    assert comparison["version1"] == 1
    assert comparison["version2"] == 2
    
    # Step 6: Get a specific version
    dataset_v1 = repository.get_dataset_version("test_dataset", 1)
    assert dataset_v1 is not None
    assert dataset_v1.version_info["version_number"] == 1
    assert dataset_v1.data.loc[0, "duration"] == 60
    
    # Step 7: Revert to version 1
    result = repository.revert_to_version("test_dataset", 1)
    assert result is True
    
    # Verify the dataset was reverted
    reverted_dataset = repository.get_dataset("test_dataset")
    assert reverted_dataset is not None
    assert reverted_dataset.version_info["version_number"] == 1
    assert reverted_dataset.data.loc[0, "duration"] == 60
    
    # Step 8: Create another version after reverting
    modified_data = reverted_dataset.data.copy()
    modified_data.loc[0, "message_type"] = "missed"
    
    # Update the dataset
    result = repository.update_dataset(
        name="test_dataset",
        data=modified_data
    )
    assert result is True
    
    # Create a new version
    version_number = repository.create_dataset_version(
        name="test_dataset",
        description="Modified message type",
        author="test_user"
    )
    assert version_number == 3
    
    # Verify the version history is correct
    history = repository.get_dataset_version_history("test_dataset")
    assert history is not None
    assert "1" in history["versions"]
    assert "2" in history["versions"]
    assert "3" in history["versions"]
    assert history["current_version"] == 3


@pytest.mark.integration
def test_versioning_error_handling(repository, sample_dataframe, sample_column_mapping):
    """Test error handling in versioning functionality."""
    # Add a dataset without versioning
    result = repository.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping
    )
    assert result is True
    
    # Try to get a version for a dataset that doesn't have versioning enabled
    dataset_v1 = repository.get_dataset_version("test_dataset", 1)
    assert dataset_v1 is None
    
    # Enable versioning
    version_number = repository.create_dataset_version(
        name="test_dataset",
        description="Initial version",
        author="test_user"
    )
    assert version_number == 1
    
    # Try to get a non-existent version
    dataset_v2 = repository.get_dataset_version("test_dataset", 2)
    assert dataset_v2 is None
    
    # Try to revert to a non-existent version
    result = repository.revert_to_version("test_dataset", 2)
    assert result is False
    
    # Try to get version history for a non-existent dataset
    history = repository.get_dataset_version_history("nonexistent_dataset")
    assert history is None
    
    # Try to compare versions for a non-existent dataset
    comparison = repository.compare_dataset_versions("nonexistent_dataset", 1, 2)
    assert comparison is None


@pytest.mark.integration
def test_versioning_persistence(temp_repo_dir, sample_dataframe, sample_column_mapping):
    """Test that versioning information persists when repository is reloaded."""
    # Create a repository and add a dataset with versioning
    repo1 = PhoneRecordRepository(storage_dir=temp_repo_dir)
    result = repo1.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping,
        enable_versioning=True,
        version_author="test_user"
    )
    assert result is True
    
    # Modify the dataset and create a new version
    dataset = repo1.get_dataset("test_dataset")
    modified_data = dataset.data.copy()
    modified_data.loc[0, "duration"] = 90
    
    # Update the dataset
    result = repo1.update_dataset(
        name="test_dataset",
        data=modified_data
    )
    assert result is True
    
    # Create a new version
    version_number = repo1.create_dataset_version(
        name="test_dataset",
        description="Modified duration",
        author="test_user"
    )
    assert version_number == 2
    
    # Create a new repository instance (simulating application restart)
    repo2 = PhoneRecordRepository(storage_dir=temp_repo_dir)
    
    # Verify the dataset and its versions are still available
    dataset = repo2.get_dataset("test_dataset")
    assert dataset is not None
    assert dataset.version_info is not None
    assert dataset.version_info["is_versioned"] is True
    assert dataset.version_info["version_number"] == 2
    
    # Get version 1
    dataset_v1 = repo2.get_dataset_version("test_dataset", 1)
    assert dataset_v1 is not None
    assert dataset_v1.version_info["version_number"] == 1
    assert dataset_v1.data.loc[0, "duration"] == 60
    
    # Get version history
    history = repo2.get_dataset_version_history("test_dataset")
    assert history is not None
    assert "1" in history["versions"]
    assert "2" in history["versions"]
    assert history["current_version"] == 2
