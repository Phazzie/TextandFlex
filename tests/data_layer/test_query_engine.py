"""
Tests for the query engine module.
"""
import pytest
import pandas as pd
from datetime import datetime
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

    # Configure query_dataset to apply the query function to the dataset
    def side_effect(dataset_name, query_func):
        if dataset_name == "test_dataset":
            return query_func(sample_dataframe)
        return None

    mock_repo.query_dataset.side_effect = side_effect

    return mock_repo

@pytest.mark.unit
def test_query_engine_initialization(mock_repository):
    """Test initializing the query engine."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Verify the query engine
    assert query_engine.repository is mock_repository

@pytest.mark.unit
def test_query_engine_filter_by_phone_number(mock_repository):
    """Test filtering by phone number."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Filter by phone number
    result = query_engine.filter_by_phone_number("test_dataset", "1234567890")

    # Verify the result
    assert result is not None
    assert len(result) == 2
    assert all(result['phone_number'] == '1234567890')

@pytest.mark.unit
def test_query_engine_filter_by_date_range(mock_repository):
    """Test filtering by date range."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Filter by date range
    result = query_engine.filter_by_date_range(
        "test_dataset",
        start_date="2023-01-01",
        end_date="2023-01-01"
    )

    # Verify the result
    assert result is not None
    assert len(result) == 3
    assert all(pd.to_datetime(result['timestamp']).dt.date.astype(str) == '2023-01-01')

@pytest.mark.unit
def test_query_engine_filter_by_message_type(mock_repository):
    """Test filtering by message type."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Filter by message type
    result = query_engine.filter_by_message_type("test_dataset", "sent")

    # Verify the result
    assert result is not None
    assert len(result) == 3
    assert all(result['message_type'] == 'sent')

@pytest.mark.unit
def test_query_engine_filter_by_content(mock_repository):
    """Test filtering by message content."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Filter by content
    result = query_engine.filter_by_content("test_dataset", "Hello")

    # Verify the result
    assert result is not None
    assert len(result) == 1
    assert result.iloc[0]['message_content'] == 'Hello, world!'

@pytest.mark.unit
def test_query_engine_sort_by_timestamp(mock_repository):
    """Test sorting by timestamp."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Sort by timestamp (ascending)
    result = query_engine.sort_by_timestamp("test_dataset", ascending=True)

    # Verify the result
    assert result is not None
    assert len(result) == 5
    assert result.iloc[0]['timestamp'] == '2023-01-01 12:00:00'
    assert result.iloc[-1]['timestamp'] == '2023-01-02 12:30:00'

    # Sort by timestamp (descending)
    result = query_engine.sort_by_timestamp("test_dataset", ascending=False)

    # Verify the result
    assert result is not None
    assert len(result) == 5
    assert result.iloc[0]['timestamp'] == '2023-01-02 12:30:00'
    assert result.iloc[-1]['timestamp'] == '2023-01-01 12:00:00'

@pytest.mark.unit
def test_query_engine_get_unique_phone_numbers(mock_repository):
    """Test getting unique phone numbers."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Get unique phone numbers
    result = query_engine.get_unique_phone_numbers("test_dataset")

    # Verify the result
    assert result is not None
    assert len(result) == 3
    assert set(result) == {'1234567890', '9876543210', '5551234567'}

@pytest.mark.unit
def test_query_engine_count_by_message_type(mock_repository):
    """Test counting by message type."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Count by message type
    result = query_engine.count_by_message_type("test_dataset")

    # Verify the result
    assert result is not None
    assert len(result) == 2
    assert result['sent'] == 3
    assert result['received'] == 2

@pytest.mark.unit
def test_query_engine_count_by_phone_number(mock_repository):
    """Test counting by phone number."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Count by phone number
    result = query_engine.count_by_phone_number("test_dataset")

    # Verify the result
    assert result is not None
    assert len(result) == 3
    assert result['1234567890'] == 2
    assert result['9876543210'] == 2
    assert result['5551234567'] == 1

@pytest.mark.unit
def test_query_engine_count_by_date(mock_repository):
    """Test counting by date."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Count by date
    result = query_engine.count_by_date("test_dataset")

    # Verify the result
    assert result is not None
    assert len(result) == 2
    assert result['2023-01-01'] == 3
    assert result['2023-01-02'] == 2

@pytest.mark.unit
def test_query_engine_build_query(mock_repository):
    """Test building a complex query."""
    from src.data_layer.query_engine import QueryEngine

    # Initialize query engine
    query_engine = QueryEngine(repository=mock_repository)

    # Build a query
    query = query_engine.build_query()
    query.filter_by_phone_number("1234567890")
    query.filter_by_message_type("received")

    # Execute the query
    result = query.execute("test_dataset")

    # Verify the result
    assert result is not None
    assert len(result) == 1
    assert result.iloc[0]['phone_number'] == '1234567890'
    assert result.iloc[0]['message_type'] == 'received'
