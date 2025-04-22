from PySide6.QtCore import QAbstractTableModel, Qt
from typing import List, Any
import pandas as pd
import os
from datetime import datetime

class FileModel(QAbstractTableModel):
    """
    Immutable data model for file data, thread-safe and validated on creation.
    Exposes data for QTableView and other Qt views.
    """
    def __init__(self, file_path: str, dataframe: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._data = dataframe.copy(deep=True)
        self._columns = list(self._data.columns)
        self._extract_metadata()
        self._validate()

    def _extract_metadata(self):
        """Extract metadata from the file and dataframe."""
        try:
            # File system metadata
            stat_result = os.stat(self._file_path)
            self._file_name = os.path.basename(self._file_path)
            self._file_size = stat_result.st_size
            self._modified_time = datetime.fromtimestamp(stat_result.st_mtime)
            self._creation_time = datetime.fromtimestamp(stat_result.st_ctime)
            self._file_extension = os.path.splitext(self._file_path)[1].lower()

            # DataFrame metadata
            self._row_count = len(self._data)
            self._column_count = len(self._columns)

            # Data summary statistics
            self._has_missing_values = self._data.isnull().any().any()
            self._date_range = None

            # Try to extract date range if timestamp column exists
            if 'timestamp' in self._data.columns:
                try:
                    timestamps = pd.to_datetime(self._data['timestamp'])
                    self._date_range = {
                        'start': timestamps.min().strftime('%Y-%m-%d'),
                        'end': timestamps.max().strftime('%Y-%m-%d'),
                        'days': (timestamps.max() - timestamps.min()).days
                    }
                except Exception:
                    # If conversion fails, leave date_range as None
                    pass
        except OSError:
            self._file_name = "Unknown"
            self._file_size = 0
            self._modified_time = None
            self._creation_time = None
            self._file_extension = ""
            self._row_count = len(self._data) if self._data is not None else 0
            self._column_count = len(self._columns) if self._columns is not None else 0
            self._has_missing_values = False
            self._date_range = None

    def _validate(self):
        # Fail fast: ensure required columns exist
        required = {'timestamp', 'phone_number', 'message_type', 'message_content'}
        missing = required - set(self._columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        # Optionally: add more validation here (types, nulls, etc.)

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
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

    @property
    def file_path(self):
        return self._file_path

    @property
    def file_name(self):
        return self._file_name

    @property
    def file_size(self):
        return self._file_size

    @property
    def modified_time(self):
        return self._modified_time

    @property
    def creation_time(self):
        return self._creation_time

    @property
    def file_extension(self):
        return self._file_extension

    @property
    def row_count(self):
        return self._row_count

    @property
    def column_count(self):
        return self._column_count

    @property
    def has_missing_values(self):
        return self._has_missing_values

    @property
    def date_range(self):
        return self._date_range

    @property
    def dataframe(self):
        # Expose a copy for thread safety
        return self._data.copy(deep=True)
