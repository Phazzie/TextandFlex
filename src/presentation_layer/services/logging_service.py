"""
Logging Service Module
-------------------
Provides centralized logging for the compatibility layer.
"""
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime


class LoggingService:
    """
    Centralized logging service for the compatibility layer.
    
    This class provides methods for logging messages at different levels
    with consistent formatting and context information.
    """
    
    def __init__(self, logger_name: str = "compatibility_layer", 
                log_level: int = logging.INFO,
                log_format: Optional[str] = None,
                log_file: Optional[str] = None):
        """
        Initialize the logging service.
        
        Args:
            logger_name: Name of the logger
            log_level: Logging level (default: INFO)
            log_format: Optional log format
            log_file: Optional log file path
        """
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)
        
        # Set default format if not provided
        if log_format is None:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(context)s - %(message)s"
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Add file handler if log file is provided
        if log_file:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Initialize context
        self.context = {}
    
    def set_context(self, **kwargs):
        """
        Set context information for logging.
        
        Args:
            **kwargs: Context key-value pairs
        """
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context information."""
        self.context.clear()
    
    def _format_context(self, additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Format context information for logging.
        
        Args:
            additional_context: Additional context for this log entry
            
        Returns:
            Formatted context string
        """
        # Combine global and additional context
        context = self.context.copy()
        if additional_context:
            context.update(additional_context)
        
        # Format context as key=value pairs
        if context:
            return ", ".join(f"{k}={v}" for k, v in context.items())
        else:
            return "-"
    
    def debug(self, message: str, **context):
        """
        Log a debug message.
        
        Args:
            message: Message to log
            **context: Additional context for this log entry
        """
        self.logger.debug(message, extra={"context": self._format_context(context)})
    
    def info(self, message: str, **context):
        """
        Log an info message.
        
        Args:
            message: Message to log
            **context: Additional context for this log entry
        """
        self.logger.info(message, extra={"context": self._format_context(context)})
    
    def warning(self, message: str, **context):
        """
        Log a warning message.
        
        Args:
            message: Message to log
            **context: Additional context for this log entry
        """
        self.logger.warning(message, extra={"context": self._format_context(context)})
    
    def error(self, message: str, **context):
        """
        Log an error message.
        
        Args:
            message: Message to log
            **context: Additional context for this log entry
        """
        self.logger.error(message, extra={"context": self._format_context(context)})
    
    def critical(self, message: str, **context):
        """
        Log a critical message.
        
        Args:
            message: Message to log
            **context: Additional context for this log entry
        """
        self.logger.critical(message, extra={"context": self._format_context(context)})
    
    def exception(self, message: str, exc: Optional[Exception] = None, **context):
        """
        Log an exception message.
        
        Args:
            message: Message to log
            exc: Optional exception to include in the log
            **context: Additional context for this log entry
        """
        if exc:
            context["exception_type"] = type(exc).__name__
            context["exception_message"] = str(exc)
        
        self.logger.exception(message, extra={"context": self._format_context(context)})
    
    def log_method_call(self, method_name: str, **kwargs):
        """
        Log a method call with parameters.
        
        Args:
            method_name: Name of the method being called
            **kwargs: Method parameters
        """
        self.debug(f"Calling {method_name}", method=method_name, params=str(kwargs))
    
    def log_method_return(self, method_name: str, result: Any):
        """
        Log a method return value.
        
        Args:
            method_name: Name of the method returning
            result: Return value (will be converted to string)
        """
        # Truncate long results
        result_str = str(result)
        if len(result_str) > 100:
            result_str = result_str[:100] + "..."
        
        self.debug(f"Returning from {method_name}", method=method_name, result=result_str)
    
    def log_method_error(self, method_name: str, error: Exception):
        """
        Log a method error.
        
        Args:
            method_name: Name of the method with error
            error: Exception that occurred
        """
        self.error(
            f"Error in {method_name}: {str(error)}",
            method=method_name,
            error_type=type(error).__name__,
            error_message=str(error)
        )
