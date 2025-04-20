"""
Tests for the analysis models module.
"""
import pytest
from datetime import datetime
from typing import Dict, List, Any

@pytest.mark.unit
def test_date_range_stats_creation():
    """Test creating a DateRangeStats object."""
    from src.analysis_layer.analysis_models import DateRangeStats
    
    # Create with default values
    stats = DateRangeStats()
    assert stats.start is None
    assert stats.end is None
    assert stats.days is None
    assert stats.total_records == 0
    
    # Create with specific values
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)
    stats = DateRangeStats(
        start=start_date,
        end=end_date,
        days=31,
        total_records=100
    )
    assert stats.start == start_date
    assert stats.end == end_date
    assert stats.days == 31
    assert stats.total_records == 100

@pytest.mark.unit
def test_date_range_stats_to_dict():
    """Test converting a DateRangeStats to a dictionary."""
    from src.analysis_layer.analysis_models import DateRangeStats
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)
    stats = DateRangeStats(
        start=start_date,
        end=end_date,
        days=31,
        total_records=100
    )
    
    result = stats.to_dict()
    assert result["start"] == start_date
    assert result["end"] == end_date
    assert result["days"] == 31
    assert result["total_records"] == 100

@pytest.mark.unit
def test_contact_stats_creation():
    """Test creating a ContactStats object."""
    from src.analysis_layer.analysis_models import ContactStats
    
    # Create with minimal values
    stats = ContactStats(
        number="1234567890",
        count=10,
        percentage=5.0
    )
    assert stats.number == "1234567890"
    assert stats.count == 10
    assert stats.percentage == 5.0
    assert stats.first_contact is None
    assert stats.last_contact is None
    
    # Create with all values
    first_contact = datetime(2023, 1, 1)
    last_contact = datetime(2023, 1, 31)
    stats = ContactStats(
        number="1234567890",
        count=10,
        percentage=5.0,
        first_contact=first_contact,
        last_contact=last_contact
    )
    assert stats.number == "1234567890"
    assert stats.count == 10
    assert stats.percentage == 5.0
    assert stats.first_contact == first_contact
    assert stats.last_contact == last_contact

@pytest.mark.unit
def test_contact_stats_to_dict():
    """Test converting a ContactStats to a dictionary."""
    from src.analysis_layer.analysis_models import ContactStats
    
    first_contact = datetime(2023, 1, 1)
    last_contact = datetime(2023, 1, 31)
    stats = ContactStats(
        number="1234567890",
        count=10,
        percentage=5.0,
        first_contact=first_contact,
        last_contact=last_contact
    )
    
    result = stats.to_dict()
    assert result["number"] == "1234567890"
    assert result["count"] == 10
    assert result["percentage"] == 5.0
    assert result["first_contact"] == first_contact
    assert result["last_contact"] == last_contact

@pytest.mark.unit
def test_duration_stats_creation():
    """Test creating a DurationStats object."""
    from src.analysis_layer.analysis_models import DurationStats
    
    # Create with default values
    stats = DurationStats()
    assert stats.total == 0
    assert stats.average == 0
    assert stats.median == 0
    assert stats.max == 0
    assert stats.min == 0
    
    # Create with specific values
    stats = DurationStats(
        total=100,
        average=10,
        median=8,
        max=30,
        min=1
    )
    assert stats.total == 100
    assert stats.average == 10
    assert stats.median == 8
    assert stats.max == 30
    assert stats.min == 1

@pytest.mark.unit
def test_duration_stats_to_dict():
    """Test converting a DurationStats to a dictionary."""
    from src.analysis_layer.analysis_models import DurationStats
    
    stats = DurationStats(
        total=100,
        average=10,
        median=8,
        max=30,
        min=1
    )
    
    result = stats.to_dict()
    assert result["total"] == 100
    assert result["average"] == 10
    assert result["median"] == 8
    assert result["max"] == 30
    assert result["min"] == 1

@pytest.mark.unit
def test_type_stats_creation():
    """Test creating a TypeStats object."""
    from src.analysis_layer.analysis_models import TypeStats
    
    # Create with default values
    stats = TypeStats()
    assert stats.types == {}
    
    # Create with specific values
    types = {"sent": 50, "received": 50}
    stats = TypeStats(types=types)
    assert stats.types == types

@pytest.mark.unit
def test_type_stats_to_dict():
    """Test converting a TypeStats to a dictionary."""
    from src.analysis_layer.analysis_models import TypeStats
    
    types = {"sent": 50, "received": 50}
    stats = TypeStats(types=types)
    
    result = stats.to_dict()
    assert result["types"] == types

@pytest.mark.unit
def test_basic_statistics_creation():
    """Test creating a BasicStatistics object."""
    from src.analysis_layer.analysis_models import BasicStatistics, DateRangeStats, ContactStats, DurationStats, TypeStats
    
    # Create with default values
    stats = BasicStatistics()
    assert stats.total_records == 0
    assert stats.date_range is None
    assert stats.top_contacts == []
    assert stats.duration_stats is None
    assert stats.type_stats is None
    
    # Create with specific values
    date_range = DateRangeStats(
        start=datetime(2023, 1, 1),
        end=datetime(2023, 1, 31),
        days=31,
        total_records=100
    )
    
    top_contacts = [
        ContactStats(
            number="1234567890",
            count=10,
            percentage=10.0,
            first_contact=datetime(2023, 1, 1),
            last_contact=datetime(2023, 1, 31)
        ),
        ContactStats(
            number="9876543210",
            count=5,
            percentage=5.0,
            first_contact=datetime(2023, 1, 5),
            last_contact=datetime(2023, 1, 25)
        )
    ]
    
    duration_stats = DurationStats(
        total=100,
        average=10,
        median=8,
        max=30,
        min=1
    )
    
    type_stats = TypeStats(
        types={"sent": 50, "received": 50}
    )
    
    stats = BasicStatistics(
        total_records=100,
        date_range=date_range,
        top_contacts=top_contacts,
        duration_stats=duration_stats,
        type_stats=type_stats
    )
    
    assert stats.total_records == 100
    assert stats.date_range == date_range
    assert stats.top_contacts == top_contacts
    assert stats.duration_stats == duration_stats
    assert stats.type_stats == type_stats

@pytest.mark.unit
def test_basic_statistics_to_dict():
    """Test converting a BasicStatistics to a dictionary."""
    from src.analysis_layer.analysis_models import BasicStatistics, DateRangeStats, ContactStats, DurationStats, TypeStats
    
    date_range = DateRangeStats(
        start=datetime(2023, 1, 1),
        end=datetime(2023, 1, 31),
        days=31,
        total_records=100
    )
    
    top_contacts = [
        ContactStats(
            number="1234567890",
            count=10,
            percentage=10.0,
            first_contact=datetime(2023, 1, 1),
            last_contact=datetime(2023, 1, 31)
        ),
        ContactStats(
            number="9876543210",
            count=5,
            percentage=5.0,
            first_contact=datetime(2023, 1, 5),
            last_contact=datetime(2023, 1, 25)
        )
    ]
    
    duration_stats = DurationStats(
        total=100,
        average=10,
        median=8,
        max=30,
        min=1
    )
    
    type_stats = TypeStats(
        types={"sent": 50, "received": 50}
    )
    
    stats = BasicStatistics(
        total_records=100,
        date_range=date_range,
        top_contacts=top_contacts,
        duration_stats=duration_stats,
        type_stats=type_stats
    )
    
    result = stats.to_dict()
    assert result["total_records"] == 100
    assert result["date_range"] == date_range.to_dict()
    assert len(result["top_contacts"]) == 2
    assert result["top_contacts"][0] == top_contacts[0].to_dict()
    assert result["top_contacts"][1] == top_contacts[1].to_dict()
    assert result["duration_stats"] == duration_stats.to_dict()
    assert result["type_stats"] == type_stats.to_dict()
