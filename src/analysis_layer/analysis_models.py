"""
Analysis Models Module
------------------
Data structures for analysis results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

@dataclass
class DateRangeStats:
    """Statistics about a date range."""
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    days: Optional[int] = None
    total_records: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start": self.start,
            "end": self.end,
            "days": self.days,
            "total_records": self.total_records
        }

@dataclass
class ContactStats:
    """Statistics about a contact."""
    number: str
    count: int
    percentage: float
    first_contact: Optional[datetime] = None
    last_contact: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "number": self.number,
            "count": self.count,
            "percentage": self.percentage,
            "first_contact": self.first_contact,
            "last_contact": self.last_contact
        }

@dataclass
class DurationStats:
    """Statistics about call durations."""
    total: float = 0
    average: float = 0
    median: float = 0
    max: float = 0
    min: float = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "average": self.average,
            "median": self.median,
            "max": self.max,
            "min": self.min
        }

@dataclass
class TypeStats:
    """Statistics about call/message types."""
    types: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "types": self.types
        }

@dataclass
class BasicStatistics:
    """Container for basic statistics."""
    total_records: int = 0
    date_range: Optional[DateRangeStats] = None
    top_contacts: List[ContactStats] = field(default_factory=list)
    duration_stats: Optional[DurationStats] = None
    type_stats: Optional[TypeStats] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_records": self.total_records,
            "date_range": self.date_range.to_dict() if self.date_range else None,
            "top_contacts": [contact.to_dict() for contact in self.top_contacts],
            "duration_stats": self.duration_stats.to_dict() if self.duration_stats else None,
            "type_stats": self.type_stats.to_dict() if self.type_stats else None
        }

@dataclass
class StatisticalSummary:
    """Summary of statistical analysis results."""
    mean: Optional[float] = None
    median: Optional[float] = None
    mode: Optional[Any] = None
    std_dev: Optional[float] = None
    variance: Optional[float] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mean": self.mean,
            "median": self.median,
            "mode": self.mode,
            "std_dev": self.std_dev,
            "variance": self.variance,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "count": self.count
        }

@dataclass
class AnalysisResult:
    """Container for analysis results."""
    success: bool = True
    error_message: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "error_message": self.error_message,
            "data": self.data
        }
