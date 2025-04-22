"""
Tests for the export service.
"""
import pytest
import pandas as pd
import os
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from src.presentation_layer.services.export_service import ExportService
from src.presentation_layer.gui.models.analysis_model import (
    AnalysisResult, AnalysisType, BasicAnalysisData
)


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        "timestamp": ["2023-01-01 12:00:00", "2023-01-02 13:00:00"],
        "phone_number": ["123456789", "987654321"],
        "message_type": ["sent", "received"],
        "content": ["Hello", "Hi there"]
    })


@pytest.fixture
def sample_analysis_result(sample_dataframe):
    """Create a sample analysis result for testing."""
    return AnalysisResult(
        result_type=AnalysisType.BASIC,
        data=sample_dataframe,
        specific_data=BasicAnalysisData(
            total_records=2,
            date_range={"start": "2023-01-01", "end": "2023-01-02", "days": 1},
            top_contacts=[{"number": "123456789", "count": 1}],
            message_types={"sent": 1, "received": 1}
        )
    )


@pytest.fixture
def export_service():
    """Create an export service for testing."""
    return ExportService()


class TestExportService:
    """Tests for the ExportService class."""

    def test_export_to_csv(self, export_service, sample_analysis_result, tmp_path):
        """Test exporting to CSV."""
        # Arrange
        file_path = tmp_path / "test_export.csv"
        
        # Act
        with patch('pandas.DataFrame.to_csv') as mock_to_csv:
            result = export_service.export_to_file(
                sample_analysis_result, 
                "csv", 
                str(file_path)
            )
        
        # Assert
        assert result is True
        mock_to_csv.assert_called_once()

    def test_export_to_excel(self, export_service, sample_analysis_result, tmp_path):
        """Test exporting to Excel."""
        # Arrange
        file_path = tmp_path / "test_export.xlsx"
        
        # Act
        with patch('pandas.DataFrame.to_excel') as mock_to_excel:
            result = export_service.export_to_file(
                sample_analysis_result, 
                "excel", 
                str(file_path)
            )
        
        # Assert
        assert result is True
        mock_to_excel.assert_called_once()

    def test_export_to_json(self, export_service, sample_analysis_result, tmp_path):
        """Test exporting to JSON."""
        # Arrange
        file_path = tmp_path / "test_export.json"
        
        # Act
        with patch('pandas.DataFrame.to_json') as mock_to_json:
            result = export_service.export_to_file(
                sample_analysis_result, 
                "json", 
                str(file_path)
            )
        
        # Assert
        assert result is True
        mock_to_json.assert_called_once()

    def test_export_to_unsupported_format(self, export_service, sample_analysis_result, tmp_path):
        """Test exporting to an unsupported format."""
        # Arrange
        file_path = tmp_path / "test_export.xyz"
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            export_service.export_to_file(
                sample_analysis_result, 
                "xyz", 
                str(file_path)
            )
        
        assert "Unsupported export format" in str(exc_info.value)

    def test_export_with_invalid_file_path(self, export_service, sample_analysis_result):
        """Test exporting with an invalid file path."""
        # Arrange
        file_path = "/invalid/path/test_export.csv"
        
        # Act
        with patch('pandas.DataFrame.to_csv', side_effect=IOError("Permission denied")):
            with pytest.raises(ValueError) as exc_info:
                export_service.export_to_file(
                    sample_analysis_result, 
                    "csv", 
                    file_path
                )
        
        # Assert
        assert "Error exporting to file" in str(exc_info.value)

    def test_export_with_none_result(self, export_service, tmp_path):
        """Test exporting with None result."""
        # Arrange
        file_path = tmp_path / "test_export.csv"
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            export_service.export_to_file(
                None, 
                "csv", 
                str(file_path)
            )
        
        assert "No analysis result provided" in str(exc_info.value)

    def test_generate_report(self, export_service, sample_analysis_result, tmp_path):
        """Test generating a report."""
        # Arrange
        file_path = tmp_path / "test_report.txt"
        
        # Act
        with patch('builtins.open', mock_open()) as mock_file:
            result = export_service.generate_report(
                sample_analysis_result, 
                str(file_path)
            )
        
        # Assert
        assert result is True
        mock_file.assert_called_once_with(str(file_path), 'w', encoding='utf-8')

    def test_generate_report_with_invalid_file_path(self, export_service, sample_analysis_result):
        """Test generating a report with an invalid file path."""
        # Arrange
        file_path = "/invalid/path/test_report.txt"
        
        # Act
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(ValueError) as exc_info:
                export_service.generate_report(
                    sample_analysis_result, 
                    file_path
                )
        
        # Assert
        assert "Error generating report" in str(exc_info.value)

    def test_get_supported_formats(self, export_service):
        """Test getting supported formats."""
        # Act
        formats = export_service.get_supported_formats()
        
        # Assert
        assert isinstance(formats, list)
        assert "csv" in formats
        assert "excel" in formats
        assert "json" in formats
