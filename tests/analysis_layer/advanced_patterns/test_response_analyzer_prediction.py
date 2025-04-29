"""
Tests for the response behavior prediction functionality of the ResponseAnalyzer.

This module contains tests for the predict_response_behavior method of the ResponseAnalyzer.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer
from src.analysis_layer.ml_model_service import MLModelService
from src.analysis_layer.ml_exceptions import MLError, PredictionError


@pytest.fixture
def prediction_df():
    """Create a DataFrame for testing prediction functionality."""
    data = [
        # Contact 1: Consistent quick responses
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 11, 4), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 12, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 12, 3), 'phone_number': '5551234567', 'message_type': 'received'},

        # Contact 2: Consistent slow responses
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 15, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 16, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 17, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 18, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 19, 0), 'phone_number': '5559876543', 'message_type': 'received'},

        # Contact 3: Variable response times
        {'timestamp': datetime(2023, 1, 2, 9, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 2, 9, 5), 'phone_number': '5552223333', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 2, 10, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 2, 11, 0), 'phone_number': '5552223333', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 2, 12, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 2, 12, 10), 'phone_number': '5552223333', 'message_type': 'received'},
    ]

    return pd.DataFrame(data)


@pytest.fixture
def prediction_with_history_df():
    """Create a DataFrame with extensive history for prediction testing."""
    data = []

    # Contact 1: Consistent quick responses over 30 days
    for day in range(1, 31):
        data.extend([
            {'timestamp': datetime(2023, 1, day, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, day, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        ])

    # Contact 2: Gradually slowing responses over 30 days
    for day in range(1, 31):
        response_time = 5 + day  # Response time increases by 1 minute each day
        data.extend([
            {'timestamp': datetime(2023, 1, day, 14, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, day, 14, response_time), 'phone_number': '5559876543', 'message_type': 'received'},
        ])

    # Contact 3: Day-of-week pattern (fast on weekdays, slow on weekends)
    for day in range(1, 31):
        date = datetime(2023, 1, day)
        is_weekend = date.weekday() >= 5  # 5=Saturday, 6=Sunday
        response_time = 30 if is_weekend else 5

        data.extend([
            {'timestamp': datetime(2023, 1, day, 12, 0), 'phone_number': '5552223333', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, day, 12, response_time), 'phone_number': '5552223333', 'message_type': 'received'},
        ])

    return pd.DataFrame(data)


@pytest.fixture
def mock_ml_service_for_prediction():
    """Create a mock ML model service for prediction testing."""
    mock_service = MagicMock(spec=MLModelService)

    # Mock the extract_features method
    mock_service.extract_features.return_value = {
        'response_times': [300, 300, 1800, 3600, 2700, 180],
        'message_counts': {'5551234567': 6, '5559876543': 6, '5552223333': 6},
        'sent_received_ratios': {'5551234567': 1.0, '5559876543': 1.0, '5552223333': 1.0},
        'time_of_day_features': [0.5, 0.2, 0.3],
        'day_of_week_features': [0.1, 0.2, 0.1, 0.2, 0.2, 0.1, 0.1]
    }

    # Mock the predict method
    def mock_predict(model_name, features, **kwargs):
        if model_name == "ResponseModel":
            contact = kwargs.get('contact', '5551234567')

            # Return different predictions based on contact
            if contact == '5551234567':
                return {
                    'predictions': {
                        'expected_response_time': 300,  # 5 minutes
                        'response_probability': 0.95,
                        'confidence': 0.9,
                        'factors': ['consistent_history', 'time_of_day', 'message_content']
                    },
                    'model_name': 'ResponseModel',
                    'model_version': '1.0'
                }
            elif contact == '5559876543':
                return {
                    'predictions': {
                        'expected_response_time': 3600,  # 1 hour
                        'response_probability': 0.8,
                        'confidence': 0.75,
                        'factors': ['consistent_history', 'time_of_day']
                    },
                    'model_name': 'ResponseModel',
                    'model_version': '1.0'
                }
            else:
                return {
                    'predictions': {
                        'expected_response_time': 1800,  # 30 minutes
                        'response_probability': 0.6,
                        'confidence': 0.5,
                        'factors': ['variable_history']
                    },
                    'model_name': 'ResponseModel',
                    'model_version': '1.0'
                }
        else:
            return {'predictions': {}, 'model_name': model_name, 'model_version': '1.0'}

    mock_service.predict = MagicMock(side_effect=mock_predict)

    return mock_service


@pytest.mark.unit
def test_predict_response_behavior_basic(prediction_df):
    """Test basic prediction functionality without ML model service."""
    analyzer = ResponseAnalyzer()
    result = analyzer.predict_response_behavior(prediction_df, '5551234567')

    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'expected_response_time' in result
    assert 'response_probability' in result
    assert 'confidence' in result

    # Check specific values for contact with quick responses
    assert result['expected_response_time'] <= 300  # 5 minutes or less
    assert result['response_probability'] >= 0.8  # High probability

    # Test with slow response contact
    result = analyzer.predict_response_behavior(prediction_df, '5559876543')
    assert result['expected_response_time'] >= 3600  # 1 hour or more


@pytest.mark.unit
def test_predict_response_behavior_with_ml_service(prediction_df, mock_ml_service_for_prediction):
    """Test prediction functionality with ML model service."""
    analyzer = ResponseAnalyzer()
    analyzer.ml_model_service = mock_ml_service_for_prediction

    # Test with quick response contact
    result = analyzer.predict_response_behavior(prediction_df, '5551234567')

    # Check that the ML service was called
    mock_ml_service_for_prediction.extract_features.assert_called()
    mock_ml_service_for_prediction.predict.assert_called()

    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'expected_response_time' in result
    assert 'response_probability' in result
    assert 'confidence' in result
    assert 'factors' in result
    assert 'model_name' in result

    # Check specific values
    assert result['expected_response_time'] == 300
    assert result['response_probability'] == 0.95
    assert result['confidence'] == 0.9
    assert 'consistent_history' in result['factors']
    assert result['model_name'] == 'ResponseModel'


@pytest.mark.unit
def test_predict_response_behavior_with_history(prediction_with_history_df):
    """Test prediction with extensive history."""
    analyzer = ResponseAnalyzer()

    # Test with contact that has consistent quick responses
    result = analyzer.predict_response_behavior(prediction_with_history_df, '5551234567')

    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'expected_response_time' in result
    assert 'response_probability' in result
    assert 'confidence' in result

    # Check specific values
    assert result['expected_response_time'] <= 300  # 5 minutes or less
    assert result['confidence'] >= 0.8  # High confidence due to consistent history

    # Test with contact that has gradually slowing responses
    result = analyzer.predict_response_behavior(prediction_with_history_df, '5559876543')

    # Check that the prediction reflects the trend
    assert result['expected_response_time'] > 300  # Should be more than 5 minutes
    assert 'trend' in result  # Should detect the slowing trend

    # Test with contact that has day-of-week pattern
    result = analyzer.predict_response_behavior(prediction_with_history_df, '5552223333')

    # Check that the prediction includes day-of-week factor
    assert 'day_of_week_factor' in result


@pytest.mark.unit
def test_prediction_confidence(prediction_df, prediction_with_history_df):
    """Test confidence score calculation."""
    analyzer = ResponseAnalyzer()

    # Test with limited history
    result_limited = analyzer.predict_response_behavior(prediction_df, '5551234567')

    # Test with extensive history
    result_extensive = analyzer.predict_response_behavior(prediction_with_history_df, '5551234567')

    # Confidence should be higher with more history
    assert result_extensive['confidence'] > result_limited['confidence']

    # Test with variable response times
    result_variable = analyzer.predict_response_behavior(prediction_df, '5552223333')

    # Confidence should be lower with variable response times
    assert result_variable['confidence'] < result_limited['confidence']


@pytest.mark.unit
def test_prediction_factors(prediction_with_history_df, mock_ml_service_for_prediction):
    """Test identification of factors influencing prediction."""
    analyzer = ResponseAnalyzer(ml_model_service=mock_ml_service_for_prediction)

    # Test with ML service
    result = analyzer.predict_response_behavior(prediction_with_history_df, '5551234567')

    # Check that factors are included
    assert 'factors' in result
    assert len(result['factors']) >= 1

    # Test without ML service
    analyzer = ResponseAnalyzer()
    result = analyzer.predict_response_behavior(prediction_with_history_df, '5552223333')

    # Check that basic factors are still identified
    assert 'factors' in result
    assert len(result['factors']) >= 1


@pytest.mark.unit
def test_ml_model_integration(prediction_df, mock_ml_service_for_prediction):
    """Test integration with ML models."""
    analyzer = ResponseAnalyzer(ml_model_service=mock_ml_service_for_prediction)

    # Test with different contacts
    contacts = ['5551234567', '5559876543', '5552223333']

    for contact in contacts:
        result = analyzer.predict_response_behavior(prediction_df, contact)

        # Check that the ML service was called with the right parameters
        mock_ml_service_for_prediction.predict.assert_called()

        # Check that the result includes ML-specific fields
        assert 'model_name' in result
        assert 'model_version' in result
        assert result['model_name'] == 'ResponseModel'


@pytest.mark.unit
def test_ml_error_handling(prediction_df, mock_ml_service_for_prediction):
    """Test handling of ML service errors."""
    # Configure the mock to raise an error
    mock_ml_service_for_prediction.predict.side_effect = MLError("Test ML error")

    analyzer = ResponseAnalyzer()
    analyzer.ml_model_service = mock_ml_service_for_prediction
    result = analyzer.predict_response_behavior(prediction_df, '5551234567')

    # Check that the prediction still works without ML
    assert isinstance(result, dict)
    assert 'expected_response_time' in result
    assert 'response_probability' in result
    assert 'confidence' in result

    # Check that the error is logged
    assert analyzer.last_error is not None
    assert 'ml error' in analyzer.last_error.lower()

    # Check that the result indicates fallback to statistical prediction
    assert 'model_name' not in result
    assert 'fallback_to_statistical' in result
    assert result['fallback_to_statistical'] is True


@pytest.mark.unit
def test_unknown_contact(prediction_df):
    """Test prediction for an unknown contact."""
    analyzer = ResponseAnalyzer()
    result = analyzer.predict_response_behavior(prediction_df, '5550000000')  # Unknown contact

    # Check that the result has the expected structure
    assert isinstance(result, dict)
    assert 'expected_response_time' in result
    assert 'response_probability' in result
    assert 'confidence' in result

    # Check that confidence is low for unknown contact
    assert result['confidence'] < 0.5

    # Check that it uses overall average as fallback
    assert 'based_on_overall_average' in result
    assert result['based_on_overall_average'] is True


@pytest.mark.unit
def test_column_mapping_prediction(prediction_df):
    """Test that column mapping works correctly for prediction."""
    # Rename columns in the DataFrame
    df_renamed = prediction_df.rename(columns={
        'timestamp': 'time',
        'phone_number': 'contact',
        'message_type': 'direction'
    })

    # Create column mapping
    column_mapping = {
        'timestamp': 'time',
        'phone_number': 'contact',
        'message_type': 'direction'
    }

    analyzer = ResponseAnalyzer()
    result = analyzer.predict_response_behavior(df_renamed, '5551234567', column_mapping=column_mapping)

    # Check that the analysis works with the mapping
    assert isinstance(result, dict)
    assert 'expected_response_time' in result
    assert 'response_probability' in result
    assert 'confidence' in result


@pytest.mark.unit
def test_error_handling_prediction():
    """Test error handling in prediction."""
    analyzer = ResponseAnalyzer()

    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = analyzer.predict_response_behavior(empty_df, '5551234567')
    assert 'error' in result
    assert analyzer.last_error is not None

    # Test with missing columns
    df_missing_column = pd.DataFrame({
        'timestamp': [datetime(2023, 1, 1, 10, 0)],
        'phone_number': ['5551234567']
    })

    result = analyzer.predict_response_behavior(df_missing_column, '5551234567')
    assert 'error' in result
    assert analyzer.last_error is not None
