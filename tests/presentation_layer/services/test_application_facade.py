"""
Tests for the application facade.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
import logging

from src.presentation_layer.services.application_facade import ApplicationFacade
from src.presentation_layer.services.dependency_container import container
from src.presentation_layer.gui.models.analysis_model import AnalysisResult, AnalysisType


@pytest.fixture
def mock_repository_service():
    """Create a mock repository service."""
    mock_service = MagicMock()
    mock_service.get_dataset_names.return_value = ["dataset1", "dataset2"]
    mock_service.get_dataset.return_value = {
        "name": "dataset1",
        "data": pd.DataFrame({
            "timestamp": ["2023-01-01 12:00:00"],
            "phone_number": ["123456789"],
            "message_type": ["sent"],
            "content": ["Hello"]
        }),
        "metadata": {"record_count": 1}
    }
    return mock_service


@pytest.fixture
def mock_analysis_service():
    """Create a mock analysis service."""
    mock_service = MagicMock()
    mock_result = MagicMock(spec=AnalysisResult)
    mock_result.result_type = AnalysisType.BASIC
    mock_service.run_analysis.return_value = mock_result
    return mock_service


@pytest.fixture
def mock_export_service():
    """Create a mock export service."""
    mock_service = MagicMock()
    mock_service.export_to_file.return_value = True
    mock_service.generate_report.return_value = True
    mock_service.get_supported_formats.return_value = ["csv", "excel", "json"]
    return mock_service


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager."""
    mock_manager = MagicMock()
    mock_manager.get_feature_flag.return_value = True
    mock_manager.get_config_value.return_value = "light"
    return mock_manager


@pytest.fixture
def mock_logging_service():
    """Create a mock logging service."""
    mock_service = MagicMock()
    return mock_service


@pytest.fixture
def application_facade(mock_repository_service, mock_analysis_service,
                      mock_export_service, mock_config_manager, mock_logging_service):
    """Create an application facade with mock services."""
    return ApplicationFacade(
        repository_service=mock_repository_service,
        analysis_service=mock_analysis_service,
        export_service=mock_export_service,
        config_manager=mock_config_manager,
        logging_service=mock_logging_service
    )


@pytest.fixture(autouse=True)
def clear_container():
    """Clear the dependency container before and after each test."""
    container.clear()
    yield
    container.clear()


class TestApplicationFacade:
    """Tests for the ApplicationFacade class."""

    def test_register_dependencies(self):
        """Test registering dependencies."""
        # Act
        ApplicationFacade.register_dependencies()

        # Assert
        assert container.has('logging_service')
        assert container.has('config_manager')
        assert container.has('repository_service')
        assert container.has('analysis_service')
        assert container.has('export_service')

    def test_create(self):
        """Test creating a facade with the factory method."""
        # Act
        facade = ApplicationFacade.create()

        # Assert
        assert facade is not None
        assert isinstance(facade, ApplicationFacade)

    def test_get_dataset_names(self, application_facade, mock_repository_service, mock_logging_service):
        """Test getting dataset names."""
        # Act
        result = application_facade.get_dataset_names()

        # Assert
        assert result == ["dataset1", "dataset2"]
        mock_repository_service.get_dataset_names.assert_called_once()
        mock_logging_service.log_method_call.assert_called_once_with('get_dataset_names')
        mock_logging_service.log_method_return.assert_called_once()

    def test_get_dataset(self, application_facade, mock_repository_service, mock_logging_service):
        """Test getting a dataset."""
        # Act
        result = application_facade.get_dataset("dataset1")

        # Assert
        assert result is not None
        assert "data" in result
        assert "metadata" in result
        mock_repository_service.get_dataset.assert_called_once_with("dataset1")
        mock_logging_service.log_method_call.assert_called_once_with('get_dataset', name="dataset1")
        mock_logging_service.log_method_return.assert_called_once()

    def test_get_dataset_error(self, application_facade, mock_repository_service, mock_logging_service):
        """Test getting a dataset with an error."""
        # Arrange
        mock_repository_service.get_dataset.side_effect = ValueError("Dataset not found")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            application_facade.get_dataset("nonexistent")

        assert "Error retrieving dataset" in str(exc_info.value)
        mock_repository_service.get_dataset.assert_called_once_with("nonexistent")
        mock_logging_service.log_method_call.assert_called_once_with('get_dataset', name="nonexistent")
        mock_logging_service.log_method_error.assert_called_once()

    def test_run_analysis(self, application_facade, mock_analysis_service, mock_logging_service):
        """Test running analysis."""
        # Arrange
        df = pd.DataFrame({"col1": [1, 2, 3]})

        # Act
        result = application_facade.run_analysis("basic", df)

        # Assert
        assert result is not None
        assert result.result_type == AnalysisType.BASIC
        mock_analysis_service.run_analysis.assert_called_once_with("basic", df, None)
        mock_logging_service.log_method_call.assert_called_once()
        mock_logging_service.log_method_return.assert_called_once()

    def test_run_analysis_with_disabled_feature(self, application_facade, mock_config_manager,
                                              mock_analysis_service, mock_logging_service):
        """Test running analysis with a disabled feature."""
        # Arrange
        df = pd.DataFrame({"col1": [1, 2, 3]})
        mock_config_manager.get_feature_flag.return_value = False

        # Act
        result = application_facade.run_analysis("basic", df)

        # Assert
        assert result is not None
        mock_config_manager.get_feature_flag.assert_called_once_with("basic_analysis")
        mock_logging_service.warning.assert_called_once()

    def test_export_results(self, application_facade, mock_export_service, mock_logging_service):
        """Test exporting results."""
        # Arrange
        mock_result = MagicMock(spec=AnalysisResult)

        # Act
        result = application_facade.export_results(mock_result, "csv", "test.csv")

        # Assert
        assert result is True
        mock_export_service.export_to_file.assert_called_once_with(
            mock_result, "csv", "test.csv"
        )

    def test_generate_report(self, application_facade, mock_export_service, mock_logging_service):
        """Test generating a report."""
        # Arrange
        mock_result = MagicMock(spec=AnalysisResult)

        # Act
        result = application_facade.generate_report(mock_result, "test.txt")

        # Assert
        assert result is True
        mock_export_service.generate_report.assert_called_once_with(
            mock_result, "test.txt"
        )

    def test_get_supported_export_formats(self, application_facade, mock_export_service):
        """Test getting supported export formats."""
        # Act
        result = application_facade.get_supported_export_formats()

        # Assert
        assert result == ["csv", "excel", "json"]
        mock_export_service.get_supported_formats.assert_called_once()

    def test_is_feature_enabled(self, application_facade, mock_config_manager):
        """Test checking if a feature is enabled."""
        # Act
        result = application_facade.is_feature_enabled("advanced_analysis")

        # Assert
        assert result is True
        mock_config_manager.get_feature_flag.assert_called_once_with("advanced_analysis")

    def test_get_config_value(self, application_facade, mock_config_manager):
        """Test getting a configuration value."""
        # Act
        result = application_facade.get_config_value("ui.theme")

        # Assert
        assert result == "light"
        mock_config_manager.get_config_value.assert_called_once_with("ui.theme", None)

    def test_set_config_value(self, application_facade, mock_config_manager):
        """Test setting a configuration value."""
        # Act
        application_facade.set_config_value("ui.theme", "dark")

        # Assert
        mock_config_manager.set_config_value.assert_called_once_with("ui.theme", "dark")
        mock_config_manager.save_config.assert_called_once()

    def test_set_feature_flag(self, application_facade, mock_config_manager):
        """Test setting a feature flag."""
        # Act
        application_facade.set_feature_flag("experimental_ml", True)

        # Assert
        mock_config_manager.set_feature_flag.assert_called_once_with("experimental_ml", True)
        mock_config_manager.save_config.assert_called_once()

    def test_get_all_feature_flags(self, application_facade, mock_config_manager):
        """Test getting all feature flags."""
        # Arrange
        mock_config_manager.get_all_feature_flags.return_value = {
            "feature1": True,
            "feature2": False
        }

        # Act
        result = application_facade.get_all_feature_flags()

        # Assert
        assert result == {"feature1": True, "feature2": False}
        mock_config_manager.get_all_feature_flags.assert_called_once()

    def test_reset_config_to_defaults(self, application_facade, mock_config_manager):
        """Test resetting configuration to defaults."""
        # Act
        application_facade.reset_config_to_defaults()

        # Assert
        mock_config_manager.reset_to_defaults.assert_called_once()
        mock_config_manager.save_config.assert_called_once()

    def test_add_dataset(self, application_facade, mock_repository_service):
        """Test adding a dataset."""
        # Arrange
        df = pd.DataFrame({"col1": [1, 2, 3]})
        column_mapping = {"col1": "col1"}
        mock_repository_service.add_dataset.return_value = True

        # Act
        result = application_facade.add_dataset("new_dataset", df, column_mapping)

        # Assert
        assert result is True
        mock_repository_service.add_dataset.assert_called_once_with(
            "new_dataset", df, column_mapping, None
        )
