"""
Tests for the data cleaning utilities.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime


@pytest.fixture
def sample_dirty_data():
    """Create a sample DataFrame with data that needs cleaning."""
    return pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00', '01/01/2023 12:30 PM', 'invalid'],
        'phone_number': ['+1 (123) 456-7890', '987-654-3210', 'abc'],
        'message_type': ['SENT', 'Received', 'unknown'],
        'message_content': ['Hello, world!', ' Hi there! ', np.nan]
    })


@pytest.mark.unit
def test_normalize_phone_numbers():
    """Test normalization of phone numbers."""
    from src.utils.data_cleaner import normalize_phone_numbers

    # Test with various phone number formats
    phone_numbers = [
        '+1 (123) 456-7890',
        '987-654-3210',
        '(555) 123 4567',
        '+44 7911 123456',
        '1234567890'
    ]

    expected = [
        '11234567890',
        '9876543210',
        '5551234567',
        '447911123456',
        '1234567890'
    ]

    # Create a DataFrame with phone numbers
    df = pd.DataFrame({'phone_number': phone_numbers})

    # Normalize the phone numbers
    result = normalize_phone_numbers(df)

    # Verify the results
    for i, expected_number in enumerate(expected):
        assert result['phone_number'].iloc[i] == expected_number

    # Test with invalid phone numbers
    df = pd.DataFrame({'phone_number': ['abc', '', np.nan]})
    result = normalize_phone_numbers(df)

    # Invalid numbers should be preserved
    assert result['phone_number'].iloc[0] == 'abc'
    assert result['phone_number'].iloc[1] == ''
    assert pd.isna(result['phone_number'].iloc[2])


@pytest.mark.unit
def test_standardize_timestamps():
    """Test standardization of timestamps."""
    from src.utils.data_cleaner import standardize_timestamps

    # Test with various timestamp formats
    timestamps = [
        '2023-01-01 12:00:00',
        '01/01/2023 12:30 PM',
        '2023-01-01T12:45:30',
        'Jan 1, 2023 1:00 PM'
    ]

    # Expected results in standard format
    expected = [
        '2023-01-01 12:00:00',
        '2023-01-01 12:30:00',
        '2023-01-01 12:45:30',
        '2023-01-01 13:00:00'
    ]

    # Create a DataFrame with timestamps
    df = pd.DataFrame({'timestamp': timestamps})

    # Standardize the timestamps
    result = standardize_timestamps(df, '%Y-%m-%d %H:%M:%S')

    # Verify the results
    for i, expected_timestamp in enumerate(expected):
        assert result['timestamp'].iloc[i] == expected_timestamp

    # Test with invalid timestamps
    df = pd.DataFrame({'timestamp': ['invalid', '', np.nan]})
    result = standardize_timestamps(df, '%Y-%m-%d %H:%M:%S')

    # Invalid timestamps should be preserved
    assert result['timestamp'].iloc[0] == 'invalid'
    assert result['timestamp'].iloc[1] == ''
    assert pd.isna(result['timestamp'].iloc[2])


@pytest.mark.unit
def test_normalize_message_types():
    """Test normalization of message types."""
    from src.utils.data_cleaner import normalize_message_types

    # Test with various message type formats
    message_types = [
        'SENT',
        'Received',
        'sent',
        'RECEIVED',
        'unknown'
    ]

    # Expected results in standard format
    expected = [
        'sent',
        'received',
        'sent',
        'received',
        'unknown'
    ]

    # Create a DataFrame with message types
    df = pd.DataFrame({'message_type': message_types})

    # Normalize the message types
    result = normalize_message_types(df)

    # Verify the results
    for i, expected_type in enumerate(expected):
        assert result['message_type'].iloc[i] == expected_type


@pytest.mark.unit
def test_clean_message_content():
    """Test cleaning of message content."""
    from src.utils.data_cleaner import clean_message_content

    # Test with various message contents
    message_contents = [
        'Hello, world!',
        ' Hi there! ',
        '\tTrimmed\n',
        np.nan,
        ''
    ]

    # Expected results after cleaning
    expected = [
        'Hello, world!',
        'Hi there!',
        'Trimmed',
        '',
        ''
    ]

    # Create a DataFrame with message contents
    df = pd.DataFrame({'message_content': message_contents})

    # Clean the message contents
    result = clean_message_content(df)

    # Verify the results
    for i, expected_content in enumerate(expected):
        if pd.isna(result['message_content'].iloc[i]):
            assert expected_content == ''
        else:
            assert result['message_content'].iloc[i] == expected_content


@pytest.mark.unit
def test_clean_dataframe(sample_dirty_data):
    """Test cleaning of the entire DataFrame."""
    from src.utils.data_cleaner import clean_dataframe

    # Clean the DataFrame
    result = clean_dataframe(sample_dirty_data)

    # Verify the results
    assert result['phone_number'].iloc[0] == '11234567890'
    assert result['phone_number'].iloc[1] == '9876543210'
    assert result['phone_number'].iloc[2] == 'abc'  # Invalid number preserved

    assert result['timestamp'].iloc[0] == '2023-01-01 12:00:00'
    assert result['timestamp'].iloc[1] == '2023-01-01 12:30:00'
    assert result['timestamp'].iloc[2] == 'invalid'  # Invalid timestamp preserved

    assert result['message_type'].iloc[0] == 'sent'
    assert result['message_type'].iloc[1] == 'received'
    assert result['message_type'].iloc[2] == 'unknown'

    assert result['message_content'].iloc[0] == 'Hello, world!'
    assert result['message_content'].iloc[1] == 'Hi there!'
    assert result['message_content'].iloc[2] == ''  # NaN replaced with empty string


@pytest.mark.unit
def test_remove_invalid_rows():
    """Test removal of invalid rows."""
    from src.utils.data_cleaner import remove_invalid_rows
    import pandas as pd

    # Create a test DataFrame with valid and invalid data
    df = pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00', '2023-01-01 12:30:00', 'invalid'],
        'phone_number': ['1234567890', '9876543210', 'abc'],
        'message_type': ['sent', 'received', 'unknown'],
        'message_content': ['Hello', 'World', 'Invalid']
    })

    # Remove invalid rows
    result = remove_invalid_rows(df)

    # Verify the results
    assert len(result) == 2  # One row should be removed
    assert 'invalid' not in result['timestamp'].values
    assert 'abc' not in result['phone_number'].values
    assert 'unknown' not in result['message_type'].values
