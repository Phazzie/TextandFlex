"""
Integration tests for the compatibility layer.
"""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.presentation_layer.gui.models.analysis_model import AnalysisType
from src.presentation_layer.services.analysis_service import AnalysisService
from src.presentation_layer.services.application_facade import ApplicationFacade
from src.presentation_layer.services.config_manager import ConfigManager
from src.presentation_layer.services.controller_factory import ControllerFactory
from src.presentation_layer.services.export_service import ExportService
from src.presentation_layer.services.repository_service import RepositoryService


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
def temp_config_file(tmp_path):
    """Create a temporary configuration file."""
    config_file = tmp_path / "test_config.json"
    return str(config_file)


@pytest.mark.integration
class TestCompatibilityLayerIntegration:
    """Integration tests for the compatibility layer."""

    def test_end_to_end_workflow(self, sample_dataframe, temp_config_file):
        """Test an end-to-end workflow through the compatibility layer."""
        # Arrange
        # Create services with the temporary config file
        config_manager = ConfigManager(config_file=temp_config_file)
        repository_service = RepositoryService()
        analysis_service = AnalysisService()
        export_service = ExportService()

        # Create the application facade
        facade = ApplicationFacade(
            repository_service=repository_service,
            analysis_service=analysis_service,
            export_service=export_service,
            config_manager=config_manager
        )

        # Create the controller factory
        factory = ControllerFactory(application_facade=facade)

        # Act
        # 1. Add a dataset
        column_mapping = {
            "timestamp": "timestamp",
            "phone_number": "phone_number",
            "message_type": "message_type",
            "content": "content"
        }

        # Mock the repository add_dataset method to avoid actual file operations
        with patch.object(repository_service.repository, 'add_dataset', return_value=True):
            add_result = facade.add_dataset("test_dataset", sample_dataframe, column_mapping)

        # 2. Run an analysis
        # Mock the basic analyzer to avoid actual analysis
        with patch.object(analysis_service.basic_analyzer, 'analyze', return_value={
            "total_records": 2,
            "date_range": {"start": "2023-01-01", "end": "2023-01-02", "days": 1},
            "top_contacts": [{"number": "123456789", "count": 1}],
            "message_types": {"sent": 1, "received": 1}
        }):
            analysis_result = facade.run_analysis("basic", sample_dataframe)

        # 3. Export the results
        # Mock the export to avoid actual file operations
        with patch.object(export_service, 'export_to_file', return_value=True):
            export_result = facade.export_results(analysis_result, "csv", "test_export.csv")

        # 4. Create controllers
        controllers = factory.create_all_controllers()

        # Assert
        assert add_result is True
        assert analysis_result is not None
        assert analysis_result.result_type == AnalysisType.BASIC
        assert export_result is True
        assert "file_controller" in controllers
        assert "analysis_controller" in controllers
        assert "results_controller" in controllers
        assert "visualization_controller" in controllers
        assert "app_controller" in controllers

    def test_feature_flags(self, temp_config_file):
        """Test feature flags in the compatibility layer."""
        # Arrange
        config_manager = ConfigManager(config_file=temp_config_file)
        facade = ApplicationFacade(config_manager=config_manager)

        # Act
        # Enable a feature flag
        facade.set_feature_flag("experimental_ml", True)

        # Check if the feature is enabled
        is_enabled = facade.is_feature_enabled("experimental_ml")

        # Disable the feature flag
        facade.set_feature_flag("experimental_ml", False)

        # Check if the feature is disabled
        is_disabled = not facade.is_feature_enabled("experimental_ml")

        # Assert
        assert is_enabled is True
        assert is_disabled is True

    def test_error_handling(self, sample_dataframe):
        """Test error handling in the compatibility layer."""
        # Arrange
        facade = ApplicationFacade()

        # Act & Assert
        # Test error handling in get_dataset
        with pytest.raises(ValueError) as exc_info:
            facade.get_dataset("nonexistent_dataset")
        assert "Error retrieving dataset" in str(exc_info.value)

        # Test error handling in run_analysis with invalid type
        with pytest.raises(ValueError) as exc_info:
            facade.run_analysis("invalid_type", sample_dataframe)
        assert "Error running invalid_type analysis" in str(exc_info.value)

        # Test error handling in export_results with invalid format
        with pytest.raises(ValueError) as exc_info:
            # Create a mock analysis result
            mock_result = MagicMock()
            facade.export_results(mock_result, "invalid_format", "test.file")
        assert "Error exporting to invalid_format" in str(exc_info.value)

    def test_controller_creation_with_feature_flags(self, temp_config_file):
        """Test controller creation with feature flags."""
        # Arrange
        config_manager = ConfigManager(config_file=temp_config_file)
        facade = ApplicationFacade(config_manager=config_manager)
        factory = ControllerFactory(application_facade=facade)

        # Act
        # Disable visualization
        facade.set_feature_flag("visualization", False)

        # Create controllers
        visualization_controller = factory.create_visualization_controller()

        # Enable visualization
        facade.set_feature_flag("visualization", True)

        # Create controllers again
        visualization_controller_enabled = factory.create_visualization_controller()

        # Assert
        assert visualization_controller is not None
        assert visualization_controller_enabled is not None
