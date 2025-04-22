"""
Application Facade Module
----------------------
Provides a unified interface for the application.
"""
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import os
import logging

from src.presentation_layer.services.repository_service import RepositoryService
from src.presentation_layer.services.analysis_service import AnalysisService
from src.presentation_layer.services.export_service import ExportService
from src.presentation_layer.services.config_manager import ConfigManager
from src.presentation_layer.services.logging_service import LoggingService
from src.presentation_layer.services.dependency_container import container
from src.presentation_layer.gui.models.analysis_model import AnalysisResult


class ApplicationFacade:
    """
    Application facade that provides a unified interface for the application.

    This class coordinates the different services and provides a simplified
    interface for the GUI controllers to interact with the backend components.
    """

    @classmethod
    def create(cls, log_level: int = logging.INFO,
              log_file: Optional[str] = None,
              config_file: Optional[str] = None) -> 'ApplicationFacade':
        """
        Create a fully configured ApplicationFacade instance.

        Args:
            log_level: Logging level
            log_file: Optional log file path
            config_file: Optional configuration file path

        Returns:
            ApplicationFacade instance
        """
        # Register dependencies
        cls.register_dependencies(log_level, log_file, config_file)

        # Create facade
        return cls()

    @classmethod
    def register_dependencies(cls, log_level: int = logging.INFO,
                            log_file: Optional[str] = None,
                            config_file: Optional[str] = None) -> None:
        """
        Register dependencies in the container.

        Args:
            log_level: Logging level
            log_file: Optional log file path
            config_file: Optional configuration file path
        """
        # Register logging service
        if not container.has('logging_service'):
            container.register_instance('logging_service',
                                      LoggingService(
                                          logger_name='compatibility_layer',
                                          log_level=log_level,
                                          log_file=log_file
                                      ))

        # Register config manager
        if not container.has('config_manager'):
            container.register('config_manager',
                             lambda: ConfigManager(config_file=config_file),
                             singleton=True)

        # Register repository service
        if not container.has('repository_service'):
            container.register('repository_service',
                             lambda: RepositoryService(),
                             singleton=True)

        # Register analysis service
        if not container.has('analysis_service'):
            container.register('analysis_service',
                             lambda: AnalysisService(),
                             singleton=True)

        # Register export service
        if not container.has('export_service'):
            container.register('export_service',
                             lambda: ExportService(),
                             singleton=True)

    def __init__(self,
                repository_service: Optional[RepositoryService] = None,
                analysis_service: Optional[AnalysisService] = None,
                export_service: Optional[ExportService] = None,
                config_manager: Optional[ConfigManager] = None,
                logging_service: Optional[LoggingService] = None):
        """
        Initialize the application facade.

        Args:
            repository_service: Optional repository service (for testing)
            analysis_service: Optional analysis service (for testing)
            export_service: Optional export service (for testing)
            config_manager: Optional configuration manager (for testing)
            logging_service: Optional logging service (for testing)
        """
        # Register dependencies if not already registered
        self.register_dependencies()

        # Get services from container or use provided instances
        self.repository_service = repository_service or container.get('repository_service')
        self.analysis_service = analysis_service or container.get('analysis_service')
        self.export_service = export_service or container.get('export_service')
        self.config_manager = config_manager or container.get('config_manager')
        self.logger = logging_service or container.get('logging_service')

        # Set context for logging
        self.logger.set_context(component='ApplicationFacade')

        # Load configuration
        self.logger.info('Initializing ApplicationFacade')
        self.config_manager.load_config()

    def get_dataset_names(self) -> List[str]:
        """
        Get a list of all dataset names.

        Returns:
            List of dataset names
        """
        self.logger.log_method_call('get_dataset_names')
        result = self.repository_service.get_dataset_names()
        self.logger.log_method_return('get_dataset_names', result)
        return result

    def get_dataset(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a dataset by name.

        Args:
            name: Name of the dataset to retrieve

        Returns:
            Dictionary containing dataset information or None if not found

        Raises:
            ValueError: If the dataset is not found or other error occurs
        """
        self.logger.log_method_call('get_dataset', name=name)
        try:
            result = self.repository_service.get_dataset(name)
            self.logger.log_method_return('get_dataset', result)
            return result
        except ValueError as e:
            # Log error and re-raise with more context
            error_msg = f"Error retrieving dataset '{name}': {str(e)}"
            self.logger.log_method_error('get_dataset', ValueError(error_msg))
            raise ValueError(error_msg)

    def add_dataset(self, name: str, data: pd.DataFrame,
                   column_mapping: Dict[str, str],
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a new dataset.

        Args:
            name: Name for the new dataset
            data: DataFrame containing the dataset
            column_mapping: Mapping of standard column names to actual column names
            metadata: Optional metadata for the dataset

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If validation fails or other error occurs
        """
        try:
            return self.repository_service.add_dataset(name, data, column_mapping, metadata)
        except ValueError as e:
            # Re-raise with more context
            raise ValueError(f"Error adding dataset '{name}': {str(e)}")

    def remove_dataset(self, name: str) -> bool:
        """
        Remove a dataset.

        Args:
            name: Name of the dataset to remove

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If the dataset is not found or other error occurs
        """
        try:
            return self.repository_service.remove_dataset(name)
        except ValueError as e:
            # Re-raise with more context
            raise ValueError(f"Error removing dataset '{name}': {str(e)}")

    def run_analysis(self, analysis_type: str, dataframe: pd.DataFrame,
                    options: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Run an analysis on the given dataframe.

        Args:
            analysis_type: Type of analysis to run ("basic", "contact", "time", "pattern")
            dataframe: DataFrame containing the data to analyze
            options: Optional dictionary of analysis options

        Returns:
            AnalysisResult containing the analysis results

        Raises:
            ValueError: If the analysis type is invalid or analysis fails
        """
        self.logger.log_method_call('run_analysis',
                                  analysis_type=analysis_type,
                                  dataframe_shape=dataframe.shape if dataframe is not None else None,
                                  options=options)
        try:
            # Check if feature is enabled
            feature_name = f"{analysis_type}_analysis"
            if not self.is_feature_enabled(feature_name):
                self.logger.warning(f"Analysis type '{analysis_type}' is disabled by feature flag",
                                  feature=feature_name)
                # Still run the analysis but log a warning

            result = self.analysis_service.run_analysis(analysis_type, dataframe, options)
            self.logger.log_method_return('run_analysis', f"Analysis completed: {analysis_type}")
            return result
        except ValueError as e:
            # Log error and re-raise with more context
            error_msg = f"Error running {analysis_type} analysis: {str(e)}"
            self.logger.log_method_error('run_analysis', ValueError(error_msg))
            raise ValueError(error_msg)

    def export_results(self, analysis_result: AnalysisResult,
                      export_format: str, file_path: str) -> bool:
        """
        Export analysis results to a file.

        Args:
            analysis_result: The analysis result to export
            export_format: The format to export to (csv, excel, json)
            file_path: The path to export to

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If the export format is unsupported or export fails
        """
        try:
            return self.export_service.export_to_file(analysis_result, export_format, file_path)
        except ValueError as e:
            # Re-raise with more context
            raise ValueError(f"Error exporting to {export_format}: {str(e)}")

    def generate_report(self, analysis_result: AnalysisResult, file_path: str) -> bool:
        """
        Generate a text report from analysis results.

        Args:
            analysis_result: The analysis result to generate a report from
            file_path: The path to save the report to

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If report generation fails
        """
        try:
            return self.export_service.generate_report(analysis_result, file_path)
        except ValueError as e:
            # Re-raise with more context
            raise ValueError(f"Error generating report: {str(e)}")

    def get_supported_export_formats(self) -> List[str]:
        """
        Get a list of supported export formats.

        Returns:
            List of supported export formats
        """
        return self.export_service.get_supported_formats()

    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature_name: Name of the feature

        Returns:
            True if the feature is enabled, False otherwise
        """
        return self.config_manager.get_feature_flag(feature_name)

    def get_config_value(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value by path.

        Args:
            path: Path to the configuration value (e.g., "ui.theme")
            default: Default value if the path is not found

        Returns:
            Configuration value
        """
        return self.config_manager.get_config_value(path, default)

    def set_config_value(self, path: str, value: Any) -> None:
        """
        Set a configuration value by path and save the configuration.

        Args:
            path: Path to the configuration value (e.g., "ui.theme")
            value: Value to set
        """
        self.config_manager.set_config_value(path, value)
        self.config_manager.save_config()

    def set_feature_flag(self, feature_name: str, value: bool) -> None:
        """
        Set the value of a feature flag and save the configuration.

        Args:
            feature_name: Name of the feature flag
            value: Value to set
        """
        self.config_manager.set_feature_flag(feature_name, value)
        self.config_manager.save_config()

    def get_all_feature_flags(self) -> Dict[str, bool]:
        """
        Get all feature flags.

        Returns:
            Dictionary of all feature flags
        """
        return self.config_manager.get_all_feature_flags()

    def reset_config_to_defaults(self) -> None:
        """Reset configuration to defaults and save."""
        self.config_manager.reset_to_defaults()
        self.config_manager.save_config()
