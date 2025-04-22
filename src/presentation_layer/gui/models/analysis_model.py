from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from typing import Any, List
import pandas as pd

from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any

class AnalysisType(Enum):
    """Enum for different types of analysis."""
    BASIC = auto()
    CONTACT = auto()
    TIME = auto()
    PATTERN = auto()
    CUSTOM = auto()

@dataclass
class BasicAnalysisData:
    """Data structure for basic analysis results."""
    total_records: int
    date_range: Optional[Dict[str, Any]] = None
    top_contacts: Optional[List[Dict[str, Any]]] = None
    message_types: Optional[Dict[str, int]] = None
    duration_stats: Optional[Dict[str, Any]] = None

@dataclass
class ContactAnalysisData:
    """Data structure for contact analysis results."""
    contact_count: int
    contact_relationships: Optional[List[Dict[str, Any]]] = None
    conversation_flow: Optional[Dict[str, Any]] = None
    contact_importance: Optional[List[Dict[str, Any]]] = None

@dataclass
class TimeAnalysisData:
    """Data structure for time analysis results."""
    time_distribution: Optional[Dict[str, Any]] = None
    hourly_patterns: Optional[Dict[int, int]] = None
    daily_patterns: Optional[Dict[str, int]] = None
    monthly_patterns: Optional[Dict[str, int]] = None
    response_times: Optional[Dict[str, Any]] = None

@dataclass
class PatternAnalysisData:
    """Data structure for pattern analysis results."""
    detected_patterns: Optional[List[Dict[str, Any]]] = None
    anomalies: Optional[List[Dict[str, Any]]] = None
    predictions: Optional[Dict[str, Any]] = None

class AnalysisResult:
    """
    Immutable analysis result data structure.
    Thread-safe, validated, and ready for use in Qt models.
    """
    def __init__(self, result_type: AnalysisType, data: pd.DataFrame,
                 specific_data: Optional[Union[BasicAnalysisData, ContactAnalysisData,
                                              TimeAnalysisData, PatternAnalysisData]] = None):
        self._result_type = result_type
        self._data = data.copy(deep=True)
        self._specific_data = specific_data
        self._validate()

    @property
    def result_type(self) -> AnalysisType:
        return self._result_type

    @property
    def data(self) -> pd.DataFrame:
        return self._data.copy(deep=True)

    @property
    def specific_data(self) -> Optional[Union[BasicAnalysisData, ContactAnalysisData,
                                            TimeAnalysisData, PatternAnalysisData]]:
        return self._specific_data

    def _validate(self):
        if not isinstance(self._data, pd.DataFrame):
            raise ValueError("AnalysisResult data must be a pandas DataFrame.")
        if self._data.empty:
            raise ValueError("AnalysisResult data must not be empty.")
        if self._specific_data is not None:
            # Validate that specific_data matches result_type
            if self._result_type == AnalysisType.BASIC and not isinstance(self._specific_data, BasicAnalysisData):
                raise ValueError("Basic analysis must use BasicAnalysisData.")
            elif self._result_type == AnalysisType.CONTACT and not isinstance(self._specific_data, ContactAnalysisData):
                raise ValueError("Contact analysis must use ContactAnalysisData.")
            elif self._result_type == AnalysisType.TIME and not isinstance(self._specific_data, TimeAnalysisData):
                raise ValueError("Time analysis must use TimeAnalysisData.")
            elif self._result_type == AnalysisType.PATTERN and not isinstance(self._specific_data, PatternAnalysisData):
                raise ValueError("Pattern analysis must use PatternAnalysisData.")

class AnalysisResultModel(QAbstractItemModel):
    """
    QAbstractItemModel for displaying analysis results in Qt views.
    Immutable and thread-safe.
    """
    def __init__(self, analysis_result: AnalysisResult, parent=None):
        super().__init__(parent)
        self._result = analysis_result
        self._data = self._result.data
        self._columns = list(self._data.columns)
        self._specific_data = self._result.specific_data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        return str(self._data.iloc[index.row(), index.column()])

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._columns[section]
        else:
            return str(section)

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column)

    def parent(self, index):
        return QModelIndex()

    @property
    def analysis_type(self) -> AnalysisType:
        return self._result.result_type

    @property
    def specific_data(self):
        return self._specific_data

    def get_summary_data(self) -> Dict[str, Any]:
        """Get a summary of the analysis results as a dictionary."""
        summary = {
            'analysis_type': self._result.result_type.name,
            'row_count': len(self._data),
            'column_count': len(self._columns)
        }

        # Add specific data based on analysis type
        if self._specific_data is not None:
            if isinstance(self._specific_data, BasicAnalysisData):
                summary.update({
                    'total_records': self._specific_data.total_records,
                    'date_range': self._specific_data.date_range,
                    'top_contacts': self._specific_data.top_contacts,
                    'message_types': self._specific_data.message_types
                })
            elif isinstance(self._specific_data, ContactAnalysisData):
                summary.update({
                    'contact_count': self._specific_data.contact_count,
                    'contact_relationships': self._specific_data.contact_relationships,
                    'contact_importance': self._specific_data.contact_importance
                })
            elif isinstance(self._specific_data, TimeAnalysisData):
                summary.update({
                    'time_distribution': self._specific_data.time_distribution,
                    'hourly_patterns': self._specific_data.hourly_patterns,
                    'daily_patterns': self._specific_data.daily_patterns,
                    'monthly_patterns': self._specific_data.monthly_patterns
                })
            elif isinstance(self._specific_data, PatternAnalysisData):
                summary.update({
                    'detected_patterns': self._specific_data.detected_patterns,
                    'anomalies': self._specific_data.anomalies,
                    'predictions': self._specific_data.predictions
                })

        return summary
