"""
Tests for the pattern detector module.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

@pytest.fixture
def sample_pattern_dataframe():
    """Create a sample DataFrame for pattern detection testing."""
    # Create a DataFrame with clear patterns
    dates = []
    numbers = []
    types = []
    contents = []
    durations = []
    
    # Pattern 1: Weekly check-in calls every Monday at 9 AM
    start_date = datetime(2023, 1, 2)  # First Monday
    for i in range(4):  # 4 weeks
        call_time = start_date + timedelta(days=i*7, hours=9)
        dates.append(call_time)
        numbers.append('1234567890')
        types.append('sent')
        contents.append('Weekly check-in')
        durations.append(300)  # 5-minute call
    
    # Pattern 2: Daily good morning texts around 7 AM
    start_date = datetime(2023, 1, 1)
    for i in range(30):  # 30 days
        text_time = start_date + timedelta(days=i, hours=7, minutes=np.random.randint(-15, 15))
        dates.append(text_time)
        numbers.append('9876543210')
        types.append('sent')
        contents.append('Good morning!')
        durations.append(0)  # Text message
    
    # Pattern 3: Friday night calls around 8 PM
    start_date = datetime(2023, 1, 6)  # First Friday
    for i in range(4):  # 4 weeks
        call_time = start_date + timedelta(days=i*7, hours=20, minutes=np.random.randint(-30, 30))
        dates.append(call_time)
        numbers.append('5551234567')
        types.append('received')
        contents.append('Friday night call')
        durations.append(np.random.randint(1800, 3600))  # 30-60 minute call
    
    # Pattern 4: Content pattern - "Meeting" texts followed by calls
    start_date = datetime(2023, 1, 5)  # First Thursday
    for i in range(4):  # 4 weeks
        # Text about meeting
        text_time = start_date + timedelta(days=i*7, hours=10)
        dates.append(text_time)
        numbers.append('3334445555')
        types.append('sent')
        contents.append('Meeting at 2pm today')
        durations.append(0)  # Text message
        
        # Call after meeting
        call_time = start_date + timedelta(days=i*7, hours=15)  # 3 PM
        dates.append(call_time)
        numbers.append('3334445555')
        types.append('sent')
        contents.append('Call after meeting')
        durations.append(np.random.randint(300, 600))  # 5-10 minute call
    
    # Add some random noise
    start_date = datetime(2023, 1, 1)
    for i in range(20):
        random_time = start_date + timedelta(
            days=np.random.randint(0, 30),
            hours=np.random.randint(8, 22),
            minutes=np.random.randint(0, 60)
        )
        dates.append(random_time)
        numbers.append(np.random.choice(['1234567890', '9876543210', '5551234567', '3334445555', '7778889999']))
        types.append(np.random.choice(['sent', 'received']))
        contents.append(np.random.choice(['Hello', 'Hi', 'How are you?', 'Call me', 'Text me later']))
        durations.append(np.random.randint(0, 300))
    
    return pd.DataFrame({
        'timestamp': pd.Series(dates),
        'phone_number': numbers,
        'message_type': types,
        'message_content': contents,
        'duration': durations
    }).sort_values('timestamp').reset_index(drop=True)

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
def test_pattern_detector_creation():
    """Test creating a PatternDetector."""
    from src.analysis_layer.pattern_detector import PatternDetector
    
    detector = PatternDetector()
    assert detector is not None

@pytest.mark.unit
def test_detect_time_patterns(sample_pattern_dataframe, sample_column_mapping):
    """Test detecting time patterns."""
    from src.analysis_layer.pattern_detector import PatternDetector
    
    detector = PatternDetector()
    
    result = detector.detect_time_patterns(sample_pattern_dataframe)
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Check pattern structure
    pattern = result[0]
    assert 'pattern_type' in pattern
    assert 'description' in pattern
    assert 'confidence' in pattern
    assert 'occurrences' in pattern
    assert 'examples' in pattern
    
    # Check for specific patterns
    pattern_descriptions = [p['description'] for p in result]
    
    # Should detect Monday morning pattern
    assert any('Monday' in desc and 'morning' in desc.lower() for desc in pattern_descriptions)
    
    # Should detect daily morning pattern
    assert any('daily' in desc.lower() and 'morning' in desc.lower() for desc in pattern_descriptions)
    
    # Should detect Friday evening pattern
    assert any('Friday' in desc and 'evening' in desc.lower() for desc in pattern_descriptions)

@pytest.mark.unit
def test_detect_contact_patterns(sample_pattern_dataframe, sample_column_mapping):
    """Test detecting contact patterns."""
    from src.analysis_layer.pattern_detector import PatternDetector
    
    detector = PatternDetector()
    
    result = detector.detect_contact_patterns(sample_pattern_dataframe)
    
    assert isinstance(result, dict)
    assert '1234567890' in result
    assert '9876543210' in result
    assert '5551234567' in result
    assert '3334445555' in result
    
    # Check pattern structure for a contact
    contact_patterns = result['1234567890']
    assert 'time_patterns' in contact_patterns
    assert 'content_patterns' in contact_patterns
    assert 'interaction_patterns' in contact_patterns
    
    # Check for specific contact patterns
    assert any('Monday' in p['description'] for p in contact_patterns['time_patterns'])
    assert any('morning' in p['description'].lower() for p in result['9876543210']['time_patterns'])
    assert any('Friday' in p['description'] for p in result['5551234567']['time_patterns'])

@pytest.mark.unit
def test_detect_sequence_patterns(sample_pattern_dataframe, sample_column_mapping):
    """Test detecting sequence patterns."""
    from src.analysis_layer.pattern_detector import PatternDetector
    
    detector = PatternDetector()
    
    result = detector.detect_sequence_patterns(sample_pattern_dataframe)
    
    assert isinstance(result, list)
    
    # Check pattern structure
    if result:  # If any patterns were detected
        pattern = result[0]
        assert 'sequence' in pattern
        assert 'confidence' in pattern
        assert 'occurrences' in pattern
        assert 'examples' in pattern
    
    # Should detect "meeting text followed by call" pattern
    meeting_pattern = [p for p in result if 'meeting' in p.get('description', '').lower()]
    assert len(meeting_pattern) > 0

@pytest.mark.unit
def test_detect_content_patterns(sample_pattern_dataframe, sample_column_mapping):
    """Test detecting content patterns."""
    from src.analysis_layer.pattern_detector import PatternDetector
    
    detector = PatternDetector()
    
    result = detector.detect_content_patterns(sample_pattern_dataframe)
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Check pattern structure
    pattern = result[0]
    assert 'pattern_type' in pattern
    assert 'description' in pattern
    assert 'confidence' in pattern
    assert 'occurrences' in pattern
    assert 'examples' in pattern
    
    # Should detect "good morning" pattern
    morning_pattern = [p for p in result if 'morning' in p.get('description', '').lower()]
    assert len(morning_pattern) > 0
    
    # Should detect "meeting" pattern
    meeting_pattern = [p for p in result if 'meeting' in p.get('description', '').lower()]
    assert len(meeting_pattern) > 0

@pytest.mark.unit
def test_calculate_pattern_significance(sample_pattern_dataframe, sample_column_mapping):
    """Test calculating pattern significance."""
    from src.analysis_layer.pattern_detector import PatternDetector
    
    detector = PatternDetector()
    
    # First get some patterns
    time_patterns = detector.detect_time_patterns(sample_pattern_dataframe)
    
    # Then calculate significance
    result = detector.calculate_pattern_significance(time_patterns, sample_pattern_dataframe)
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Check that patterns have significance scores
    for pattern in result:
        assert 'significance_score' in pattern
        assert 0 <= pattern['significance_score'] <= 1
    
    # Patterns should be sorted by significance
    significance_scores = [p['significance_score'] for p in result]
    assert significance_scores == sorted(significance_scores, reverse=True)

@pytest.mark.unit
def test_filter_patterns_by_confidence(sample_pattern_dataframe, sample_column_mapping):
    """Test filtering patterns by confidence."""
    from src.analysis_layer.pattern_detector import PatternDetector
    
    detector = PatternDetector()
    
    # First get some patterns
    time_patterns = detector.detect_time_patterns(sample_pattern_dataframe)
    
    # Then filter by high confidence
    high_confidence = detector.filter_patterns_by_confidence(time_patterns, min_confidence=0.8)
    assert all(p['confidence'] >= 0.8 for p in high_confidence)
    
    # Filter by medium confidence
    medium_confidence = detector.filter_patterns_by_confidence(time_patterns, min_confidence=0.5, max_confidence=0.8)
    assert all(0.5 <= p['confidence'] < 0.8 for p in medium_confidence)
    
    # Filter by low confidence
    low_confidence = detector.filter_patterns_by_confidence(time_patterns, max_confidence=0.5)
    assert all(p['confidence'] < 0.5 for p in low_confidence)
