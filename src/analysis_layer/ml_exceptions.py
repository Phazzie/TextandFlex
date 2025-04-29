"""
ML Exceptions Module
-------------------
Provides custom exceptions for the ML model components.
"""

class MLError(Exception):
    """Base exception for all ML-related errors."""
    
    def __init__(self, message: str, details: str = None):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            details: Optional details about the error
        """
        super().__init__(message)
        self.details = details
        
    def __str__(self):
        """Return string representation of the error."""
        if self.details:
            return f"{super().__str__()} - Details: {self.details}"
        return super().__str__()


class ModelError(MLError):
    """Exception for errors in ML model operations."""
    pass


class TrainingError(ModelError):
    """Exception for errors during model training."""
    pass


class PredictionError(ModelError):
    """Exception for errors during model prediction."""
    pass


class FeatureExtractionError(MLError):
    """Exception for errors during feature extraction."""
    pass


class ModelPersistenceError(MLError):
    """Exception for errors during model saving or loading."""
    pass


class InvalidModelStateError(MLError):
    """Exception for operations that require a specific model state."""
    pass
