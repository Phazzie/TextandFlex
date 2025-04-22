import pytest
from pytestqt.qt_compat import qt_api
from src.presentation_layer.gui.controllers.file_controller import FileController
from src.presentation_layer.gui.utils.file_validator import FileValidationError

class DummyErrorHandler:
    def __init__(self):
        self.logged = []
    def log(self, severity, operation, message, user_message=None, exc=None):
        self.logged.append((severity, operation, message, user_message))

@pytest.fixture
def file_controller(monkeypatch):
    controller = FileController()
    # Patch error handler for testability
    dummy_handler = DummyErrorHandler()
    controller.error_handler = dummy_handler
    return controller

def test_file_validated_signal_emitted(tmp_path, file_controller, qtbot):
    file_path = tmp_path / "test.csv"
    file_path.write_text("timestamp,phone_number,message_type,message_content\n1,2,3,4\n")
    spy = qtbot.waitSignal(file_controller.file_validated, raising=False)
    file_controller.select_and_validate_file(str(file_path))
    assert spy.args[0] == str(file_path)

def test_file_validation_failed_signal_emitted(tmp_path, file_controller, qtbot):
    file_path = tmp_path / "bad.csv"
    file_path.write_text("")  # Empty file, will fail content validation
    spy = qtbot.waitSignal(file_controller.file_validation_failed, raising=False)
    file_controller.select_and_validate_file(str(file_path))
    assert "Failed to read file" in spy.args[0] or "Missing required columns" in spy.args[0]
    # Error handler should have logged the error
    assert file_controller.error_handler.logged

def test_file_validation_failed_bad_extension(tmp_path, file_controller, qtbot):
    file_path = tmp_path / "bad.txt"
    file_path.write_text("foo")
    spy = qtbot.waitSignal(file_controller.file_validation_failed, raising=False)
    file_controller.select_and_validate_file(str(file_path))
    assert "Unsupported file extension" in spy.args[0]
    assert file_controller.error_handler.logged
