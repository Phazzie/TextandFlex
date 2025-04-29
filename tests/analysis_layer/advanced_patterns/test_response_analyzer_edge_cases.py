"""
Edge case tests for the ResponseAnalyzer component.

This module contains tests for boundary conditions and error handling in the ResponseAnalyzer.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer


@pytest.mark.unit
def test_empty_dataframe():
    """Test with empty DataFrame."""
    analyzer = ResponseAnalyzer()
    empty_df = pd.DataFrame()
    
    # Test analyze_response_patterns
    result = analyzer.analyze_response_patterns(empty_df)
    assert 'error' in result
    assert 'empty data' in result['error'].lower()
    
    # Test analyze_conversation_flows
    result = analyzer.analyze_conversation_flows(empty_df)
    assert isinstance(result, dict)
    assert len(result) == 0
    
    # Test analyze_response_times
    result = analyzer.analyze_response_times(empty_df)
    assert isinstance(result, dict)
    assert len(result) == 0
    
    # Test detect_reciprocity_patterns
    result = analyzer.detect_reciprocity_patterns(empty_df)
    assert isinstance(result, dict)
    assert len(result) == 0
    
    # Test predict_response_behavior
    result = analyzer.predict_response_behavior(empty_df, '5551234567')
    assert 'error' in result


@pytest.mark.unit
def test_single_message():
    """Test with single-message DataFrame."""
    analyzer = ResponseAnalyzer()
    single_message_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'}
    ])
    
    # Test analyze_response_patterns
    result = analyzer.analyze_response_patterns(single_message_df)
    assert isinstance(result, dict)
    assert 'conversation_flows' in result
    assert 'response_times' in result
    assert 'reciprocity_patterns' in result
    
    # Check that response times are empty (need at least 2 messages)
    assert result['response_times'] == {} or len(result['response_times']) == 0
    
    # Test predict_response_behavior
    result = analyzer.predict_response_behavior(single_message_df, '5551234567')
    assert 'error' in result or result['confidence'] < 0.5  # Should have low confidence


@pytest.mark.unit
def test_all_sent_messages():
    """Test with only sent messages."""
    analyzer = ResponseAnalyzer()
    all_sent_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 12, 0), 'phone_number': '5551234567', 'message_type': 'sent'}
    ])
    
    # Test analyze_response_patterns
    result = analyzer.analyze_response_patterns(all_sent_df)
    assert isinstance(result, dict)
    
    # Check that response times are empty (need both sent and received)
    assert result['response_times'] == {} or len(result['response_times']) == 0
    
    # Check reciprocity patterns
    assert result['reciprocity_patterns'] != {}
    assert 'message_ratios' in result['reciprocity_patterns']
    assert '5551234567' in result['reciprocity_patterns']['message_ratios']
    assert result['reciprocity_patterns']['message_ratios']['5551234567'] > 1.0  # All sent


@pytest.mark.unit
def test_all_received_messages():
    """Test with only received messages."""
    analyzer = ResponseAnalyzer()
    all_received_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 12, 0), 'phone_number': '5551234567', 'message_type': 'received'}
    ])
    
    # Test analyze_response_patterns
    result = analyzer.analyze_response_patterns(all_received_df)
    assert isinstance(result, dict)
    
    # Check that response times are empty (need both sent and received)
    assert result['response_times'] == {} or len(result['response_times']) == 0
    
    # Check reciprocity patterns
    assert result['reciprocity_patterns'] != {}
    assert 'message_ratios' in result['reciprocity_patterns']
    assert '5551234567' in result['reciprocity_patterns']['message_ratios']
    assert result['reciprocity_patterns']['message_ratios']['5551234567'] < 1.0  # All received


@pytest.mark.unit
def test_malformed_timestamps():
    """Test with invalid timestamp formats."""
    analyzer = ResponseAnalyzer()
    malformed_df = pd.DataFrame([
        {'timestamp': 'not a date', 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': '2023-01-01', 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': 123456789, 'phone_number': '5551234567', 'message_type': 'sent'}
    ])
    
    # Test analyze_response_patterns
    result = analyzer.analyze_response_patterns(malformed_df)
    assert 'error' in result
    
    # Create a DataFrame with mixed timestamp types
    mixed_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': '2023-01-01 11:00:00', 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': np.datetime64('2023-01-01T12:00:00'), 'phone_number': '5551234567', 'message_type': 'sent'}
    ])
    
    # Test analyze_response_patterns with mixed timestamps
    result = analyzer.analyze_response_patterns(mixed_df)
    assert isinstance(result, dict)
    assert 'error' not in result  # Should handle mixed timestamp formats


@pytest.mark.unit
def test_duplicate_timestamps():
    """Test with duplicate timestamps."""
    analyzer = ResponseAnalyzer()
    duplicate_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567', 'message_type': 'received'}
    ])
    
    # Test analyze_response_patterns
    result = analyzer.analyze_response_patterns(duplicate_df)
    assert isinstance(result, dict)
    assert 'error' not in result  # Should handle duplicate timestamps
    
    # Check response times
    assert result['response_times'] != {}
    
    # Check that the response times are calculated correctly
    # With duplicate timestamps, the response time might be 0 seconds
    if 'overall_avg_response_time' in result['response_times']:
        assert result['response_times']['overall_avg_response_time'] >= 0


@pytest.mark.unit
def test_future_timestamps():
    """Test with future timestamps."""
    analyzer = ResponseAnalyzer()
    future_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime.now() + timedelta(days=365), 'phone_number': '5551234567', 'message_type': 'sent'}
    ])
    
    # Test analyze_response_patterns
    result = analyzer.analyze_response_patterns(future_df)
    assert isinstance(result, dict)
    assert 'error' not in result  # Should handle future timestamps
    
    # Check that the analysis still works
    assert 'conversation_flows' in result
    assert 'response_times' in result
    assert 'reciprocity_patterns' in result


@pytest.mark.unit
def test_missing_required_columns():
    """Test with missing required columns."""
    analyzer = ResponseAnalyzer()
    
    # Test with missing timestamp
    missing_timestamp_df = pd.DataFrame([
        {'phone_number': '5551234567', 'message_type': 'sent'},
        {'phone_number': '5551234567', 'message_type': 'received'}
    ])
    
    result = analyzer.analyze_response_patterns(missing_timestamp_df)
    assert 'error' in result
    assert 'missing required column' in result['error'].lower()
    
    # Test with missing phone_number
    missing_phone_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'message_type': 'received'}
    ])
    
    result = analyzer.analyze_response_patterns(missing_phone_df)
    assert 'error' in result
    assert 'missing required column' in result['error'].lower()
    
    # Test with missing message_type
    missing_type_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567'}
    ])
    
    result = analyzer.analyze_response_patterns(missing_type_df)
    assert 'error' in result
    assert 'missing required column' in result['error'].lower()


@pytest.mark.unit
def test_invalid_column_types():
    """Test with invalid column types."""
    analyzer = ResponseAnalyzer()
    
    # Test with non-string phone_number
    invalid_phone_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': 5551234567, 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': 5551234567, 'message_type': 'received'}
    ])
    
    result = analyzer.analyze_response_patterns(invalid_phone_df)
    assert isinstance(result, dict)
    assert 'error' not in result  # Should handle non-string phone numbers
    
    # Test with non-string message_type
    invalid_type_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 1},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567', 'message_type': 0}
    ])
    
    result = analyzer.analyze_response_patterns(invalid_type_df)
    assert 'error' in result  # Should not handle non-string message types


@pytest.mark.unit
def test_invalid_message_types():
    """Test with invalid message type values."""
    analyzer = ResponseAnalyzer()
    invalid_types_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'outgoing'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567', 'message_type': 'incoming'}
    ])
    
    # Test analyze_response_patterns
    result = analyzer.analyze_response_patterns(invalid_types_df)
    assert 'error' in result
    assert 'invalid message type' in result['error'].lower()
    
    # Test with mixed valid and invalid types
    mixed_types_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567', 'message_type': 'incoming'}
    ])
    
    result = analyzer.analyze_response_patterns(mixed_types_df)
    assert 'error' in result
    assert 'invalid message type' in result['error'].lower()


@pytest.mark.unit
def test_extreme_response_times():
    """Test with extreme response times."""
    analyzer = ResponseAnalyzer()
    
    # Test with very short response time (1 second)
    short_response_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 0, 1), 'phone_number': '5551234567', 'message_type': 'received'}
    ])
    
    result = analyzer.analyze_response_times(short_response_df)
    assert isinstance(result, dict)
    assert 'overall_avg_response_time' in result
    assert result['overall_avg_response_time'] == 1.0  # 1 second
    
    # Test with very long response time (30 days)
    long_response_df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 31, 10, 0), 'phone_number': '5551234567', 'message_type': 'received'}
    ])
    
    result = analyzer.analyze_response_times(long_response_df)
    assert isinstance(result, dict)
    assert 'overall_avg_response_time' in result
    assert result['overall_avg_response_time'] == 30 * 24 * 3600  # 30 days in seconds


@pytest.mark.unit
def test_invalid_contact_for_prediction():
    """Test prediction with invalid contact."""
    analyzer = ResponseAnalyzer()
    df = pd.DataFrame([
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'}
    ])
    
    # Test with empty contact
    result = analyzer.predict_response_behavior(df, '')
    assert 'error' in result
    
    # Test with None contact
    result = analyzer.predict_response_behavior(df, None)
    assert 'error' in result
    
    # Test with contact not in the DataFrame
    result = analyzer.predict_response_behavior(df, '5559876543')
    assert 'error' in result or result['confidence'] < 0.5  # Should have low confidence


@pytest.mark.unit
def test_invalid_column_mapping():
    """Test with invalid column mapping."""
    analyzer = ResponseAnalyzer()
    df = pd.DataFrame([
        {'time': datetime(2023, 1, 1, 10, 0), 'contact': '5551234567', 'direction': 'sent'},
        {'time': datetime(2023, 1, 1, 10, 5), 'contact': '5551234567', 'direction': 'received'}
    ])
    
    # Test with missing mapping
    result = analyzer.analyze_response_patterns(df)
    assert 'error' in result
    
    # Test with incomplete mapping
    incomplete_mapping = {
        'timestamp': 'time',
        'phone_number': 'contact'
        # Missing message_type mapping
    }
    
    result = analyzer.analyze_response_patterns(df, column_mapping=incomplete_mapping)
    assert 'error' in result
    
    # Test with incorrect mapping
    incorrect_mapping = {
        'timestamp': 'time',
        'phone_number': 'contact',
        'message_type': 'wrong_column'  # Column doesn't exist
    }
    
    result = analyzer.analyze_response_patterns(df, column_mapping=incorrect_mapping)
    assert 'error' in result
