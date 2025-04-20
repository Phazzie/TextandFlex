"""
Exceptions Module
--------------
Custom exceptions for the data layer.
"""

class DataLayerError(Exception):
    """Base exception for all data layer errors."""
    pass


class DatasetError(DataLayerError):
    """Base exception for dataset-related errors."""
    pass


class DatasetNotFoundError(DatasetError):
    """Exception raised when a dataset is not found."""
    def __init__(self, dataset_name, message=None):
        self.dataset_name = dataset_name
        self.message = message or f"Dataset '{dataset_name}' not found"
        super().__init__(self.message)


class DatasetExistsError(DatasetError):
    """Exception raised when trying to create a dataset that already exists."""
    def __init__(self, dataset_name, message=None):
        self.dataset_name = dataset_name
        self.message = message or f"Dataset '{dataset_name}' already exists"
        super().__init__(self.message)


class DatasetSaveError(DatasetError):
    """Exception raised when a dataset cannot be saved."""
    def __init__(self, dataset_name, cause=None):
        self.dataset_name = dataset_name
        self.cause = cause
        message = f"Failed to save dataset '{dataset_name}'"
        if cause:
            message += f": {str(cause)}"
        self.message = message
        super().__init__(self.message)


class DatasetLoadError(DatasetError):
    """Exception raised when a dataset cannot be loaded."""
    def __init__(self, dataset_name, cause=None):
        self.dataset_name = dataset_name
        self.cause = cause
        message = f"Failed to load dataset '{dataset_name}'"
        if cause:
            message += f": {str(cause)}"
        self.message = message
        super().__init__(self.message)


class MetadataError(DataLayerError):
    """Base exception for metadata-related errors."""
    pass


class MetadataSaveError(MetadataError):
    """Exception raised when metadata cannot be saved."""
    def __init__(self, cause=None):
        self.cause = cause
        message = "Failed to save repository metadata"
        if cause:
            message += f": {str(cause)}"
        self.message = message
        super().__init__(self.message)


class MetadataLoadError(MetadataError):
    """Exception raised when metadata cannot be loaded."""
    def __init__(self, cause=None):
        self.cause = cause
        message = "Failed to load repository metadata"
        if cause:
            message += f": {str(cause)}"
        self.message = message
        super().__init__(self.message)


class QueryError(DataLayerError):
    """Base exception for query-related errors."""
    pass


class InvalidQueryError(QueryError):
    """Exception raised when a query is invalid."""
    pass


class DateParseError(QueryError):
    """Exception raised when a date cannot be parsed."""
    def __init__(self, date_str, cause=None):
        self.date_str = date_str
        self.cause = cause
        message = f"Failed to parse date '{date_str}'"
        if cause:
            message += f": {str(cause)}"
        self.message = message
        super().__init__(self.message)


class ColumnNotFoundError(QueryError):
    """Exception raised when a column is not found in a dataset."""
    def __init__(self, column_name, dataset_name=None):
        self.column_name = column_name
        self.dataset_name = dataset_name
        message = f"Column '{column_name}' not found"
        if dataset_name:
            message += f" in dataset '{dataset_name}'"
        self.message = message
        super().__init__(self.message)


class IndexError(DataLayerError):
    """Base exception for index-related errors."""
    pass


class IndexNotFoundError(IndexError):
    """Exception raised when an index is not found."""
    def __init__(self, column_name, dataset_name=None):
        self.column_name = column_name
        self.dataset_name = dataset_name
        message = f"Index for column '{column_name}' not found"
        if dataset_name:
            message += f" in dataset '{dataset_name}'"
        self.message = message
        super().__init__(self.message)


class ValidationError(DataLayerError):
    """Exception raised when validation fails."""
    def __init__(self, message, field=None):
        self.field = field
        self.message = message
        if field:
            self.message = f"Validation error for field '{field}': {message}"
        super().__init__(self.message)
