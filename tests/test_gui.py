#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUI Tests

This module contains tests for the GUI components.
"""

import sys
import os
import pytest
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.presentation_layer.gui.views.main_window import MainWindow
from src.presentation_layer.gui.views.file_view import FileView
from src.presentation_layer.gui.views.analysis_view import AnalysisView
from src.presentation_layer.gui.views.results_view import ResultsView
from src.presentation_layer.gui.views.visualization_view import VisualizationView
from src.presentation_layer.gui.widgets.data_table_widget import DataTableWidget


@pytest.fixture
def qapp():
    """Create a QApplication fixture."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window(qtbot):
    """Test the main window."""
    # Create the main window
    window = MainWindow()
    qtbot.addWidget(window)

    # Check that the window has the correct title
    assert window.windowTitle() == "TextandFlex Phone Analyzer"

    # Check that the window has the correct minimum size
    from src.presentation_layer.gui.stylesheets.constants import Dimensions
    assert window.minimumSize().width() >= Dimensions.MIN_WINDOW_WIDTH
    assert window.minimumSize().height() >= Dimensions.MIN_WINDOW_HEIGHT


def test_file_view(qtbot):
    """Test the file view."""
    # Create the file view
    view = FileView()
    qtbot.addWidget(view)

    # Check that the view has the correct components
    assert hasattr(view, "select_file_button")
    assert hasattr(view, "drop_area")
    assert hasattr(view, "file_path_edit")

    # Test setting the record count
    view.set_record_count(100)
    assert view.record_count_edit.text() == "100"


def test_analysis_view(qtbot):
    """Test the analysis view."""
    # Create the analysis view
    view = AnalysisView()
    qtbot.addWidget(view)

    # Check that the view has the correct components
    assert hasattr(view, "analysis_type_combo")
    assert hasattr(view, "progress_bar")
    assert hasattr(view, "run_button")

    # Test setting the progress
    view.set_progress(50, "Testing...")
    assert view.progress_bar.value() == 50
    assert view.status_label.text() == "Testing..."


def test_results_view(qtbot):
    """Test the results view."""
    # Create the results view
    view = ResultsView()
    qtbot.addWidget(view)

    # Check that the view has the correct components
    assert hasattr(view, "results_table")
    assert hasattr(view, "filter_input")
    assert hasattr(view, "export_button")

    # Test setting the results
    headers = ["Name", "Value", "Type"]
    data = [
        ["Item 1", "100", "Type A"],
        ["Item 2", "200", "Type B"]
    ]
    view.set_results(headers, data)

    # Check that the model has the correct data
    assert view.model.rowCount() == 2
    assert view.model.columnCount() == 3
    from PySide6.QtCore import Qt
    assert view.model.headerData(0, Qt.Horizontal) == "Name"
    assert view.model.headerData(1, Qt.Horizontal) == "Value"
    assert view.model.headerData(2, Qt.Horizontal) == "Type"


def test_visualization_view(qtbot):
    """Test the visualization view."""
    # Create the visualization view
    view = VisualizationView()
    qtbot.addWidget(view)

    # Check that the view has the correct components
    assert hasattr(view, "canvas")
    assert hasattr(view, "chart_type_combo")
    assert hasattr(view, "export_button")

    # Test setting the data
    data = {
        "Category 1": 100,
        "Category 2": 200
    }
    view.set_data(data, "Test Chart", "Categories", "Values")

    # Check that the data was set correctly
    assert view.current_data == data
    assert view.current_title == "Test Chart"
    assert view.current_x_label == "Categories"
    assert view.current_y_label == "Values"


def test_data_table_widget(qtbot):
    """Test the data table widget."""
    # Create the data table widget
    widget = DataTableWidget()
    qtbot.addWidget(widget)

    # Check that the widget has the correct properties
    assert widget.selectionBehavior() == 1  # QAbstractItemView.SelectRows
    assert widget.alternatingRowColors() is True

    # Test setting the data
    headers = ["Name", "Value", "Type"]
    data = [
        ["Item 1", "100", "Type A"],
        ["Item 2", "200", "Type B"]
    ]
    widget.set_data(headers, data)

    # Check that the model has the correct data
    assert widget.source_model.rowCount() == 2
    assert widget.source_model.columnCount() == 3
    from PySide6.QtCore import Qt
    assert widget.source_model.headerData(0, Qt.Horizontal) == "Name"
    assert widget.source_model.headerData(1, Qt.Horizontal) == "Value"
    assert widget.source_model.headerData(2, Qt.Horizontal) == "Type"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
