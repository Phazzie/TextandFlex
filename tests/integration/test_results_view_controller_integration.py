"""
Integration test for the ResultsView and ResultsController.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from src.presentation_layer.gui.controllers.results_controller import ResultsController
from src.presentation_layer.gui.views.results_view import ResultsView
from src.presentation_layer.gui.models.analysis_model import AnalysisResult, AnalysisType

from tests.utils.gui_test_helpers import click_button


@pytest.fixture
def app(qtbot):
    """Create a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def sample_analysis_result():
    """Create a sample analysis result for testing."""
    # Create a sample dataframe
    df = pd.DataFrame({
        'Category': ['A', 'B', 'C', 'D', 'E'],
        'Value': [10, 20, 30, 40, 50]
    })
    
    # Create a sample analysis result
    result = AnalysisResult(
        result_type=AnalysisType.BASIC,
        data=df,
        metadata={
            'title': 'Test Analysis',
            'description': 'Test analysis description'
        }
    )
    
    return result


@pytest.mark.integration
def test_results_view_controller_integration(app, qtbot, sample_analysis_result):
    """Test the integration between ResultsView and ResultsController."""
    # Create the controller
    results_controller = ResultsController()
    
    # Create the view with the controller
    results_view = ResultsView(results_controller=results_controller)
    
    # Show the view
    results_view.show()
    qtbot.addWidget(results_view)
    
    # Set the result in the controller
    results_controller.set_result(sample_analysis_result)
    
    # Set the results in the view
    results_view.set_results(
        sample_analysis_result.data.columns.tolist(),
        sample_analysis_result.data.values.tolist()
    )
    
    # Verify the results are displayed
    assert results_view.model.rowCount() == 5
    assert results_view.model.columnCount() == 2
    assert results_view.model.data(results_view.model.index(0, 0), Qt.DisplayRole) == 'A'
    assert results_view.model.data(results_view.model.index(0, 1), Qt.DisplayRole) == '10'


@pytest.mark.integration
def test_results_export_functionality(app, qtbot, sample_analysis_result, tmp_path):
    """Test the export functionality in the ResultsView and ResultsController integration."""
    # Create the controller
    results_controller = ResultsController()
    
    # Create the view with the controller
    results_view = ResultsView(results_controller=results_controller)
    
    # Show the view
    results_view.show()
    qtbot.addWidget(results_view)
    
    # Set the result in the controller
    results_controller.set_result(sample_analysis_result)
    
    # Set the results in the view
    results_view.set_results(
        sample_analysis_result.data.columns.tolist(),
        sample_analysis_result.data.values.tolist()
    )
    
    # Create a temporary file path for export
    export_path = str(tmp_path / "test_export.csv")
    
    # Mock QFileDialog.getSaveFileName to return our temporary file path
    with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=(export_path, "CSV Files (*.csv)")):
        # Mock QMessageBox.information to avoid showing dialogs during testing
        with patch('PySide6.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok):
            # Select CSV export format
            results_view.export_format_combo.setCurrentText("CSV")
            
            # Click the export button
            click_button(qtbot, results_view.export_button)
            
            # Wait for the export to complete
            qtbot.wait(500)
            
            # Verify the file was created
            assert os.path.exists(export_path)
            
            # Verify the file contains the expected data
            exported_df = pd.read_csv(export_path)
            assert len(exported_df) == 5
            assert list(exported_df.columns) == ['Category', 'Value']
            assert exported_df['Category'].tolist() == ['A', 'B', 'C', 'D', 'E']
            assert exported_df['Value'].tolist() == [10, 20, 30, 40, 50]


@pytest.mark.integration
def test_visualization_request(app, qtbot, sample_analysis_result):
    """Test the visualization request in the ResultsView and ResultsController integration."""
    # Create the controller
    results_controller = ResultsController()
    
    # Create the view with the controller
    results_view = ResultsView(results_controller=results_controller)
    
    # Show the view
    results_view.show()
    qtbot.addWidget(results_view)
    
    # Set the result in the controller
    results_controller.set_result(sample_analysis_result)
    
    # Set the results in the view
    results_view.set_results(
        sample_analysis_result.data.columns.tolist(),
        sample_analysis_result.data.values.tolist()
    )
    
    # Create a mock to capture the visualization_requested signal
    visualization_requested_mock = MagicMock()
    results_controller.visualization_requested.connect(visualization_requested_mock)
    
    # Click the visualize button
    click_button(qtbot, results_view.visualize_button)
    
    # Wait for the signal to be emitted
    qtbot.wait(500)
    
    # Verify the signal was emitted with the expected data
    visualization_requested_mock.assert_called_once()
    args = visualization_requested_mock.call_args[0]
    
    # Check that the data is a dictionary with the expected keys
    assert isinstance(args[0], dict)
    assert 'A' in args[0]
    assert args[0]['A'] == 10
    
    # Check that the title is as expected
    assert 'Analysis Results' in args[1]
