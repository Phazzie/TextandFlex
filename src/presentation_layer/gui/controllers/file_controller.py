from PySide6.QtCore import QObject, Signal
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Any

from src.presentation_layer.gui.utils.file_validator import (
    validate_file_path,
    validate_file_content,
    FileValidationError
)
from src.presentation_layer.gui.utils.error_handler import ErrorHandler, ErrorSeverity
from src.presentation_layer.gui.models.file_model import FileModel
from src.data_layer.repository import PhoneRecordRepository
from src.data_layer.excel_parser import ExcelParser

class FileController(QObject):
    file_validated = Signal(str)
    file_validation_failed = Signal(str)
    file_loaded = Signal(object)  # Emits FileModel
    file_load_failed = Signal(str)

    def __init__(self, repository: Optional[PhoneRecordRepository] = None, parser: Optional[ExcelParser] = None, component_name="FileController"):
        super().__init__()
        self.error_handler = ErrorHandler(component_name)
        self.repository = repository or PhoneRecordRepository()
        self.parser = parser or ExcelParser()
        self.current_file_model = None

    def select_and_validate_file(self, file_path: str):
        """Validate a file path and content.

        Args:
            file_path: Path to the file to validate
        """
        try:
            validate_file_path(file_path)
            validate_file_content(file_path)
            self.file_validated.emit(file_path)
        except FileValidationError as exc:
            self.error_handler.log(
                ErrorSeverity.ERROR,
                "file_validation",
                str(exc),
                user_message="File validation failed. Please select a valid .xlsx or .csv file under 10MB with required columns."
            )
            self.file_validation_failed.emit(str(exc))

    def load_file(self, file_path: str):
        """Load a file into the repository and create a FileModel.

        Args:
            file_path: Path to the file to load
        """
        try:
            # First validate the file
            validate_file_path(file_path)
            validate_file_content(file_path)

            # Parse the file
            df, column_mapping, error = self.parser.parse_and_detect(file_path)

            if error:
                raise FileValidationError(f"Failed to parse file: {error}")

            if df is None or df.empty:
                raise FileValidationError("File contains no data")

            # Create a dataset name from the file name
            dataset_name = Path(file_path).stem

            # Add to repository
            success = self.repository.add_dataset(dataset_name, df, column_mapping)

            if not success:
                error_msg = self.repository._last_error or "Unknown error adding dataset to repository"
                raise FileValidationError(f"Failed to add dataset to repository: {error_msg}")

            # Create a FileModel
            file_model = FileModel(file_path, df)
            self.current_file_model = file_model

            # Emit the file_loaded signal
            self.file_loaded.emit(file_model)

        except (FileValidationError, Exception) as exc:
            error_msg = str(exc)
            self.error_handler.log(
                ErrorSeverity.ERROR,
                "file_load",
                error_msg,
                user_message="Failed to load file. Please check the file format and try again."
            )
            self.file_load_failed.emit(error_msg)

    def get_dataset_names(self) -> list:
        """Get a list of dataset names in the repository.

        Returns:
            List of dataset names
        """
        return list(self.repository.metadata.datasets.keys())

    def get_dataset(self, name: str) -> Optional[pd.DataFrame]:
        """Get a dataset from the repository.

        Args:
            name: Name of the dataset to get

        Returns:
            DataFrame or None if not found
        """
        dataset = self.repository.get_dataset(name)
        if dataset:
            return dataset.data
        return None
