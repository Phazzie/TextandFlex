"""
Tests for the analysis service.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from src.presentation_layer.services.analysis_service import AnalysisService
from src.presentation_layer.gui.models.analysis_model import AnalysisType


@pytest.fixture
def mock_basic_analyzer():
    """Create a mock basic statistics analyzer."""
    mock_analyzer = MagicMock()
    mock_analyzer.analyze.return_value = {
        "total_records": 10,
        "date_range": {
            "start": "2023-01-01",
            "end": "2023-01-10",
            "days": 10
        },
        "top_contacts": [
            {"number": "123456789", "count": 5}
        ],
        "message_types": {
            "sent": 6,
            "received": 4
        }
    }
    return mock_analyzer


@pytest.fixture
def mock_contact_analyzer():
    """Create a mock contact analyzer."""
    mock_analyzer = MagicMock()
    mock_analyzer.analyze_all.return_value = {
        "contact_count": 3,
        "contact_relationships": [
            {"contact": "123456789", "relationship": "frequent"}
        ],
        "conversation_flow": {
            "average_response_time": 120
        },
        "contact_importance": [
            {"contact": "123456789", "importance": 0.8}
        ]
    }
    return mock_analyzer


@pytest.fixture
def mock_time_analyzer():
    """Create a mock time analyzer."""
    mock_analyzer = MagicMock()
    mock_analyzer.analyze_time_patterns.return_value = {
        "hourly_distribution": {
            "0": 1, "1": 0, "2": 0, "3": 0, "4": 0,
            "5": 0, "6": 0, "7": 0, "8": 2, "9": 3,
            "10": 1, "11": 0, "12": 1, "13": 0, "14": 0,
            "15": 0, "16": 0, "17": 1, "18": 0, "19": 0,
            "20": 0, "21": 0, "22": 1, "23": 0
        },
        "daily_distribution": {
            "Monday": 2, "Tuesday": 1, "Wednesday": 3,
            "Thursday": 1, "Friday": 2, "Saturday": 0, "Sunday": 1
        },
        "monthly_distribution": {
            "January": 10, "February": 0, "March": 0,
            "April": 0, "May": 0, "June": 0,
            "July": 0, "August": 0, "September": 0,
            "October": 0, "November": 0, "December": 0
        }
    }
    return mock_analyzer


@pytest.fixture
def mock_pattern_detector():
    """Create a mock pattern detector."""
    mock_detector = MagicMock()
    mock_detector.detect_patterns.return_value = {
        "patterns": [
            {
                "type": "time",
                "description": "Regular communication on Wednesday mornings",
                "confidence": 0.85,
                "supporting_data": {
                    "count": 3,
                    "examples": ["2023-01-04 09:00", "2023-01-11 09:15", "2023-01-18 09:05"]
                }
            }
        ],
        "anomalies": [
            {
                "type": "frequency",
                "description": "Unusual spike in communication on January 5th",
                "severity": 0.7,
                "details": {
                    "expected": 1,
                    "actual": 5,
                    "date": "2023-01-05"
                }
            }
        ]
    }
    return mock_detector


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        "timestamp": [
            "2023-01-01 12:00:00", "2023-01-02 09:30:00",
            "2023-01-03 17:45:00", "2023-01-04 08:15:00",
            "2023-01-05 10:00:00", "2023-01-05 10:30:00",
            "2023-01-05 11:00:00", "2023-01-05 11:30:00",
            "2023-01-05 12:00:00", "2023-01-10 22:15:00"
        ],
        "phone_number": [
            "123456789", "123456789", "987654321",
            "123456789", "123456789", "555555555",
            "987654321", "555555555", "123456789",
            "987654321"
        ],
        "message_type": [
            "sent", "received", "sent", "sent", "received",
            "sent", "sent", "received", "sent", "sent"
        ],
        "content": [
            "Hello", "Hi there", "Meeting tomorrow?",
            "Good morning", "Yes, 2pm works", "Can you talk?",
            "I'll be late", "No problem", "Thanks", "Goodnight"
        ]
    })


@pytest.fixture
def analysis_service(mock_basic_analyzer, mock_contact_analyzer, 
                    mock_time_analyzer, mock_pattern_detector):
    """Create an analysis service with mock analyzers."""
    return AnalysisService(
        basic_analyzer=mock_basic_analyzer,
        contact_analyzer=mock_contact_analyzer,
        time_analyzer=mock_time_analyzer,
        pattern_detector=mock_pattern_detector
    )


class TestAnalysisService:
    """Tests for the AnalysisService class."""

    def test_run_basic_analysis(self, analysis_service, mock_basic_analyzer, sample_dataframe):
        """Test running basic analysis."""
        # Act
        result = analysis_service.run_analysis("basic", sample_dataframe)
        
        # Assert
        assert result is not None
        assert result.result_type == AnalysisType.BASIC
        assert isinstance(result.data, pd.DataFrame)
        assert result.specific_data is not None
        assert result.specific_data.total_records == 10
        mock_basic_analyzer.analyze.assert_called_once()

    def test_run_contact_analysis(self, analysis_service, mock_contact_analyzer, sample_dataframe):
        """Test running contact analysis."""
        # Act
        result = analysis_service.run_analysis("contact", sample_dataframe)
        
        # Assert
        assert result is not None
        assert result.result_type == AnalysisType.CONTACT
        assert isinstance(result.data, pd.DataFrame)
        assert result.specific_data is not None
        assert result.specific_data.contact_count == 3
        mock_contact_analyzer.analyze_all.assert_called_once()

    def test_run_time_analysis(self, analysis_service, mock_time_analyzer, sample_dataframe):
        """Test running time analysis."""
        # Act
        result = analysis_service.run_analysis("time", sample_dataframe)
        
        # Assert
        assert result is not None
        assert result.result_type == AnalysisType.TIME
        assert isinstance(result.data, pd.DataFrame)
        assert result.specific_data is not None
        assert "hourly_distribution" in result.specific_data.time_patterns
        mock_time_analyzer.analyze_time_patterns.assert_called_once()

    def test_run_pattern_analysis(self, analysis_service, mock_pattern_detector, sample_dataframe):
        """Test running pattern analysis."""
        # Act
        result = analysis_service.run_analysis("pattern", sample_dataframe)
        
        # Assert
        assert result is not None
        assert result.result_type == AnalysisType.PATTERN
        assert isinstance(result.data, pd.DataFrame)
        assert result.specific_data is not None
        assert len(result.specific_data.patterns) == 1
        assert len(result.specific_data.anomalies) == 1
        mock_pattern_detector.detect_patterns.assert_called_once()

    def test_run_analysis_with_invalid_type(self, analysis_service, sample_dataframe):
        """Test running analysis with invalid type."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            analysis_service.run_analysis("invalid", sample_dataframe)
        
        assert "Invalid analysis type" in str(exc_info.value)

    def test_run_analysis_with_empty_dataframe(self, analysis_service):
        """Test running analysis with empty dataframe."""
        # Arrange
        empty_df = pd.DataFrame()
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            analysis_service.run_analysis("basic", empty_df)
        
        assert "Empty dataframe" in str(exc_info.value)

    def test_run_analysis_with_options(self, analysis_service, mock_basic_analyzer, sample_dataframe):
        """Test running analysis with options."""
        # Arrange
        options = {"max_contacts": 5, "include_duration_stats": True}
        
        # Act
        result = analysis_service.run_analysis("basic", sample_dataframe, options)
        
        # Assert
        assert result is not None
        mock_basic_analyzer.analyze.assert_called_once()
        # Check that options were passed to the analyzer
        args, kwargs = mock_basic_analyzer.analyze.call_args
        assert "options" in kwargs
        assert kwargs["options"] == options
