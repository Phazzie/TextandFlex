#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUI Application

This module implements the main GUI application using PySide6.
It integrates all the UI components and connects them to the application logic.
"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, Qt

# Import views
from .views.main_window import MainWindow
from .views.file_view import FileView
from .views.analysis_view import AnalysisView
from .views.results_view import ResultsView
from .views.visualization_view import VisualizationView

# Mock controllers for testing
class MockFileController:
    """Mock file controller for testing."""

    def load_file(self, file_path):
        """
        Load a file.

        Args:
            file_path (str): The path to the file

        Returns:
            dict: The loaded data
        """
        print(f"Loading file: {file_path}")
        return {"record_count": 100}


class MockAnalysisController:
    """Mock analysis controller for testing."""

    def run_analysis(self, analysis_type, options):
        """
        Run an analysis.

        Args:
            analysis_type (str): The type of analysis to run
            options (dict): The analysis options

        Returns:
            dict: The analysis results
        """
        print(f"Running {analysis_type} analysis with options: {options}")

        # Simulate a delay
        QTimer.singleShot(1000, lambda: self.on_progress(25, "Processing data..."))
        QTimer.singleShot(2000, lambda: self.on_progress(50, "Analyzing..."))
        QTimer.singleShot(3000, lambda: self.on_progress(75, "Generating results..."))
        QTimer.singleShot(4000, lambda: self.on_progress(100, "Complete"))

        # Simulate results
        QTimer.singleShot(4000, self.on_analysis_complete)

    def on_progress(self, value, status):
        """
        Handle progress updates.

        Args:
            value (int): The progress value (0-100)
            status (str): The status message
        """
        if hasattr(self, "progress_callback"):
            self.progress_callback(value, status)

    def on_analysis_complete(self):
        """Handle analysis completion."""
        if hasattr(self, "complete_callback"):
            # Generate mock results based on the analysis type
            headers = ["Category", "Value", "Percentage"]
            data = [
                ["Category 1", "100", "20%"],
                ["Category 2", "150", "30%"],
                ["Category 3", "75", "15%"],
                ["Category 4", "175", "35%"]
            ]

            # Generate mock visualization data
            viz_data = {
                "Category 1": 100,
                "Category 2": 150,
                "Category 3": 75,
                "Category 4": 175
            }

            self.complete_callback(headers, data, viz_data)


class Application:
    """
    Main GUI application.

    This class implements the main GUI application, integrating all the UI
    components and connecting them to the application logic.
    """

    def __init__(self):
        """Initialize the application."""
        # Create the Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("TextandFlex Phone Analyzer")
        self.app.setOrganizationName("TextandFlex")

        # Create the main window
        self.main_window = MainWindow()

        # Create the views
        self.file_view = FileView()
        self.analysis_view = AnalysisView()
        self.results_view = ResultsView()
        self.visualization_view = VisualizationView()

        # Add the views to the main window
        self.main_window.add_view(self.file_view, "file_view")
        self.main_window.add_view(self.analysis_view, "analysis_view")
        self.main_window.add_view(self.results_view, "results_view")
        self.main_window.add_view(self.visualization_view, "visualization_view")

        # Show the file view initially
        self.main_window.show_view("file_view")

        # Create the controllers
        self.file_controller = MockFileController()
        self.analysis_controller = MockAnalysisController()

        # Connect signals and slots
        self._connect_signals()

    def _connect_signals(self):
        """Connect signals and slots."""
        # Main window signals
        self.main_window.file_opened.connect(self.on_file_opened)
        self.main_window.analysis_requested.connect(self.on_analysis_requested)

        # File view signals
        self.file_view.file_selected.connect(self.on_file_selected)

        # Analysis view signals
        self.analysis_view.analysis_requested.connect(self.on_analysis_requested)

        # Results view signals
        self.results_view.export_requested.connect(self.on_export_requested)

        # Visualization view signals
        self.visualization_view.export_requested.connect(self.on_export_requested)

        # Controller callbacks
        self.analysis_controller.progress_callback = self.on_analysis_progress
        self.analysis_controller.complete_callback = self.on_analysis_complete

    def on_file_opened(self, file_path):
        """
        Handle file opened event.

        Args:
            file_path (str): The path to the opened file
        """
        # Show the file view
        self.main_window.show_view("file_view")

        # Set the file in the file view
        self.file_view._set_file(file_path)

    def on_file_selected(self, file_path):
        """
        Handle file selected event.

        Args:
            file_path (str): The path to the selected file
        """
        # Load the file
        data = self.file_controller.load_file(file_path)

        # Update the file view with the record count
        self.file_view.set_record_count(data["record_count"])

        # Show the analysis view
        self.main_window.show_view("analysis_view")

    def on_analysis_requested(self, analysis_type, options):
        """
        Handle analysis requested event.

        Args:
            analysis_type (str): The type of analysis to run
            options (dict): The analysis options
        """
        # Run the analysis
        self.analysis_controller.run_analysis(analysis_type, options)

    def on_analysis_progress(self, value, status):
        """
        Handle analysis progress event.

        Args:
            value (int): The progress value (0-100)
            status (str): The status message
        """
        # Update the analysis view
        self.analysis_view.set_progress(value, status)

    def on_analysis_complete(self, headers, data, viz_data):
        """
        Handle analysis complete event.

        Args:
            headers (list): The column headers for the results
            data (list): The data rows for the results
            viz_data (dict): The visualization data
        """
        # Update the results view
        self.results_view.set_results(headers, data)

        # Update the visualization view
        self.visualization_view.set_data(
            viz_data,
            "Analysis Results",
            "Categories",
            "Values"
        )

        # Show the results view
        self.main_window.show_view("results_view")

    def on_export_requested(self, export_format, file_path):
        """
        Handle export requested event.

        Args:
            export_format (str): The format to export to
            file_path (str): The path to export to
        """
        # Show a message box
        QMessageBox.information(
            self.main_window,
            "Export Requested",
            f"Export requested in {export_format} format to {file_path}"
        )

    def run(self):
        """Run the application."""
        # Show the main window
        self.main_window.show()

        # Run the application
        return self.app.exec()


def main():
    """Main entry point."""
    # Create and run the application
    app = Application()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())