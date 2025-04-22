#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUI Integration Tests

This module contains tests for integration between GUI components.
"""

import sys
import os
import pytest
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

# Import views directly instead of using Application class
from src.presentation_layer.gui.views.main_window import MainWindow
from src.presentation_layer.gui.views.file_view import FileView
from src.presentation_layer.gui.views.analysis_view import AnalysisView
from src.presentation_layer.gui.views.results_view import ResultsView
from src.presentation_layer.gui.views.visualization_view import VisualizationView


@pytest.fixture
def qapp():
    """Create a QApplication fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qtbot):
    """Create a MainWindow fixture."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window

@pytest.fixture
def file_view(qtbot):
    """Create a FileView fixture."""
    view = FileView()
    qtbot.addWidget(view)
    return view

@pytest.fixture
def analysis_view(qtbot):
    """Create an AnalysisView fixture."""
    view = AnalysisView()
    qtbot.addWidget(view)
    return view

@pytest.fixture
def results_view(qtbot):
    """Create a ResultsView fixture."""
    view = ResultsView()
    qtbot.addWidget(view)

    # Add some test data
    headers = ["Name", "Value", "Type"]
    data = [
        ["Item 1", "100", "Type A"],
        ["Item 2", "200", "Type B"],
        ["Item 3", "300", "Type A"],
        ["Item 4", "400", "Type C"],
        ["Item 5", "500", "Type B"]
    ]
    view.set_results(headers, data)

    return view

@pytest.fixture
def visualization_view(qtbot):
    """Create a VisualizationView fixture."""
    view = VisualizationView()
    qtbot.addWidget(view)

    # Add some test data
    data = {
        "Category 1": 100,
        "Category 2": 200,
        "Category 3": 150,
        "Category 4": 300
    }
    view.set_data(data, "Test Chart", "Categories", "Values")

    return view


def test_file_view_signal(qtbot, file_view, monkeypatch):
    """Test that the file view emits the correct signal when a file is selected."""
    # Mock the QFileDialog.getOpenFileName method
    def mock_get_open_file_name(*args, **kwargs):
        return "test_file.xlsx", "Excel Files (*.xlsx)"

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_get_open_file_name)

    # Create a flag to check if the signal was emitted
    file_selected_called = False
    file_path_received = None

    # Connect to the file_selected signal
    def on_file_selected(file_path):
        nonlocal file_selected_called, file_path_received
        file_selected_called = True
        file_path_received = file_path

    file_view.file_selected.connect(on_file_selected)

    # Select a file
    file_view._set_file("test_file.xlsx")

    # Check that the signal was emitted with the correct file path
    assert file_selected_called
    assert file_path_received == "test_file.xlsx"


def test_analysis_view_signal(qtbot, analysis_view):
    """Test that the analysis view emits the correct signal when analysis is requested."""
    # Create a flag to check if the signal was emitted
    analysis_requested_called = False
    analysis_type_received = None
    options_received = None

    # Connect to the analysis_requested signal
    def on_analysis_requested(analysis_type, options):
        nonlocal analysis_requested_called, analysis_type_received, options_received
        analysis_requested_called = True
        analysis_type_received = analysis_type
        options_received = options

    analysis_view.analysis_requested.connect(on_analysis_requested)

    # Select the basic analysis type
    analysis_view.analysis_type_combo.setCurrentIndex(0)

    # Click the run button
    qtbot.mouseClick(analysis_view.run_button, Qt.LeftButton)

    # Check that the signal was emitted with the correct analysis type
    assert analysis_requested_called
    assert analysis_type_received == "basic"


def test_main_window_file_menu(qtbot, main_window, monkeypatch):
    """Test the file menu in the main window."""
    # Create a flag to check if the signal was emitted
    file_opened_called = False
    file_path_received = None

    # Connect to the file_opened signal
    def on_file_opened(file_path):
        nonlocal file_opened_called, file_path_received
        file_opened_called = True
        file_path_received = file_path

    main_window.file_opened.connect(on_file_opened)

    # Mock the QFileDialog.getOpenFileName method
    def mock_get_open_file_name(*args, **kwargs):
        return "test_file.xlsx", "Excel Files (*.xlsx)"

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_get_open_file_name)

    # Find the File menu
    file_menu = None
    for action in main_window.menuBar().actions():
        if action.text() == "&File":
            file_menu = action.menu()
            break

    assert file_menu is not None

    # Find the Open action
    open_action = None
    for action in file_menu.actions():
        if action.text() == "&Open...":
            open_action = action
            break

    assert open_action is not None

    # Trigger the Open action
    open_action.trigger()

    # Check that the signal was emitted with the correct file path
    assert file_opened_called
    assert file_path_received == "test_file.xlsx"


def test_export_functionality(qtbot, results_view, monkeypatch):
    """Test the export functionality."""
    # Create a flag to check if the signal was emitted
    export_requested_called = False
    export_format_received = None
    export_path_received = None

    # Connect to the export_requested signal
    def on_export_requested(export_format, file_path):
        nonlocal export_requested_called, export_format_received, export_path_received
        export_requested_called = True
        export_format_received = export_format
        export_path_received = file_path

    results_view.export_requested.connect(on_export_requested)

    # Mock the QFileDialog.getSaveFileName method
    def mock_get_save_file_name(*args, **kwargs):
        return "export_file.csv", "CSV Files (*.csv)"

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(QFileDialog, "getSaveFileName", mock_get_save_file_name)

    # Click the export button
    qtbot.mouseClick(results_view.export_button, Qt.LeftButton)

    # Check that the signal was emitted with the correct format and path
    assert export_requested_called
    assert export_format_received == "csv"
    assert export_path_received == "export_file.csv"


def test_visualization_chart_type(qtbot, visualization_view):
    """Test changing the chart type in the visualization view."""
    # Check initial chart type
    assert visualization_view.chart_type_combo.currentData() == "bar"

    # Change the chart type to line
    index = visualization_view.chart_type_combo.findData("line")
    visualization_view.chart_type_combo.setCurrentIndex(index)

    # Check that the chart type was changed
    assert visualization_view.chart_type_combo.currentData() == "line"

    # Change the chart type to pie
    index = visualization_view.chart_type_combo.findData("pie")
    visualization_view.chart_type_combo.setCurrentIndex(index)

    # Check that the chart type was changed
    assert visualization_view.chart_type_combo.currentData() == "pie"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
