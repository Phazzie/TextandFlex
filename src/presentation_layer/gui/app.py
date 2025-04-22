import sys
import traceback
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QTimer

from src.presentation_layer.gui.controllers.file_controller import FileController
from src.presentation_layer.gui.controllers.analysis_controller import AnalysisController
from src.presentation_layer.gui.controllers.app_controller import AppController
from src.presentation_layer.gui.utils.error_handler import ErrorHandler, ErrorSeverity
from src.presentation_layer.gui.views.main_window import MainWindow
from src.presentation_layer.gui.views.file_view import FileView
from src.presentation_layer.gui.views.analysis_view import AnalysisView
from src.presentation_layer.gui.views.results_view import ResultsView
from src.presentation_layer.gui.views.visualization_view import VisualizationView

# Import real analyzers
from src.data_layer.repository import PhoneRecordRepository
from src.data_layer.excel_parser import ExcelParser
from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
from src.analysis_layer.contact_analysis import ContactAnalyzer
from src.analysis_layer.time_analysis import TimeAnalyzer
from src.analysis_layer.pattern_detector import PatternDetector

def show_error_dialog(title, message):
    """Show an error dialog with the given title and message."""
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Critical)
    error_box.setWindowTitle(title)
    error_box.setText(message)
    error_box.setStandardButtons(QMessageBox.Ok)
    error_box.exec()

def main():
    """Main entry point for the GUI application."""
    # Create the Qt Application
    app = QApplication(sys.argv)

    try:
        # Initialize data layer components
        repository = PhoneRecordRepository()
        parser = ExcelParser()

        # Initialize analysis layer components
        basic_analyzer = BasicStatisticsAnalyzer()
        contact_analyzer = ContactAnalyzer()
        time_analyzer = TimeAnalyzer()
        pattern_detector = PatternDetector()

        # Initialize controllers
        file_controller = FileController(repository=repository, parser=parser)
        analysis_controller = AnalysisController(
            basic_analyzer=basic_analyzer,
            contact_analyzer=contact_analyzer,
            time_analyzer=time_analyzer,
            pattern_detector=pattern_detector
        )
        app_controller = AppController(file_controller, analysis_controller)

        # Initialize views
        main_window = MainWindow()
        file_view = FileView()
        analysis_view = AnalysisView()
        results_view = ResultsView()
        visualization_view = VisualizationView()

        # Add views to main window
        main_window.add_view(file_view, "file_view")
        main_window.add_view(analysis_view, "analysis_view")
        main_window.add_view(results_view, "results_view")
        main_window.add_view(visualization_view, "visualization_view")

        # Connect signals and slots
        # File view connections
        file_view.file_selected.connect(file_controller.load_file)
        file_controller.file_loaded.connect(lambda file_model: main_window.show_view("analysis_view"))
        file_controller.file_load_failed.connect(lambda error: show_error_dialog("File Load Error", error))

        # Analysis view connections
        analysis_view.analysis_requested.connect(lambda analysis_type, options:
            analysis_controller.run_analysis(analysis_type, file_controller.current_file_model, options))
        analysis_controller.analysis_started.connect(lambda msg: analysis_view.set_progress_message(msg))
        analysis_controller.analysis_progress.connect(lambda percent: analysis_view.set_progress(percent))
        analysis_controller.analysis_completed.connect(lambda result: (
            results_view.set_results(result.data.columns.tolist(), result.data.values.tolist()),
            main_window.show_view("results_view")
        ))
        analysis_controller.analysis_failed.connect(lambda error: show_error_dialog("Analysis Error", error))

        # Results view connections
        results_view.visualization_requested.connect(lambda data, title: (
            visualization_view.set_data(data, title, "Categories", "Values"),
            main_window.show_view("visualization_view")
        ))

        # App controller connections
        app_controller.app_state_changed.connect(lambda state: print(f"App state changed: {state}"))
        app_controller.error_occurred.connect(lambda error: show_error_dialog("Application Error", error))

        # Show the main window with the file view
        main_window.show_view("file_view")
        main_window.show()

        # Start the application event loop
        return app.exec()

    except Exception as exc:
        # Log the error
        handler = ErrorHandler("AppEntryPoint")
        handler.log(
            ErrorSeverity.CRITICAL,
            "initialization",
            str(exc),
            user_message="Critical error during application startup. Please contact support."
        )

        # Show error dialog
        error_message = f"Critical error during application startup:\n{str(exc)}\n\nPlease check the logs for details."

        # Use QTimer to show the dialog after the event loop has started
        def show_error():
            show_error_dialog("Application Error", error_message)
            QTimer.singleShot(0, lambda: sys.exit(1))

        QTimer.singleShot(0, show_error)
        return app.exec()

if __name__ == "__main__":
    sys.exit(main())
