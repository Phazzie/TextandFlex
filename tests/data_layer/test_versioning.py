"""
Tests for the versioning module.
"""
import pytest
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import shutil
from unittest.mock import patch, MagicMock

from src.data_layer.versioning import VersionManager
from src.data_layer.version_metadata import DatasetVersion, VersionHistory
from src.data_layer.models import PhoneRecordDataset
from src.data_layer.exceptions import ValidationError, VersioningError, VersionNotFoundError

@pytest.fixture
def temp_version_dir(tmpdir):
    """Create a temporary directory for version data."""
    version_dir = Path(tmpdir) / "version_data"
    version_dir.mkdir(exist_ok=True)
    yield version_dir
    # Clean up
    shutil.rmtree(version_dir, ignore_errors=True)

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
        "timestamp": "date",
        "phone_number": "contact",
        "message_type": "type",
        "message_content": "content"
    }

@pytest.fixture
def sample_dataset(sample_dataframe, sample_column_mapping):
    """Create a sample dataset for testing."""
    return PhoneRecordDataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping
    )

@pytest.fixture
def version_manager(temp_version_dir):
    """Create a version manager for testing."""
    return VersionManager(storage_dir=temp_version_dir)

@pytest.mark.unit
def test_dataset_version_creation():
    """Test creating a DatasetVersion."""
    # Create a version
    version = DatasetVersion(
        version_number=1,
        author="test_user",
        description="Initial version",
        changes={"type": "initial", "record_count": 100}
    )
    
    # Verify the version
    assert version.version_number == 1
    assert version.author == "test_user"
    assert version.description == "Initial version"
    assert version.changes["type"] == "initial"
    assert version.changes["record_count"] == 100
    assert version.parent_version is None

@pytest.mark.unit
def test_dataset_version_validation():
    """Test validation in DatasetVersion."""
    # Test invalid version number
    with pytest.raises(ValidationError):
        DatasetVersion(version_number=0)
    
    with pytest.raises(ValidationError):
        DatasetVersion(version_number="1")
    
    # Test invalid timestamp
    with pytest.raises(ValidationError):
        DatasetVersion(version_number=1, timestamp="invalid")
    
    # Test invalid description
    with pytest.raises(ValidationError):
        DatasetVersion(version_number=1, description=123)
    
    # Test invalid changes
    with pytest.raises(ValidationError):
        DatasetVersion(version_number=1, changes="invalid")
    
    # Test invalid parent version
    with pytest.raises(ValidationError):
        DatasetVersion(version_number=1, parent_version=0)
    
    with pytest.raises(ValidationError):
        DatasetVersion(version_number=1, parent_version="1")

@pytest.mark.unit
def test_dataset_version_serialization():
    """Test serialization of DatasetVersion."""
    # Create a version
    version = DatasetVersion(
        version_number=1,
        author="test_user",
        description="Initial version",
        changes={"type": "initial", "record_count": 100}
    )
    
    # Convert to dictionary
    version_dict = version.to_dict()
    
    # Verify the dictionary
    assert version_dict["version_number"] == 1
    assert version_dict["author"] == "test_user"
    assert version_dict["description"] == "Initial version"
    assert version_dict["changes"]["type"] == "initial"
    assert version_dict["changes"]["record_count"] == 100
    assert version_dict["parent_version"] is None
    
    # Convert back to DatasetVersion
    version2 = DatasetVersion.from_dict(version_dict)
    
    # Verify the new version
    assert version2.version_number == version.version_number
    assert version2.author == version.author
    assert version2.description == version.description
    assert version2.changes == version.changes
    assert version2.parent_version == version.parent_version

@pytest.mark.unit
def test_version_history_creation():
    """Test creating a VersionHistory."""
    # Create a version
    version = DatasetVersion(
        version_number=1,
        author="test_user",
        description="Initial version",
        changes={"type": "initial", "record_count": 100}
    )
    
    # Create a history
    history = VersionHistory(
        dataset_name="test_dataset",
        versions={1: version},
        current_version=1
    )
    
    # Verify the history
    assert history.dataset_name == "test_dataset"
    assert len(history.versions) == 1
    assert history.versions[1] == version
    assert history.current_version == 1

@pytest.mark.unit
def test_version_history_validation():
    """Test validation in VersionHistory."""
    # Create a valid version
    version = DatasetVersion(
        version_number=1,
        author="test_user",
        description="Initial version"
    )
    
    # Test invalid dataset name
    with pytest.raises(ValidationError):
        VersionHistory(dataset_name="")
    
    with pytest.raises(ValidationError):
        VersionHistory(dataset_name=123)
    
    # Test invalid versions
    with pytest.raises(ValidationError):
        VersionHistory(dataset_name="test_dataset", versions="invalid")
    
    with pytest.raises(ValidationError):
        VersionHistory(dataset_name="test_dataset", versions={0: version})
    
    with pytest.raises(ValidationError):
        VersionHistory(dataset_name="test_dataset", versions={"1": version})
    
    with pytest.raises(ValidationError):
        VersionHistory(dataset_name="test_dataset", versions={1: "invalid"})
    
    # Test invalid current version
    with pytest.raises(ValidationError):
        VersionHistory(
            dataset_name="test_dataset",
            versions={1: version},
            current_version=0
        )
    
    with pytest.raises(ValidationError):
        VersionHistory(
            dataset_name="test_dataset",
            versions={1: version},
            current_version=2  # Not in versions
        )

@pytest.mark.unit
def test_version_history_add_version():
    """Test adding a version to VersionHistory."""
    # Create initial version
    version1 = DatasetVersion(
        version_number=1,
        author="test_user",
        description="Initial version"
    )
    
    # Create history
    history = VersionHistory(
        dataset_name="test_dataset",
        versions={1: version1},
        current_version=1
    )
    
    # Create second version
    version2 = DatasetVersion(
        version_number=2,
        author="test_user",
        description="Second version",
        parent_version=1
    )
    
    # Add second version
    history.add_version(version2)
    
    # Verify the history
    assert len(history.versions) == 2
    assert history.versions[1] == version1
    assert history.versions[2] == version2
    assert history.current_version == 2
    
    # Test adding a duplicate version
    with pytest.raises(ValidationError):
        history.add_version(version2)

@pytest.mark.unit
def test_version_history_serialization():
    """Test serialization of VersionHistory."""
    # Create a version
    version = DatasetVersion(
        version_number=1,
        author="test_user",
        description="Initial version"
    )
    
    # Create a history
    history = VersionHistory(
        dataset_name="test_dataset",
        versions={1: version},
        current_version=1
    )
    
    # Convert to dictionary
    history_dict = history.to_dict()
    
    # Verify the dictionary
    assert history_dict["dataset_name"] == "test_dataset"
    assert "1" in history_dict["versions"]  # Keys are converted to strings in JSON
    assert history_dict["versions"]["1"]["version_number"] == 1
    assert history_dict["current_version"] == 1
    
    # Convert back to VersionHistory
    history2 = VersionHistory.from_dict(history_dict)
    
    # Verify the new history
    assert history2.dataset_name == history.dataset_name
    assert len(history2.versions) == len(history.versions)
    assert history2.versions[1].version_number == history.versions[1].version_number
    assert history2.current_version == history.current_version

@pytest.mark.unit
def test_version_manager_initialization(temp_version_dir):
    """Test initializing the VersionManager."""
    # Initialize version manager
    manager = VersionManager(storage_dir=temp_version_dir)
    
    # Verify the manager
    assert manager.storage_dir == temp_version_dir
    assert isinstance(manager.version_histories, dict)
    assert len(manager.version_histories) == 0
    assert manager.last_error is None

@pytest.mark.unit
def test_version_manager_initialize_versioning(version_manager, sample_dataset):
    """Test initializing versioning for a dataset."""
    # Initialize versioning
    with patch('src.utils.file_io.save_json', return_value=True), \
         patch('src.utils.file_io.save_pickle', return_value=True):
        result = version_manager.initialize_versioning(sample_dataset, author="test_user")
    
    # Verify the result
    assert result is True
    assert sample_dataset.name in version_manager.version_histories
    
    # Verify the history
    history = version_manager.version_histories[sample_dataset.name]
    assert history.dataset_name == sample_dataset.name
    assert len(history.versions) == 1
    assert history.versions[1].version_number == 1
    assert history.versions[1].author == "test_user"
    assert history.current_version == 1

@pytest.mark.unit
def test_version_manager_create_version(version_manager, sample_dataset):
    """Test creating a new version."""
    # Initialize versioning
    with patch('src.utils.file_io.save_json', return_value=True), \
         patch('src.utils.file_io.save_pickle', return_value=True):
        version_manager.initialize_versioning(sample_dataset, author="test_user")
    
    # Create a new version
    with patch('src.utils.file_io.save_json', return_value=True), \
         patch('src.utils.file_io.save_pickle', return_value=True):
        version_number = version_manager.create_version(
            sample_dataset,
            description="Second version",
            author="test_user",
            changes={"type": "update", "record_count": 3}
        )
    
    # Verify the result
    assert version_number == 2
    
    # Verify the history
    history = version_manager.version_histories[sample_dataset.name]
    assert len(history.versions) == 2
    assert history.versions[2].version_number == 2
    assert history.versions[2].description == "Second version"
    assert history.versions[2].parent_version == 1
    assert history.current_version == 2

@pytest.mark.unit
def test_version_manager_get_version(version_manager, sample_dataset):
    """Test getting a specific version."""
    # Initialize versioning and create versions
    with patch('src.utils.file_io.save_json', return_value=True), \
         patch('src.utils.file_io.save_pickle', return_value=True):
        version_manager.initialize_versioning(sample_dataset, author="test_user")
        version_manager.create_version(
            sample_dataset,
            description="Second version",
            author="test_user"
        )
    
    # Get version 1
    with patch('src.utils.file_io.load_pickle', return_value=sample_dataset):
        dataset_v1 = version_manager.get_version(sample_dataset.name, 1)
    
    # Verify the result
    assert dataset_v1 is not None
    assert dataset_v1.name == sample_dataset.name
    
    # Get version 2
    with patch('src.utils.file_io.load_pickle', return_value=sample_dataset):
        dataset_v2 = version_manager.get_version(sample_dataset.name, 2)
    
    # Verify the result
    assert dataset_v2 is not None
    assert dataset_v2.name == sample_dataset.name
    
    # Get non-existent version
    with patch('src.utils.file_io.load_pickle', return_value=None):
        dataset_v3 = version_manager.get_version(sample_dataset.name, 3)
    
    # Verify the result
    assert dataset_v3 is None
    assert isinstance(version_manager.last_error, VersionNotFoundError)

@pytest.mark.unit
def test_version_manager_get_current_version(version_manager, sample_dataset):
    """Test getting the current version."""
    # Initialize versioning and create versions
    with patch('src.utils.file_io.save_json', return_value=True), \
         patch('src.utils.file_io.save_pickle', return_value=True):
        version_manager.initialize_versioning(sample_dataset, author="test_user")
        version_manager.create_version(
            sample_dataset,
            description="Second version",
            author="test_user"
        )
    
    # Get current version
    with patch('src.utils.file_io.load_pickle', return_value=sample_dataset):
        current_dataset = version_manager.get_current_version(sample_dataset.name)
    
    # Verify the result
    assert current_dataset is not None
    assert current_dataset.name == sample_dataset.name
    
    # Verify the current version is 2
    history = version_manager.version_histories[sample_dataset.name]
    assert history.current_version == 2

@pytest.mark.unit
def test_version_manager_set_current_version(version_manager, sample_dataset):
    """Test setting the current version."""
    # Initialize versioning and create versions
    with patch('src.utils.file_io.save_json', return_value=True), \
         patch('src.utils.file_io.save_pickle', return_value=True):
        version_manager.initialize_versioning(sample_dataset, author="test_user")
        version_manager.create_version(
            sample_dataset,
            description="Second version",
            author="test_user"
        )
    
    # Set current version to 1
    with patch('src.utils.file_io.save_json', return_value=True):
        result = version_manager.set_current_version(sample_dataset.name, 1)
    
    # Verify the result
    assert result is True
    
    # Verify the current version is 1
    history = version_manager.version_histories[sample_dataset.name]
    assert history.current_version == 1
    
    # Set current version to non-existent version
    with patch('src.utils.file_io.save_json', return_value=True):
        result = version_manager.set_current_version(sample_dataset.name, 3)
    
    # Verify the result
    assert result is False
    assert isinstance(version_manager.last_error, VersionNotFoundError)

@pytest.mark.unit
def test_version_manager_compare_versions(version_manager, sample_dataset):
    """Test comparing versions."""
    # Initialize versioning and create versions
    with patch('src.utils.file_io.save_json', return_value=True), \
         patch('src.utils.file_io.save_pickle', return_value=True):
        version_manager.initialize_versioning(sample_dataset, author="test_user")
        
        # Create a modified dataset
        modified_data = sample_dataset.data.copy()
        modified_data.loc[0, "message_content"] = "Modified message"
        modified_dataset = PhoneRecordDataset(
            name=sample_dataset.name,
            data=modified_data,
            column_mapping=sample_dataset.column_mapping
        )
        
        version_manager.create_version(
            modified_dataset,
            description="Modified version",
            author="test_user",
            changes={"type": "update", "modified_fields": ["message_content"]}
        )
    
    # Compare versions
    with patch('src.utils.file_io.load_pickle', side_effect=[sample_dataset, modified_dataset]):
        comparison = version_manager.compare_versions(sample_dataset.name, 1, 2)
    
    # Verify the comparison
    assert comparison is not None
    assert comparison["dataset_name"] == sample_dataset.name
    assert comparison["version1"] == 1
    assert comparison["version2"] == 2
    assert comparison["record_count1"] == len(sample_dataset.data)
    assert comparison["record_count2"] == len(modified_dataset.data)
    assert comparison["record_count_diff"] == 0  # Same number of records
    assert "modified_fields" in comparison["metadata_diff"]

@pytest.mark.unit
def test_version_manager_delete_version(version_manager, sample_dataset):
    """Test deleting a version."""
    # Initialize versioning and create versions
    with patch('src.utils.file_io.save_json', return_value=True), \
         patch('src.utils.file_io.save_pickle', return_value=True), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.unlink'):
        version_manager.initialize_versioning(sample_dataset, author="test_user")
        version_manager.create_version(
            sample_dataset,
            description="Second version",
            author="test_user"
        )
        version_manager.create_version(
            sample_dataset,
            description="Third version",
            author="test_user"
        )
        
        # Delete version 2
        result = version_manager.delete_version(sample_dataset.name, 2)
    
    # Verify the result
    assert result is True
    
    # Verify the history
    history = version_manager.version_histories[sample_dataset.name]
    assert len(history.versions) == 2
    assert 1 in history.versions
    assert 3 in history.versions
    assert 2 not in history.versions
    
    # Verify version 3's parent is now 1
    assert history.versions[3].parent_version == 1
    
    # Try to delete current version
    with patch('src.utils.file_io.save_json', return_value=True):
        result = version_manager.delete_version(sample_dataset.name, 3)
    
    # Verify the result
    assert result is False
    assert isinstance(version_manager.last_error, VersioningError)
    
    # Try to delete only remaining version
    with patch('src.utils.file_io.save_json', return_value=True), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.unlink'):
        # First delete version 3
        version_manager.set_current_version(sample_dataset.name, 1)
        version_manager.delete_version(sample_dataset.name, 3)
        
        # Now try to delete version 1
        result = version_manager.delete_version(sample_dataset.name, 1)
    
    # Verify the result
    assert result is False
    assert isinstance(version_manager.last_error, VersioningError)

@pytest.mark.unit
def test_version_manager_get_version_lineage(version_manager, sample_dataset):
    """Test getting version lineage."""
    # Initialize versioning and create versions
    with patch('src.utils.file_io.save_json', return_value=True), \
         patch('src.utils.file_io.save_pickle', return_value=True):
        version_manager.initialize_versioning(sample_dataset, author="test_user")
        version_manager.create_version(
            sample_dataset,
            description="Second version",
            author="test_user"
        )
        version_manager.create_version(
            sample_dataset,
            description="Third version",
            author="test_user"
        )
        
        # Create a branch from version 1
        version_manager.set_current_version(sample_dataset.name, 1)
        version_manager.create_version(
            sample_dataset,
            description="Branch version",
            author="test_user"
        )
    
    # Get lineage
    lineage = version_manager.get_version_lineage(sample_dataset.name)
    
    # Verify the lineage
    assert lineage is not None
    assert 1 in lineage
    assert 2 in lineage
    assert 3 in lineage
    assert 4 in lineage
    assert 2 in lineage[1]  # Version 2 is a child of version 1
    assert 4 in lineage[1]  # Version 4 is a child of version 1
    assert 3 in lineage[2]  # Version 3 is a child of version 2
    assert len(lineage[3]) == 0  # Version 3 has no children
    assert len(lineage[4]) == 0  # Version 4 has no children
