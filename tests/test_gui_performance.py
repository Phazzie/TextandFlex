#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUI Performance Tests

This module contains performance tests for the GUI components.
"""

import sys
import os
import time
import pytest
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.presentation_layer.gui.views.results_view import ResultsView
from src.presentation_layer.gui.views.visualization_view import VisualizationView
from src.presentation_layer.gui.widgets.data_table_widget import DataTableWidget


@pytest.fixture
def qapp(qtbot):
    """Create a QApplication fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def generate_large_dataset(size):
    """Generate a large dataset for testing."""
    headers = ["ID", "Name", "Value", "Type", "Description"]
    data = []
    
    for i in range(size):
        row = [
            str(i),
            f"Item {i}",
            str(i * 10),
            f"Type {i % 5}",
            f"Description for item {i}"
        ]
        data.append(row)
    
    return headers, data


def generate_large_chart_data(size):
    """Generate large chart data for testing."""
    data = {}
    
    for i in range(size):
        data[f"Category {i}"] = i * 10
    
    return data


def test_results_view_large_dataset(qtbot, benchmark):
    """Test the performance of the results view with a large dataset."""
    # Create the results view
    view = ResultsView()
    qtbot.addWidget(view)
    
    # Generate a large dataset
    headers, data = generate_large_dataset(1000)
    
    # Benchmark setting the results
    def set_results():
        view.set_results(headers, data)
    
    # Run the benchmark
    result = benchmark(set_results)
    
    # Check that the model has the correct data
    assert view.model.rowCount() == 1000
    assert view.model.columnCount() == 5
    
    # The operation should complete in a reasonable time (less than 1 second)
    assert result.stats.stats.mean < 1.0


def test_results_view_filtering_performance(qtbot, benchmark):
    """Test the performance of filtering in the results view."""
    # Create the results view
    view = ResultsView()
    qtbot.addWidget(view)
    
    # Generate a large dataset
    headers, data = generate_large_dataset(1000)
    view.set_results(headers, data)
    
    # Benchmark filtering
    def filter_results():
        view.filter_input.setText("Type 1")
        view.filter_input.clear()
    
    # Run the benchmark
    result = benchmark(filter_results)
    
    # The operation should complete in a reasonable time (less than 0.5 seconds)
    assert result.stats.stats.mean < 0.5


def test_data_table_widget_large_dataset(qtbot, benchmark):
    """Test the performance of the data table widget with a large dataset."""
    # Create the data table widget
    widget = DataTableWidget()
    qtbot.addWidget(widget)
    
    # Generate a large dataset
    headers, data = generate_large_dataset(1000)
    
    # Benchmark setting the data
    def set_data():
        widget.set_data(headers, data)
    
    # Run the benchmark
    result = benchmark(set_data)
    
    # Check that the model has the correct data
    assert widget.source_model.rowCount() == 1000
    assert widget.source_model.columnCount() == 5
    
    # The operation should complete in a reasonable time (less than 1 second)
    assert result.stats.stats.mean < 1.0


def test_visualization_view_large_dataset(qtbot, benchmark):
    """Test the performance of the visualization view with a large dataset."""
    # Create the visualization view
    view = VisualizationView()
    qtbot.addWidget(view)
    
    # Generate large chart data
    data = generate_large_chart_data(100)
    
    # Benchmark setting the data
    def set_data():
        view.set_data(data, "Test Chart", "Categories", "Values")
    
    # Run the benchmark
    result = benchmark(set_data)
    
    # Check that the data was set correctly
    assert view.current_data == data
    assert view.current_title == "Test Chart"
    
    # The operation should complete in a reasonable time (less than 2 seconds)
    assert result.stats.stats.mean < 2.0


def test_visualization_view_chart_type_change(qtbot, benchmark):
    """Test the performance of changing chart types in the visualization view."""
    # Create the visualization view
    view = VisualizationView()
    qtbot.addWidget(view)
    
    # Generate chart data
    data = generate_large_chart_data(50)
    view.set_data(data, "Test Chart", "Categories", "Values")
    
    # Benchmark changing chart types
    def change_chart_type():
        # Change to line chart
        index = view.chart_type_combo.findData("line")
        view.chart_type_combo.setCurrentIndex(index)
        
        # Change to pie chart
        index = view.chart_type_combo.findData("pie")
        view.chart_type_combo.setCurrentIndex(index)
        
        # Change back to bar chart
        index = view.chart_type_combo.findData("bar")
        view.chart_type_combo.setCurrentIndex(index)
    
    # Run the benchmark
    result = benchmark(change_chart_type)
    
    # The operation should complete in a reasonable time (less than 3 seconds)
    assert result.stats.stats.mean < 3.0


if __name__ == "__main__":
    pytest.main(["-v", "--benchmark-skip", __file__])
