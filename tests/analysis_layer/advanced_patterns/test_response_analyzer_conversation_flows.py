"""
Tests for the conversation flow analysis functionality of the ResponseAnalyzer.

This module contains tests for the analyze_conversation_flows method of the ResponseAnalyzer.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer


@pytest.fixture
def simple_conversation_df():
    """Create a simple conversation DataFrame for testing."""
    data = [
        # A simple back-and-forth conversation
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 10), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 15), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # A gap of 3 hours (conversation break)
        
        # Another conversation with the same contact
        {'timestamp': datetime(2023, 1, 1, 13, 30), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 13, 35), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 13, 40), 'phone_number': '5551234567', 'message_type': 'received'},
    ]
    
    return pd.DataFrame(data)


@pytest.fixture
def complex_conversation_df():
    """Create a complex conversation DataFrame with multiple interleaved conversations."""
    data = [
        # Conversation with contact 1
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Interleaved conversation with contact 2
        {'timestamp': datetime(2023, 1, 1, 10, 7), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 9), 'phone_number': '5559876543', 'message_type': 'sent'},
        
        # Back to contact 1
        {'timestamp': datetime(2023, 1, 1, 10, 12), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 15), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Back to contact 2
        {'timestamp': datetime(2023, 1, 1, 10, 20), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 25), 'phone_number': '5559876543', 'message_type': 'sent'},
        
        # A gap of 2 hours (conversation break)
        
        # New conversation with contact 3
        {'timestamp': datetime(2023, 1, 1, 12, 30), 'phone_number': '5552223333', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 12, 35), 'phone_number': '5552223333', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 12, 40), 'phone_number': '5552223333', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 12, 45), 'phone_number': '5552223333', 'message_type': 'sent'},
    ]
    
    return pd.DataFrame(data)


@pytest.fixture
def one_sided_conversation_df():
    """Create a one-sided conversation DataFrame for testing."""
    data = [
        # All sent messages to contact 1
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 30), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        
        # A gap of 2 hours
        
        # All received messages from contact 2
        {'timestamp': datetime(2023, 1, 1, 13, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 13, 30), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'received'},
    ]
    
    return pd.DataFrame(data)


@pytest.mark.unit
def test_detect_conversation_flows_simple(simple_conversation_df):
    """Test conversation flow detection with a simple back-and-forth conversation."""
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_conversation_flows(simple_conversation_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'conversation_count' in result
    assert 'conversation_initiators' in result
    assert 'conversation_terminators' in result
    assert 'avg_conversation_length' in result
    
    # Check specific values
    assert result['conversation_count'] == 2  # Two conversations with a gap
    assert '5551234567' in result['conversation_initiators']
    assert result['conversation_initiators']['5551234567'] == 1  # Initiated one conversation
    assert '5551234567' in result['conversation_terminators']
    assert result['avg_conversation_length'] > 0


@pytest.mark.unit
def test_detect_conversation_flows_complex(complex_conversation_df):
    """Test conversation flow detection with multiple interleaved conversations."""
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_conversation_flows(complex_conversation_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'conversation_count' in result
    assert 'conversation_initiators' in result
    assert 'conversation_terminators' in result
    
    # Check specific values
    assert result['conversation_count'] >= 2  # At least two conversation groups
    
    # Check that all contacts are represented
    all_contacts = ['5551234567', '5559876543', '5552223333']
    for contact in all_contacts:
        assert contact in result['conversation_initiators'] or contact in result['conversation_terminators']


@pytest.mark.unit
def test_detect_conversation_flows_one_sided(one_sided_conversation_df):
    """Test conversation flow detection with one-sided conversations."""
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_conversation_flows(one_sided_conversation_df)
    
    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'conversation_count' in result
    assert 'conversation_initiators' in result
    assert 'conversation_terminators' in result
    
    # Check specific values
    assert result['conversation_count'] >= 2  # At least two conversation groups
    assert '5551234567' in result['conversation_initiators']
    assert '5559876543' in result['conversation_initiators']


@pytest.mark.unit
def test_identify_conversations_timeout():
    """Test conversation timeout functionality."""
    # Create a DataFrame with varying gaps
    data = [
        # First conversation
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Small gap (15 minutes) - should be same conversation
        {'timestamp': datetime(2023, 1, 1, 10, 20), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 25), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Medium gap (45 minutes) - should be same conversation with default timeout
        {'timestamp': datetime(2023, 1, 1, 11, 10), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 11, 15), 'phone_number': '5551234567', 'message_type': 'received'},
        
        # Large gap (2 hours) - should be new conversation
        {'timestamp': datetime(2023, 1, 1, 13, 20), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 13, 25), 'phone_number': '5551234567', 'message_type': 'received'},
    ]
    
    df = pd.DataFrame(data)
    
    # Test with default timeout (60 minutes)
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_conversation_flows(df)
    assert result['conversation_count'] == 2  # Should detect 2 conversations
    
    # Test with custom timeout (30 minutes)
    result = analyzer.analyze_conversation_flows(df, conversation_timeout_minutes=30)
    assert result['conversation_count'] == 3  # Should detect 3 conversations
    
    # Test with very long timeout (180 minutes)
    result = analyzer.analyze_conversation_flows(df, conversation_timeout_minutes=180)
    assert result['conversation_count'] == 1  # Should detect 1 conversation


@pytest.mark.unit
def test_conversation_initiators():
    """Test correct identification of conversation initiators."""
    # Create a DataFrame with clear initiators
    data = [
        # Conversation 1: initiated by contact
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'sent'},
        
        # Gap (2 hours)
        
        # Conversation 2: initiated by user
        {'timestamp': datetime(2023, 1, 1, 12, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 12, 5), 'phone_number': '5559876543', 'message_type': 'received'},
        
        # Gap (2 hours)
        
        # Conversation 3: initiated by contact
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5552223333', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 5), 'phone_number': '5552223333', 'message_type': 'sent'},
    ]
    
    df = pd.DataFrame(data)
    
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_conversation_flows(df)
    
    # Check initiators
    assert '5551234567' in result['conversation_initiators']
    assert result['conversation_initiators']['5551234567'] == 1
    
    assert '5559876543' not in result['conversation_initiators'] or result['conversation_initiators']['5559876543'] == 0
    
    assert '5552223333' in result['conversation_initiators']
    assert result['conversation_initiators']['5552223333'] == 1
    
    # Check user-initiated count
    assert result.get('user_initiated_count', 0) == 1


@pytest.mark.unit
def test_conversation_terminators():
    """Test correct identification of conversation terminators."""
    # Create a DataFrame with clear terminators
    data = [
        # Conversation 1: terminated by user
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'sent'},
        
        # Gap (2 hours)
        
        # Conversation 2: terminated by contact
        {'timestamp': datetime(2023, 1, 1, 12, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 12, 5), 'phone_number': '5559876543', 'message_type': 'received'},
        
        # Gap (2 hours)
        
        # Conversation 3: terminated by user
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5552223333', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 5), 'phone_number': '5552223333', 'message_type': 'sent'},
    ]
    
    df = pd.DataFrame(data)
    
    analyzer = ResponseAnalyzer()
    result = analyzer.analyze_conversation_flows(df)
    
    # Check terminators
    assert '5551234567' not in result['conversation_terminators'] or result['conversation_terminators']['5551234567'] == 0
    
    assert '5559876543' in result['conversation_terminators']
    assert result['conversation_terminators']['5559876543'] == 1
    
    assert '5552223333' not in result['conversation_terminators'] or result['conversation_terminators']['5552223333'] == 0
    
    # Check user-terminated count
    assert result.get('user_terminated_count', 0) == 2


@pytest.mark.unit
def test_column_mapping_conversation_flows():
    """Test that column mapping works correctly for conversation flow analysis."""
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
    result = analyzer.analyze_conversation_flows(df, column_mapping=column_mapping)
    
    # Check that the analysis works with the mapping
    assert isinstance(result, dict)
    assert 'conversation_count' in result
    assert 'conversation_initiators' in result
    assert 'conversation_terminators' in result
    assert 'avg_conversation_length' in result
    
    # Check specific values
    assert result['conversation_count'] == 1
    assert '5551234567' in result['conversation_initiators'] or '5551234567' in result['conversation_terminators']


@pytest.mark.unit
def test_error_handling_conversation_flows():
    """Test error handling in conversation flow analysis."""
    analyzer = ResponseAnalyzer()
    
    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = analyzer.analyze_conversation_flows(empty_df)
    assert isinstance(result, dict)
    assert len(result) == 0
    assert analyzer.last_error is not None
    
    # Test with missing columns
    df_missing_column = pd.DataFrame({
        'timestamp': [datetime(2023, 1, 1, 10, 0)],
        'phone_number': ['5551234567']
    })
    
    result = analyzer.analyze_conversation_flows(df_missing_column)
    assert isinstance(result, dict)
    assert len(result) == 0
    assert analyzer.last_error is not None
