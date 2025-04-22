# Error handling system for GUI core functionality
import logging
from datetime import datetime
from PySide6.QtWidgets import QMessageBox

class ErrorSeverity:
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorHandler:
    def __init__(self, component: str):
        self.component = component
        self.logger = logging.getLogger(component)

    def log(self, severity, operation, message, user_message=None, exc=None):
        timestamp = datetime.utcnow().isoformat()
        sanitized_message = self._sanitize(message)
        log_entry = f"{timestamp} | {self.component} | {operation} | {severity} | {sanitized_message}"
        if severity in (ErrorSeverity.ERROR, ErrorSeverity.CRITICAL):
            self.logger.error(log_entry)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(log_entry)
        else:
            self.logger.info(log_entry)
        if user_message:
            self.show_user_error(user_message, severity)

    def show_user_error(self, message, severity):
        icon = {
            ErrorSeverity.INFO: QMessageBox.Information,
            ErrorSeverity.WARNING: QMessageBox.Warning,
            ErrorSeverity.ERROR: QMessageBox.Critical,
            ErrorSeverity.CRITICAL: QMessageBox.Critical,
        }[severity]
        msg_box = QMessageBox()
        msg_box.setIcon(icon)
        msg_box.setText(message)
        msg_box.setWindowTitle(f"{severity} Error")
        msg_box.exec()

    def _sanitize(self, message):
        # Remove file paths, emails, and anything that looks like PII
        import re
        sanitized_message = str(message)
        # Remove Windows and Unix file paths
        sanitized_message = re.sub(
            r'[A-Za-z]:\\[^\s]+|/[^\s]+',
            '[REDACTED_PATH]',
            sanitized_message
        )
        # Remove email addresses
        sanitized_message = re.sub(
            r'[\w\.-]+@[\w\.-]+',
            '[REDACTED_EMAIL]',
            sanitized_message
        )
        # Remove phone numbers (simple pattern)
        sanitized_message = re.sub(
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            '[REDACTED_PHONE]',
            sanitized_message
        )
        # Remove anything that looks like a credit card (very basic)
        sanitized_message = re.sub(
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            '[REDACTED_CREDITCARD]',
            sanitized_message
        )
        # Remove user names (very basic, e.g., 'user: JohnDoe')
        sanitized_message = re.sub(
            r'user:\s*\w+',
            'user:[REDACTED]',
            sanitized_message,
            flags=re.IGNORECASE
        )
        return sanitized_message
