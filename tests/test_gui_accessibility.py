#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUI Accessibility Tests

This module contains tests for accessibility features of the GUI components.
"""

import sys
import os
import pytest
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from src.presentation_layer.gui.views.main_window import MainWindow
from src.presentation_layer.gui.views.file_view import FileView
from src.presentation_layer.gui.views.analysis_view import AnalysisView
from src.presentation_layer.gui.views.results_view import ResultsView
from src.presentation_layer.gui.views.visualization_view import VisualizationView


@pytest.fixture
def qapp(qtbot):
    """Create a QApplication fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_tab_order_main_window(qtbot):
    """Test the tab order in the main window."""
    # Create the main window
    window = MainWindow()
    qtbot.addWidget(window)
    
    # Get all focusable widgets
    focusable_widgets = []
    
    def collect_focusable_widgets(widget):
        if widget.focusPolicy() != Qt.NoFocus and widget.isEnabled():
            focusable_widgets.append(widget)
        
        for child in widget.findChildren(QWidget):
            collect_focusable_widgets(child)
    
    collect_focusable_widgets(window)
    
    # Check that there are focusable widgets
    assert len(focusable_widgets) > 0
    
    # Test tab navigation
    window.setFocus()
    
    # Simulate tabbing through all widgets
    for _ in range(len(focusable_widgets) * 2):
        qtbot.keyClick(window, Qt.Key_Tab)


def test_keyboard_navigation_file_view(qtbot):
    """Test keyboard navigation in the file view."""
    # Create the file view
    view = FileView()
    qtbot.addWidget(view)
    
    # Set focus to the select file button
    view.select_file_button.setFocus()
    
    # Check that the button has focus
    assert view.select_file_button.hasFocus()
    
    # Simulate pressing Enter to activate the button
    qtbot.keyClick(view.select_file_button, Qt.Key_Return)


def test_keyboard_navigation_analysis_view(qtbot):
    """Test keyboard navigation in the analysis view."""
    # Create the analysis view
    view = AnalysisView()
    qtbot.addWidget(view)
    
    # Set focus to the analysis type combo
    view.analysis_type_combo.setFocus()
    
    # Check that the combo has focus
    assert view.analysis_type_combo.hasFocus()
    
    # Simulate pressing Down to open the dropdown
    qtbot.keyClick(view.analysis_type_combo, Qt.Key_Down)
    
    # Tab to the run button
    qtbot.keyClick(view, Qt.Key_Tab)
    qtbot.keyClick(view, Qt.Key_Tab)
    qtbot.keyClick(view, Qt.Key_Tab)
    
    # Check that the run button has focus
    assert view.run_button.hasFocus()
    
    # Simulate pressing Enter to activate the button
    qtbot.keyClick(view.run_button, Qt.Key_Return)


def test_keyboard_navigation_results_view(qtbot):
    """Test keyboard navigation in the results view."""
    # Create the results view
    view = ResultsView()
    qtbot.addWidget(view)
    
    # Set some test data
    headers = ["Name", "Value", "Type"]
    data = [
        ["Item 1", "100", "Type A"],
        ["Item 2", "200", "Type B"]
    ]
    view.set_results(headers, data)
    
    # Set focus to the filter input
    view.filter_input.setFocus()
    
    # Check that the filter input has focus
    assert view.filter_input.hasFocus()
    
    # Simulate typing in the filter input
    qtbot.keyClicks(view.filter_input, "Type")
    
    # Check that the filter was applied
    assert view.filter_input.text() == "Type"
    
    # Tab to the results table
    qtbot.keyClick(view, Qt.Key_Tab)
    qtbot.keyClick(view, Qt.Key_Tab)
    
    # Check that the results table has focus
    assert view.results_table.hasFocus()
    
    # Simulate pressing Down to navigate the table
    qtbot.keyClick(view.results_table, Qt.Key_Down)


def test_keyboard_navigation_visualization_view(qtbot):
    """Test keyboard navigation in the visualization view."""
    # Create the visualization view
    view = VisualizationView()
    qtbot.addWidget(view)
    
    # Set some test data
    data = {
        "Category 1": 100,
        "Category 2": 200
    }
    view.set_data(data, "Test Chart", "Categories", "Values")
    
    # Set focus to the chart type combo
    view.chart_type_combo.setFocus()
    
    # Check that the combo has focus
    assert view.chart_type_combo.hasFocus()
    
    # Simulate pressing Down to open the dropdown
    qtbot.keyClick(view.chart_type_combo, Qt.Key_Down)
    
    # Tab to the export button
    qtbot.keyClick(view, Qt.Key_Tab)
    
    # Check that the export button has focus
    assert view.export_button.hasFocus()
    
    # Simulate pressing Enter to activate the button
    qtbot.keyClick(view.export_button, Qt.Key_Return)


def test_tooltips(qtbot):
    """Test that important controls have tooltips."""
    # Create the views
    file_view = FileView()
    analysis_view = AnalysisView()
    results_view = ResultsView()
    visualization_view = VisualizationView()
    
    # Check file view tooltips
    assert file_view.select_file_button.toolTip() != ""
    
    # Check analysis view tooltips
    assert analysis_view.run_button.toolTip() != ""
    assert analysis_view.cancel_button.toolTip() != ""
    
    # Check results view tooltips
    assert results_view.export_button.toolTip() != ""
    assert results_view.filter_input.toolTip() != ""
    
    # Check visualization view tooltips
    assert visualization_view.export_button.toolTip() != ""
    assert visualization_view.chart_type_combo.toolTip() != ""


if __name__ == "__main__":
    pytest.main(["-v", __file__])
