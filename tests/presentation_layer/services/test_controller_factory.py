"""
Tests for the controller factory.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.presentation_layer.services.controller_factory import ControllerFactory
from src.presentation_layer.services.application_facade import ApplicationFacade
from src.presentation_layer.gui.controllers.file_controller import FileController
from src.presentation_layer.gui.controllers.analysis_controller import AnalysisController
from src.presentation_layer.gui.controllers.results_controller import ResultsController
from src.presentation_layer.gui.controllers.visualization_controller import VisualizationController
from src.presentation_layer.gui.controllers.app_controller import AppController


@pytest.fixture
def mock_application_facade():
    """Create a mock application facade."""
    mock_facade = MagicMock(spec=ApplicationFacade)
    mock_facade.is_feature_enabled.return_value = True
    return mock_facade


@pytest.fixture
def controller_factory(mock_application_facade):
    """Create a controller factory with a mock application facade."""
    return ControllerFactory(application_facade=mock_application_facade)


class TestControllerFactory:
    """Tests for the ControllerFactory class."""

    def test_create_file_controller(self, controller_factory):
        """Test creating a file controller."""
        # Act
        controller = controller_factory.create_file_controller()
        
        # Assert
        assert isinstance(controller, FileController)

    def test_create_analysis_controller(self, controller_factory):
        """Test creating an analysis controller."""
        # Act
        controller = controller_factory.create_analysis_controller()
        
        # Assert
        assert isinstance(controller, AnalysisController)

    def test_create_results_controller(self, controller_factory):
        """Test creating a results controller."""
        # Act
        controller = controller_factory.create_results_controller()
        
        # Assert
        assert isinstance(controller, ResultsController)

    def test_create_visualization_controller(self, controller_factory):
        """Test creating a visualization controller."""
        # Act
        controller = controller_factory.create_visualization_controller()
        
        # Assert
        assert isinstance(controller, VisualizationController)

    def test_create_app_controller(self, controller_factory):
        """Test creating an app controller."""
        # Arrange
        file_controller = controller_factory.create_file_controller()
        analysis_controller = controller_factory.create_analysis_controller()
        
        # Act
        controller = controller_factory.create_app_controller(
            file_controller=file_controller,
            analysis_controller=analysis_controller
        )
        
        # Assert
        assert isinstance(controller, AppController)

    def test_create_all_controllers(self, controller_factory):
        """Test creating all controllers."""
        # Act
        controllers = controller_factory.create_all_controllers()
        
        # Assert
        assert "file_controller" in controllers
        assert "analysis_controller" in controllers
        assert "results_controller" in controllers
        assert "visualization_controller" in controllers
        assert "app_controller" in controllers
        
        assert isinstance(controllers["file_controller"], FileController)
        assert isinstance(controllers["analysis_controller"], AnalysisController)
        assert isinstance(controllers["results_controller"], ResultsController)
        assert isinstance(controllers["visualization_controller"], VisualizationController)
        assert isinstance(controllers["app_controller"], AppController)

    def test_feature_flag_disabled(self, mock_application_facade):
        """Test creating a controller with a disabled feature flag."""
        # Arrange
        mock_application_facade.is_feature_enabled.return_value = False
        factory = ControllerFactory(application_facade=mock_application_facade)
        
        # Act
        controller = factory.create_visualization_controller()
        
        # Assert
        assert controller is not None  # Should still create a controller, but with limited functionality
        mock_application_facade.is_feature_enabled.assert_called_with("visualization")
