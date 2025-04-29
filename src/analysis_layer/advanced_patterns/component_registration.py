"""
Advanced Pattern Detection Component Registration Module
--------------------------------------------------
Provides functions for registering advanced pattern detection components with the dependency container.

This module serves as an integration point between the core ML architecture and
the TextandFlex Analysis Engine components.
"""
from typing import Optional

from ...presentation_layer.services.dependency_container import DependencyContainer
from ...presentation_layer.services.logging_service import LoggingService
from ..ml_model_service import MLModelService


def register_advanced_pattern_components(
    container: DependencyContainer,
    logging_service: Optional[LoggingService] = None,
    config_manager = None
):
    """
    Register advanced pattern detection components with the dependency container.

    This function registers components for advanced pattern detection, including gap detection,
    overlap analysis, and response analysis.

    Args:
        container: Dependency container to register components with
        logging_service: Optional logging service
        config_manager: Optional configuration manager
    """
    # Log the registration
    if logging_service:
        logging_service.info(
            "Registering advanced pattern detection components with dependency container",
            component="AdvancedPatternComponentRegistration"
        )

    # Get the ML model service from the container
    ml_service = container.get("MLModelService")

    # Register the GapDetector factory
    container.register(
        "GapDetector",
        lambda: create_gap_detector(ml_service, logging_service, config_manager),
        singleton=True
    )

    # Register the OverlapAnalyzer factory
    container.register(
        "OverlapAnalyzer",
        lambda: create_overlap_analyzer(ml_service, logging_service, config_manager),
        singleton=True
    )

    # Register the ResponseAnalyzer factory
    container.register(
        "ResponseAnalyzer",
        lambda: create_response_analyzer(ml_service, logging_service, config_manager),
        singleton=True
    )


def create_gap_detector(
    ml_model_service: MLModelService,
    logging_service: Optional[LoggingService] = None,
    config_manager = None
):
    """
    Create a gap detector with the given dependencies.

    Args:
        ml_model_service: ML model service (not used in constructor but stored for reference)
        logging_service: Optional logging service (not used in constructor but stored for reference)
        config_manager: Optional configuration manager (not used in constructor)

    Returns:
        Configured gap detector
    """
    from .gap_detector import GapDetector

    detector = GapDetector()

    # Store references to services (these aren't used in the constructor but may be needed later)
    detector.ml_model_service = ml_model_service
    detector.logging_service = logging_service

    return detector


def create_overlap_analyzer(
    ml_model_service: MLModelService,
    logging_service: Optional[LoggingService] = None,
    config_manager = None
):
    """
    Create an overlap analyzer with the given dependencies.

    Args:
        ml_model_service: ML model service (not used in constructor but stored for reference)
        logging_service: Optional logging service (not used in constructor but stored for reference)
        config_manager: Optional configuration manager (not used in constructor)

    Returns:
        Configured overlap analyzer
    """
    from .overlap_analyzer import OverlapAnalyzer

    analyzer = OverlapAnalyzer()

    # Store references to services (these aren't used in the constructor but may be needed later)
    analyzer.ml_model_service = ml_model_service
    analyzer.logging_service = logging_service

    return analyzer


def create_response_analyzer(
    ml_model_service: MLModelService,
    logging_service: Optional[LoggingService] = None,
    config_manager = None
):
    """
    Create a response analyzer with the given dependencies.

    Args:
        ml_model_service: ML model service
        logging_service: Optional logging service
        config_manager: Optional configuration manager

    Returns:
        Configured response analyzer
    """
    from .response_analyzer import ResponseAnalyzer

    # Create analyzer with dependencies directly in constructor
    analyzer = ResponseAnalyzer(
        ml_model_service=ml_model_service,
        config=config_manager,
        logging_service=logging_service
    )

    return analyzer
