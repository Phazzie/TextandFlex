"""
Tests for the indexer module.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

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
def mock_repository(sample_dataframe):
    """Create a mock repository for testing."""
    from src.data_layer.models import PhoneRecordDataset
    
    # Create a mock repository
    mock_repo = MagicMock()
    
    # Create a dataset
    dataset = PhoneRecordDataset(
        name="test_dataset",
        data=sample_dataframe,
        column_mapping={
            'timestamp': 'timestamp',
            'phone_number': 'phone_number',
            'message_type': 'message_type',
            'message_content': 'message_content'
        }
    )
    
    # Configure the mock repository
    mock_repo.get_dataset.return_value = dataset
    
    return mock_repo

@pytest.mark.unit
def test_indexer_initialization(mock_repository):
    """Test initializing the indexer."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Verify the indexer
    assert indexer.repository is mock_repository
    assert isinstance(indexer.indices, dict)
    assert len(indexer.indices) == 0

@pytest.mark.unit
def test_indexer_create_index(mock_repository):
    """Test creating an index."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Create an index
    result = indexer.create_index("test_dataset", "phone_number")
    
    # Verify the result
    assert result is True
    assert "test_dataset" in indexer.indices
    assert "phone_number" in indexer.indices["test_dataset"]
    
    # Verify the index structure
    index = indexer.indices["test_dataset"]["phone_number"]
    assert "1234567890" in index
    assert "9876543210" in index
    assert "5551234567" in index
    assert len(index["1234567890"]) == 2
    assert len(index["9876543210"]) == 2
    assert len(index["5551234567"]) == 1

@pytest.mark.unit
def test_indexer_create_index_dataset_not_found(mock_repository):
    """Test creating an index for a non-existent dataset."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Configure the mock repository to return None
    mock_repository.get_dataset.return_value = None
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Create an index
    result = indexer.create_index("non_existent_dataset", "phone_number")
    
    # Verify the result
    assert result is False
    assert "non_existent_dataset" not in indexer.indices

@pytest.mark.unit
def test_indexer_create_index_invalid_column(mock_repository):
    """Test creating an index for an invalid column."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Create an index
    result = indexer.create_index("test_dataset", "non_existent_column")
    
    # Verify the result
    assert result is False
    assert "test_dataset" not in indexer.indices

@pytest.mark.unit
def test_indexer_get_index(mock_repository):
    """Test getting an index."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Create an index
    indexer.create_index("test_dataset", "phone_number")
    
    # Get the index
    index = indexer.get_index("test_dataset", "phone_number")
    
    # Verify the index
    assert index is not None
    assert "1234567890" in index
    assert "9876543210" in index
    assert "5551234567" in index

@pytest.mark.unit
def test_indexer_get_index_not_found(mock_repository):
    """Test getting a non-existent index."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Get a non-existent index
    index = indexer.get_index("test_dataset", "phone_number")
    
    # Verify the result
    assert index is None

@pytest.mark.unit
def test_indexer_query_by_index(mock_repository, sample_dataframe):
    """Test querying by index."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Create an index
    indexer.create_index("test_dataset", "phone_number")
    
    # Query by index
    result = indexer.query_by_index("test_dataset", "phone_number", "1234567890")
    
    # Verify the result
    assert result is not None
    assert len(result) == 2
    assert all(result['phone_number'] == '1234567890')

@pytest.mark.unit
def test_indexer_query_by_index_not_found(mock_repository):
    """Test querying by a non-existent index."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Query by a non-existent index
    result = indexer.query_by_index("test_dataset", "phone_number", "1234567890")
    
    # Verify the result
    assert result is None

@pytest.mark.unit
def test_indexer_query_by_index_value_not_found(mock_repository):
    """Test querying by an index with a non-existent value."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Create an index
    indexer.create_index("test_dataset", "phone_number")
    
    # Query by index with a non-existent value
    result = indexer.query_by_index("test_dataset", "phone_number", "non_existent_value")
    
    # Verify the result
    assert result is not None
    assert len(result) == 0

@pytest.mark.unit
def test_indexer_create_multiple_indices(mock_repository):
    """Test creating multiple indices."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Create indices
    indexer.create_index("test_dataset", "phone_number")
    indexer.create_index("test_dataset", "message_type")
    
    # Verify the indices
    assert "test_dataset" in indexer.indices
    assert "phone_number" in indexer.indices["test_dataset"]
    assert "message_type" in indexer.indices["test_dataset"]
    
    # Verify the phone_number index
    phone_index = indexer.indices["test_dataset"]["phone_number"]
    assert "1234567890" in phone_index
    assert "9876543210" in phone_index
    assert "5551234567" in phone_index
    
    # Verify the message_type index
    type_index = indexer.indices["test_dataset"]["message_type"]
    assert "sent" in type_index
    assert "received" in type_index
    assert len(type_index["sent"]) == 3
    assert len(type_index["received"]) == 2

@pytest.mark.unit
def test_indexer_remove_index(mock_repository):
    """Test removing an index."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Create indices
    indexer.create_index("test_dataset", "phone_number")
    indexer.create_index("test_dataset", "message_type")
    
    # Remove an index
    result = indexer.remove_index("test_dataset", "phone_number")
    
    # Verify the result
    assert result is True
    assert "test_dataset" in indexer.indices
    assert "phone_number" not in indexer.indices["test_dataset"]
    assert "message_type" in indexer.indices["test_dataset"]

@pytest.mark.unit
def test_indexer_remove_index_not_found(mock_repository):
    """Test removing a non-existent index."""
    from src.data_layer.indexer import DatasetIndexer
    
    # Initialize indexer
    indexer = DatasetIndexer(repository=mock_repository)
    
    # Remove a non-existent index
    result = indexer.remove_index("test_dataset", "phone_number")
    
    # Verify the result
    assert result is False
