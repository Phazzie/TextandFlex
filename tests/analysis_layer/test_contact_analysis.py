"""
Tests for the contact analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

@pytest.fixture
def sample_contact_dataframe():
    """Create a sample DataFrame for contact analysis testing."""
    return pd.DataFrame({
        'timestamp': pd.to_datetime([
            '2023-01-01 08:00:00',  # Morning
            '2023-01-01 12:30:00',  # Afternoon
            '2023-01-01 20:00:00',  # Evening
            '2023-01-02 09:00:00',  # Morning
            '2023-01-02 13:00:00',  # Afternoon
            '2023-01-02 22:00:00',  # Evening
            '2023-01-03 07:00:00',  # Morning
            '2023-01-03 14:00:00',  # Afternoon
            '2023-01-03 21:00:00',  # Evening
            '2023-01-04 10:00:00',  # Morning
        ]),
        'phone_number': [
            '1234567890',  # Contact A - frequent
            '9876543210',  # Contact B - medium
            '5551234567',  # Contact C - infrequent
            '1234567890',  # Contact A
            '1234567890',  # Contact A
            '9876543210',  # Contact B
            '1234567890',  # Contact A
            '1234567890',  # Contact A
            '9876543210',  # Contact B
            '5551234567',  # Contact C
        ],
        'message_type': [
            'sent',
            'received',
            'sent',
            'received',
            'sent',
            'received',
            'sent',
            'received',
            'sent',
            'received',
        ],
        'message_content': [
            'Good morning!',
            'Hello there',
            'Good evening',
            'How are you today?',
            'I am fine, thanks!',
            'What are you doing?',
            'Just woke up',
            'Want to meet later?',
            'Sorry, busy tonight',
            'No problem, another time',
        ],
        'duration': [
            0,  # Text message
            0,  # Text message
            0,  # Text message
            120,  # 2-minute call
            180,  # 3-minute call
            240,  # 4-minute call
            0,  # Text message
            300,  # 5-minute call
            0,  # Text message
            600,  # 10-minute call
        ]
    })

@pytest.fixture
def sample_column_mapping():
    """Create a sample column mapping for testing."""
    return {
        'timestamp': 'timestamp',
        'phone_number': 'phone_number',
        'message_type': 'message_type',
        'message_content': 'message_content',
        'duration': 'duration'
    }

@pytest.mark.unit
def test_contact_analyzer_creation():
    """Test creating a ContactAnalyzer."""
    from src.analysis_layer.contact_analysis import ContactAnalyzer
    
    analyzer = ContactAnalyzer()
    assert analyzer is not None

@pytest.mark.unit
def test_analyze_contact_frequency(sample_contact_dataframe, sample_column_mapping):
    """Test analyzing contact frequency."""
    from src.analysis_layer.contact_analysis import ContactAnalyzer
    
    analyzer = ContactAnalyzer()
    
    result = analyzer.analyze_contact_frequency(sample_contact_dataframe)
    
    assert isinstance(result, dict)
    assert '1234567890' in result
    assert '9876543210' in result
    assert '5551234567' in result
    
    # Contact A should have the highest frequency
    assert result['1234567890'] > result['9876543210']
    assert result['9876543210'] > result['5551234567']

@pytest.mark.unit
def test_categorize_contacts(sample_contact_dataframe, sample_column_mapping):
    """Test categorizing contacts."""
    from src.analysis_layer.contact_analysis import ContactAnalyzer
    
    analyzer = ContactAnalyzer()
    
    result = analyzer.categorize_contacts(sample_contact_dataframe)
    
    assert isinstance(result, dict)
    assert 'frequent' in result
    assert 'moderate' in result
    assert 'infrequent' in result
    
    # Contact A should be frequent
    assert '1234567890' in result['frequent']
    # Contact B should be moderate
    assert '9876543210' in result['moderate']
    # Contact C should be infrequent
    assert '5551234567' in result['infrequent']

@pytest.mark.unit
def test_analyze_contact_relationships(sample_contact_dataframe, sample_column_mapping):
    """Test analyzing contact relationships."""
    from src.analysis_layer.contact_analysis import ContactAnalyzer
    
    analyzer = ContactAnalyzer()
    
    result = analyzer.analyze_contact_relationships(sample_contact_dataframe)
    
    assert isinstance(result, dict)
    assert '1234567890' in result
    assert '9876543210' in result
    assert '5551234567' in result
    
    # Check relationship metrics
    for contact_id, metrics in result.items():
        assert 'interaction_count' in metrics
        assert 'last_interaction' in metrics
        assert 'first_interaction' in metrics
        assert 'avg_response_time' in metrics
        assert 'relationship_score' in metrics

@pytest.mark.unit
def test_detect_contact_patterns(sample_contact_dataframe, sample_column_mapping):
    """Test detecting contact patterns."""
    from src.analysis_layer.contact_analysis import ContactAnalyzer
    
    analyzer = ContactAnalyzer()
    
    result = analyzer.detect_contact_patterns(sample_contact_dataframe)
    
    assert isinstance(result, dict)
    assert '1234567890' in result
    assert '9876543210' in result
    assert '5551234567' in result
    
    # Check pattern metrics
    for contact_id, patterns in result.items():
        assert 'time_patterns' in patterns
        assert 'content_patterns' in patterns
        assert 'response_patterns' in patterns

@pytest.mark.unit
def test_analyze_conversation_flow(sample_contact_dataframe, sample_column_mapping):
    """Test analyzing conversation flow."""
    from src.analysis_layer.contact_analysis import ContactAnalyzer
    
    analyzer = ContactAnalyzer()
    
    result = analyzer.analyze_conversation_flow(sample_contact_dataframe)
    
    assert isinstance(result, dict)
    assert 'conversation_count' in result
    assert 'avg_conversation_length' in result
    assert 'avg_messages_per_conversation' in result
    assert 'conversation_initiators' in result
    assert 'conversation_closers' in result

@pytest.mark.unit
def test_analyze_contact_importance(sample_contact_dataframe, sample_column_mapping):
    """Test analyzing contact importance."""
    from src.analysis_layer.contact_analysis import ContactAnalyzer
    
    analyzer = ContactAnalyzer()
    
    result = analyzer.analyze_contact_importance(sample_contact_dataframe)
    
    assert isinstance(result, list)
    assert len(result) == 3  # Three contacts
    
    # Contacts should be ordered by importance score
    assert result[0]['phone_number'] == '1234567890'  # Most important
    assert result[1]['phone_number'] == '9876543210'  # Second most important
    assert result[2]['phone_number'] == '5551234567'  # Least important
    
    # Check importance metrics
    for contact in result:
        assert 'phone_number' in contact
        assert 'importance_score' in contact
        assert 'interaction_count' in contact
        assert 'response_rate' in contact
        assert 'avg_response_time' in contact
