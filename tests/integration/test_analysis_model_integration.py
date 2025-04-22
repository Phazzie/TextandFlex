"""
Integration tests for the AnalysisModel with the analyzers.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from src.presentation_layer.gui.models.analysis_model import (
    AnalysisResult, AnalysisType, AnalysisResultModel,
    BasicAnalysisData, ContactAnalysisData, TimeAnalysisData, PatternAnalysisData
)
from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
from src.analysis_layer.contact_analysis import ContactAnalyzer
from src.analysis_layer.time_analysis import TimeAnalyzer
from src.analysis_layer.pattern_detector import PatternDetector
from src.presentation_layer.gui.controllers.analysis_controller import AnalysisController

from tests.utils.gui_test_helpers import create_sample_dataframe


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    return create_sample_dataframe()


@pytest.fixture
def basic_analyzer():
    """Create a BasicStatisticsAnalyzer for testing."""
    return BasicStatisticsAnalyzer()


@pytest.fixture
def contact_analyzer():
    """Create a ContactAnalyzer for testing."""
    return ContactAnalyzer()


@pytest.fixture
def time_analyzer():
    """Create a TimeAnalyzer for testing."""
    return TimeAnalyzer()


@pytest.fixture
def pattern_detector():
    """Create a PatternDetector for testing."""
    return PatternDetector()


@pytest.mark.integration
def test_analysis_result_creation():
    """Test creating an AnalysisResult."""
    # Create a sample dataframe for the result
    df = pd.DataFrame({
        "Metric": ["Total Records", "Date Range"],
        "Value": [100, "2023-01-01 to 2023-01-31"]
    })
    
    # Create specific data
    specific_data = BasicAnalysisData(
        total_records=100,
        date_range={"start": "2023-01-01", "end": "2023-01-31"},
        top_contacts=[{"number": "1234567890", "count": 50}],
        message_types={"sent": 60, "received": 40}
    )
    
    # Create an AnalysisResult
    result = AnalysisResult(
        result_type=AnalysisType.BASIC,
        data=df,
        specific_data=specific_data
    )
    
    # Verify the result was created correctly
    assert result.result_type == AnalysisType.BASIC
    assert result.data is df
    assert result.specific_data is specific_data
    
    # Create a model from the result
    model = AnalysisResultModel(result)
    
    # Verify the model was created correctly
    assert model.rowCount() == len(df)
    assert model.columnCount() == len(df.columns)
    assert model.analysis_type == AnalysisType.BASIC
    assert model.specific_data is specific_data
    
    # Test the get_summary_data method
    summary = model.get_summary_data()
    assert summary["analysis_type"] == "BASIC"
    assert summary["row_count"] == len(df)
    assert summary["column_count"] == len(df.columns)
    assert summary["total_records"] == 100
    assert summary["date_range"] == {"start": "2023-01-01", "end": "2023-01-31"}
    assert summary["top_contacts"] == [{"number": "1234567890", "count": 50}]
    assert summary["message_types"] == {"sent": 60, "received": 40}


@pytest.mark.integration
def test_basic_analysis_integration(sample_dataframe, basic_analyzer):
    """Test integration with the BasicStatisticsAnalyzer."""
    # Run the analysis
    stats, error = basic_analyzer.analyze(sample_dataframe)
    
    # Verify the analysis was successful
    assert error is None
    assert stats is not None
    assert stats.total_records == len(sample_dataframe)
    
    # Create specific data from the stats
    specific_data = BasicAnalysisData(
        total_records=stats.total_records,
        date_range=stats.date_range.to_dict() if stats.date_range else None,
        top_contacts=[contact.to_dict() for contact in stats.top_contacts] if stats.top_contacts else None,
        message_types={t.name: t.count for t in stats.type_stats.types} if stats.type_stats else None
    )
    
    # Create a result dataframe
    result_df = pd.DataFrame({
        "Metric": ["Total Records", "Date Range", "Top Contact", "Message Types"],
        "Value": [
            stats.total_records,
            f"{stats.date_range.start} to {stats.date_range.end}" if stats.date_range else "N/A",
            f"{stats.top_contacts[0].number} ({stats.top_contacts[0].count} records)" if stats.top_contacts else "N/A",
            ", ".join([f"{t.name}: {t.count}" for t in stats.type_stats.types]) if stats.type_stats else "N/A"
        ]
    })
    
    # Create an AnalysisResult
    result = AnalysisResult(
        result_type=AnalysisType.BASIC,
        data=result_df,
        specific_data=specific_data
    )
    
    # Create a model from the result
    model = AnalysisResultModel(result)
    
    # Verify the model was created correctly
    assert model.rowCount() == len(result_df)
    assert model.columnCount() == len(result_df.columns)
    assert model.analysis_type == AnalysisType.BASIC
    assert model.specific_data is specific_data


@pytest.mark.integration
def test_contact_analysis_integration(sample_dataframe, contact_analyzer):
    """Test integration with the ContactAnalyzer."""
    # Run the analysis
    contact_data = contact_analyzer.analyze_all(sample_dataframe)
    
    # Verify the analysis was successful
    assert contact_data is not None
    
    # Create specific data from the contact data
    specific_data = ContactAnalysisData(
        contact_count=len(contact_data.get('contact_relationships', [])),
        contact_relationships=contact_data.get('contact_relationships'),
        conversation_flow=contact_data.get('conversation_flow'),
        contact_importance=contact_data.get('contact_importance')
    )
    
    # Create a result dataframe
    if contact_data.get('contact_relationships'):
        result_df = pd.DataFrame({
            "Contact": [r['contact'] for r in contact_data.get('contact_relationships', [])],
            "Frequency": [r['frequency'] for r in contact_data.get('contact_relationships', [])],
            "Importance": [r.get('importance', 'N/A') for r in contact_data.get('contact_relationships', [])]
        })
    else:
        result_df = pd.DataFrame()
    
    # Create an AnalysisResult
    result = AnalysisResult(
        result_type=AnalysisType.CONTACT,
        data=result_df,
        specific_data=specific_data
    )
    
    # Create a model from the result
    model = AnalysisResultModel(result)
    
    # Verify the model was created correctly
    assert model.analysis_type == AnalysisType.CONTACT
    assert model.specific_data is specific_data


@pytest.mark.integration
def test_time_analysis_integration(sample_dataframe, time_analyzer):
    """Test integration with the TimeAnalyzer."""
    # Run the analysis
    time_data = time_analyzer.analyze_all(sample_dataframe)
    
    # Verify the analysis was successful
    assert time_data is not None
    
    # Create specific data from the time data
    specific_data = TimeAnalysisData(
        time_distribution=time_data.get('time_distribution'),
        hourly_patterns=time_data.get('hourly_patterns'),
        daily_patterns=time_data.get('daily_patterns'),
        monthly_patterns=time_data.get('monthly_patterns'),
        response_times=time_data.get('response_times')
    )
    
    # Create a result dataframe
    if time_data.get('hourly_patterns'):
        result_df = pd.DataFrame({
            "Hour": list(time_data['hourly_patterns'].keys()),
            "Count": list(time_data['hourly_patterns'].values())
        })
    else:
        result_df = pd.DataFrame()
    
    # Create an AnalysisResult
    result = AnalysisResult(
        result_type=AnalysisType.TIME,
        data=result_df,
        specific_data=specific_data
    )
    
    # Create a model from the result
    model = AnalysisResultModel(result)
    
    # Verify the model was created correctly
    assert model.analysis_type == AnalysisType.TIME
    assert model.specific_data is specific_data


@pytest.mark.integration
def test_pattern_analysis_integration(sample_dataframe, pattern_detector):
    """Test integration with the PatternDetector."""
    # Run the analysis
    pattern_data = pattern_detector.detect_all_patterns(sample_dataframe)
    
    # Verify the analysis was successful
    assert pattern_data is not None
    
    # Create specific data from the pattern data
    specific_data = PatternAnalysisData(
        detected_patterns=pattern_data.get('detected_patterns'),
        anomalies=pattern_data.get('anomalies'),
        predictions=pattern_data.get('predictions')
    )
    
    # Create a result dataframe
    if pattern_data.get('detected_patterns'):
        result_df = pd.DataFrame({
            "Pattern": [p['pattern_name'] for p in pattern_data['detected_patterns']],
            "Confidence": [p['confidence'] for p in pattern_data['detected_patterns']],
            "Description": [p['description'] for p in pattern_data['detected_patterns']]
        })
    else:
        result_df = pd.DataFrame()
    
    # Create an AnalysisResult
    result = AnalysisResult(
        result_type=AnalysisType.PATTERN,
        data=result_df,
        specific_data=specific_data
    )
    
    # Create a model from the result
    model = AnalysisResultModel(result)
    
    # Verify the model was created correctly
    assert model.analysis_type == AnalysisType.PATTERN
    assert model.specific_data is specific_data


@pytest.mark.integration
def test_analysis_controller_integration(sample_dataframe):
    """Test integration with the AnalysisController."""
    # Create a mock file model
    file_model = MagicMock()
    file_model.dataframe = sample_dataframe
    
    # Create mock analyzers
    basic_analyzer = MagicMock(spec=BasicStatisticsAnalyzer)
    contact_analyzer = MagicMock(spec=ContactAnalyzer)
    time_analyzer = MagicMock(spec=TimeAnalyzer)
    pattern_detector = MagicMock(spec=PatternDetector)
    
    # Set up the basic analyzer to return a mock result
    stats = MagicMock()
    stats.total_records = 3
    stats.date_range.start = "2023-01-01"
    stats.date_range.end = "2023-01-01"
    stats.date_range.to_dict.return_value = {"start": "2023-01-01", "end": "2023-01-01"}
    contact = MagicMock()
    contact.number = "1234567890"
    contact.count = 2
    contact.to_dict.return_value = {"number": "1234567890", "count": 2}
    stats.top_contacts = [contact]
    type_stat = MagicMock()
    type_stat.name = "sent"
    type_stat.count = 2
    stats.type_stats.types = [type_stat]
    basic_analyzer.analyze.return_value = (stats, None)
    
    # Create the analysis controller
    analysis_controller = AnalysisController(
        basic_analyzer=basic_analyzer,
        contact_analyzer=contact_analyzer,
        time_analyzer=time_analyzer,
        pattern_detector=pattern_detector
    )
    
    # Create a signal spy for the analysis_completed signal
    analysis_completed_called = False
    result_model = None
    
    def on_analysis_completed(result):
        nonlocal analysis_completed_called, result_model
        analysis_completed_called = True
        result_model = result
    
    analysis_controller.analysis_completed.connect(on_analysis_completed)
    
    # Run the analysis
    analysis_controller.run_analysis("basic", file_model)
    
    # Wait for the analysis to complete (in a real test, we would use qtbot.waitSignal)
    import time
    time.sleep(0.5)
    
    # Verify the analysis was completed
    assert analysis_completed_called
    assert result_model is not None
    assert result_model.result_type == AnalysisType.BASIC
    assert basic_analyzer.analyze.called
