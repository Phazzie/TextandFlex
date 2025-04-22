"""
Integration tests for the GUI components.
Tests the complete workflow from file selection to analysis to results display.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog

from src.presentation_layer.gui.controllers.file_controller import FileController
from src.presentation_layer.gui.controllers.analysis_controller import AnalysisController
from src.presentation_layer.gui.controllers.app_controller import AppController
from src.presentation_layer.gui.models.file_model import FileModel
from src.presentation_layer.gui.models.analysis_model import AnalysisResult, AnalysisType
from src.presentation_layer.gui.views.main_window import MainWindow
from src.presentation_layer.gui.views.file_view import FileView
from src.presentation_layer.gui.views.analysis_view import AnalysisView
from src.presentation_layer.gui.views.results_view import ResultsView

from src.data_layer.repository import PhoneRecordRepository
from src.data_layer.excel_parser import ExcelParser
from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer


# Fixture for a test application
@pytest.fixture
def app(qtbot):
    """Create a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


# Fixture for a sample dataframe
@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00', '2023-01-01 12:30:00', '2023-01-01 13:00:00'],
        'phone_number': ['1234567890', '9876543210', '5551234567'],
        'message_type': ['sent', 'received', 'sent'],
        'message_content': ['Hello, world!', 'Hi there!', 'How are you?']
    })


# Fixture for a sample file path
@pytest.fixture
def sample_file_path(tmp_path):
    """Create a sample file path for testing."""
    return str(tmp_path / "test_data.xlsx")


# Fixture for a mock repository
@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    repo = MagicMock(spec=PhoneRecordRepository)
    repo.add_dataset.return_value = True
    repo.metadata.datasets = {}
    return repo


# Fixture for a mock parser
@pytest.fixture
def mock_parser(sample_dataframe):
    """Create a mock parser for testing."""
    parser = MagicMock(spec=ExcelParser)
    parser.parse_and_detect.return_value = (sample_dataframe, {'timestamp': 'timestamp', 'phone_number': 'phone_number', 'message_type': 'message_type'}, None)
    return parser


# Fixture for a mock analyzer
@pytest.fixture
def mock_analyzer():
    """Create a mock analyzer for testing."""
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
def test_file_selection_to_analysis_flow(app, qtbot, sample_file_path, mock_repository, mock_parser, mock_analyzer):
    """Test the complete workflow from file selection to analysis to results display."""
    # Create controllers with mock dependencies
    file_controller = FileController(repository=mock_repository, parser=mock_parser)
    analysis_controller = AnalysisController(basic_analyzer=mock_analyzer)
    app_controller = AppController(file_controller, analysis_controller)
    
    # Create views
    main_window = MainWindow()
    file_view = FileView()
    analysis_view = AnalysisView()
    results_view = ResultsView()
    
    # Add views to main window
    main_window.add_view(file_view, "file_view")
    main_window.add_view(analysis_view, "analysis_view")
    main_window.add_view(results_view, "results_view")
    
    # Show the main window
    main_window.show()
    qtbot.addWidget(main_window)
    
    # Connect signals and slots
    file_view.file_selected.connect(file_controller.load_file)
    file_controller.file_loaded.connect(lambda file_model: main_window.show_view("analysis_view"))
    
    analysis_view.analysis_requested.connect(lambda analysis_type, options: 
        analysis_controller.run_analysis(analysis_type, file_controller.current_file_model, options))
    analysis_controller.analysis_completed.connect(lambda result: (
        results_view.set_results(result.data.columns.tolist(), result.data.values.tolist()),
        main_window.show_view("results_view")
    ))
    
    # Mock QFileDialog.getOpenFileName to return our sample file path
    with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=(sample_file_path, "Excel Files (*.xlsx)")):
        # Trigger file selection
        file_view.select_file_button.click()
        qtbot.waitForWindowShown(main_window)
        
        # Verify file was loaded
        assert file_controller.current_file_model is not None
        assert mock_parser.parse_and_detect.called
        assert mock_repository.add_dataset.called
        
        # Verify we're now on the analysis view
        assert main_window.current_view_name == "analysis_view"
        
        # Trigger analysis
        analysis_view.run_analysis_button.click()
        qtbot.wait(500)  # Wait for analysis to complete
        
        # Verify analysis was performed
        assert mock_analyzer.analyze.called
        
        # Verify we're now on the results view
        assert main_window.current_view_name == "results_view"
        
        # Verify results were set
        assert len(results_view.results_table.model().data_values) > 0


@pytest.mark.integration
def test_error_propagation(app, qtbot, sample_file_path, mock_repository, mock_parser, mock_analyzer):
    """Test error propagation across components."""
    # Create controllers with mock dependencies
    file_controller = FileController(repository=mock_repository, parser=mock_parser)
    analysis_controller = AnalysisController(basic_analyzer=mock_analyzer)
    app_controller = AppController(file_controller, analysis_controller)
    
    # Create a spy for the error signals
    file_load_failed_spy = qtbot.createSignalSpy(file_controller.file_load_failed)
    analysis_failed_spy = qtbot.createSignalSpy(analysis_controller.analysis_failed)
    
    # Test file loading error
    mock_parser.parse_and_detect.return_value = (None, None, "File parsing error")
    file_controller.load_file(sample_file_path)
    
    # Verify error signal was emitted
    assert file_load_failed_spy.count() > 0
    
    # Reset mock
    mock_parser.parse_and_detect.return_value = (pd.DataFrame(), {'timestamp': 'timestamp'}, None)
    
    # Test analysis error
    mock_analyzer.analyze.return_value = (None, "Analysis error")
    file_controller.current_file_model = FileModel(sample_file_path, pd.DataFrame())
    analysis_controller.run_analysis("basic", file_controller.current_file_model)
    
    # Verify error signal was emitted
    assert analysis_failed_spy.count() > 0


@pytest.mark.integration
def test_application_state_management(app, qtbot, sample_file_path, mock_repository, mock_parser, mock_analyzer):
    """Test application state management."""
    # Create controllers with mock dependencies
    file_controller = FileController(repository=mock_repository, parser=mock_parser)
    analysis_controller = AnalysisController(basic_analyzer=mock_analyzer)
    app_controller = AppController(file_controller, analysis_controller)
    
    # Create a spy for the app state changed signal
    app_state_changed_spy = qtbot.createSignalSpy(app_controller.app_state_changed)
    
    # Test initial state
    assert app_controller.current_state == "idle"
    
    # Test state transition to loading
    app_controller.set_state("loading")
    assert app_controller.current_state == "loading"
    assert app_state_changed_spy.count() > 0
    
    # Test state transition to analyzing
    app_controller.set_state("analyzing")
    assert app_controller.current_state == "analyzing"
    assert app_state_changed_spy.count() > 1
    
    # Test state transition to results
    app_controller.set_state("results")
    assert app_controller.current_state == "results"
    assert app_state_changed_spy.count() > 2
    
    # Test state transition back to idle
    app_controller.set_state("idle")
    assert app_controller.current_state == "idle"
    assert app_state_changed_spy.count() > 3
