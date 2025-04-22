from PySide6.QtCore import QObject, Signal
from src.presentation_layer.gui.controllers.file_controller import FileController
from src.presentation_layer.gui.controllers.analysis_controller import AnalysisController
from src.presentation_layer.gui.utils.error_handler import ErrorHandler, ErrorSeverity

class AppController(QObject):
    app_state_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, file_controller: FileController, analysis_controller: AnalysisController, component_name="AppController"):
        super().__init__()
        self.file_controller = file_controller
        self.analysis_controller = analysis_controller
        self.error_handler = ErrorHandler(component_name)
        self._connect_signals()
        self.state = "initialized"

    def _connect_signals(self):
        self.file_controller.file_validated.connect(self.on_file_validated)
        self.file_controller.file_validation_failed.connect(self.on_file_validation_failed)
        self.analysis_controller.analysis_started.connect(self.on_analysis_started)
        self.analysis_controller.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_controller.analysis_failed.connect(self.on_analysis_failed)

    def on_file_validated(self, file_path):
        self.state = "file_validated"
        self.app_state_changed.emit(self.state)
        # Optionally trigger analysis or notify UI

    def on_file_validation_failed(self, error_msg):
        self.state = "file_validation_failed"
        self.error_occurred.emit(error_msg)

    def on_analysis_started(self, msg):
        self.state = "analysis_started"
        self.app_state_changed.emit(self.state)

    def on_analysis_completed(self, result):
        self.state = "analysis_completed"
        self.app_state_changed.emit(self.state)
        # Optionally pass result to UI

    def on_analysis_failed(self, error_msg):
        self.state = "analysis_failed"
        self.error_handler.log(
            ErrorSeverity.ERROR,
            "app_analysis_failed",
            error_msg,
            user_message="Analysis failed at application level."
        )
        self.error_occurred.emit(error_msg)
