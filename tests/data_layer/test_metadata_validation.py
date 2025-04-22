"""
Tests for dataset metadata validation.
"""
import pytest
import pandas as pd
from unittest.mock import patch
import datetime

@pytest.mark.unit
def test_validate_dataset_metadata_schema():
    """Test validation of dataset metadata schema."""
    from src.data_layer.validation_schema import validate_dataset_metadata
    from src.data_layer.exceptions import ValidationError

    # Valid metadata
    valid_metadata = {
        "created_at": datetime.datetime.now().isoformat(),
        "record_count": 100,
        "columns": ["timestamp", "phone_number", "message_type", "message_content"]
    }

    # Validate valid metadata
    assert validate_dataset_metadata(valid_metadata) is True

    # Invalid metadata (missing required fields)
    invalid_metadata = {
        "created_at": datetime.datetime.now().isoformat()
    }

    # Validate invalid metadata
    with pytest.raises(ValidationError) as excinfo:
        validate_dataset_metadata(invalid_metadata)
    assert "record_count" in str(excinfo.value)

    # Invalid metadata (wrong type)
    invalid_type_metadata = {
        "created_at": datetime.datetime.now().isoformat(),
        "record_count": "100",  # Should be int
        "columns": ["timestamp", "phone_number", "message_type", "message_content"]
    }

    # Validate invalid metadata
    with pytest.raises(ValidationError) as excinfo:
        validate_dataset_metadata(invalid_type_metadata)
    assert "record_count" in str(excinfo.value)
    assert "type" in str(excinfo.value)

@pytest.mark.unit
def test_validate_column_mapping_schema():
    """Test validation of column mapping schema."""
    from src.data_layer.validation_schema import validate_column_mapping
    from src.data_layer.exceptions import ValidationError

    # Valid column mapping
    valid_mapping = {
        "timestamp": "date",
        "phone_number": "contact",
        "message_type": "type",
        "message_content": "content"
    }

    # Validate valid mapping
    assert validate_column_mapping(valid_mapping) is True

    # Invalid mapping (missing required fields)
    invalid_mapping = {
        "timestamp": "date",
        "phone_number": "contact"
    }

    # Validate invalid mapping
    with pytest.raises(ValidationError) as excinfo:
        validate_column_mapping(invalid_mapping)
    assert "message_type" in str(excinfo.value)

    # Invalid mapping (wrong type)
    invalid_type_mapping = {
        "timestamp": "date",
        "phone_number": "contact",
        "message_type": 123,  # Should be string
        "message_content": "content"
    }

    # Validate invalid mapping
    with pytest.raises(ValidationError) as excinfo:
        validate_column_mapping(invalid_type_mapping)
    assert "message_type" in str(excinfo.value)
    assert "type" in str(excinfo.value)

@pytest.mark.unit
def test_validate_dataset_properties():
    """Test validation of dataset properties."""
    from src.data_layer.validation_schema import validate_dataset_properties
    from src.data_layer.exceptions import ValidationError

    # Create a valid dataset
    df = pd.DataFrame({
        "timestamp": ["2023-01-01 12:00:00", "2023-01-01 12:30:00"],
        "phone_number": ["1234567890", "9876543210"],
        "message_type": ["sent", "received"],
        "message_content": ["Hello, world!", "Hi there!"]
    })

    # Valid column mapping
    valid_mapping = {
        "timestamp": "date",
        "phone_number": "contact",
        "message_type": "type",
        "message_content": "content"
    }

    # Validate valid properties
    assert validate_dataset_properties(df, valid_mapping) is True

    # Invalid properties (DataFrame columns don't match mapping)
    invalid_df = pd.DataFrame({
        "timestamp": ["2023-01-01 12:00:00", "2023-01-01 12:30:00"],
        "phone": ["1234567890", "9876543210"],  # Column name doesn't match mapping
        "message_type": ["sent", "received"],
        "message_content": ["Hello, world!", "Hi there!"]
    })

    # Validate invalid properties
    with pytest.raises(ValidationError) as excinfo:
        validate_dataset_properties(invalid_df, valid_mapping)
    assert "phone_number" in str(excinfo.value)

    # Invalid properties (Empty DataFrame)
    empty_df = pd.DataFrame()

    # Validate invalid properties
    with pytest.raises(ValidationError) as excinfo:
        validate_dataset_properties(empty_df, valid_mapping)
    assert "empty" in str(excinfo.value)

@pytest.mark.unit
def test_dataset_post_init_validation():
    """Test validation in PhoneRecordDataset.__post_init__."""
    from src.data_layer.models import PhoneRecordDataset
    from src.data_layer.exceptions import ValidationError

    # Create a valid dataset
    df = pd.DataFrame({
        "timestamp": ["2023-01-01 12:00:00", "2023-01-01 12:30:00"],
        "phone_number": ["1234567890", "9876543210"],
        "message_type": ["sent", "received"],
        "message_content": ["Hello, world!", "Hi there!"]
    })

    # Valid column mapping
    valid_mapping = {
        "timestamp": "date",
        "phone_number": "contact",
        "message_type": "type",
        "message_content": "content"
    }

    # Create a valid dataset
    dataset = PhoneRecordDataset(
        name="test_dataset",
        data=df,
        column_mapping=valid_mapping
    )

    # Verify the dataset was created successfully
    assert dataset.name == "test_dataset"
    assert dataset.data is not None
    assert dataset.column_mapping == valid_mapping

    # Create an invalid dataset (missing required columns)
    invalid_df = pd.DataFrame({
        "timestamp": ["2023-01-01 12:00:00", "2023-01-01 12:30:00"],
        "phone": ["1234567890", "9876543210"],  # Column name doesn't match mapping
        "message_type": ["sent", "received"],
        "message_content": ["Hello, world!", "Hi there!"]
    })

    # Create an invalid dataset
    with pytest.raises(ValidationError) as excinfo:
        dataset = PhoneRecordDataset(
            name="test_dataset",
            data=invalid_df,
            column_mapping=valid_mapping
        )
    assert "phone_number" in str(excinfo.value)

@pytest.mark.unit
def test_repository_metadata_validation():
    """Test validation in RepositoryMetadata."""
    from src.data_layer.models import RepositoryMetadata
    from src.data_layer.exceptions import ValidationError

    # Create valid metadata
    metadata = RepositoryMetadata()

    # Add a valid dataset
    metadata.datasets["test_dataset"] = {
        "name": "test_dataset",
        "column_mapping": {
            "timestamp": "date",
            "phone_number": "contact",
            "message_type": "type",
            "message_content": "content"
        },
        "metadata": {
            "created_at": datetime.datetime.now().isoformat(),
            "record_count": 100,
            "columns": ["timestamp", "phone_number", "message_type", "message_content"]
        }
    }

    # Verify the metadata was created successfully
    assert "test_dataset" in metadata.datasets

    # Add an invalid dataset (missing required fields)
    with pytest.raises(ValidationError) as excinfo:
        metadata.add_dataset_metadata("invalid_dataset", {
            "column_mapping": {
                "timestamp": "date"
                # Missing required fields
            },
            "metadata": {
                "created_at": datetime.datetime.now().isoformat()
                # Missing required fields
            }
        })
    # The error message will contain the specific missing field, which could be any of the required fields
    # We just need to verify that a ValidationError was raised

@pytest.mark.unit
def test_repository_add_dataset_validation():
    """Test validation when adding a dataset to the repository."""
    from src.data_layer.repository import PhoneRecordRepository
    from src.data_layer.exceptions import ValidationError

    # Initialize repository
    repo = PhoneRecordRepository()

    # Create a valid dataset
    df = pd.DataFrame({
        "timestamp": ["2023-01-01 12:00:00", "2023-01-01 12:30:00"],
        "phone_number": ["1234567890", "9876543210"],
        "message_type": ["sent", "received"],
        "message_content": ["Hello, world!", "Hi there!"]
    })

    # Valid column mapping
    valid_mapping = {
        "timestamp": "date",
        "phone_number": "contact",
        "message_type": "type",
        "message_content": "content"
    }

    # Mock save_pickle and save_json to return True
    with patch('src.utils.file_io.save_pickle', return_value=True):
        with patch('src.utils.file_io.save_json', return_value=True):
            # Add a valid dataset
            result = repo.add_dataset(
                name="test_dataset",
                data=df,
                column_mapping=valid_mapping
            )
            assert result is True

            # Add an invalid dataset (missing required columns)
            invalid_df = pd.DataFrame({
                "timestamp": ["2023-01-01 12:00:00", "2023-01-01 12:30:00"],
                "phone": ["1234567890", "9876543210"],  # Column name doesn't match mapping
                "message_type": ["sent", "received"],
                "message_content": ["Hello, world!", "Hi there!"]
            })

            # Add an invalid dataset
            result = repo.add_dataset(
                name="invalid_dataset",
                data=invalid_df,
                column_mapping=valid_mapping
            )
            assert result is False
            assert repo.last_error is not None
            assert "validation" in str(repo.last_error).lower()
