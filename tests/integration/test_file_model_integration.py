"""
Integration tests for the FileModel with the repository.
"""
import os
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.presentation_layer.gui.models.file_model import FileModel, FileTableModel
from src.data_layer.repository import PhoneRecordRepository
from src.data_layer.excel_parser import ExcelParser
from src.presentation_layer.gui.controllers.file_controller import FileController

from tests.utils.gui_test_helpers import create_sample_excel_file


@pytest.fixture
def temp_excel_file(tmp_path):
    """Create a temporary Excel file for testing."""
    file_path = tmp_path / "test_data.xlsx"
    return create_sample_excel_file(str(file_path))


@pytest.fixture
def real_repository(tmp_path):
    """Create a real repository for testing."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir(exist_ok=True)
    return PhoneRecordRepository(storage_dir=str(repo_dir))


@pytest.mark.integration
def test_file_model_creation(temp_excel_file):
    """Test creating a FileModel from a file."""
    # Create a FileModel from the file
    file_model = FileModel(temp_excel_file)
    
    # Verify the model was created correctly
    assert file_model.file_path == temp_excel_file
    assert file_model.dataframe is not None
    assert len(file_model.dataframe) > 0
    assert "timestamp" in file_model.dataframe.columns
    assert "phone_number" in file_model.dataframe.columns
    assert "message_type" in file_model.dataframe.columns
    
    # Verify the table model was created correctly
    table_model = file_model.create_table_model()
    assert isinstance(table_model, FileTableModel)
    assert table_model.rowCount() == len(file_model.dataframe)
    assert table_model.columnCount() == len(file_model.dataframe.columns)


@pytest.mark.integration
def test_file_controller_with_repository(temp_excel_file, real_repository):
    """Test the FileController with a real repository."""
    # Create a FileController with the real repository
    parser = ExcelParser()
    file_controller = FileController(repository=real_repository, parser=parser)
    
    # Load the file
    file_controller.load_file(temp_excel_file)
    
    # Verify the file was loaded correctly
    assert file_controller.current_file_model is not None
    assert file_controller.current_file_model.file_path == temp_excel_file
    
    # Verify the dataset was added to the repository
    dataset_name = Path(temp_excel_file).stem
    assert dataset_name in real_repository.metadata.datasets
    
    # Get the dataset from the repository
    dataset = real_repository.get_dataset(dataset_name)
    assert dataset is not None
    assert len(dataset.data) == len(file_controller.current_file_model.dataframe)


@pytest.mark.integration
def test_file_controller_error_handling(tmp_path):
    """Test error handling in the FileController."""
    # Create a non-existent file path
    non_existent_file = str(tmp_path / "non_existent.xlsx")
    
    # Create a FileController
    file_controller = FileController()
    
    # Create a signal spy for the file_load_failed signal
    file_load_failed_called = False
    error_message = None
    
    def on_file_load_failed(message):
        nonlocal file_load_failed_called, error_message
        file_load_failed_called = True
        error_message = message
    
    file_controller.file_load_failed.connect(on_file_load_failed)
    
    # Try to load a non-existent file
    file_controller.load_file(non_existent_file)
    
    # Verify the error was handled correctly
    assert file_load_failed_called
    assert error_message is not None
    assert "not found" in error_message.lower() or "does not exist" in error_message.lower()


@pytest.mark.integration
def test_repository_integration_with_multiple_datasets(tmp_path, real_repository):
    """Test integration with multiple datasets in the repository."""
    # Create multiple test files
    file1 = create_sample_excel_file(str(tmp_path / "data1.xlsx"))
    file2 = create_sample_excel_file(str(tmp_path / "data2.xlsx"))
    
    # Create a FileController with the real repository
    parser = ExcelParser()
    file_controller = FileController(repository=real_repository, parser=parser)
    
    # Load the files
    file_controller.load_file(file1)
    file_controller.load_file(file2)
    
    # Verify both datasets were added to the repository
    dataset_names = file_controller.get_dataset_names()
    assert len(dataset_names) == 2
    assert Path(file1).stem in dataset_names
    assert Path(file2).stem in dataset_names
    
    # Verify we can get both datasets
    dataset1 = file_controller.get_dataset(Path(file1).stem)
    dataset2 = file_controller.get_dataset(Path(file2).stem)
    assert dataset1 is not None
    assert dataset2 is not None
