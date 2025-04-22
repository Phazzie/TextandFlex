"""
End-to-end integration tests for the complete application flow.
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
from src.presentation_layer.gui.app import main as gui_main

from src.data_layer.repository import PhoneRecordRepository
from src.data_layer.excel_parser import ExcelParser
from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer

from tests.utils.gui_test_helpers import (
    create_sample_excel_file, wait_for, find_widget, click_button,
    enter_text, select_combo_item, select_combo_text
)


@pytest.fixture
def temp_excel_file(tmp_path):
    """Create a temporary Excel file for testing."""
    file_path = tmp_path / "test_data.xlsx"
    return create_sample_excel_file(str(file_path))


@pytest.fixture
def app(qtbot):
    """Create a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.mark.integration
def test_file_selection_to_analysis_to_results(app, qtbot, temp_excel_file, monkeypatch):
    """Test the complete end-to-end flow from file selection to analysis to results."""
    # Mock QFileDialog.getOpenFileName to return our sample file path
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (temp_excel_file, "Excel Files (*.xlsx)"))
    
    # Create controllers with real dependencies
    repository = PhoneRecordRepository()
    parser = ExcelParser()
    file_controller = FileController(repository=repository, parser=parser)
    
    basic_analyzer = BasicStatisticsAnalyzer()
    analysis_controller = AnalysisController(basic_analyzer=basic_analyzer)
    
    app_controller = AppController(file_controller, analysis_controller)
    
    # Track signal emissions
    file_loaded_called = False
    analysis_completed_called = False
    result_model = None
    
    def on_file_loaded(file_model):
        nonlocal file_loaded_called
        file_loaded_called = True
    
    def on_analysis_completed(result):
        nonlocal analysis_completed_called, result_model
        analysis_completed_called = True
        result_model = result
    
    file_controller.file_loaded.connect(on_file_loaded)
    analysis_controller.analysis_completed.connect(on_analysis_completed)
    
    # Step 1: Load the file
    file_controller.load_file(temp_excel_file)
    
    # Verify the file was loaded
    assert file_loaded_called
    assert file_controller.current_file_model is not None
    assert file_controller.current_file_model.file_path == temp_excel_file
    
    # Step 2: Run the analysis
    analysis_controller.run_analysis("basic", file_controller.current_file_model)
    
    # Wait for the analysis to complete
    import time
    time.sleep(0.5)
    
    # Verify the analysis was completed
    assert analysis_completed_called
    assert result_model is not None
    assert result_model.result_type == AnalysisType.BASIC
    assert result_model.data is not None
    assert len(result_model.data) > 0


@pytest.mark.integration
def test_error_handling_in_flow(app, qtbot, monkeypatch):
    """Test error handling in the end-to-end flow."""
    # Mock QFileDialog.getOpenFileName to return a non-existent file
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: ("non_existent.xlsx", "Excel Files (*.xlsx)"))
    
    # Create controllers
    file_controller = FileController()
    analysis_controller = AnalysisController()
    app_controller = AppController(file_controller, analysis_controller)
    
    # Track signal emissions
    file_load_failed_called = False
    error_message = None
    
    def on_file_load_failed(message):
        nonlocal file_load_failed_called, error_message
        file_load_failed_called = True
        error_message = message
    
    file_controller.file_load_failed.connect(on_file_load_failed)
    
    # Try to load a non-existent file
    file_controller.load_file("non_existent.xlsx")
    
    # Verify the error was handled correctly
    assert file_load_failed_called
    assert error_message is not None
    assert "not found" in error_message.lower() or "does not exist" in error_message.lower()


@pytest.mark.integration
def test_app_controller_state_transitions(app, qtbot):
    """Test state transitions in the AppController."""
    # Create controllers
    file_controller = FileController()
    analysis_controller = AnalysisController()
    app_controller = AppController(file_controller, analysis_controller)
    
    # Track state changes
    state_changes = []
    
    def on_state_changed(state):
        state_changes.append(state)
    
    app_controller.app_state_changed.connect(on_state_changed)
    
    # Verify initial state
    assert app_controller.current_state == "idle"
    
    # Trigger state transitions
    app_controller.set_state("loading")
    app_controller.set_state("analyzing")
    app_controller.set_state("results")
    app_controller.set_state("idle")
    
    # Verify state transitions
    assert state_changes == ["loading", "analyzing", "results", "idle"]


@pytest.mark.integration
def test_integration_with_real_data(app, qtbot, temp_excel_file, monkeypatch):
    """Test integration with real data."""
    # Mock QFileDialog.getOpenFileName to return our sample file path
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (temp_excel_file, "Excel Files (*.xlsx)"))
    
    # Create controllers with real dependencies
    repository = PhoneRecordRepository()
    parser = ExcelParser()
    file_controller = FileController(repository=repository, parser=parser)
    
    basic_analyzer = BasicStatisticsAnalyzer()
    contact_analyzer = MagicMock()  # Mock the other analyzers for simplicity
    time_analyzer = MagicMock()
    pattern_detector = MagicMock()
    
    analysis_controller = AnalysisController(
        basic_analyzer=basic_analyzer,
        contact_analyzer=contact_analyzer,
        time_analyzer=time_analyzer,
        pattern_detector=pattern_detector
    )
    
    app_controller = AppController(file_controller, analysis_controller)
    
    # Track signal emissions
    file_loaded_called = False
    analysis_started_called = False
    analysis_completed_called = False
    result_model = None
    
    def on_file_loaded(file_model):
        nonlocal file_loaded_called
        file_loaded_called = True
    
    def on_analysis_started(message):
        nonlocal analysis_started_called
        analysis_started_called = True
    
    def on_analysis_completed(result):
        nonlocal analysis_completed_called, result_model
        analysis_completed_called = True
        result_model = result
    
    file_controller.file_loaded.connect(on_file_loaded)
    analysis_controller.analysis_started.connect(on_analysis_started)
    analysis_controller.analysis_completed.connect(on_analysis_completed)
    
    # Step 1: Load the file
    file_controller.load_file(temp_excel_file)
    
    # Verify the file was loaded
    assert file_loaded_called
    assert file_controller.current_file_model is not None
    
    # Step 2: Run the analysis
    analysis_controller.run_analysis("basic", file_controller.current_file_model)
    
    # Wait for the analysis to complete
    import time
    time.sleep(0.5)
    
    # Verify the analysis was completed
    assert analysis_started_called
    assert analysis_completed_called
    assert result_model is not None
    assert result_model.result_type == AnalysisType.BASIC
    
    # Verify the result contains the expected data
    assert result_model.data is not None
    assert len(result_model.data) > 0
    assert "Metric" in result_model.data.columns
    assert "Value" in result_model.data.columns
    
    # Verify the specific data
    assert result_model.specific_data is not None
    assert result_model.specific_data.total_records == len(file_controller.current_file_model.dataframe)
    
    # Get a summary of the data
    summary = result_model.get_summary_data()
    assert summary["analysis_type"] == "BASIC"
    assert summary["row_count"] == len(result_model.data)
    assert summary["total_records"] == len(file_controller.current_file_model.dataframe)
