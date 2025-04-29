"""
Tests for the reciprocity pattern detection functionality of the ResponseAnalyzer.

This module contains tests for the detect_reciprocity_patterns method of the ResponseAnalyzer.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer


@pytest.fixture
def balanced_communication_df():
    """Create a DataFrame with balanced communication patterns."""
    data = [
        # Contact 1: Balanced (1:1 ratio)
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 10), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 15), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 20), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 25), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Contact 2: Also balanced (1:1 ratio)
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 5), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 14, 10), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 15), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 14, 20), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 25), 'phone_number': '5559876543', 'message_type': 'sent'},
    ]
    
    return pd.DataFrame(data)


@pytest.fixture
def unbalanced_communication_df():
    """Create a DataFrame with unbalanced communication patterns."""
    data = [
        # Contact 1: User sends more (3:1 ratio)
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 10), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 15), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 20), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 25), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 30), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 35), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Contact 2: User receives more (1:3 ratio)
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 5), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 10), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 15), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 14, 20), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 25), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 30), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 35), 'phone_number': '5559876543', 'message_type': 'sent'},
    ]
    
    return pd.DataFrame(data)


@pytest.fixture
def mixed_communication_df():
    """Create a DataFrame with mixed communication patterns."""
    data = [
        # Contact 1: Balanced (1:1 ratio)
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 10), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 15), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Contact 2: User sends more (2:1 ratio)
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 14, 5), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 14, 10), 'phone_number': '5559876543', 'message_type': 'received'},
        
        # Contact 3: User receives more (1:2 ratio)
        {'timestamp': datetime(2023, 1, 2, 9, 0), 'phone_number': '5552223333', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 2, 9, 5), 'phone_number': '5552223333', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 2, 9, 10), 'phone_number': '5552223333', 'message_type': 'sent'},
    ]
    
    return pd.DataFrame(data)


@pytest.fixture
def initiation_pattern_df():
    """Create a DataFrame with clear conversation initiation patterns."""
    data = [
        # Conversation 1: Contact 1 initiates
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 10), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 15), 'phone_number': '5551234567', 'message_type': 'sent'},
        
        # Gap (2 hours)
        
        # Conversation 2: Contact 1 initiates again
        {'timestamp': datetime(2023, 1, 1, 12, 0), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 12, 5), 'phone_number': '5551234567', 'message_type': 'sent'},
        
        # Gap (2 hours)
        
        # Conversation 3: User initiates with Contact 2
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 14, 5), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 10), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 14, 15), 'phone_number': '5559876543', 'message_type': 'received'},
        
        # Gap (2 hours)
        
        # Conversation 4: User initiates with Contact 2 again
        {'timestamp': datetime(2023, 1, 1, 16, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 16, 5), 'phone_number': '5559876543', 'message_type': 'received'},
    ]
    
    return pd.DataFrame(data)


@pytest.fixture
def reciprocity_over_time_df():
    """Create a DataFrame with changing reciprocity patterns over time."""
    data = []
    
    # Month 1: Balanced communication (1:1)
    for day in range(1, 11):  # 10 days
        data.extend([
            {'timestamp': datetime(2023, 1, day, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, day, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        ])
    
    # Month 2: User sends more (2:1)
    for day in range(1, 11):  # 10 days
        data.extend([
            {'timestamp': datetime(2023, 2, day, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 2, day, 10, 5), 'phone_number': '5551234567', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 2, day, 10, 10), 'phone_number': '5551234567', 'message_type': 'received'},
        ])
    
    # Month 3: User receives more (1:2)
    for day in range(1, 11):  # 10 days
        data.extend([
            {'timestamp': datetime(2023, 3, day, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 3, day, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
            {'timestamp': datetime(2023, 3, day, 10, 10), 'phone_number': '5551234567', 'message_type': 'received'},
        ])
    
    return pd.DataFrame(data)


@pytest.mark.unit
def test_detect_reciprocity_patterns_balanced(balanced_communication_df):
    """Test reciprocity pattern detection with balanced communication."""
    analyzer = ResponseAnalyzer()
    result = analyzer.detect_reciprocity_patterns(balanced_communication_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'message_ratios' in result
    assert 'balanced_contacts' in result
    assert 'unbalanced_contacts' in result
    
    # Check specific values
    assert '5551234567' in result['message_ratios']
    assert '5559876543' in result['message_ratios']
    
    # Check that both contacts are balanced
    assert '5551234567' in result['balanced_contacts']
    assert '5559876543' in result['balanced_contacts']
    assert len(result['unbalanced_contacts']) == 0
    
    # Check that ratios are close to 1.0
    assert 0.8 <= result['message_ratios']['5551234567'] <= 1.2
    assert 0.8 <= result['message_ratios']['5559876543'] <= 1.2


@pytest.mark.unit
def test_detect_reciprocity_patterns_unbalanced(unbalanced_communication_df):
    """Test reciprocity pattern detection with unbalanced communication."""
    analyzer = ResponseAnalyzer()
    result = analyzer.detect_reciprocity_patterns(unbalanced_communication_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'message_ratios' in result
    assert 'balanced_contacts' in result
    assert 'unbalanced_contacts' in result
    
    # Check specific values
    assert '5551234567' in result['message_ratios']
    assert '5559876543' in result['message_ratios']
    
    # Check that both contacts are unbalanced
    assert '5551234567' in result['unbalanced_contacts']
    assert '5559876543' in result['unbalanced_contacts']
    assert len(result['balanced_contacts']) == 0
    
    # Check that ratios reflect the expected imbalance
    assert result['message_ratios']['5551234567'] > 2.0  # User sends more
    assert result['message_ratios']['5559876543'] < 0.5  # User receives more


@pytest.mark.unit
def test_message_ratio_calculation(mixed_communication_df):
    """Test message ratio calculation."""
    analyzer = ResponseAnalyzer()
    result = analyzer.detect_reciprocity_patterns(mixed_communication_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'message_ratios' in result
    
    # Check specific values
    assert '5551234567' in result['message_ratios']
    assert '5559876543' in result['message_ratios']
    assert '5552223333' in result['message_ratios']
    
    # Check that ratios match expected values
    assert 0.8 <= result['message_ratios']['5551234567'] <= 1.2  # Balanced (1:1)
    assert 1.8 <= result['message_ratios']['5559876543'] <= 2.2  # User sends more (2:1)
    assert 0.4 <= result['message_ratios']['5552223333'] <= 0.6  # User receives more (1:2)
    
    # Check classification
    assert '5551234567' in result['balanced_contacts']
    assert '5559876543' in result['unbalanced_contacts']
    assert '5552223333' in result['unbalanced_contacts']


@pytest.mark.unit
def test_initiation_pattern_detection(initiation_pattern_df):
    """Test detection of conversation initiation patterns."""
    analyzer = ResponseAnalyzer()
    result = analyzer.detect_reciprocity_patterns(initiation_pattern_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'initiation_patterns' in result
    
    # Check initiation patterns
    initiation = result['initiation_patterns']
    assert 'contact_initiated' in initiation
    assert 'user_initiated' in initiation
    
    # Check specific values
    assert '5551234567' in initiation['contact_initiated']
    assert initiation['contact_initiated']['5551234567'] == 2
    
    assert '5559876543' in initiation['user_initiated']
    assert initiation['user_initiated']['5559876543'] == 2
    
    # Check overall stats
    assert 'total_conversations' in initiation
    assert 'contact_initiated_percent' in initiation
    assert 'user_initiated_percent' in initiation
    
    assert initiation['total_conversations'] == 4
    assert initiation['contact_initiated_percent'] == 50.0
    assert initiation['user_initiated_percent'] == 50.0


@pytest.mark.unit
def test_reciprocity_over_time(reciprocity_over_time_df):
    """Test detection of changes in reciprocity over time."""
    analyzer = ResponseAnalyzer()
    result = analyzer.detect_reciprocity_patterns(reciprocity_over_time_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'reciprocity_over_time' in result
    
    # Check time-based analysis
    time_analysis = result['reciprocity_over_time']
    assert '5551234567' in time_analysis
    
    # Check that we have data for each month
    contact_data = time_analysis['5551234567']
    assert len(contact_data) == 3
    
    # Check that the trend shows the expected pattern
    # Month 1: Balanced (ratio ≈ 1.0)
    # Month 2: User sends more (ratio > 1.0)
    # Month 3: User receives more (ratio < 1.0)
    assert 0.8 <= contact_data[0]['ratio'] <= 1.2
    assert contact_data[1]['ratio'] > 1.5
    assert contact_data[2]['ratio'] < 0.7
    
    # Check that we detect the trend
    assert 'trend_detected' in result
    assert result['trend_detected'] is True


@pytest.mark.unit
def test_column_mapping_reciprocity():
    """Test that column mapping works correctly for reciprocity pattern detection."""
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
    result = analyzer.detect_reciprocity_patterns(df, column_mapping=column_mapping)
    
    # Check that the analysis works with the mapping
    assert isinstance(result, dict)
    assert 'message_ratios' in result
    assert 'balanced_contacts' in result
    assert '5551234567' in result['message_ratios']
    assert '5551234567' in result['balanced_contacts']


@pytest.mark.unit
def test_error_handling_reciprocity():
    """Test error handling in reciprocity pattern detection."""
    analyzer = ResponseAnalyzer()
    
    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = analyzer.detect_reciprocity_patterns(empty_df)
    assert isinstance(result, dict)
    assert len(result) == 0
    assert analyzer.last_error is not None
    
    # Test with missing columns
    df_missing_column = pd.DataFrame({
        'timestamp': [datetime(2023, 1, 1, 10, 0)],
        'phone_number': ['5551234567']
    })
    
    result = analyzer.detect_reciprocity_patterns(df_missing_column)
    assert isinstance(result, dict)
    assert len(result) == 0
    assert analyzer.last_error is not None
