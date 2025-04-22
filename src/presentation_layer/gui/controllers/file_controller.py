from PySide6.QtCore import QObject, Signal
from src.presentation_layer.gui.utils.file_validator import (
    validate_file_path,
    validate_file_content,
    FileValidationError
)
from src.presentation_layer.gui.utils.error_handler import ErrorHandler, ErrorSeverity

class FileController(QObject):
    file_validated = Signal(str)
    file_validation_failed = Signal(str)

    def __init__(self, component_name="FileController"):
        super().__init__()
        self.error_handler = ErrorHandler(component_name)

    def select_and_validate_file(self, file_path: str):
        try:
            validate_file_path(file_path)
            validate_file_content(file_path)
            self.file_validated.emit(file_path)
        except FileValidationError as exc:
            self.error_handler.log(
                ErrorSeverity.ERROR,
                "file_validation",
                str(exc),
                user_message="File validation failed. Please select a valid .xlsx or .csv file under 10MB with required columns."
            )
            self.file_validation_failed.emit(str(exc))
