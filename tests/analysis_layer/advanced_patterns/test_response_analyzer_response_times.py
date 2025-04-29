"""
Tests for the response time analysis functionality of the ResponseAnalyzer.

This module contains tests for the analyze_response_times method of the ResponseAnalyzer.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer


@pytest.fixture
def quick_response_df():
    """Create a DataFrame with quick response patterns."""
    data = [
        # Contact 1: Quick responses (< 5 minutes)
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 3), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 10), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 12), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Contact 2: Also quick responses
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 14, 4), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 10), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 14, 13), 'phone_number': '5559876543', 'message_type': 'received'},
    ]
    
    return pd.DataFrame(data)


@pytest.fixture
def delayed_response_df():
    """Create a DataFrame with delayed response patterns."""
    data = [
        # Contact 1: Delayed responses (> 1 hour)
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 11, 30), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 12, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Contact 2: Also delayed responses
        {'timestamp': datetime(2023, 1, 1, 15, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 17, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 18, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 20, 0), 'phone_number': '5559876543', 'message_type': 'received'},
    ]
    
    return pd.DataFrame(data)


@pytest.fixture
def mixed_response_df():
    """Create a DataFrame with mixed response patterns."""
    data = [
        # Contact 1: Quick responses
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 10), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 15), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Contact 2: Delayed responses
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 16, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 16, 30), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 18, 30), 'phone_number': '5559876543', 'message_type': 'received'},
        
        # Contact 3: Mixed response times
        {'timestamp': datetime(2023, 1, 2, 9, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 2, 9, 45), 'phone_number': '5552223333', 'message_type': 'received'},  # 45 min
        {'timestamp': datetime(2023, 1, 2, 10, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 2, 10, 3), 'phone_number': '5552223333', 'message_type': 'received'},  # 3 min
    ]
    
    return pd.DataFrame(data)


@pytest.fixture
def time_of_day_df():
    """Create a DataFrame with time-of-day response patterns."""
    data = []
    
    # Morning responses (fast)
    for day in range(1, 6):  # 5 days
        data.extend([
            {'timestamp': datetime(2023, 1, day, 8, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, day, 8, 5), 'phone_number': '5551234567', 'message_type': 'received'},
            {'timestamp': datetime(2023, 1, day, 8, 30), 'phone_number': '5551234567', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, day, 8, 33), 'phone_number': '5551234567', 'message_type': 'received'},
        ])
    
    # Afternoon responses (medium)
    for day in range(1, 6):  # 5 days
        data.extend([
            {'timestamp': datetime(2023, 1, day, 14, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, day, 14, 15), 'phone_number': '5559876543', 'message_type': 'received'},
            {'timestamp': datetime(2023, 1, day, 14, 30), 'phone_number': '5559876543', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, day, 14, 50), 'phone_number': '5559876543', 'message_type': 'received'},
        ])
    
    # Evening responses (slow)
    for day in range(1, 6):  # 5 days
        data.extend([
            {'timestamp': datetime(2023, 1, day, 20, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, day, 20, 45), 'phone_number': '5552223333', 'message_type': 'received'},
            {'timestamp': datetime(2023, 1, day, 21, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, day, 21, 40), 'phone_number': '5552223333', 'message_type': 'received'},
        ])
    
    return pd.DataFrame(data)


@pytest.mark.unit
def test_analyze_response_times_quick(quick_response_df):
    """Test response time analysis with quick response patterns."""
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_response_times(quick_response_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'overall_avg_response_time' in result
    assert 'response_time_by_contact' in result
    assert 'response_time_by_hour' in result
    assert 'response_time_by_day' in result
    assert 'quick_responses' in result
    
    # Check specific values
    assert result['overall_avg_response_time'] < 300  # Less than 5 minutes
    assert '5551234567' in result['response_time_by_contact']
    assert '5559876543' in result['response_time_by_contact']
    
    # Check quick responses
    assert 'contacts' in result['quick_responses']
    assert len(result['quick_responses']['contacts']) >= 2
    assert '5551234567' in result['quick_responses']['contacts']
    assert '5559876543' in result['quick_responses']['contacts']


@pytest.mark.unit
def test_analyze_response_times_delayed(delayed_response_df):
    """Test response time analysis with delayed response patterns."""
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_response_times(delayed_response_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'overall_avg_response_time' in result
    assert 'response_time_by_contact' in result
    assert 'delayed_responses' in result
    
    # Check specific values
    assert result['overall_avg_response_time'] > 3600  # More than 1 hour
    assert '5551234567' in result['response_time_by_contact']
    assert '5559876543' in result['response_time_by_contact']
    
    # Check delayed responses
    assert 'contacts' in result['delayed_responses']
    assert len(result['delayed_responses']['contacts']) >= 2
    assert '5551234567' in result['delayed_responses']['contacts']
    assert '5559876543' in result['delayed_responses']['contacts']


@pytest.mark.unit
def test_analyze_response_times_mixed(mixed_response_df):
    """Test response time analysis with mixed response patterns."""
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_response_times(mixed_response_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'overall_avg_response_time' in result
    assert 'response_time_by_contact' in result
    
    # Check specific values
    assert '5551234567' in result['response_time_by_contact']
    assert '5559876543' in result['response_time_by_contact']
    assert '5552223333' in result['response_time_by_contact']
    
    # Check that contact 1 has faster responses than contact 2
    assert result['response_time_by_contact']['5551234567'] < result['response_time_by_contact']['5559876543']
    
    # Check quick and delayed responses
    if 'quick_responses' in result and 'contacts' in result['quick_responses']:
        assert '5551234567' in result['quick_responses']['contacts']
    
    if 'delayed_responses' in result and 'contacts' in result['delayed_responses']:
        assert '5559876543' in result['delayed_responses']['contacts']


@pytest.mark.unit
def test_response_time_distribution(mixed_response_df):
    """Test response time distribution calculation."""
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_response_times(mixed_response_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'response_time_distribution' in result
    
    # Check distribution structure
    distribution = result['response_time_distribution']
    assert 'bins' in distribution
    assert 'counts' in distribution
    assert 'percentiles' in distribution
    
    # Check that bins and counts have the same length
    assert len(distribution['bins']) == len(distribution['counts']) + 1
    
    # Check that percentiles include common values
    percentiles = distribution['percentiles']
    assert 50 in percentiles  # Median
    assert 90 in percentiles  # 90th percentile


@pytest.mark.unit
def test_time_of_day_effects(time_of_day_df):
    """Test detection of time-of-day effects on responses."""
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_response_times(time_of_day_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'response_time_by_hour' in result
    assert 'time_of_day_effects' in result
    
    # Check time of day effects
    time_effects = result['time_of_day_effects']
    assert 'morning' in time_effects
    assert 'afternoon' in time_effects
    assert 'evening' in time_effects
    
    # Morning should be faster than evening
    assert time_effects['morning']['avg_response_time'] < time_effects['evening']['avg_response_time']
    
    # Check best response time hour
    assert 'best_hour' in result
    assert isinstance(result['best_hour'], int)
    assert 8 <= result['best_hour'] <= 9  # Should be morning hour


@pytest.mark.unit
def test_response_time_anomalies(mixed_response_df):
    """Test detection of unusual response times."""
    # Add some anomalous response times
    anomalous_data = [
        # Very quick response (10 seconds)
        {'timestamp': datetime(2023, 1, 3, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 3, 10, 0, 10), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Very delayed response (12 hours)
        {'timestamp': datetime(2023, 1, 3, 14, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 4, 2, 0), 'phone_number': '5559876543', 'message_type': 'received'},
    ]
    
    df = pd.concat([mixed_response_df, pd.DataFrame(anomalous_data)], ignore_index=True)
    
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_response_times(df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'anomalies' in result
    
    # Check anomalies
    anomalies = result['anomalies']
    assert len(anomalies) >= 2
    
    # Check that we have both quick and delayed anomalies
    anomaly_types = [a['type'] for a in anomalies]
    assert 'unusually_quick' in anomaly_types
    assert 'unusually_delayed' in anomaly_types


@pytest.mark.unit
def test_column_mapping_response_times():
    """Test that column mapping works correctly for response time analysis."""
    # Create a DataFrame with renamed columns
    data = [
        {'time': datetime(2023, 1, 1, 10, 0), 'contact': '5551234567', 'direction': 'sent'},
        {'time': datetime(2023, 1, 1, 10, 5), 'contact': '5551234567', 'direction': 'received'},
        {'time': datetime(2023, 1, 1, 10, 10), 'contact': '5551234567', 'direction': 'sent'},
        {'time': datetime(2023, 1, 1, 10, 15), 'contact': '5551234567', 'direction': 'received'},
    ]
    
    df = pd.DataFrame(data)
    
    # Create column mapping
    column_mapping = {
        'timestamp': 'time',
        'phone_number': 'contact',
        'message_type': 'direction'
    }
    
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_response_times(df, column_mapping=column_mapping)
    
    # Check that the analysis works with the mapping
    assert isinstance(result, dict)
    assert 'overall_avg_response_time' in result
    assert 'response_time_by_contact' in result
    assert '5551234567' in result['response_time_by_contact']


@pytest.mark.unit
def test_error_handling_response_times():
    """Test error handling in response time analysis."""
    analyzer = ResponseAnalyzer()
    
    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = analyzer.analyze_response_times(empty_df)
    assert isinstance(result, dict)
    assert len(result) == 0
    assert analyzer.last_error is not None
    
    # Test with missing columns
    df_missing_column = pd.DataFrame({
        'timestamp': [datetime(2023, 1, 1, 10, 0)],
        'phone_number': ['5551234567']
    })
    
    result = analyzer.analyze_response_times(df_missing_column)
    assert isinstance(result, dict)
    assert len(result) == 0
    assert analyzer.last_error is not None
    
    # Test with invalid data types
    df_invalid_type = pd.DataFrame({
        'timestamp': ['not a datetime'],
        'phone_number': ['5551234567'],
        'message_type': ['sent']
    })
    
    result = analyzer.analyze_response_times(df_invalid_type)
    assert isinstance(result, dict)
    assert len(result) == 0
    assert analyzer.last_error is not None
