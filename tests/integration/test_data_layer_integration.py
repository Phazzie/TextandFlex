"""
Integration tests for the data layer components.
"""
import os
import pytest
import pandas as pd
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after the test
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'timestamp': [
            '2023-01-01 12:00:00', 
            '2023-01-01 12:30:00', 
            '2023-01-01 13:00:00',
            '2023-01-02 12:00:00',
            '2023-01-02 12:30:00'
        ],
        'phone_number': [
            '1234567890', 
            '9876543210', 
            '5551234567',
            '1234567890',
            '9876543210'
        ],
        'message_type': [
            'sent', 
            'received', 
            'sent',
            'received',
            'sent'
        ],
        'message_content': [
            'Hello, world!', 
            'Hi there!', 
            'How are you?',
            'I am fine, thanks!',
            'Great to hear that!'
        ]
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

@pytest.mark.integration
def test_repository_query_engine_integration(temp_storage_dir, sample_dataframe, sample_column_mapping):
    """Test integration between repository and query engine."""
    from src.data_layer.repository import PhoneRecordRepository
    from src.data_layer.query_engine import QueryEngine
    
    # Initialize repository
    repo = PhoneRecordRepository(storage_dir=temp_storage_dir)
    
    # Add a dataset
    result = repo.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping
    )
    
    assert result is True
    
    # Initialize query engine
    query_engine = QueryEngine(repository=repo)
    
    # Test filtering by phone number
    filtered_data = query_engine.filter_by_phone_number("test_dataset", "1234567890")
    assert filtered_data is not None
    assert len(filtered_data) == 2
    assert all(filtered_data['phone_number'] == '1234567890')
    
    # Test filtering by date range
    filtered_data = query_engine.filter_by_date_range("test_dataset", "2023-01-01")
    assert filtered_data is not None
    assert len(filtered_data) == 3
    
    # Test filtering by message type
    filtered_data = query_engine.filter_by_message_type("test_dataset", "sent")
    assert filtered_data is not None
    assert len(filtered_data) == 3
    assert all(filtered_data['message_type'] == 'sent')
    
    # Test counting by message type
    counts = query_engine.count_by_message_type("test_dataset")
    assert counts is not None
    assert counts['sent'] == 3
    assert counts['received'] == 2

@pytest.mark.integration
def test_repository_indexer_integration(temp_storage_dir, sample_dataframe, sample_column_mapping):
    """Test integration between repository and indexer."""
    from src.data_layer.repository import PhoneRecordRepository
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize repository
    repo = PhoneRecordRepository(storage_dir=temp_storage_dir)
    
    # Add a dataset
    result = repo.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping
    )
    
    assert result is True
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=repo)
    
    # Create an index
    result = indexer.create_index("test_dataset", "phone_number")
    assert result is True
    
    # Query by index
    filtered_data = indexer.query_by_index("test_dataset", "phone_number", "1234567890")
    assert filtered_data is not None
    assert len(filtered_data) == 2
    assert all(filtered_data['phone_number'] == '1234567890')
    
    # Create another index
    result = indexer.create_index("test_dataset", "message_type")
    assert result is True
    
    # Query by index
    filtered_data = indexer.query_by_index("test_dataset", "message_type", "sent")
    assert filtered_data is not None
    assert len(filtered_data) == 3
    assert all(filtered_data['message_type'] == 'sent')

@pytest.mark.integration
def test_full_data_layer_integration(temp_storage_dir, sample_dataframe, sample_column_mapping):
    """Test integration between repository, query engine, and indexer."""
    from src.data_layer.repository import PhoneRecordRepository
    from src.data_layer.query_engine import QueryEngine
    from src.data_layer.indexer import DatasetIndexer
    from src.data_layer.models import Message, Contact
    
    # Initialize repository
    repo = PhoneRecordRepository(storage_dir=temp_storage_dir)
    
    # Add a dataset
    result = repo.add_dataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping=sample_column_mapping
    )
    
    assert result is True
    
    # Initialize query engine
    query_engine = QueryEngine(repository=repo)
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=repo)
    
    # Create an index
    result = indexer.create_index("test_dataset", "phone_number")
    assert result is True
    
    # Get unique phone numbers
    phone_numbers = query_engine.get_unique_phone_numbers("test_dataset")
    assert len(phone_numbers) == 3
    
    # Create contacts from the dataset
    contacts = {}
    for phone_number in phone_numbers:
        # Get messages for this contact using the indexer
        messages_df = indexer.query_by_index("test_dataset", "phone_number", phone_number)
        
        # Create a contact
        contact = Contact(phone_number=phone_number)
        
        # Add messages to the contact
        for _, row in messages_df.iterrows():
            message = Message(
                timestamp=row['timestamp'],
                phone_number=row['phone_number'],
                message_type=row['message_type'],
                content=row['message_content']
            )
            contact.add_message(message)
        
        contacts[phone_number] = contact
    
    # Verify the contacts
    assert len(contacts) == 3
    assert len(contacts['1234567890'].messages) == 2
    assert len(contacts['9876543210'].messages) == 2
    assert len(contacts['5551234567'].messages) == 1
    
    # Test updating a dataset
    # Create a new dataframe with additional data
    new_data = pd.DataFrame({
        'timestamp': ['2023-01-03 12:00:00'],
        'phone_number': ['1234567890'],
        'message_type': ['sent'],
        'message_content': ['New message!']
    })
    
    # Update the dataset
    result = repo.update_dataset(
        name="test_dataset",
        data=pd.concat([sample_dataframe, new_data], ignore_index=True)
    )
    
    assert result is True
    
    # Verify the update
    dataset = repo.get_dataset("test_dataset")
    assert len(dataset.data) == 6
    
    # Re-create the index
    result = indexer.create_index("test_dataset", "phone_number")
    assert result is True
    
    # Query by index again
    filtered_data = indexer.query_by_index("test_dataset", "phone_number", "1234567890")
    assert filtered_data is not None
    assert len(filtered_data) == 3  # Now there should be 3 messages for this contact
