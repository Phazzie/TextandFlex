"""
ML Component Registration Module
---------------------------
Provides functions for registering ML components with the dependency container.
"""
from typing import Optional

from ..presentation_layer.services.dependency_container import DependencyContainer
from ..presentation_layer.services.logging_service import LoggingService
from .ml_model_service import MLModelService
from .ml_models import TimePatternModel, ContactPatternModel, AnomalyDetectionModel


def register_ml_components(
    container: DependencyContainer,
    logging_service: Optional[LoggingService] = None,
    config_manager = None,
    models_dir: str = None
):
    """
    Register ML components with the dependency container.
    
    This function registers the ML model service and individual models
    with the dependency container for use throughout the application.
    
    Args:
        container: Dependency container to register components with
        logging_service: Optional logging service
        config_manager: Optional configuration manager
        models_dir: Optional directory for model persistence
    """
    # Log the registration
    if logging_service:
        logging_service.info(
            "Registering ML components with dependency container",
            component="MLComponentRegistration"
        )
        
    # Create the ML model service
    ml_service = MLModelService(
        logging_service=logging_service,
        config_manager=config_manager,
        models_dir=models_dir
    )
    
    # Register the ML model service
    container.register_instance("MLModelService", ml_service)
    
    # Register individual model factories
    container.register(
        "TimePatternModel",
        lambda: ml_service.get_model("TimePatternModel"),
        singleton=True
    )
    
    container.register(
        "ContactPatternModel",
        lambda: ml_service.get_model("ContactPatternModel"),
        singleton=True
    )
    
    container.register(
        "AnomalyDetectionModel",
        lambda: ml_service.get_model("AnomalyDetectionModel"),
        singleton=True
    )
    
    # Register the pattern detector factory
    container.register(
        "PatternDetector",
        lambda: create_pattern_detector(ml_service, logging_service, config_manager),
        singleton=True
    )
    
    if logging_service:
        logging_service.info(
            "ML components successfully registered with dependency container",
            component="MLComponentRegistration",
            registered_components=[
                "MLModelService",
                "TimePatternModel",
                "ContactPatternModel", 
                "AnomalyDetectionModel",
                "PatternDetector"
            ]
        )


def create_pattern_detector(
    ml_model_service: MLModelService,
    logging_service: Optional[LoggingService] = None,
    config_manager = None
):
    """
    Create a pattern detector with the given dependencies.
    
    Args:
        ml_model_service: ML model service
        logging_service: Optional logging service
        config_manager: Optional configuration manager
        
    Returns:
        Configured pattern detector
    """
    from .pattern_detector import PatternDetector
    
    detector = PatternDetector(
        ml_model_service=ml_model_service,
        logging_service=logging_service,
        config_manager=config_manager
    )
    
    return detector
