import pytest
from PySide6.QtWidgets import QApplication
from src.presentation_layer.gui.utils.error_handler import ErrorHandler, ErrorSeverity

@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

class DummyComponent:
    def __init__(self):
        self.error_handler = ErrorHandler("DummyComponent")

    def fail(self):
        self.error_handler.log(
            ErrorSeverity.ERROR,
            "test_operation",
            "Sensitive info: C:/Users/user/secret.txt, user: JohnDoe, john@example.com, 555-123-4567, 1234-5678-9012-3456",
            user_message="Something went wrong. Please try again."
        )

def test_error_handler_sanitization(qt_app, caplog):
    dummy = DummyComponent()
    with caplog.at_level("ERROR"):
        dummy.fail()
    log_output = caplog.text
    assert "[REDACTED_PATH]" in log_output
    assert "[REDACTED_EMAIL]" in log_output
    assert "[REDACTED_PHONE]" in log_output
    assert "[REDACTED_CREDITCARD]" in log_output
    assert "user:[REDACTED]" in log_output
    assert "Sensitive info" not in log_output  # Should be sanitized
    assert "C:/Users/user/secret.txt" not in log_output
    assert "john@example.com" not in log_output
    assert "555-123-4567" not in log_output
    assert "1234-5678-9012-3456" not in log_output

def test_error_handler_user_message(qt_app, monkeypatch):
    dummy = DummyComponent()
    # Patch QMessageBox.exec to avoid blocking
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.exec", lambda self: None)
    dummy.error_handler.show_user_error("Test user message", ErrorSeverity.WARNING)
    # No exception means success
