from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
from src.presentation_layer.gui.utils.error_handler import ErrorHandler, ErrorSeverity

class AnalysisController(QObject):
    analysis_started = Signal(str)
    analysis_completed = Signal(object)
    analysis_failed = Signal(str)

    def __init__(self, analyzer, component_name="AnalysisController"):
        super().__init__()
        self.analyzer = analyzer  # Dependency injection for testability
        self.error_handler = ErrorHandler(component_name)
        self.thread_pool = QThreadPool.globalInstance()

    def run_analysis(self, file_model):
        self.analysis_started.emit("Analysis started")
        runnable = _AnalysisTask(self.analyzer, file_model, self)
        self.thread_pool.start(runnable)

class _AnalysisTask(QRunnable):
    def __init__(self, analyzer, file_model, controller):
        super().__init__()
        self.analyzer = analyzer
        self.file_model = file_model
        self.controller = controller

    def run(self):
        try:
            result = self.analyzer.analyze(self.file_model)
            self.controller.analysis_completed.emit(result)
        except Exception as exc:
            self.controller.error_handler.log(
                ErrorSeverity.ERROR,
                "analysis_execution",
                str(exc),
                user_message="Analysis failed. Please check your input file and try again."
            )
            self.controller.analysis_failed.emit(str(exc))
