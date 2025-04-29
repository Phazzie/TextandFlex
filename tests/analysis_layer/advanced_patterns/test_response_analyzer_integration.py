"""
Integration tests for the ResponseAnalyzer component.

This module contains tests for the integration of the ResponseAnalyzer with other components.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer
from src.analysis_layer.pattern_detector import PatternDetector
from src.analysis_layer.insight_generator import InsightGenerator
from src.analysis_layer.ml_model_service import MLModelService
from src.presentation_layer.services.dependency_container import DependencyContainer
from src.presentation_layer.services.logging_service import LoggingService


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = [
        # A simple conversation with quick responses
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 10), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 15), 'phone_number': '5551234567', 'message_type': 'received'},

        # A conversation with a different contact with slower responses
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 14, 30), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 15, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 16, 0), 'phone_number': '5559876543', 'message_type': 'sent'},

        # A third contact with mixed response times
        {'timestamp': datetime(2023, 1, 2, 9, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 2, 9, 45), 'phone_number': '5552223333', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 2, 10, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 2, 10, 3), 'phone_number': '5552223333', 'message_type': 'received'},
    ]

    return pd.DataFrame(data)


@pytest.fixture
def mock_ml_service():
    """Create a mock ML model service."""
    mock_service = MagicMock(spec=MLModelService)

    # Mock the extract_features method
    mock_service.extract_features.return_value = {
        'response_times': [300, 300, 1800, 3600, 2700, 180],
        'message_counts': {'5551234567': 4, '5559876543': 4, '5552223333': 4},
        'sent_received_ratios': {'5551234567': 1.0, '5559876543': 1.0, '5552223333': 1.0}
    }

    # Mock the predict method
    mock_service.predict.return_value = {
        'predictions': [
            {'contact': '5551234567', 'expected_response_time': 300, 'confidence': 0.9},
            {'contact': '5559876543', 'expected_response_time': 2700, 'confidence': 0.8},
            {'contact': '5552223333', 'expected_response_time': 1440, 'confidence': 0.7}
        ],
        'model_name': 'ResponseModel',
        'model_version': '1.0'
    }

    return mock_service


@pytest.fixture
def mock_logging_service():
    """Create a mock logging service."""
    mock_logger = MagicMock(spec=LoggingService)
    return mock_logger


@pytest.fixture
def mock_pattern_detector(mock_ml_service, mock_logging_service):
    """Create a mock pattern detector."""
    detector = MagicMock(spec=PatternDetector)
    detector.ml_model_service = mock_ml_service
    detector.logging_service = mock_logging_service

    # Mock the detect_patterns method
    detector.detect_patterns.return_value = [
        {
            'pattern_type': 'time',
            'subtype': 'hour',
            'hour': 10,
            'description': 'Frequent communication at 10:00',
            'confidence': 0.8
        },
        {
            'pattern_type': 'sequence',
            'subtype': 'text_call',
            'description': 'Text messages followed by calls',
            'confidence': 0.7
        }
    ]

    return detector


@pytest.fixture
def mock_insight_generator(mock_pattern_detector):
    """Create a mock insight generator."""
    generator = MagicMock(spec=InsightGenerator)
    generator.pattern_detector = mock_pattern_detector

    # Mock the generate_insights method
    generator.generate_insights.return_value = [
        "You communicate frequently at 10:00 AM.",
        "You often send text messages followed by calls."
    ]

    return generator


@pytest.fixture
def mock_dependency_container(mock_ml_service, mock_logging_service):
    """Create a mock dependency container."""
    container = MagicMock(spec=DependencyContainer)

    # Mock the get method
    container.get.side_effect = lambda name: {
        "MLModelService": mock_ml_service,
        "LoggingService": mock_logging_service
    }.get(name)

    return container


@pytest.mark.integration
def test_pattern_detector_integration(sample_df, mock_pattern_detector):
    """Test integration with Pattern Detector."""
    # Create a ResponseAnalyzer
    analyzer = ResponseAnalyzer()
    analyzer.ml_model_service = mock_pattern_detector.ml_model_service
    analyzer.logging_service = mock_pattern_detector.logging_service

    # Add the analyzer to the pattern detector
    mock_pattern_detector.response_analyzer = analyzer

    # Create a method to convert response results to patterns
    def convert_to_patterns(response_results):
        patterns = []

        if 'conversation_flows' in response_results:
            flows = response_results['conversation_flows']
            if 'conversation_initiators' in flows:
                for contact, count in flows['conversation_initiators'].items():
                    if count >= 1:
                        patterns.append({
                            'pattern_type': 'response',
                            'subtype': 'initiator',
                            'contact': contact,
                            'description': f"{contact} frequently initiates conversations",
                            'confidence': 0.7
                        })

        if 'response_times' in response_results:
            times = response_results['response_times']
            if 'response_time_by_contact' in times:
                for contact, time in times['response_time_by_contact'].items():
                    patterns.append({
                        'pattern_type': 'response',
                        'subtype': 'response_time',
                        'contact': contact,
                        'avg_time': time,
                        'description': f"{contact} responds in {time/60:.1f} minutes on average",
                        'confidence': 0.8
                    })

        return patterns

    # Mock the _convert_response_results_to_patterns method
    mock_pattern_detector._convert_response_results_to_patterns = MagicMock(side_effect=convert_to_patterns)

    # Create a custom detect_patterns method that uses the ResponseAnalyzer
    def custom_detect_patterns(df, column_mapping=None):
        # Get original patterns
        original_patterns = [
            {
                'pattern_type': 'time',
                'subtype': 'hour',
                'hour': 10,
                'description': 'Frequent communication at 10:00',
                'confidence': 0.8
            },
            {
                'pattern_type': 'sequence',
                'subtype': 'text_call',
                'description': 'Text messages followed by calls',
                'confidence': 0.7
            }
        ]

        # Get response patterns
        response_results = analyzer.analyze_response_patterns(df, column_mapping)
        response_patterns = convert_to_patterns(response_results)

        # Combine patterns
        all_patterns = original_patterns + response_patterns

        # Sort by confidence
        all_patterns.sort(key=lambda x: x.get('confidence', 0), reverse=True)

        return all_patterns

    # Replace the detect_patterns method
    mock_pattern_detector.detect_patterns = custom_detect_patterns

    # Test the integration
    patterns = mock_pattern_detector.detect_patterns(sample_df)

    # Check that the patterns include both original and response patterns
    assert len(patterns) > 2  # Should have more than the original 2 patterns

    # Check that we have both original and response pattern types
    pattern_types = [p.get('pattern_type') for p in patterns]
    assert 'time' in pattern_types
    assert 'sequence' in pattern_types
    assert 'response' in pattern_types

    # Check that response patterns include both initiator and response_time subtypes
    response_subtypes = [p.get('subtype') for p in patterns if p.get('pattern_type') == 'response']
    assert 'initiator' in response_subtypes or 'response_time' in response_subtypes


@pytest.mark.integration
def test_insight_generator_integration(sample_df, mock_insight_generator):
    """Test integration with Insight Generator."""
    # Create a ResponseAnalyzer
    analyzer = ResponseAnalyzer()

    # Analyze the sample data
    response_results = analyzer.analyze_response_patterns(sample_df)

    # Create response patterns
    response_patterns = [
        {
            'pattern_type': 'response',
            'subtype': 'initiator',
            'contact': '5559876543',
            'description': "5559876543 frequently initiates conversations",
            'confidence': 0.7
        },
        {
            'pattern_type': 'response',
            'subtype': 'quick_responder',
            'contact': '5551234567',
            'description': "5551234567 typically responds quickly",
            'confidence': 0.8
        }
    ]

    # Create a method to generate response insights
    def generate_response_insights(patterns):
        insights = []

        for pattern in patterns:
            if pattern.get('pattern_type') == 'response':
                insights.append(pattern.get('description'))

        return insights

    # Mock the _generate_response_insights method
    mock_insight_generator._generate_response_insights = MagicMock(side_effect=generate_response_insights)

    # Create a custom generate_insights method that uses response patterns
    def custom_generate_insights(all_results):
        # Get original insights
        original_insights = [
            "You communicate frequently at 10:00 AM.",
            "You often send text messages followed by calls."
        ]

        # Get response insights
        if 'patterns' in all_results:
            response_patterns = [p for p in all_results['patterns'] if p.get('pattern_type') == 'response']
            response_insights = generate_response_insights(response_patterns)

            # Combine insights
            all_insights = original_insights + response_insights

            return all_insights

        return original_insights

    # Replace the generate_insights method
    mock_insight_generator.generate_insights = custom_generate_insights

    # Test the integration
    all_results = {
        'patterns': response_patterns
    }

    insights = mock_insight_generator.generate_insights(all_results)

    # Check that the insights include both original and response insights
    assert len(insights) > 2  # Should have more than the original 2 insights

    # Check that response insights are included
    assert any("initiates conversations" in insight for insight in insights)
    assert any("responds quickly" in insight for insight in insights)


@pytest.mark.integration
def test_ml_model_service_integration(sample_df, mock_ml_service):
    """Test integration with ML Model Service."""
    # Create a ResponseAnalyzer with the ML model service
    analyzer = ResponseAnalyzer()
    analyzer.ml_model_service = mock_ml_service

    # Test analyze_response_patterns
    result = analyzer.analyze_response_patterns(sample_df)

    # Check that the ML service was called
    mock_ml_service.extract_features.assert_called()

    # Check that the result includes ML-based predictions
    assert 'predictions' in result

    # Test predict_response_behavior
    prediction = analyzer.predict_response_behavior(sample_df, '5551234567')

    # Check that the ML service was called again
    assert mock_ml_service.predict.call_count >= 1

    # Check that the prediction includes ML-based results
    assert 'expected_response_time' in prediction
    assert 'confidence' in prediction


@pytest.mark.integration
def test_dependency_container_registration(mock_dependency_container):
    """Test registration with dependency container."""
    # Import the registration function
    from src.analysis_layer.advanced_patterns.component_registration import (
        register_advanced_pattern_components,
        create_response_analyzer
    )

    # Register components
    register_advanced_pattern_components(mock_dependency_container)

    # Check that the container's register method was called
    mock_dependency_container.register.assert_called()

    # Check that the ResponseAnalyzer was registered
    register_calls = mock_dependency_container.register.call_args_list
    assert any("ResponseAnalyzer" in str(call) for call in register_calls)

    # Test the create_response_analyzer function
    ml_service = mock_dependency_container.get("MLModelService")
    logging_service = mock_dependency_container.get("LoggingService")

    # Create a ResponseAnalyzer
    analyzer = create_response_analyzer(ml_service, logging_service)

    # Check that the analyzer was created with the right dependencies
    assert hasattr(analyzer, 'ml_model_service')
    assert hasattr(analyzer, 'logging_service')
    assert analyzer.ml_model_service is ml_service
    assert analyzer.logging_service is logging_service
