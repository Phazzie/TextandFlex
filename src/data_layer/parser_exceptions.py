"""
Custom exceptions for the data parsing module.

This module defines custom exceptions that can be raised during the parsing
and validation of phone records data.
"""


class ParserError(Exception):
    """Base exception for all parser-related errors."""
    pass


class ValidationError(ParserError):
    """Exception raised when data validation fails."""
    
    def __init__(self, message, validation_errors=None):
        """
        Initialize with a message and optional validation errors.
        
        Args:
            message: Error message
            validation_errors: DataFrame containing validation errors
        """
        super().__init__(message)
        self.validation_errors = validation_errors


class MappingError(ParserError):
    """Exception raised when column mapping fails."""
    
    def __init__(self, message, missing_columns=None):
        """
        Initialize with a message and optional missing columns.
        
        Args:
            message: Error message
            missing_columns: List of missing column names
        """
        super().__init__(message)
        self.missing_columns = missing_columns or []
