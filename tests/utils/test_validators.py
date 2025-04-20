"""
Tests for the data validation utilities.
"""
import os
import pytest
from unittest.mock import patch, mock_open
import pandas as pd
import numpy as np


@pytest.mark.unit
def test_validate_file_exists():
    """Test validation of file existence."""
    from src.utils.validators import validate_file_exists
    
    # Test with existing file
    with patch('os.path.isfile', return_value=True):
        # Should not raise an exception
        validate_file_exists('existing_file.xlsx')
    
    # Test with non-existent file
    with patch('os.path.isfile', return_value=False):
        with pytest.raises(FileNotFoundError):
            validate_file_exists('non_existent_file.xlsx')


@pytest.mark.unit
def test_validate_file_extension():
    """Test validation of file extension."""
    from src.utils.validators import validate_file_extension
    
    # Test with valid extension
    validate_file_extension('file.xlsx', ['.xlsx'])
    validate_file_extension('file.xls', ['.xlsx', '.xls'])
    
    # Test with invalid extension
    with pytest.raises(ValueError):
        validate_file_extension('file.csv', ['.xlsx', '.xls'])
    
    # Test case insensitivity
    validate_file_extension('file.XLSX', ['.xlsx'])
    validate_file_extension('file.xlsx', ['.XLSX'])


@pytest.mark.unit
def test_validate_excel_file():
    """Test validation of Excel file."""
    from src.utils.validators import validate_excel_file
    
    # Mock file existence check
    with patch('os.path.isfile', return_value=True):
        # Test with valid extension
        validate_excel_file('file.xlsx')
        validate_excel_file('file.xls')
        
        # Test with invalid extension
        with pytest.raises(ValueError):
            validate_excel_file('file.csv')


@pytest.mark.unit
def test_validate_dataframe_columns():
    """Test validation of DataFrame columns."""
    from src.utils.validators import validate_dataframe_columns
    
    # Create test DataFrames
    df_valid = pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00'],
        'phone_number': ['1234567890'],
        'message_type': ['sent'],
        'message_content': ['Hello, world!']
    })
    
    df_missing_column = pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00'],
        'phone_number': ['1234567890'],
        'message_content': ['Hello, world!']
    })
    
    df_empty = pd.DataFrame()
    
    # Define required columns
    required_columns = ['timestamp', 'phone_number', 'message_type', 'message_content']
    
    # Test with valid DataFrame
    validate_dataframe_columns(df_valid, required_columns)
    
    # Test with missing column
    with pytest.raises(ValueError) as excinfo:
        validate_dataframe_columns(df_missing_column, required_columns)
    assert 'message_type' in str(excinfo.value)
    
    # Test with empty DataFrame
    with pytest.raises(ValueError):
        validate_dataframe_columns(df_empty, required_columns)


@pytest.mark.unit
def test_validate_phone_number_format():
    """Test validation of phone number format."""
    from src.utils.validators import validate_phone_number_format
    
    # Test with valid phone numbers
    assert validate_phone_number_format('1234567890')  # Simple 10-digit
    assert validate_phone_number_format('+1 (123) 456-7890')  # Formatted US
    assert validate_phone_number_format('+44 7911 123456')  # UK format
    
    # Test with invalid phone numbers
    assert not validate_phone_number_format('123')  # Too short
    assert not validate_phone_number_format('abcdefghij')  # Non-numeric
    assert not validate_phone_number_format('')  # Empty


@pytest.mark.unit
def test_validate_timestamp_format():
    """Test validation of timestamp format."""
    from src.utils.validators import validate_timestamp_format
    
    # Test with valid timestamps
    assert validate_timestamp_format('2023-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')
    assert validate_timestamp_format('01/01/2023 12:00 PM', '%m/%d/%Y %I:%M %p')
    
    # Test with invalid timestamps
    assert not validate_timestamp_format('2023-01-01', '%Y-%m-%d %H:%M:%S')
    assert not validate_timestamp_format('invalid', '%Y-%m-%d %H:%M:%S')
    assert not validate_timestamp_format('', '%Y-%m-%d %H:%M:%S')


@pytest.mark.unit
def test_validate_message_type():
    """Test validation of message type."""
    from src.utils.validators import validate_message_type
    
    # Test with valid message types
    assert validate_message_type('sent', ['sent', 'received'])
    assert validate_message_type('received', ['sent', 'received'])
    
    # Test with case insensitivity
    assert validate_message_type('SENT', ['sent', 'received'])
    assert validate_message_type('Received', ['sent', 'received'])
    
    # Test with invalid message types
    assert not validate_message_type('draft', ['sent', 'received'])
    assert not validate_message_type('', ['sent', 'received'])


@pytest.mark.unit
def test_validate_dataframe_values():
    """Test validation of DataFrame values."""
    from src.utils.validators import validate_dataframe_values
    
    # Create test DataFrames
    df_valid = pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00'],
        'phone_number': ['1234567890'],
        'message_type': ['sent'],
        'message_content': ['Hello, world!']
    })
    
    df_invalid_phone = pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00'],
        'phone_number': ['abc'],  # Invalid phone
        'message_type': ['sent'],
        'message_content': ['Hello, world!']
    })
    
    df_invalid_timestamp = pd.DataFrame({
        'timestamp': ['invalid'],  # Invalid timestamp
        'phone_number': ['1234567890'],
        'message_type': ['sent'],
        'message_content': ['Hello, world!']
    })
    
    df_invalid_message_type = pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00'],
        'phone_number': ['1234567890'],
        'message_type': ['draft'],  # Invalid message type
        'message_content': ['Hello, world!']
    })
    
    # Define validation parameters
    timestamp_format = '%Y-%m-%d %H:%M:%S'
    valid_message_types = ['sent', 'received']
    
    # Test with valid DataFrame
    result = validate_dataframe_values(df_valid, timestamp_format, valid_message_types)
    assert result.empty  # No validation errors
    
    # Test with invalid phone number
    result = validate_dataframe_values(df_invalid_phone, timestamp_format, valid_message_types)
    assert not result.empty
    assert 'phone_number' in result.columns
    
    # Test with invalid timestamp
    result = validate_dataframe_values(df_invalid_timestamp, timestamp_format, valid_message_types)
    assert not result.empty
    assert 'timestamp' in result.columns
    
    # Test with invalid message type
    result = validate_dataframe_values(df_invalid_message_type, timestamp_format, valid_message_types)
    assert not result.empty
    assert 'message_type' in result.columns
