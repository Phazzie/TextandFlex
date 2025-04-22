"""
Integration test for the AnalysisView and AnalysisController.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from src.presentation_layer.gui.controllers.analysis_controller import AnalysisController
from src.presentation_layer.gui.views.analysis_view import AnalysisView
from src.presentation_layer.gui.models.file_model import FileModel
from src.presentation_layer.gui.models.analysis_model import AnalysisResult, AnalysisType
from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
from src.analysis_layer.contact_analysis import ContactAnalyzer
from src.analysis_layer.time_analysis import TimeAnalyzer
from src.analysis_layer.pattern_detector import PatternDetector

from tests.utils.gui_test_helpers import create_sample_dataframe, click_button


@pytest.fixture
def app(qtbot):
    """Create a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    return create_sample_dataframe()


@pytest.fixture
def sample_file_model(sample_dataframe):
    """Create a sample file model for testing."""
    file_model = MagicMock(spec=FileModel)
    file_model.dataframe = sample_dataframe
    file_model.file_path = "test_data.xlsx"
    file_model.file_name = "test_data.xlsx"
    file_model.record_count = len(sample_dataframe)
    return file_model


@pytest.fixture
def mock_basic_analyzer():
    """Create a mock BasicStatisticsAnalyzer for testing."""
    analyzer = MagicMock(spec=BasicStatisticsAnalyzer)
    
    # Create a mock statistics result
    stats = MagicMock()
    stats.total_records = 3
    stats.date_range.start = "2023-01-01"
    stats.date_range.end = "2023-01-01"
    stats.date_range.to_dict.return_value = {"start": "2023-01-01", "end": "2023-01-01"}
    
    # Create mock contact stats
    contact = MagicMock()
    contact.number = "1234567890"
    contact.count = 2
    contact.to_dict.return_value = {"number": "1234567890", "count": 2}
    stats.top_contacts = [contact]
    
    # Create mock message type stats
    type_stat = MagicMock()
    type_stat.name = "sent"
    type_stat.count = 2
    stats.type_stats.types = [type_stat]
    
    # Set up the analyzer to return the mock stats
    analyzer.analyze.return_value = (stats, None)
    
    return analyzer


@pytest.mark.integration
def test_analysis_view_controller_integration(app, qtbot, sample_file_model, mock_basic_analyzer):
    """Test the integration between AnalysisView and AnalysisController."""
    # Create the controller with mock dependencies
    analysis_controller = AnalysisController(basic_analyzer=mock_basic_analyzer)
    
    # Create the view with the controller
    analysis_view = AnalysisView(analysis_controller=analysis_controller)
    
    # Show the view
    analysis_view.show()
    qtbot.addWidget(analysis_view)
    
    # Set the current file model
    analysis_view.set_current_file_model(sample_file_model)
    
    # Mock QMessageBox.information to avoid showing dialogs during testing
    with patch('PySide6.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok):
        # Select the basic analysis type
        analysis_view.analysis_type_combo.setCurrentText("Basic Statistics")
        
        # Click the run analysis button
        click_button(qtbot, analysis_view.run_button)
        
        # Wait for the analysis to complete
        qtbot.wait(500)
        
        # Verify the analysis was started
        assert analysis_view.run_button.isEnabled() is False
        assert analysis_view.cancel_button.isEnabled() is True
        
        # Verify the analysis was completed
        assert mock_basic_analyzer.analyze.called
        assert analysis_view.progress_bar.value() == 100
        assert analysis_view.status_label.text() == "Analysis complete"
        assert analysis_view.run_button.isEnabled() is True
        assert analysis_view.cancel_button.isEnabled() is False


@pytest.mark.integration
def test_analysis_view_controller_error_handling(app, qtbot, sample_file_model, mock_basic_analyzer):
    """Test error handling in the AnalysisView and AnalysisController integration."""
    # Create the controller with mock dependencies
    analysis_controller = AnalysisController(basic_analyzer=mock_basic_analyzer)
    
    # Set up the analyzer to return an error
    mock_basic_analyzer.analyze.return_value = (None, "Analysis failed")
    
    # Create the view with the controller
    analysis_view = AnalysisView(analysis_controller=analysis_controller)
    
    # Show the view
    analysis_view.show()
    qtbot.addWidget(analysis_view)
    
    # Set the current file model
    analysis_view.set_current_file_model(sample_file_model)
    
    # Mock QMessageBox.critical to avoid showing dialogs during testing
    with patch('PySide6.QtWidgets.QMessageBox.critical', return_value=QMessageBox.Ok):
        # Select the basic analysis type
        analysis_view.analysis_type_combo.setCurrentText("Basic Statistics")
        
        # Click the run analysis button
        click_button(qtbot, analysis_view.run_button)
        
        # Wait for the error to be handled
        qtbot.wait(500)
        
        # Verify the analysis was started
        assert mock_basic_analyzer.analyze.called
        
        # Verify the error was handled
        assert analysis_view.status_label.text() == "Analysis failed"
        assert analysis_view.run_button.isEnabled() is True
        assert analysis_view.cancel_button.isEnabled() is False


@pytest.mark.integration
def test_analysis_progress_reporting(app, qtbot, sample_file_model):
    """Test progress reporting in the AnalysisView and AnalysisController integration."""
    # Create a custom analyzer that reports progress
    class ProgressReportingAnalyzer:
        def analyze(self, df, column_mapping=None):
            # Create a mock statistics result
            stats = MagicMock()
            stats.total_records = len(df)
            stats.date_range.start = "2023-01-01"
            stats.date_range.end = "2023-01-01"
            stats.date_range.to_dict.return_value = {"start": "2023-01-01", "end": "2023-01-01"}
            
            # Create mock contact stats
            contact = MagicMock()
            contact.number = "1234567890"
            contact.count = 2
            contact.to_dict.return_value = {"number": "1234567890", "count": 2}
            stats.top_contacts = [contact]
            
            # Create mock message type stats
            type_stat = MagicMock()
            type_stat.name = "sent"
            type_stat.count = 2
            stats.type_stats.types = [type_stat]
            
            return (stats, None)
    
    # Create the controller with the custom analyzer
    analysis_controller = AnalysisController(basic_analyzer=ProgressReportingAnalyzer())
    
    # Create the view with the controller
    analysis_view = AnalysisView(analysis_controller=analysis_controller)
    
    # Show the view
    analysis_view.show()
    qtbot.addWidget(analysis_view)
    
    # Set the current file model
    analysis_view.set_current_file_model(sample_file_model)
    
    # Mock QMessageBox.information to avoid showing dialogs during testing
    with patch('PySide6.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok):
        # Select the basic analysis type
        analysis_view.analysis_type_combo.setCurrentText("Basic Statistics")
        
        # Click the run analysis button
        click_button(qtbot, analysis_view.run_button)
        
        # Manually emit progress signals
        analysis_controller.analysis_progress.emit(25)
        qtbot.wait(100)
        assert analysis_view.progress_bar.value() == 25
        
        analysis_controller.analysis_progress.emit(50)
        qtbot.wait(100)
        assert analysis_view.progress_bar.value() == 50
        
        analysis_controller.analysis_progress.emit(75)
        qtbot.wait(100)
        assert analysis_view.progress_bar.value() == 75
        
        analysis_controller.analysis_progress.emit(100)
        qtbot.wait(100)
        assert analysis_view.progress_bar.value() == 100
        
        # Verify the analysis was completed
        assert analysis_view.status_label.text() == "Analysis complete"
        assert analysis_view.run_button.isEnabled() is True
        assert analysis_view.cancel_button.isEnabled() is False
