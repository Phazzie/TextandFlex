"""
Tests for the insight generator module.
"""
import pytest
import pandas as pd
from datetime import datetime
from src.analysis_layer.insight_generator import (
    InsightGenerator, TIME_INSIGHT_ERROR, CONTACT_INSIGHT_ERROR,
    RELATIONSHIP_INSIGHT_ERROR, SUMMARY_ERROR, RECOMMENDATION_ERROR
)


# Fixtures for sample analysis results
@pytest.fixture
def sample_time_results():
    """Fixture for valid time analysis results."""
    return {
        'hourly_distribution': pd.Series([10, 5, 20], index=[9, 10, 11]), # Peak at 11
        'daily_distribution': pd.Series([50, 30, 70], index=['Mon', 'Tue', 'Wed']), # Peak on Wed
        'anomalies': [datetime(2025, 4, 20, 3, 0)] # One anomaly
    }

@pytest.fixture
def sample_contact_results():
    """Fixture for valid contact analysis results."""
    return {
        'contact_frequency': pd.Series([100, 150, 80], index=['Alice', 'Bob', 'Charlie']), # Peak Bob
        'contact_importance': pd.Series([0.8, 0.9, 0.7], index=['Alice', 'Bob', 'Charlie']), # Peak Bob
        'categories': {'Friends': ['Alice', 'Bob'], 'Work': ['Charlie']}
    }

@pytest.fixture
def sample_relationship_results():
    """Fixture for valid relationship analysis results."""
    return {
         'relationship_strength': {('Alice', 'Bob'): 0.9, ('Bob', 'Charlie'): 0.5}
     }

@pytest.fixture
def sample_basic_stats():
    """Fixture for basic statistics results."""
    return {'total_messages': 330, 'unique_contacts': 3}

@pytest.fixture
def insight_generator():
    """Fixture for InsightGenerator instance."""
    return InsightGenerator()

# --- Test Cases ---

@pytest.mark.unit
def test_insight_generator_creation(insight_generator):
    """Test creating an InsightGenerator."""
    assert insight_generator is not None
    assert insight_generator.last_error is None

@pytest.mark.unit
def test_generate_time_insights(insight_generator, sample_time_results):
    """Test generating time-based insights."""
    insights = insight_generator.generate_time_insights(sample_time_results)
    assert isinstance(insights, list)
    assert len(insights) == 3
    assert "Peak communication hour: 11:00." in insights
    assert "Most active day: Wed." in insights
    assert "Detected 1 potential time anomalies." in insights

@pytest.mark.unit
def test_generate_time_insights_missing_data(insight_generator):
    """Test time insights with missing or empty data."""
    insights = insight_generator.generate_time_insights({})
    assert insights == ["No specific time insights generated from the provided data."]
    insights_empty_series = insight_generator.generate_time_insights(
        {'hourly_distribution': pd.Series(dtype=float), 'daily_distribution': pd.Series(dtype=float)}
    )
    assert insights_empty_series == ["No specific time insights generated from the provided data."]


@pytest.mark.unit
def test_generate_time_insights_error(insight_generator, caplog):
    """Test time insights generation with faulty data causing an error."""
    faulty_results = {'hourly_distribution': 'not a series'}
    insights = insight_generator.generate_time_insights(faulty_results)
    assert insights == [TIME_INSIGHT_ERROR]
    assert insight_generator.last_error is not None
    assert "Error generating time insights" in caplog.text


@pytest.mark.unit
def test_generate_contact_insights(insight_generator, sample_contact_results):
    """Test generating contact-based insights."""
    insights = insight_generator.generate_contact_insights(sample_contact_results)
    assert isinstance(insights, list)
    assert len(insights) == 3
    assert "Most frequent contact: Bob." in insights
    assert "Potentially most important contact (based on ranking): Bob." in insights
    assert "Contacts categorized into 2 groups." in insights

@pytest.mark.unit
def test_generate_contact_insights_missing_data(insight_generator):
    """Test contact insights with missing or empty data."""
    insights = insight_generator.generate_contact_insights({})
    assert insights == ["No specific contact insights generated from the provided data."]
    insights_empty_series = insight_generator.generate_contact_insights(
         {'contact_frequency': pd.Series(dtype=float), 'contact_importance': pd.Series(dtype=float)}
    )
    assert insights_empty_series == ["No specific contact insights generated from the provided data."]


@pytest.mark.unit
def test_generate_contact_insights_error(insight_generator, caplog):
    """Test contact insights generation with faulty data causing an error."""
    faulty_results = {'contact_frequency': 'not a series'}
    insights = insight_generator.generate_contact_insights(faulty_results)
    assert insights == [CONTACT_INSIGHT_ERROR]
    assert insight_generator.last_error is not None
    assert "Error generating contact insights" in caplog.text


@pytest.mark.unit
def test_generate_relationship_insights(insight_generator, sample_relationship_results):
    """Test generating relationship insights."""
    insights = insight_generator.generate_relationship_insights(sample_relationship_results)
    assert isinstance(insights, list)
    assert len(insights) == 1
    # Note: Tuple string representation might vary slightly, check content
    assert "Strongest detected relationship pair: ('Alice', 'Bob')" in insights[0]

@pytest.mark.unit
def test_generate_relationship_insights_missing_data(insight_generator):
    """Test relationship insights with missing or empty data."""
    insights = insight_generator.generate_relationship_insights({})
    assert insights == ["Basic relationship insights generated."]
    insights_empty_dict = insight_generator.generate_relationship_insights(
        {'relationship_strength': {}}
    )
    assert insights_empty_dict == ["Basic relationship insights generated."]


@pytest.mark.unit
def test_generate_relationship_insights_error(insight_generator, caplog):
    """Test relationship insights generation with faulty data causing an error."""
    faulty_results = {'relationship_strength': 'not a dict'}
    insights = insight_generator.generate_relationship_insights(faulty_results)
    assert insights == [RELATIONSHIP_INSIGHT_ERROR]
    assert insight_generator.last_error is not None
    assert "Error generating relationship insights" in caplog.text


@pytest.mark.unit
def test_generate_narrative_summary(insight_generator, sample_basic_stats, sample_time_results, sample_contact_results, sample_relationship_results):
    """Test generating a narrative summary."""
    all_results = {
        'basic_stats': sample_basic_stats,
        'time_analysis': sample_time_results,
        'contact_analysis': sample_contact_results,
        'relationship_analysis': sample_relationship_results
    }
    summary = insight_generator.generate_narrative_summary(all_results)
    assert isinstance(summary, str)
    assert "Analysis covers 330 messages with 3 unique contacts." in summary
    assert "Peak communication hour: 11:00." in summary
    assert "Most frequent contact: Bob." in summary
    assert "Strongest detected relationship pair: ('Alice', 'Bob')" in summary
    assert "Error occurred" not in summary # Ensure no error messages leak

@pytest.mark.unit
def test_generate_narrative_summary_minimal_data(insight_generator, sample_basic_stats):
    """Test narrative summary with only basic stats."""
    summary = insight_generator.generate_narrative_summary({'basic_stats': sample_basic_stats})
    expected_msg = (
        "Basic analysis complete. More detailed insights require "
        "further analysis results or data."
    )
    assert summary == expected_msg

@pytest.mark.unit
def test_generate_narrative_summary_with_errors(insight_generator, sample_basic_stats, caplog):
    """Test narrative summary when underlying insight generation fails."""
    all_results = {
        'basic_stats': sample_basic_stats,
        'time_analysis': {'hourly_distribution': 'bad data'}, # Will cause error
        'contact_analysis': {}
    }
    summary = insight_generator.generate_narrative_summary(all_results)
    assert isinstance(summary, str)
    assert "Analysis covers 330 messages with 3 unique contacts." in summary
    # The specific error insight should be filtered out
    assert TIME_INSIGHT_ERROR not in summary
    assert CONTACT_INSIGHT_ERROR not in summary
    # Check logs for the original error
    assert "Error generating time insights" in caplog.text


@pytest.mark.unit
def test_generate_narrative_summary_overall_error(insight_generator, caplog):
    """Test narrative summary generation itself failing."""
    # Force an error by passing unexpected structure
    faulty_results = {'basic_stats': 'not a dict'}
    summary = insight_generator.generate_narrative_summary(faulty_results)
    assert summary == SUMMARY_ERROR
    assert insight_generator.last_error is not None
    assert "Error generating narrative summary" in caplog.text


@pytest.mark.unit
def test_generate_recommendations(insight_generator, sample_time_results, sample_contact_results):
    """Test generating recommendations."""
    all_results = {
        'time_analysis': sample_time_results,
        'contact_analysis': sample_contact_results
    }
    recommendations = insight_generator.generate_recommendations(all_results)
    assert isinstance(recommendations, list)
    assert len(recommendations) == 2
    assert "Review detected time anomalies for unusual activity." in recommendations
    assert "Consider prioritizing communication with Bob." in recommendations

@pytest.mark.unit
def test_generate_recommendations_no_triggers(insight_generator):
    """Test recommendations when no specific triggers are met."""
    recommendations = insight_generator.generate_recommendations({})
    assert recommendations == ["No specific recommendations generated at this time."]
    recommendations_empty = insight_generator.generate_recommendations(
        {'time_analysis': {}, 'contact_analysis': {}}
    )
    assert recommendations_empty == ["No specific recommendations generated at this time."]


@pytest.mark.unit
def test_generate_recommendations_error(insight_generator, caplog):
    """Test recommendations generation with faulty data causing an error."""
    faulty_results = {'contact_analysis': {'contact_importance': 'not a series'}}
    recommendations = insight_generator.generate_recommendations(faulty_results)
    assert recommendations == [RECOMMENDATION_ERROR]
    assert insight_generator.last_error is not None
    assert "Error generating recommendations" in caplog.text
