"""
Tests for the Excel parser module.
"""
import os
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, mock_open
import tempfile


@pytest.fixture
def sample_excel_data():
    """Create a sample DataFrame that would be read from Excel."""
    return pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00', '2023-01-01 12:30:00', '2023-01-01 13:00:00'],
        'phone_number': ['1234567890', '9876543210', '5551234567'],
        'message_type': ['sent', 'received', 'sent'],
        'message_content': ['Hello, world!', 'Hi there!', 'How are you?']
    })


@pytest.fixture
def malformed_excel_data():
    """Create a malformed DataFrame that would be read from Excel."""
    return pd.DataFrame({
        'date': ['2023-01-01 12:00:00', 'invalid', '2023-01-01 13:00:00'],
        'contact': ['1234567890', 'abc', '5551234567'],
        'type': ['sent', 'unknown', 'sent'],
        'content': ['Hello, world!', 'Hi there!', 'How are you?']
    })


@pytest.mark.unit
def test_excel_parser_initialization():
    """Test that ExcelParser initializes correctly."""
    from src.data_layer.excel_parser import ExcelParser

    # Test with default parameters
    parser = ExcelParser()
    assert parser is not None
    assert hasattr(parser, 'parse')

    # Test with custom parameters
    custom_parser = ExcelParser(
        required_columns=['col1', 'col2'],
        date_format='%d/%m/%Y',
        valid_message_types=['type1', 'type2']
    )
    assert custom_parser.required_columns == ['col1', 'col2']
    assert custom_parser.date_format == '%d/%m/%Y'
    assert custom_parser.valid_message_types == ['type1', 'type2']


@pytest.mark.unit
def test_excel_parser_parse_valid_file(sample_excel_data):
    """Test parsing a valid Excel file."""
    from src.data_layer.excel_parser import ExcelParser

    # Mock pd.read_excel to return our sample data
    with patch('pandas.read_excel', return_value=sample_excel_data):
        # Mock file existence check
        with patch('os.path.isfile', return_value=True):
            # Mock file extension check
            with patch('pathlib.Path.suffix', return_value='.xlsx'):
                parser = ExcelParser()
                result = parser.parse('dummy.xlsx')

                # Verify the result
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 3
                assert list(result.columns) == ['timestamp', 'phone_number', 'message_type', 'message_content']
                assert result['message_type'].iloc[0] == 'sent'


@pytest.mark.unit
def test_excel_parser_parse_invalid_file():
    """Test parsing an invalid Excel file."""
    from src.data_layer.excel_parser import ExcelParser
    from src.data_layer.parser_exceptions import ParserError

    # Test with non-existent file
    with patch('os.path.isfile', return_value=False):
        parser = ExcelParser()
        with pytest.raises(FileNotFoundError):
            parser.parse('non_existent_file.xlsx')

    # Test with file that exists but has invalid extension
    with patch('os.path.isfile', return_value=True):
        parser = ExcelParser()
        with pytest.raises(ValueError):
            parser.parse('invalid_extension.csv')

    # Test with file that exists but pandas can't read it
    with patch('os.path.isfile', return_value=True):
        with patch('pandas.read_excel', side_effect=Exception('Excel read error')):
            parser = ExcelParser()
            with pytest.raises(ParserError):
                parser.parse('unreadable_file.xlsx')


@pytest.mark.unit
def test_excel_parser_parse_missing_columns(malformed_excel_data):
    """Test parsing an Excel file with missing required columns."""
    from src.data_layer.excel_parser import ExcelParser
    from src.data_layer.parser_exceptions import ValidationError

    # Mock pd.read_excel to return malformed data
    with patch('pandas.read_excel', return_value=malformed_excel_data):
        # Mock file existence check
        with patch('os.path.isfile', return_value=True):
            # Mock file extension check
            with patch('pathlib.Path.suffix', return_value='.xlsx'):
                parser = ExcelParser()
                with pytest.raises(ValueError) as excinfo:
                    parser.parse('malformed_file.xlsx')

                # Verify the error message mentions missing columns
                assert 'missing required columns' in str(excinfo.value).lower()


@pytest.mark.unit
def test_excel_parser_column_mapping():
    """Test column mapping functionality."""
    from src.data_layer.excel_parser import ExcelParser

    # Create a DataFrame with differently named columns
    df = pd.DataFrame({
        'Date': ['2023-01-01 12:00:00'],
        'Phone': ['1234567890'],
        'Type': ['sent'],
        'Message': ['Hello, world!']
    })

    # Create a column mapping
    column_mapping = {
        'timestamp': 'Date',
        'phone_number': 'Phone',
        'message_type': 'Type',
        'message_content': 'Message'
    }

    # Mock pd.read_excel to return our DataFrame
    with patch('pandas.read_excel', return_value=df):
        # Mock file existence check
        with patch('os.path.isfile', return_value=True):
            parser = ExcelParser(column_mapping=column_mapping)
            result = parser.parse('mapped_file.xlsx')

            # Verify the result has the standard column names
            assert list(result.columns) == ['timestamp', 'phone_number', 'message_type', 'message_content']


@pytest.mark.unit
def test_excel_parser_auto_column_mapping():
    """Test automatic column mapping functionality."""
    from src.data_layer.excel_parser import ExcelParser

    # Create a DataFrame with differently named columns
    df = pd.DataFrame({
        'Date': ['2023-01-01 12:00:00'],
        'Contact Number': ['1234567890'],
        'Message Direction': ['sent'],
        'Text Content': ['Hello, world!']
    })

    # Mock pd.read_excel to return our DataFrame
    with patch('pandas.read_excel', return_value=df):
        # Mock file existence check
        with patch('os.path.isfile', return_value=True):
            parser = ExcelParser(auto_map_columns=True)
            result = parser.parse('auto_mapped_file.xlsx')

            # Verify the result has the standard column names
            assert list(result.columns) == ['timestamp', 'phone_number', 'message_type', 'message_content']


@pytest.mark.unit
def test_excel_parser_data_validation(sample_excel_data):
    """Test data validation during parsing."""
    from src.data_layer.excel_parser import ExcelParser
    from src.data_layer.parser_exceptions import ValidationError, ParserError

    # Create a DataFrame with invalid values
    invalid_df = sample_excel_data.copy()
    invalid_df.loc[1, 'timestamp'] = 'invalid'
    invalid_df.loc[2, 'phone_number'] = 'abc'

    # Mock pd.read_excel to return invalid data
    with patch('pandas.read_excel', return_value=invalid_df):
        # Mock file existence check
        with patch('os.path.isfile', return_value=True):
            # Mock file extension check
            with patch('pathlib.Path.suffix', return_value='.xlsx'):
                parser = ExcelParser(validate_data=True)
                with pytest.raises(ParserError) as excinfo:
                    parser.parse('invalid_data.xlsx')

                # Verify the error message mentions validation errors
                assert 'validation errors' in str(excinfo.value).lower()

    # Test with validation disabled
    with patch('pandas.read_excel', return_value=invalid_df):
        with patch('os.path.isfile', return_value=True):
            # Mock file extension check
            with patch('pathlib.Path.suffix', return_value='.xlsx'):
                parser = ExcelParser(validate_data=False)
                result = parser.parse('invalid_data_no_validation.xlsx')

                # Verify the result contains the invalid data
                assert result.loc[1, 'timestamp'] == 'invalid'
                assert result.loc[2, 'phone_number'] == 'abc'


@pytest.mark.unit
def test_excel_parser_sheet_selection():
    """Test sheet selection functionality."""
    from src.data_layer.excel_parser import ExcelParser

    # Mock pd.read_excel to verify sheet name is passed
    with patch('pandas.read_excel') as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame({
            'timestamp': ['2023-01-01 12:00:00'],
            'phone_number': ['1234567890'],
            'message_type': ['sent'],
            'message_content': ['Hello, world!']
        })

        # Mock file existence check
        with patch('os.path.isfile', return_value=True):
            parser = ExcelParser()

            # Test with default sheet (None)
            parser.parse('file.xlsx')
            mock_read_excel.assert_called_with('file.xlsx', sheet_name=0)

            # Test with specific sheet name
            parser.parse('file.xlsx', sheet_name='Sheet1')
            mock_read_excel.assert_called_with('file.xlsx', sheet_name='Sheet1')

            # Test with sheet index
            parser.parse('file.xlsx', sheet_name=2)
            mock_read_excel.assert_called_with('file.xlsx', sheet_name=2)
