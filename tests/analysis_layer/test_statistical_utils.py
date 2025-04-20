"""
Tests for the statistical utilities module.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-15', '2023-01-31', '2023-02-15', '2023-02-28']),
        'number': ['1234567890', '1234567890', '9876543210', '5551234567', '9876543210'],
        'message_type': ['sent', 'received', 'sent', 'received', 'sent'],
        'message_content': ['Hello', 'Hi there', 'How are you?', 'Good, thanks!', 'Bye'],
        'duration': [10, 15, 5, 20, 8]
    })

@pytest.fixture
def sample_column_mapping():
    """Create a sample column mapping for testing."""
    return {
        'date': 'date',
        'number': 'number',
        'type': 'message_type',
        'content': 'message_content',
        'duration': 'duration'
    }

@pytest.mark.unit
def test_calculate_time_distribution(sample_dataframe):
    """Test calculating time distribution."""
    from src.analysis_layer.statistical_utils import calculate_time_distribution

    # Test hourly distribution
    hourly_dist = calculate_time_distribution(sample_dataframe, 'date', 'hour')
    assert isinstance(hourly_dist, dict)
    assert len(hourly_dist) <= 24  # At most 24 hours

    # Test daily distribution
    daily_dist = calculate_time_distribution(sample_dataframe, 'date', 'day')
    assert isinstance(daily_dist, dict)
    assert len(daily_dist) <= 7  # At most 7 days of the week

    # Test monthly distribution
    monthly_dist = calculate_time_distribution(sample_dataframe, 'date', 'month')
    assert isinstance(monthly_dist, dict)
    assert len(monthly_dist) <= 12  # At most 12 months

    # Test with invalid period
    with pytest.raises(ValueError):
        calculate_time_distribution(sample_dataframe, 'date', 'invalid_period')

@pytest.mark.unit
def test_calculate_message_frequency(sample_dataframe):
    """Test calculating message frequency."""
    from src.analysis_layer.statistical_utils import calculate_message_frequency

    # Test daily frequency
    daily_freq = calculate_message_frequency(sample_dataframe, 'date', 'day')
    assert isinstance(daily_freq, float)
    assert daily_freq > 0

    # Test weekly frequency
    weekly_freq = calculate_message_frequency(sample_dataframe, 'date', 'week')
    assert isinstance(weekly_freq, float)
    assert weekly_freq > 0

    # Test monthly frequency
    monthly_freq = calculate_message_frequency(sample_dataframe, 'date', 'month')
    assert isinstance(monthly_freq, float)
    assert monthly_freq > 0

    # Test with invalid period
    with pytest.raises(ValueError):
        calculate_message_frequency(sample_dataframe, 'date', 'invalid_period')

@pytest.mark.unit
def test_calculate_response_times(sample_dataframe):
    """Test calculating response times."""
    from src.analysis_layer.statistical_utils import calculate_response_times

    # Create a DataFrame with conversation flow
    conversation_df = pd.DataFrame({
        'date': pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:05:00',
            '2023-01-01 10:15:00',
            '2023-01-01 10:30:00',
            '2023-01-01 11:00:00'
        ]),
        'number': ['1234567890', '1234567890', '1234567890', '1234567890', '1234567890'],
        'message_type': ['sent', 'received', 'sent', 'received', 'sent']
    })

    response_times = calculate_response_times(conversation_df, 'date', 'message_type', 'number')

    assert isinstance(response_times, dict)
    assert 'average_response_time' in response_times
    assert 'median_response_time' in response_times
    assert 'max_response_time' in response_times
    assert 'min_response_time' in response_times

@pytest.mark.unit
def test_calculate_conversation_gaps(sample_dataframe):
    """Test calculating conversation gaps."""
    from src.analysis_layer.statistical_utils import calculate_conversation_gaps

    # Create a DataFrame with conversation gaps
    conversation_df = pd.DataFrame({
        'date': pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 10:05:00',
            '2023-01-02 10:00:00',  # 1 day gap
            '2023-01-02 10:05:00',
            '2023-01-05 10:00:00'   # 3 day gap
        ]),
        'number': ['1234567890', '1234567890', '1234567890', '1234567890', '1234567890'],
        'message_type': ['sent', 'received', 'sent', 'received', 'sent']
    })

    gaps = calculate_conversation_gaps(conversation_df, 'date', gap_threshold=12*3600)

    assert isinstance(gaps, dict)
    assert 'gap_indices' in gaps
    assert 'gap_durations' in gaps
    assert len(gaps['gap_indices']) == 2  # Two gaps > 12 hours

@pytest.mark.unit
def test_calculate_contact_activity_periods(sample_dataframe):
    """Test calculating contact activity periods."""
    from src.analysis_layer.statistical_utils import calculate_contact_activity_periods

    # Create a DataFrame with contact activity
    activity_df = pd.DataFrame({
        'date': pd.to_datetime([
            '2023-01-01 10:00:00',
            '2023-01-01 22:00:00',
            '2023-01-02 08:00:00',
            '2023-01-02 23:00:00',
            '2023-01-03 09:00:00'
        ]),
        'number': ['1234567890', '1234567890', '1234567890', '1234567890', '1234567890'],
        'message_type': ['sent', 'received', 'sent', 'received', 'sent']
    })

    activity_periods = calculate_contact_activity_periods(activity_df, 'date', 'number')

    assert isinstance(activity_periods, dict)
    assert '1234567890' in activity_periods

@pytest.mark.unit
def test_calculate_word_frequency(sample_dataframe):
    """Test calculating word frequency."""
    from src.analysis_layer.statistical_utils import calculate_word_frequency

    word_freq = calculate_word_frequency(sample_dataframe, 'message_content')

    assert isinstance(word_freq, dict)
    assert len(word_freq) > 0

@pytest.mark.unit
def test_get_cached_result():
    """Test getting a cached result."""
    from src.analysis_layer.statistical_utils import get_cached_result, cache_result

    # Cache a result
    cache_key = "test_key"
    test_value = {"result": "test_value"}
    cache_result(cache_key, test_value)

    # Get the cached result
    result = get_cached_result(cache_key)
    assert result == test_value

    # Get a non-existent cached result
    result = get_cached_result("non_existent_key")
    assert result is None
