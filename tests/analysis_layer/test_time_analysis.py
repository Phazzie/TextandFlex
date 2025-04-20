"""
Tests for the time analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

@pytest.fixture
def sample_time_dataframe():
    """Create a sample DataFrame for time analysis testing."""
    # Create a DataFrame with data spanning multiple days with specific patterns
    dates = []
    numbers = []
    types = []
    contents = []
    durations = []
    
    # Create 30 days of data with specific patterns
    start_date = datetime(2023, 1, 1)
    
    # Morning pattern - Contact A calls every morning (7-9 AM)
    for i in range(30):
        day = start_date + timedelta(days=i)
        # Morning call - around 8 AM with some variation
        morning_time = day + timedelta(hours=8, minutes=np.random.randint(-60, 60))
        dates.append(morning_time)
        numbers.append('1234567890')  # Contact A
        types.append('received' if i % 2 == 0 else 'sent')
        contents.append('Morning call')
        durations.append(np.random.randint(60, 180))  # 1-3 minutes
    
    # Evening pattern - Contact B texts every other evening (6-8 PM)
    for i in range(0, 30, 2):
        day = start_date + timedelta(days=i)
        # Evening text - around 7 PM with some variation
        evening_time = day + timedelta(hours=19, minutes=np.random.randint(-60, 60))
        dates.append(evening_time)
        numbers.append('9876543210')  # Contact B
        types.append('received' if i % 4 == 0 else 'sent')
        contents.append('Evening text')
        durations.append(0)  # Text message
    
    # Weekend pattern - Contact C calls on weekends
    for i in range(4):  # 4 weekends in our 30-day period
        # Saturday
        saturday = start_date + timedelta(days=i*7 + 5)  # Jan 6, 13, 20, 27
        saturday_time = saturday + timedelta(hours=14, minutes=np.random.randint(-60, 60))
        dates.append(saturday_time)
        numbers.append('5551234567')  # Contact C
        types.append('received')
        contents.append('Weekend call')
        durations.append(np.random.randint(300, 600))  # 5-10 minutes
        
        # Sunday
        sunday = start_date + timedelta(days=i*7 + 6)  # Jan 7, 14, 21, 28
        sunday_time = sunday + timedelta(hours=16, minutes=np.random.randint(-60, 60))
        dates.append(sunday_time)
        numbers.append('5551234567')  # Contact C
        types.append('sent')
        contents.append('Weekend call')
        durations.append(np.random.randint(300, 600))  # 5-10 minutes
    
    # Random calls/texts to add noise
    for i in range(20):
        random_day = start_date + timedelta(days=np.random.randint(0, 30))
        random_hour = np.random.randint(9, 22)  # Between 9 AM and 10 PM
        random_time = random_day + timedelta(hours=random_hour, minutes=np.random.randint(0, 60))
        dates.append(random_time)
        numbers.append(np.random.choice(['1234567890', '9876543210', '5551234567', '3334445555']))
        types.append(np.random.choice(['sent', 'received']))
        contents.append('Random message')
        durations.append(np.random.randint(0, 300))  # 0-5 minutes
    
    return pd.DataFrame({
        'timestamp': pd.Series(dates),
        'phone_number': numbers,
        'message_type': types,
        'message_content': contents,
        'duration': durations
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
def test_time_analyzer_creation():
    """Test creating a TimeAnalyzer."""
    from src.analysis_layer.time_analysis import TimeAnalyzer
    
    analyzer = TimeAnalyzer()
    assert analyzer is not None

@pytest.mark.unit
def test_analyze_hourly_patterns(sample_time_dataframe, sample_column_mapping):
    """Test analyzing hourly patterns."""
    from src.analysis_layer.time_analysis import TimeAnalyzer
    
    analyzer = TimeAnalyzer()
    
    result = analyzer.analyze_hourly_patterns(sample_time_dataframe)
    
    assert isinstance(result, dict)
    assert 'peak_hours' in result
    assert 'quiet_hours' in result
    assert 'hourly_distribution' in result
    
    # Morning pattern should be detected (around 8 AM)
    assert 8 in result['peak_hours']
    
    # Evening pattern should be detected (around 7 PM)
    assert 19 in result['peak_hours']
    
    # Check hourly distribution
    assert len(result['hourly_distribution']) == 24
    assert all(isinstance(count, int) for count in result['hourly_distribution'].values())

@pytest.mark.unit
def test_analyze_daily_patterns(sample_time_dataframe, sample_column_mapping):
    """Test analyzing daily patterns."""
    from src.analysis_layer.time_analysis import TimeAnalyzer
    
    analyzer = TimeAnalyzer()
    
    result = analyzer.analyze_daily_patterns(sample_time_dataframe)
    
    assert isinstance(result, dict)
    assert 'weekday_distribution' in result
    assert 'weekend_vs_weekday' in result
    assert 'busiest_days' in result
    
    # Weekend pattern should be detected
    assert result['weekend_vs_weekday']['weekend_percentage'] > 0
    
    # Check weekday distribution
    assert len(result['weekday_distribution']) == 7
    assert all(isinstance(count, int) for count in result['weekday_distribution'].values())

@pytest.mark.unit
def test_analyze_periodicity(sample_time_dataframe, sample_column_mapping):
    """Test analyzing periodicity."""
    from src.analysis_layer.time_analysis import TimeAnalyzer
    
    analyzer = TimeAnalyzer()
    
    result = analyzer.analyze_periodicity(sample_time_dataframe)
    
    assert isinstance(result, dict)
    assert 'daily_patterns' in result
    assert 'weekly_patterns' in result
    assert 'monthly_patterns' in result
    
    # Daily pattern should be detected (morning calls)
    assert len(result['daily_patterns']) > 0
    
    # Weekly pattern should be detected (weekend calls)
    assert len(result['weekly_patterns']) > 0

@pytest.mark.unit
def test_detect_time_anomalies(sample_time_dataframe, sample_column_mapping):
    """Test detecting time anomalies."""
    from src.analysis_layer.time_analysis import TimeAnalyzer
    
    analyzer = TimeAnalyzer()
    
    result = analyzer.detect_time_anomalies(sample_time_dataframe)
    
    assert isinstance(result, list)
    # We can't assert exact anomalies since they depend on the algorithm,
    # but we can check the structure
    if result:  # If any anomalies were detected
        anomaly = result[0]
        assert 'timestamp' in anomaly
        assert 'phone_number' in anomaly
        assert 'anomaly_score' in anomaly
        assert 'reason' in anomaly

@pytest.mark.unit
def test_analyze_contact_time_patterns(sample_time_dataframe, sample_column_mapping):
    """Test analyzing contact-specific time patterns."""
    from src.analysis_layer.time_analysis import TimeAnalyzer
    
    analyzer = TimeAnalyzer()
    
    result = analyzer.analyze_contact_time_patterns(sample_time_dataframe)
    
    assert isinstance(result, dict)
    assert '1234567890' in result  # Contact A
    assert '9876543210' in result  # Contact B
    assert '5551234567' in result  # Contact C
    
    # Contact A should have morning pattern
    contact_a = result['1234567890']
    assert 'preferred_hours' in contact_a
    assert 8 in contact_a['preferred_hours']  # 8 AM
    
    # Contact B should have evening pattern
    contact_b = result['9876543210']
    assert 'preferred_hours' in contact_b
    assert 19 in contact_b['preferred_hours']  # 7 PM
    
    # Contact C should have weekend pattern
    contact_c = result['5551234567']
    assert 'preferred_days' in contact_c
    assert 'Saturday' in contact_c['preferred_days']
    assert 'Sunday' in contact_c['preferred_days']

@pytest.mark.unit
def test_analyze_response_time_patterns(sample_time_dataframe, sample_column_mapping):
    """Test analyzing response time patterns."""
    from src.analysis_layer.time_analysis import TimeAnalyzer
    
    analyzer = TimeAnalyzer()
    
    result = analyzer.analyze_response_time_patterns(sample_time_dataframe)
    
    assert isinstance(result, dict)
    assert 'overall_avg_response_time' in result
    assert 'response_time_by_contact' in result
    assert 'response_time_by_hour' in result
    assert 'response_time_by_day' in result
    
    # Check response time by contact
    assert isinstance(result['response_time_by_contact'], dict)
    
    # Check response time by hour
    assert isinstance(result['response_time_by_hour'], dict)
    assert all(0 <= hour <= 23 for hour in result['response_time_by_hour'].keys())
    
    # Check response time by day
    assert isinstance(result['response_time_by_day'], dict)
    assert all(day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] 
               for day in result['response_time_by_day'].keys())
