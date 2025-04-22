"""
Controller Factory Module
----------------------
Factory for creating controllers with appropriate dependencies.
"""
from typing import Dict, Optional, Any, Type, ClassVar
import logging

from src.presentation_layer.services.application_facade import ApplicationFacade
from src.presentation_layer.services.dependency_container import container
from src.presentation_layer.services.logging_service import LoggingService
from src.presentation_layer.gui.controllers.file_controller import FileController
from src.presentation_layer.gui.controllers.analysis_controller import AnalysisController
from src.presentation_layer.gui.controllers.results_controller import ResultsController
from src.presentation_layer.gui.controllers.visualization_controller import VisualizationController
from src.presentation_layer.gui.controllers.app_controller import AppController
from src.data_layer.repository import PhoneRecordRepository
from src.data_layer.excel_parser import ExcelParser
from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
from src.analysis_layer.contact_analysis import ContactAnalyzer
from src.analysis_layer.time_analysis import TimeAnalyzer
from src.analysis_layer.pattern_detector import PatternDetector


class ControllerFactory:
    """
    Factory for creating controllers with appropriate dependencies.

    This class is responsible for creating controllers with the correct
    dependencies and feature flags.
    """

    # Class variable to store the singleton instance
    _instance: ClassVar[Optional['ControllerFactory']] = None

    @classmethod
    def get_instance(
        cls, application_facade: Optional[ApplicationFacade] = None
    ) -> 'ControllerFactory':
        """
        Get the singleton instance of the controller factory.

        Args:
            application_facade: Optional application facade (for testing)

        Returns:
            ControllerFactory instance
        """
        if cls._instance is None:
            cls._instance = cls(application_facade)
        return cls._instance

    def __init__(self, application_facade: Optional[ApplicationFacade] = None):
        """
        Initialize the controller factory.

        Args:
            application_facade: Optional application facade (for testing)
        """
        # Get application facade from container or use provided instance
        if application_facade is not None:
            self.application_facade = application_facade
        elif container.has('application_facade'):
            self.application_facade = container.get('application_facade')
        else:
            # Create a new application facade and register it
            self.application_facade = ApplicationFacade.create()
            container.register_instance('application_facade', self.application_facade)

        # Get logger from container
        if container.has('logging_service'):
            self.logger = container.get('logging_service')
        else:
            # Create a new logger and register it
            self.logger = LoggingService(logger_name='controller_factory')
            container.register_instance('logging_service', self.logger)

        # Set context for logging
        self.logger.set_context(component='ControllerFactory')
        self.logger.info('Initializing ControllerFactory')

    def create_file_controller(self) -> FileController:
        """
        Create a file controller.

        Returns:
            FileController instance
        """
        self.logger.log_method_call('create_file_controller')

        # Check if we should use the repository service
        use_repository_service = self.application_facade.is_feature_enabled("repository_service")
        self.logger.debug(f"Repository service enabled: {use_repository_service}")

        # Get repository from container or create new one
        if container.has('repository'):
            repository = container.get('repository')
        else:
            repository = PhoneRecordRepository()

        # Get parser from container or create new one
        if container.has('excel_parser'):
            parser = container.get('excel_parser')
        else:
            parser = ExcelParser()

        # Create the controller
        controller = FileController(
            repository=repository,
            parser=parser,
            component_name="FileController"
        )

        self.logger.log_method_return('create_file_controller', controller)
        return controller

    def create_analysis_controller(self) -> AnalysisController:
        """
        Create an analysis controller.

        Returns:
            AnalysisController instance
        """
        self.logger.log_method_call('create_analysis_controller')

        # Check which analyzers are enabled
        enable_contact_analysis = self.application_facade.is_feature_enabled("contact_analysis")
        enable_time_analysis = self.application_facade.is_feature_enabled("time_analysis")
        enable_pattern_detection = self.application_facade.is_feature_enabled("pattern_detection")

        self.logger.debug(
            "Feature flags",
            contact_analysis=enable_contact_analysis,
            time_analysis=enable_time_analysis,
            pattern_detection=enable_pattern_detection
        )

        # Get or create analyzers
        if container.has('basic_analyzer'):
            basic_analyzer = container.get('basic_analyzer')
        else:
            basic_analyzer = BasicStatisticsAnalyzer()
            container.register_instance('basic_analyzer', basic_analyzer)

        # Only create optional analyzers if enabled
        contact_analyzer = None
        if enable_contact_analysis:
            if container.has('contact_analyzer'):
                contact_analyzer = container.get('contact_analyzer')
            else:
                contact_analyzer = ContactAnalyzer()
                container.register_instance('contact_analyzer', contact_analyzer)

        time_analyzer = None
        if enable_time_analysis:
            if container.has('time_analyzer'):
                time_analyzer = container.get('time_analyzer')
            else:
                time_analyzer = TimeAnalyzer()
                container.register_instance('time_analyzer', time_analyzer)

        pattern_detector = None
        if enable_pattern_detection:
            if container.has('pattern_detector'):
                pattern_detector = container.get('pattern_detector')
            else:
                pattern_detector = PatternDetector()
                container.register_instance('pattern_detector', pattern_detector)

        # Create the controller
        controller = AnalysisController(
            basic_analyzer=basic_analyzer,
            contact_analyzer=contact_analyzer,
            time_analyzer=time_analyzer,
            pattern_detector=pattern_detector,
            component_name="AnalysisController"
        )

        self.logger.log_method_return('create_analysis_controller', controller)
        return controller

    def create_results_controller(self) -> ResultsController:
        """
        Create a results controller.

        Returns:
            ResultsController instance
        """
        self.logger.log_method_call('create_results_controller')

        # Check if export service is enabled
        use_export_service = self.application_facade.is_feature_enabled("export_service")
        self.logger.debug(f"Export service enabled: {use_export_service}")

        # Create the controller
        controller = ResultsController(component_name="ResultsController")

        self.logger.log_method_return('create_results_controller', controller)
        return controller

    def create_visualization_controller(self) -> VisualizationController:
        """
        Create a visualization controller.

        Returns:
            VisualizationController instance
        """
        self.logger.log_method_call('create_visualization_controller')

        # Check if visualization is enabled
        enable_visualization = self.application_facade.is_feature_enabled("visualization")
        self.logger.debug(f"Visualization enabled: {enable_visualization}")

        # Create the controller
        controller = VisualizationController(component_name="VisualizationController")

        self.logger.log_method_return('create_visualization_controller', controller)
        return controller

    def create_app_controller(
        self,
        file_controller: Optional[FileController] = None,
        analysis_controller: Optional[AnalysisController] = None
    ) -> AppController:
        """
        Create an app controller.

        Args:
            file_controller: Optional file controller (if None, one will be created)
            analysis_controller: Optional analysis controller (if None, one will be created)

        Returns:
            AppController instance
        """
        self.logger.log_method_call(
            'create_app_controller',
            has_file_controller=file_controller is not None,
            has_analysis_controller=analysis_controller is not None
        )

        # Create controllers if not provided
        file_ctrl = file_controller or self.create_file_controller()
        analysis_ctrl = analysis_controller or self.create_analysis_controller()

        # Create the controller
        controller = AppController(
            file_controller=file_ctrl,
            analysis_controller=analysis_ctrl,
            component_name="AppController"
        )

        self.logger.log_method_return('create_app_controller', controller)
        return controller

    def create_all_controllers(self) -> Dict[str, Any]:
        """
        Create all controllers.

        Returns:
            Dictionary of controllers
        """
        self.logger.log_method_call('create_all_controllers')

        # Create individual controllers
        file_controller = self.create_file_controller()
        analysis_controller = self.create_analysis_controller()
        results_controller = self.create_results_controller()
        visualization_controller = self.create_visualization_controller()

        # Create app controller with the other controllers
        app_controller = self.create_app_controller(
            file_controller=file_controller,
            analysis_controller=analysis_controller
        )

        # Create controller dictionary
        controllers = {
            "file_controller": file_controller,
            "analysis_controller": analysis_controller,
            "results_controller": results_controller,
            "visualization_controller": visualization_controller,
            "app_controller": app_controller
        }

        self.logger.log_method_return('create_all_controllers',
                                    f"Created {len(controllers)} controllers")
        return controllers
