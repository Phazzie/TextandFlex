"""
Longitudinal Analysis Component Registration Module
--------------------------------------------------
Provides functions for registering longitudinal analysis components with the dependency container.

This module serves as an integration point between the core ML architecture and 
the TextandFlex Analysis Engine components.
"""
from typing import Optional

from ..presentation_layer.services.dependency_container import DependencyContainer
from ..presentation_layer.services.logging_service import LoggingService
from .ml_model_service import MLModelService


def register_longitudinal_components(
    container: DependencyContainer,
    logging_service: Optional[LoggingService] = None,
    config_manager = None
):
    """
    Register longitudinal analysis components with the dependency container.
    
    This function registers components for longitudinal analysis, including trend analysis,
    contact evolution tracking, and seasonality detection.
    
    Args:
        container: Dependency container to register components with
        logging_service: Optional logging service
        config_manager: Optional configuration manager
    """
    # Log the registration
    if logging_service:
        logging_service.info(
            "Registering longitudinal analysis components with dependency container",
            component="LongitudinalComponentRegistration"
        )
    
    # Get the ML model service from the container
    ml_service = container.get("MLModelService")
    
    # Register the trend analyzer factory
    container.register(
        "TrendAnalyzer",
        lambda: create_trend_analyzer(ml_service, logging_service, config_manager),
        singleton=True
    )
    
    # Register the contact evolution tracker factory
    container.register(
        "ContactEvolutionTracker",
        lambda: create_contact_evolution_tracker(ml_service, logging_service, config_manager),
        singleton=True
    )
    
    # Register the seasonality detector factory
    container.register(
        "SeasonalityDetector",
        lambda: create_seasonality_detector(ml_service, logging_service, config_manager),
        singleton=True
    )
    
    if logging_service:
        logging_service.info(
            "Longitudinal analysis components successfully registered with dependency container",
            component="LongitudinalComponentRegistration",
            registered_components=[
                "TrendAnalyzer",
                "ContactEvolutionTracker", 
                "SeasonalityDetector"
            ]
        )


def create_trend_analyzer(
    ml_model_service: MLModelService,
    logging_service: Optional[LoggingService] = None,
    config_manager = None
):
    """
    Create a trend analyzer with the given dependencies.
    
    Args:
        ml_model_service: ML model service
        logging_service: Optional logging service
        config_manager: Optional configuration manager
        
    Returns:
        Configured trend analyzer
    """
    # Import here to avoid circular dependencies
    from .longitudinal.trend_analyzer import TrendAnalyzer
    
    analyzer = TrendAnalyzer(
        ml_model_service=ml_model_service,
        logging_service=logging_service,
        config_manager=config_manager
    )
    
    return analyzer


def create_contact_evolution_tracker(
    ml_model_service: MLModelService,
    logging_service: Optional[LoggingService] = None,
    config_manager = None
):
    """
    Create a contact evolution tracker with the given dependencies.
    
    Args:
        ml_model_service: ML model service
        logging_service: Optional logging service
        config_manager: Optional configuration manager
        
    Returns:
        Configured contact evolution tracker
    """
    # Import here to avoid circular dependencies
    from .longitudinal.contact_evolution import ContactEvolutionTracker
    
    tracker = ContactEvolutionTracker(
        ml_model_service=ml_model_service,
        logging_service=logging_service,
        config_manager=config_manager
    )
    
    return tracker


def create_seasonality_detector(
    ml_model_service: MLModelService,
    logging_service: Optional[LoggingService] = None,
    config_manager = None
):
    """
    Create a seasonality detector with the given dependencies.
    
    Args:
        ml_model_service: ML model service
        logging_service: Optional logging service
        config_manager: Optional configuration manager
        
    Returns:
        Configured seasonality detector
    """
    # Import here to avoid circular dependencies
    from .longitudinal.seasonality_detector import SeasonalityDetector
    
    detector = SeasonalityDetector(
        ml_model_service=ml_model_service,
        logging_service=logging_service,
        config_manager=config_manager
    )
    
    return detector
