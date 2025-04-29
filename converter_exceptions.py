"""
Custom exceptions for the file converter.
These exceptions provide more specific error information and help with error handling.
"""

class ConverterError(Exception):
    """Base exception for all converter errors."""
    pass

class FileReadError(ConverterError):
    """Exception raised when there's an error reading the input file."""
    def __init__(self, file_path, original_error=None):
        self.file_path = file_path
        self.original_error = original_error
        message = f"Could not read file: {file_path}"
        if original_error:
            message += f" - {str(original_error)}"
        super().__init__(message)

class FileWriteError(ConverterError):
    """Exception raised when there's an error writing the output file."""
    def __init__(self, file_path, original_error=None):
        self.file_path = file_path
        self.original_error = original_error
        message = f"Could not write to file: {file_path}"
        if original_error:
            message += f" - {str(original_error)}"
        super().__init__(message)

class MissingColumnsError(ConverterError):
    """Exception raised when required columns are missing from the input file."""
    def __init__(self, missing_columns):
        self.missing_columns = missing_columns
        columns_str = ", ".join(missing_columns)
        message = f"Missing required columns: {columns_str}"
        super().__init__(message)

class DataValidationError(ConverterError):
    """Exception raised when there are data validation issues."""
    def __init__(self, validation_issues):
        self.validation_issues = validation_issues
        message = "Data validation failed"
        if validation_issues:
            message += f": {validation_issues[0]}"
            if len(validation_issues) > 1:
                message += f" (and {len(validation_issues) - 1} more issues)"
        super().__init__(message)

class DateTimeFormatError(ConverterError):
    """Exception raised when there's an error with date/time format."""
    def __init__(self, details=None, original_error=None):
        self.details = details
        self.original_error = original_error
        message = "Date/time format error"
        if details:
            message += f": {details}"
        if original_error:
            message += f" - {str(original_error)}"
        super().__init__(message)

class EmptyDataError(ConverterError):
    """Exception raised when the input file contains no data."""
    def __init__(self, file_path):
        self.file_path = file_path
        message = f"File contains no data: {file_path}"
        super().__init__(message)
