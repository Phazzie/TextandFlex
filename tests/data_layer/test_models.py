"""
Tests for the data models module.
"""
import pytest
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00', '2023-01-01 12:30:00', '2023-01-01 13:00:00'],
        'phone_number': ['1234567890', '9876543210', '5551234567'],
        'message_type': ['sent', 'received', 'sent'],
        'message_content': ['Hello, world!', 'Hi there!', 'How are you?']
    })

@pytest.fixture
def sample_column_mapping():
    """Create a sample column mapping for testing."""
    return {
        'timestamp': 'timestamp',
        'phone_number': 'phone_number',
        'message_type': 'message_type',
        'message_content': 'message_content'
    }

@pytest.mark.unit
def test_phone_record_dataset_creation(sample_dataframe, sample_column_mapping):
    """Test creating a PhoneRecordDataset."""
    from src.data_layer.models import PhoneRecordDataset
    
    # Create a dataset
    dataset = PhoneRecordDataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping
    )
    
    # Verify the dataset
    assert dataset.name == "test_dataset"
    assert dataset.data is sample_dataframe
    assert dataset.column_mapping == sample_column_mapping
    assert "created_at" in dataset.metadata
    assert dataset.metadata["record_count"] == 3
    assert dataset.metadata["columns"] == ['timestamp', 'phone_number', 'message_type', 'message_content']

@pytest.mark.unit
def test_phone_record_dataset_to_dict(sample_dataframe, sample_column_mapping):
    """Test converting a PhoneRecordDataset to a dictionary."""
    from src.data_layer.models import PhoneRecordDataset
    
    # Create a dataset
    dataset = PhoneRecordDataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping
    )
    
    # Convert to dictionary
    result = dataset.to_dict()
    
    # Verify the result
    assert result["name"] == "test_dataset"
    assert result["column_mapping"] == sample_column_mapping
    assert "metadata" in result
    assert "created_at" in result["metadata"]
    assert result["metadata"]["record_count"] == 3
    assert result["metadata"]["columns"] == ['timestamp', 'phone_number', 'message_type', 'message_content']

@pytest.mark.unit
def test_phone_record_dataset_get_summary(sample_dataframe, sample_column_mapping):
    """Test getting a summary of a PhoneRecordDataset."""
    from src.data_layer.models import PhoneRecordDataset
    
    # Create a dataset
    dataset = PhoneRecordDataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping
    )
    
    # Get summary
    summary = dataset.get_summary()
    
    # Verify the summary
    assert summary["name"] == "test_dataset"
    assert summary["record_count"] == 3
    assert summary["columns"] == ['timestamp', 'phone_number', 'message_type', 'message_content']
    assert summary["column_mapping"] == sample_column_mapping
    assert "created_at" in summary

@pytest.mark.unit
def test_repository_metadata_creation():
    """Test creating RepositoryMetadata."""
    from src.data_layer.models import RepositoryMetadata
    
    # Create metadata
    metadata = RepositoryMetadata()
    
    # Verify the metadata
    assert isinstance(metadata.datasets, dict)
    assert len(metadata.datasets) == 0
    assert metadata.created_at is not None
    assert metadata.last_updated is not None

@pytest.mark.unit
def test_repository_metadata_to_dict():
    """Test converting RepositoryMetadata to a dictionary."""
    from src.data_layer.models import RepositoryMetadata
    
    # Create metadata
    metadata = RepositoryMetadata()
    
    # Add a dataset
    metadata.datasets["test_dataset"] = {
        "column_mapping": {"timestamp": "date"},
        "metadata": {"record_count": 10}
    }
    
    # Convert to dictionary
    result = metadata.to_dict()
    
    # Verify the result
    assert "datasets" in result
    assert "test_dataset" in result["datasets"]
    assert result["datasets"]["test_dataset"]["column_mapping"]["timestamp"] == "date"
    assert result["datasets"]["test_dataset"]["metadata"]["record_count"] == 10
    assert "created_at" in result
    assert "last_updated" in result

@pytest.mark.unit
def test_repository_metadata_update_last_updated():
    """Test updating the last_updated timestamp."""
    from src.data_layer.models import RepositoryMetadata
    
    # Create metadata
    metadata = RepositoryMetadata()
    
    # Store the original timestamp
    original_timestamp = metadata.last_updated
    
    # Wait a moment to ensure the timestamp changes
    import time
    time.sleep(0.001)
    
    # Update the timestamp
    metadata.update_last_updated()
    
    # Verify the timestamp changed
    assert metadata.last_updated != original_timestamp

@pytest.mark.unit
def test_message_model_creation():
    """Test creating a Message model."""
    from src.data_layer.models import Message
    
    # Create a message
    message = Message(
        timestamp="2023-01-01 12:00:00",
        phone_number="1234567890",
        message_type="sent",
        content="Hello, world!"
    )
    
    # Verify the message
    assert message.timestamp == "2023-01-01 12:00:00"
    assert message.phone_number == "1234567890"
    assert message.message_type == "sent"
    assert message.content == "Hello, world!"

@pytest.mark.unit
def test_message_model_to_dict():
    """Test converting a Message to a dictionary."""
    from src.data_layer.models import Message
    
    # Create a message
    message = Message(
        timestamp="2023-01-01 12:00:00",
        phone_number="1234567890",
        message_type="sent",
        content="Hello, world!"
    )
    
    # Convert to dictionary
    result = message.to_dict()
    
    # Verify the result
    assert result["timestamp"] == "2023-01-01 12:00:00"
    assert result["phone_number"] == "1234567890"
    assert result["message_type"] == "sent"
    assert result["content"] == "Hello, world!"

@pytest.mark.unit
def test_contact_model_creation():
    """Test creating a Contact model."""
    from src.data_layer.models import Contact
    
    # Create a contact
    contact = Contact(
        phone_number="1234567890",
        messages=[]
    )
    
    # Verify the contact
    assert contact.phone_number == "1234567890"
    assert contact.messages == []

@pytest.mark.unit
def test_contact_model_add_message():
    """Test adding a message to a Contact."""
    from src.data_layer.models import Contact, Message
    
    # Create a contact
    contact = Contact(
        phone_number="1234567890",
        messages=[]
    )
    
    # Create a message
    message = Message(
        timestamp="2023-01-01 12:00:00",
        phone_number="1234567890",
        message_type="sent",
        content="Hello, world!"
    )
    
    # Add the message
    contact.add_message(message)
    
    # Verify the message was added
    assert len(contact.messages) == 1
    assert contact.messages[0] is message

@pytest.mark.unit
def test_contact_model_to_dict():
    """Test converting a Contact to a dictionary."""
    from src.data_layer.models import Contact, Message
    
    # Create a contact
    contact = Contact(
        phone_number="1234567890",
        messages=[]
    )
    
    # Create a message
    message = Message(
        timestamp="2023-01-01 12:00:00",
        phone_number="1234567890",
        message_type="sent",
        content="Hello, world!"
    )
    
    # Add the message
    contact.add_message(message)
    
    # Convert to dictionary
    result = contact.to_dict()
    
    # Verify the result
    assert result["phone_number"] == "1234567890"
    assert len(result["messages"]) == 1
    assert result["messages"][0]["timestamp"] == "2023-01-01 12:00:00"
    assert result["messages"][0]["phone_number"] == "1234567890"
    assert result["messages"][0]["message_type"] == "sent"
    assert result["messages"][0]["content"] == "Hello, world!"
