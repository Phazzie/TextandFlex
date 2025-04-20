"""
Tests for the result formatter module.
"""
import pytest
import pandas as pd
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

@pytest.fixture
def sample_basic_statistics():
    """Create a sample BasicStatistics object for testing."""
    from src.analysis_layer.analysis_models import BasicStatistics, DateRangeStats, ContactStats, DurationStats, TypeStats

    date_range = DateRangeStats(
        start=datetime(2023, 1, 1),
        end=datetime(2023, 2, 28),
        days=59,
        total_records=5
    )

    top_contacts = [
        ContactStats(
            number="1234567890",
            count=2,
            percentage=40.0,
            first_contact=datetime(2023, 1, 1),
            last_contact=datetime(2023, 1, 15)
        ),
        ContactStats(
            number="9876543210",
            count=2,
            percentage=40.0,
            first_contact=datetime(2023, 1, 31),
            last_contact=datetime(2023, 2, 28)
        ),
        ContactStats(
            number="5551234567",
            count=1,
            percentage=20.0,
            first_contact=datetime(2023, 2, 15),
            last_contact=datetime(2023, 2, 15)
        )
    ]

    duration_stats = DurationStats(
        total=58,
        average=11.6,
        median=10,
        max=20,
        min=5
    )

    type_stats = TypeStats(
        types={"sent": 3, "received": 2}
    )

    return BasicStatistics(
        total_records=5,
        date_range=date_range,
        top_contacts=top_contacts,
        duration_stats=duration_stats,
        type_stats=type_stats
    )

@pytest.mark.unit
def test_format_as_text(sample_basic_statistics):
    """Test formatting results as text."""
    from src.analysis_layer.result_formatter import format_as_text

    text_result = format_as_text(sample_basic_statistics)

    assert isinstance(text_result, str)
    assert "Basic Statistics Summary" in text_result
    assert "Total Records: 5" in text_result
    assert "Date Range" in text_result
    assert "Top Contacts" in text_result
    assert "Duration Statistics" in text_result
    assert "Message Type Statistics" in text_result

@pytest.mark.unit
def test_format_as_json(sample_basic_statistics):
    """Test formatting results as JSON."""
    from src.analysis_layer.result_formatter import format_as_json

    json_result = format_as_json(sample_basic_statistics)

    assert isinstance(json_result, str)

    # Parse the JSON to verify it's valid
    parsed = json.loads(json_result)

    assert parsed["total_records"] == 5
    assert "date_range" in parsed
    assert "top_contacts" in parsed
    assert "duration_stats" in parsed
    assert "type_stats" in parsed

    # Check specific values
    assert parsed["date_range"]["days"] == 59
    assert len(parsed["top_contacts"]) == 3
    assert parsed["duration_stats"]["average"] == 11.6
    assert parsed["type_stats"]["types"]["sent"] == 3

@pytest.mark.unit
def test_format_as_csv(sample_basic_statistics):
    """Test formatting results as CSV."""
    from src.analysis_layer.result_formatter import format_as_csv

    csv_result = format_as_csv(sample_basic_statistics)

    assert isinstance(csv_result, str)
    assert "total_records,5" in csv_result

    # Check that we can parse it as CSV
    lines = csv_result.strip().split('\n')
    assert len(lines) > 1  # At least header and one data row

@pytest.mark.unit
def test_format_as_html(sample_basic_statistics):
    """Test formatting results as HTML."""
    from src.analysis_layer.result_formatter import format_as_html

    html_result = format_as_html(sample_basic_statistics)

    assert isinstance(html_result, str)
    assert "<html" in html_result
    assert "<table" in html_result
    assert "Basic Statistics Summary" in html_result
    assert "<strong>Total Records:</strong> 5" in html_result
    assert "</html>" in html_result

@pytest.mark.unit
def test_format_as_markdown(sample_basic_statistics):
    """Test formatting results as Markdown."""
    from src.analysis_layer.result_formatter import format_as_markdown

    md_result = format_as_markdown(sample_basic_statistics)

    assert isinstance(md_result, str)
    assert "# Basic Statistics Summary" in md_result
    assert "## Date Range" in md_result
    assert "## Top Contacts" in md_result
    assert "## Duration Statistics" in md_result
    assert "## Message Type Statistics" in md_result

    # Check for markdown tables
    assert "| Number | Count | Percentage |" in md_result
    assert "| --- | --- | --- |" in md_result

@pytest.mark.unit
def test_get_formatter(sample_basic_statistics):
    """Test getting a formatter by format name."""
    from src.analysis_layer.result_formatter import get_formatter, format_as_text, format_as_json

    # Test getting text formatter
    formatter = get_formatter("text")
    assert formatter == format_as_text

    # Test getting JSON formatter
    formatter = get_formatter("json")
    assert formatter == format_as_json

    # Test getting unknown formatter
    with pytest.raises(ValueError):
        get_formatter("unknown_format")

@pytest.mark.unit
def test_format_result(sample_basic_statistics):
    """Test formatting results with the format_result function."""
    from src.analysis_layer.result_formatter import format_result

    # Test text format
    text_result = format_result(sample_basic_statistics, "text")
    assert isinstance(text_result, str)
    assert "Basic Statistics Summary" in text_result

    # Test JSON format
    json_result = format_result(sample_basic_statistics, "json")
    assert isinstance(json_result, str)
    parsed = json.loads(json_result)
    assert parsed["total_records"] == 5

    # Test with unknown format
    with pytest.raises(ValueError):
        format_result(sample_basic_statistics, "unknown_format")
