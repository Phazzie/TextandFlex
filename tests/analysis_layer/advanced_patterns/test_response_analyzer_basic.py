"""
Basic tests for the ResponseAnalyzer component.

This module contains tests for the constructor and basic functionality of the ResponseAnalyzer.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer
from src.analysis_layer.ml_model_service import MLModelService
from src.analysis_layer.ml_exceptions import MLError, PredictionError


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = [
        # A simple conversation with quick responses
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 10), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 15), 'phone_number': '5551234567', 'message_type': 'received'},

        # A conversation with a different contact with slower responses
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 30), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 15, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 16, 0), 'phone_number': '5559876543', 'message_type': 'sent'},

        # A third contact with mixed response times
        {'timestamp': datetime(2023, 1, 2, 9, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 2, 9, 45), 'phone_number': '5552223333', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 2, 10, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 2, 10, 3), 'phone_number': '5552223333', 'message_type': 'received'},
    ]

    return pd.DataFrame(data)


@pytest.fixture
def mock_ml_service():
    """Create a mock ML model service."""
    mock_service = MagicMock(spec=MLModelService)

    # Mock the extract_features method
    mock_service.extract_features.return_value = {
        'response_times': [300, 300, 1800, 3600, 2700, 180],
        'message_counts': {'5551234567': 4, '5559876543': 4, '5552223333': 4},
        'sent_received_ratios': {'5551234567': 1.0, '5559876543': 1.0, '5552223333': 1.0}
    }

    # Mock the predict method
    mock_service.predict.return_value = {
        'predictions': [
            {'contact': '5551234567', 'expected_response_time': 300, 'confidence': 0.9},
            {'contact': '5559876543', 'expected_response_time': 2700, 'confidence': 0.8},
            {'contact': '5552223333', 'expected_response_time': 1440, 'confidence': 0.7}
        ],
        'model_name': 'ResponseModel',
        'model_version': '1.0'
    }

    return mock_service


@pytest.fixture
def mock_logging_service():
    """Create a mock logging service."""
    mock_logger = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()
    return mock_logger


@pytest.mark.unit
def test_init_default():
    """Test that the ResponseAnalyzer can be initialized with default parameters."""
    analyzer = ResponseAnalyzer()
    assert analyzer is not None
    assert hasattr(analyzer, 'last_error')
    assert analyzer.last_error is None


@pytest.mark.unit
def test_init_with_ml_service(mock_ml_service, mock_logging_service):
    """Test that the ResponseAnalyzer can be initialized and have services assigned."""
    analyzer = ResponseAnalyzer()
    analyzer.ml_model_service = mock_ml_service
    analyzer.logging_service = mock_logging_service

    assert analyzer is not None
    assert analyzer.ml_model_service is mock_ml_service
    assert analyzer.logging_service is mock_logging_service
    assert analyzer.last_error is None


@pytest.mark.unit
def test_analyze_response_patterns_basic(sample_df):
    """Test basic response pattern analysis functionality."""
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_response_patterns(sample_df)

    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'conversation_flows' in result
    assert 'response_times' in result
    assert 'reciprocity_patterns' in result

    # Check that there's no error
    assert 'error' not in result


@pytest.mark.unit
def test_analyze_response_patterns_with_ml_service(sample_df, mock_ml_service):
    """Test response pattern analysis with ML model service."""
    analyzer = ResponseAnalyzer()
    analyzer.ml_model_service = mock_ml_service

    result = analyzer.analyze_response_patterns(sample_df)

    # Check that the ML service was called
    mock_ml_service.extract_features.assert_called_once()

    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'conversation_flows' in result
    assert 'response_times' in result
    assert 'reciprocity_patterns' in result
    assert 'predictions' in result

    # Check that there's no error
    assert 'error' not in result


@pytest.mark.unit
def test_analyze_response_patterns_empty_df():
    """Test handling of empty DataFrame."""
    analyzer = ResponseAnalyzer()
    empty_df = pd.DataFrame()
    result = analyzer.analyze_response_patterns(empty_df)

    # Check that an error is returned
    assert 'error' in result
    assert 'empty data' in result['error'].lower()

    # Check that last_error is set
    assert analyzer.last_error is not None
    assert 'empty data' in analyzer.last_error.lower()


@pytest.mark.unit
def test_analyze_response_patterns_missing_columns():
    """Test handling of DataFrame with missing required columns."""
    analyzer = ResponseAnalyzer()

    # DataFrame missing 'message_type'
    df_missing_column = pd.DataFrame({
        'timestamp': [datetime(2023, 1, 1, 10, 0)],
        'phone_number': ['5551234567']
    })

    result = analyzer.analyze_response_patterns(df_missing_column)

    # Check that an error is returned
    assert 'error' in result
    assert 'missing required column' in result['error'].lower()

    # Check that last_error is set
    assert analyzer.last_error is not None
    assert 'missing required column' in analyzer.last_error.lower()


@pytest.mark.unit
def test_analyze_response_patterns_ml_error(sample_df, mock_ml_service):
    """Test handling of ML service errors."""
    # Configure the mock to raise an error
    mock_ml_service.extract_features.side_effect = MLError("Test ML error")

    analyzer = ResponseAnalyzer()
    analyzer.ml_model_service = mock_ml_service

    result = analyzer.analyze_response_patterns(sample_df)

    # Check that the analysis still completes without ML features
    assert isinstance(result, dict)
    assert 'conversation_flows' in result
    assert 'response_times' in result
    assert 'reciprocity_patterns' in result

    # Check that there's no predictions due to the error
    assert 'predictions' not in result

    # Check that the error is logged but not returned (graceful degradation)
    assert 'error' not in result
    assert analyzer.last_error is not None
    assert 'ml error' in analyzer.last_error.lower()


@pytest.mark.unit
def test_error_tracking(sample_df):
    """Test that the last_error attribute is properly updated."""
    analyzer = ResponseAnalyzer()

    # First call with valid data should not set an error
    analyzer.analyze_response_patterns(sample_df)
    assert analyzer.last_error is None

    # Call with empty data should set an error
    analyzer.analyze_response_patterns(pd.DataFrame())
    assert analyzer.last_error is not None
    assert 'empty data' in analyzer.last_error.lower()

    # Another call with valid data should clear the error
    analyzer.analyze_response_patterns(sample_df)
    assert analyzer.last_error is None


@pytest.mark.unit
def test_column_mapping(sample_df):
    """Test that column mapping works correctly."""
    # Rename columns in the DataFrame
    df_renamed = sample_df.rename(columns={
        'timestamp': 'time',
        'phone_number': 'contact',
        'message_type': 'direction'
    })

    # Create column mapping
    column_mapping = {
        'timestamp': 'time',
        'phone_number': 'contact',
        'message_type': 'direction'
    }

    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_response_patterns(df_renamed, column_mapping)

    # Check that the analysis works with the mapping
    assert isinstance(result, dict)
    assert 'conversation_flows' in result
    assert 'response_times' in result
    assert 'reciprocity_patterns' in result

    # Check that there's no error
    assert 'error' not in result
