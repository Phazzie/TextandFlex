"""
Tests for the basic statistics module.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import patch, MagicMock

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'date': ['2023-01-01', '2023-01-15', '2023-01-31', '2023-02-15', '2023-02-28'],
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
def test_basic_statistics_analyzer_initialization():
    """Test initializing the BasicStatisticsAnalyzer."""
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer

    analyzer = BasicStatisticsAnalyzer()
    assert analyzer.last_error is None

@pytest.mark.unit
def test_analyze_empty_dataframe():
    """Test analyzing an empty DataFrame."""
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer

    analyzer = BasicStatisticsAnalyzer()
    empty_df = pd.DataFrame()
    column_mapping = {}

    result, error = analyzer.analyze(empty_df, column_mapping)

    assert result is None
    assert error == "Cannot analyze empty DataFrame"
    assert analyzer.last_error == "Cannot analyze empty DataFrame"

@pytest.mark.unit
def test_analyze_with_exception():
    """Test analyzing with an exception."""
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer

    analyzer = BasicStatisticsAnalyzer()

    # Mock a DataFrame that raises an exception when accessed
    mock_df = MagicMock()
    # Make sure the DataFrame doesn't appear empty
    mock_df.__len__.return_value = 5
    mock_df.empty = False

    # Mock the column mapping to ensure it passes the initial checks
    column_mapping = {'date': 'date', 'duration': 'duration'}
    mock_df.columns = ['date', 'duration']

    # Make the exception happen during duration analysis
    mock_df.__getitem__.return_value.sum.side_effect = Exception("Test exception")

    # Trigger the exception in the duration analysis
    result, error = analyzer.analyze(mock_df, column_mapping)

    assert result is None
    assert "Error analyzing basic statistics: Test exception" in error
    assert "Error analyzing basic statistics: Test exception" in analyzer.last_error

@pytest.mark.unit
def test_analyze_date_range(sample_dataframe, sample_column_mapping):
    """Test analyzing date range statistics."""
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
    from src.analysis_layer.analysis_models import DateRangeStats

    analyzer = BasicStatisticsAnalyzer()

    # Convert date strings to datetime objects for comparison
    sample_dataframe['date'] = pd.to_datetime(sample_dataframe['date'])

    date_range = analyzer._analyze_date_range(sample_dataframe, 'date')

    assert isinstance(date_range, DateRangeStats)
    assert date_range.start == pd.Timestamp('2023-01-01')
    assert date_range.end == pd.Timestamp('2023-02-28')
    assert date_range.days == 58  # 31 days in January + 28 days in February - 1 (inclusive)
    assert date_range.total_records == 5

@pytest.mark.unit
def test_analyze_top_contacts(sample_dataframe, sample_column_mapping):
    """Test analyzing top contacts statistics."""
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
    from src.analysis_layer.analysis_models import ContactStats

    analyzer = BasicStatisticsAnalyzer()

    # Convert date strings to datetime objects for comparison
    sample_dataframe['date'] = pd.to_datetime(sample_dataframe['date'])

    top_contacts = analyzer._analyze_top_contacts(sample_dataframe, sample_column_mapping)

    assert isinstance(top_contacts, list)
    assert len(top_contacts) == 3  # Three unique phone numbers

    # Check the first contact (most frequent)
    assert top_contacts[0].number in ['1234567890', '9876543210']  # Both have 2 occurrences
    assert top_contacts[0].count == 2
    assert top_contacts[0].percentage == 40.0  # 2/5 * 100

    # Check the last contact (least frequent)
    assert top_contacts[2].number == '5551234567'
    assert top_contacts[2].count == 1
    assert top_contacts[2].percentage == 20.0  # 1/5 * 100

@pytest.mark.unit
def test_analyze_durations(sample_dataframe, sample_column_mapping):
    """Test analyzing duration statistics."""
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
    from src.analysis_layer.analysis_models import DurationStats

    analyzer = BasicStatisticsAnalyzer()

    duration_stats = analyzer._analyze_durations(sample_dataframe, 'duration')

    assert isinstance(duration_stats, DurationStats)
    assert duration_stats.total == 58  # Sum of all durations
    assert duration_stats.average == 11.6  # Average of all durations
    assert duration_stats.median == 10  # Median of all durations
    assert duration_stats.max == 20  # Maximum duration
    assert duration_stats.min == 5  # Minimum duration

@pytest.mark.unit
def test_analyze_types(sample_dataframe, sample_column_mapping):
    """Test analyzing type statistics."""
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
    from src.analysis_layer.analysis_models import TypeStats

    analyzer = BasicStatisticsAnalyzer()

    type_stats = analyzer._analyze_types(sample_dataframe, 'message_type')

    assert isinstance(type_stats, TypeStats)
    assert type_stats.types == {'sent': 3, 'received': 2}

@pytest.mark.unit
def test_analyze_full_statistics(sample_dataframe, sample_column_mapping):
    """Test analyzing full statistics."""
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
    from src.analysis_layer.analysis_models import BasicStatistics

    analyzer = BasicStatisticsAnalyzer()

    # Convert date strings to datetime objects for comparison
    sample_dataframe['date'] = pd.to_datetime(sample_dataframe['date'])

    result, error = analyzer.analyze(sample_dataframe, sample_column_mapping)

    assert error == ""
    assert isinstance(result, BasicStatistics)
    assert result.total_records == 5

    # Check date range
    assert result.date_range.start == pd.Timestamp('2023-01-01')
    assert result.date_range.end == pd.Timestamp('2023-02-28')

    # Check top contacts
    assert len(result.top_contacts) == 3

    # Check duration stats
    assert result.duration_stats.total == 58
    assert result.duration_stats.average == 11.6

    # Check type stats
    assert result.type_stats.types == {'sent': 3, 'received': 2}

@pytest.mark.unit
def test_analyze_time_distribution(sample_dataframe):
    """Test analyzing time distribution."""
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer

    analyzer = BasicStatisticsAnalyzer()

    # Convert date strings to datetime objects
    sample_dataframe['date'] = pd.to_datetime(sample_dataframe['date'])

    # Mock the cache functions
    with patch('src.analysis_layer.basic_statistics.get_cached_result', return_value=None):
        with patch('src.analysis_layer.basic_statistics.cache_result'):
            with patch('src.analysis_layer.basic_statistics.calculate_time_distribution') as mock_calc:
                # Configure the mock to return specific values
                mock_calc.side_effect = lambda df, col, period: {
                    'hour': {'0': 1, '12': 4},
                    'day': {'Monday': 2, 'Friday': 3},
                    'month': {'January': 3, 'February': 2}
                }[period]

                result = analyzer.analyze_time_distribution(sample_dataframe, 'date')

                assert isinstance(result, dict)
                assert 'hourly' in result
                assert 'daily' in result
                assert 'monthly' in result
                assert result['hourly'] == {'0': 1, '12': 4}
                assert result['daily'] == {'Monday': 2, 'Friday': 3}
                assert result['monthly'] == {'January': 3, 'February': 2}

@pytest.mark.unit
def test_analyze_message_frequency(sample_dataframe):
    """Test analyzing message frequency."""
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer

    analyzer = BasicStatisticsAnalyzer()

    # Convert date strings to datetime objects
    sample_dataframe['date'] = pd.to_datetime(sample_dataframe['date'])

    # Mock the cache functions
    with patch('src.analysis_layer.basic_statistics.get_cached_result', return_value=None):
        with patch('src.analysis_layer.basic_statistics.cache_result'):
            with patch('src.analysis_layer.basic_statistics.calculate_message_frequency') as mock_calc:
                # Configure the mock to return specific values
                mock_calc.side_effect = lambda df, col, period: {
                    'day': 0.5,
                    'week': 2.5,
                    'month': 10.0
                }[period]

                result = analyzer.analyze_message_frequency(sample_dataframe, 'date')

                assert isinstance(result, dict)
                assert 'daily' in result
                assert 'weekly' in result
                assert 'monthly' in result
                assert result['daily'] == 0.5
                assert result['weekly'] == 2.5
                assert result['monthly'] == 10.0
