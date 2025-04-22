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

from src.presentation_layer.gui.app import Application


@pytest.fixture
def qapp(qtbot):
    """Create a QApplication fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def app(qtbot, monkeypatch):
    """Create an Application fixture with mocked file dialog."""
    # Mock the QFileDialog.getOpenFileName method
    def mock_get_open_file_name(*args, **kwargs):
        return "test_file.xlsx", "Excel Files (*.xlsx)"
    
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_get_open_file_name)
    
    # Mock the QMessageBox.information method
    def mock_information(*args, **kwargs):
        return QMessageBox.Ok
    
    monkeypatch.setattr(QMessageBox, "information", mock_information)
    
    # Create the application
    application = Application()
    qtbot.addWidget(application.main_window)
    
    return application


def test_file_to_analysis_flow(qtbot, app, monkeypatch):
    """Test the flow from file selection to analysis view."""
    # Initially, the file view should be shown
    assert app.main_window.current_view() == app.file_view
    
    # Select a file
    app.file_view._set_file("test_file.xlsx")
    
    # The analysis view should now be shown
    assert app.main_window.current_view() == app.analysis_view
    
    # The record count should be set
    assert app.file_view.record_count_edit.text() == "100"


def test_analysis_to_results_flow(qtbot, app, monkeypatch):
    """Test the flow from analysis to results view."""
    # Start with the analysis view
    app.main_window.show_view("analysis_view")
    
    # Select the basic analysis type
    app.analysis_view.analysis_type_combo.setCurrentIndex(0)
    
    # Click the run button
    qtbot.mouseClick(app.analysis_view.run_button, Qt.LeftButton)
    
    # The run button should be disabled
    assert not app.analysis_view.run_button.isEnabled()
    
    # Wait for the analysis to complete (mock controller completes in 4 seconds)
    qtbot.wait(5000)
    
    # The results view should now be shown
    assert app.main_window.current_view() == app.results_view
    
    # The results table should have data
    assert app.results_view.model.rowCount() > 0


def test_main_window_file_menu(qtbot, app, monkeypatch):
    """Test the file menu in the main window."""
    # Find the File menu
    file_menu = None
    for action in app.main_window.menuBar().actions():
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
    
    # The file view should be shown
    assert app.main_window.current_view() == app.file_view
    
    # The file path should be set
    assert app.file_view.file_path_edit.text() == "test_file.xlsx"


def test_export_functionality(qtbot, app, monkeypatch):
    """Test the export functionality."""
    # Mock the QFileDialog.getSaveFileName method
    def mock_get_save_file_name(*args, **kwargs):
        return "export_file.csv", "CSV Files (*.csv)"
    
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(QFileDialog, "getSaveFileName", mock_get_save_file_name)
    
    # Show the results view
    app.main_window.show_view("results_view")
    
    # Set some test data
    headers = ["Name", "Value", "Type"]
    data = [
        ["Item 1", "100", "Type A"],
        ["Item 2", "200", "Type B"]
    ]
    app.results_view.set_results(headers, data)
    
    # Click the export button
    qtbot.mouseClick(app.results_view.export_button, Qt.LeftButton)
    
    # The export format should be set to CSV
    assert app.results_view.export_format_combo.currentData() == "csv"


def test_visualization_integration(qtbot, app):
    """Test the visualization integration."""
    # Show the visualization view
    app.main_window.show_view("visualization_view")
    
    # Set some test data
    data = {
        "Category 1": 100,
        "Category 2": 200
    }
    app.visualization_view.set_data(data, "Test Chart", "Categories", "Values")
    
    # Check that the data was set correctly
    assert app.visualization_view.current_data == data
    assert app.visualization_view.current_title == "Test Chart"
    
    # Change the chart type to line
    index = app.visualization_view.chart_type_combo.findData("line")
    app.visualization_view.chart_type_combo.setCurrentIndex(index)
    
    # Check that the chart type was changed
    assert app.visualization_view.chart_type_combo.currentData() == "line"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
