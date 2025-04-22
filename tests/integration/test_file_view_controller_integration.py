"""
Integration test for the FileView and FileController.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from src.presentation_layer.gui.controllers.file_controller import FileController
from src.presentation_layer.gui.views.file_view import FileView
from src.presentation_layer.gui.models.file_model import FileModel
from src.data_layer.repository import PhoneRecordRepository
from src.data_layer.excel_parser import ExcelParser

from tests.utils.gui_test_helpers import create_sample_excel_file, click_button


@pytest.fixture
def app(qtbot):
    """Create a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def temp_excel_file(tmp_path):
    """Create a temporary Excel file for testing."""
    file_path = tmp_path / "test_data.xlsx"
    return create_sample_excel_file(str(file_path))


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    repo = MagicMock(spec=PhoneRecordRepository)
    repo.add_dataset.return_value = True
    repo.metadata.datasets = {}
    return repo


@pytest.fixture
def mock_parser(tmp_path):
    """Create a mock parser for testing."""
    parser = MagicMock(spec=ExcelParser)
    
    # Create a sample dataframe
    df = pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00', '2023-01-01 12:30:00', '2023-01-01 13:00:00'],
        'phone_number': ['1234567890', '9876543210', '5551234567'],
        'message_type': ['sent', 'received', 'sent'],
        'message_content': ['Hello, world!', 'Hi there!', 'How are you?']
    })
    
    # Set up the parser to return the sample dataframe
    parser.parse_and_detect.return_value = (df, {'timestamp': 'timestamp', 'phone_number': 'phone_number', 'message_type': 'message_type', 'message_content': 'message_content'}, None)
    
    return parser


@pytest.mark.integration
def test_file_view_controller_integration(app, qtbot, temp_excel_file, mock_repository, mock_parser):
    """Test the integration between FileView and FileController."""
    # Create the controller with mock dependencies
    file_controller = FileController(repository=mock_repository, parser=mock_parser)
    
    # Create the view with the controller
    file_view = FileView(file_controller=file_controller)
    
    # Show the view
    file_view.show()
    qtbot.addWidget(file_view)
    
    # Mock QFileDialog.getOpenFileName to return our sample file path
    with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=(temp_excel_file, "Excel Files (*.xlsx)")):
        # Mock QMessageBox.information to avoid showing dialogs during testing
        with patch('PySide6.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok):
            # Click the select file button
            click_button(qtbot, file_view.select_file_button)
            
            # Wait for the file to be loaded
            qtbot.wait(500)
            
            # Verify the file was loaded
            assert file_controller.current_file_model is not None
            assert file_controller.current_file_model.file_path == temp_excel_file
            
            # Verify the file information was updated in the view
            assert file_view.file_path_edit.text() == temp_excel_file
            assert file_view.file_type_edit.text() == "Excel Spreadsheet"
            assert file_view.record_count_edit.text() == "3"


@pytest.mark.integration
def test_file_view_controller_error_handling(app, qtbot, mock_repository, mock_parser):
    """Test error handling in the FileView and FileController integration."""
    # Create the controller with mock dependencies
    file_controller = FileController(repository=mock_repository, parser=mock_parser)
    
    # Set up the parser to return an error
    mock_parser.parse_and_detect.return_value = (None, None, "Failed to parse file")
    
    # Create the view with the controller
    file_view = FileView(file_controller=file_controller)
    
    # Show the view
    file_view.show()
    qtbot.addWidget(file_view)
    
    # Mock QFileDialog.getOpenFileName to return a non-existent file
    with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=("non_existent.xlsx", "Excel Files (*.xlsx)")):
        # Mock QMessageBox.critical to avoid showing dialogs during testing
        with patch('PySide6.QtWidgets.QMessageBox.critical', return_value=QMessageBox.Ok):
            # Click the select file button
            click_button(qtbot, file_view.select_file_button)
            
            # Wait for the error to be handled
            qtbot.wait(500)
            
            # Verify the file was not loaded
            assert file_controller.current_file_model is None
            
            # Verify the file information was cleared in the view
            assert file_view.file_path_edit.text() == ""
            assert file_view.file_size_edit.text() == ""
            assert file_view.file_type_edit.text() == ""
            assert file_view.record_count_edit.text() == ""


@pytest.mark.integration
def test_drag_and_drop_integration(app, qtbot, temp_excel_file, mock_repository, mock_parser):
    """Test drag and drop integration between FileView and FileController."""
    # Create the controller with mock dependencies
    file_controller = FileController(repository=mock_repository, parser=mock_parser)
    
    # Create the view with the controller
    file_view = FileView(file_controller=file_controller)
    
    # Show the view
    file_view.show()
    qtbot.addWidget(file_view)
    
    # Mock QMessageBox.information to avoid showing dialogs during testing
    with patch('PySide6.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok):
        # Create a mock drop event
        from PySide6.QtCore import QUrl, QMimeData
        from PySide6.QtGui import QDropEvent
        
        # Create a mime data object with a URL
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(temp_excel_file)])
        
        # Create a drop event
        drop_event = QDropEvent(
            file_view.drop_area.rect().center(),
            Qt.CopyAction,
            mime_data,
            Qt.LeftButton,
            Qt.NoModifier
        )
        
        # Process the drop event
        file_view.dropEvent(drop_event)
        
        # Wait for the file to be loaded
        qtbot.wait(500)
        
        # Verify the file was loaded
        assert file_controller.current_file_model is not None
        assert file_controller.current_file_model.file_path == temp_excel_file
        
        # Verify the file information was updated in the view
        assert file_view.file_path_edit.text() == temp_excel_file
        assert file_view.file_type_edit.text() == "Excel Spreadsheet"
        assert file_view.record_count_edit.text() == "3"
