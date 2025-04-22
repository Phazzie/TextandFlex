"""
Integration test for the VisualizationView and VisualizationController.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from src.presentation_layer.gui.controllers.visualization_controller import VisualizationController
from src.presentation_layer.gui.views.visualization_view import VisualizationView

from tests.utils.gui_test_helpers import click_button


@pytest.fixture
def app(qtbot):
    """Create a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def sample_data():
    """Create sample data for visualization."""
    return {
        'A': 10,
        'B': 20,
        'C': 30,
        'D': 40,
        'E': 50
    }


@pytest.mark.integration
def test_visualization_view_controller_integration(app, qtbot, sample_data):
    """Test the integration between VisualizationView and VisualizationController."""
    # Create the controller
    visualization_controller = VisualizationController()
    
    # Create the view with the controller
    visualization_view = VisualizationView(visualization_controller=visualization_controller)
    
    # Show the view
    visualization_view.show()
    qtbot.addWidget(visualization_view)
    
    # Set the data in the controller
    visualization_controller.set_data(
        sample_data,
        title="Test Visualization",
        x_label="Categories",
        y_label="Values"
    )
    
    # Set the data in the view
    visualization_view.set_data(
        sample_data,
        title="Test Visualization",
        x_label="Categories",
        y_label="Values"
    )
    
    # Verify the data was set
    assert visualization_view.current_data == sample_data
    assert visualization_view.current_title == "Test Visualization"
    assert visualization_view.current_x_label == "Categories"
    assert visualization_view.current_y_label == "Values"
    
    # Verify the chart was created
    assert visualization_view.canvas is not None
    assert visualization_view.canvas.fig is not None


@pytest.mark.integration
def test_visualization_export_functionality(app, qtbot, sample_data, tmp_path):
    """Test the export functionality in the VisualizationView and VisualizationController integration."""
    # Create the controller
    visualization_controller = VisualizationController()
    
    # Create the view with the controller
    visualization_view = VisualizationView(visualization_controller=visualization_controller)
    
    # Show the view
    visualization_view.show()
    qtbot.addWidget(visualization_view)
    
    # Set the data in the controller
    visualization_controller.set_data(
        sample_data,
        title="Test Visualization",
        x_label="Categories",
        y_label="Values"
    )
    
    # Set the data in the view
    visualization_view.set_data(
        sample_data,
        title="Test Visualization",
        x_label="Categories",
        y_label="Values"
    )
    
    # Create a temporary file path for export
    export_path = str(tmp_path / "test_export.png")
    
    # Mock QFileDialog.getSaveFileName to return our temporary file path
    with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=(export_path, "PNG Files (*.png)")):
        # Mock QMessageBox.information to avoid showing dialogs during testing
        with patch('PySide6.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok):
            # Select PNG export format
            visualization_view.export_format_combo.setCurrentText("PNG")
            
            # Click the export button
            click_button(qtbot, visualization_view.export_button)
            
            # Wait for the export to complete
            qtbot.wait(500)
            
            # Verify the file was created
            assert os.path.exists(export_path)
            
            # Verify the file is a valid image file (check file size > 0)
            assert os.path.getsize(export_path) > 0


@pytest.mark.integration
def test_chart_type_change(app, qtbot, sample_data):
    """Test changing the chart type in the VisualizationView and VisualizationController integration."""
    # Create the controller
    visualization_controller = VisualizationController()
    
    # Create the view with the controller
    visualization_view = VisualizationView(visualization_controller=visualization_controller)
    
    # Show the view
    visualization_view.show()
    qtbot.addWidget(visualization_view)
    
    # Set the data in the controller
    visualization_controller.set_data(
        sample_data,
        title="Test Visualization",
        x_label="Categories",
        y_label="Values"
    )
    
    # Set the data in the view
    visualization_view.set_data(
        sample_data,
        title="Test Visualization",
        x_label="Categories",
        y_label="Values"
    )
    
    # Get the initial chart type
    initial_chart_type = visualization_view.chart_type_combo.currentText()
    
    # Change the chart type
    new_chart_type = "Pie" if initial_chart_type != "Pie" else "Bar"
    visualization_view.chart_type_combo.setCurrentText(new_chart_type)
    
    # Wait for the chart to update
    qtbot.wait(500)
    
    # Verify the chart type was changed
    assert visualization_view.current_type == new_chart_type.lower()
    
    # Verify the chart was updated
    assert visualization_view.canvas is not None
    assert visualization_view.canvas.fig is not None
