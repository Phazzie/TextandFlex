"""
Tests for the machine learning models module.
"""
import pytest
import pandas as pd
import numpy as np
import os
from datetime import datetime
from src.analysis_layer.ml_models import (
    MLModel, TimePatternModel, ContactPatternModel,
    AnomalyDetectionModel, extract_features, run_model_evaluation, evaluate_model
)
@pytest.fixture
def sample_dataframe():
    """Sample DataFrame similar to what might come from the repository."""
    data = {
        'Timestamp': pd.to_datetime(['2025-04-20 09:00', '2025-04-20 10:30', '2025-04-21 11:00', '2025-04-21 09:15', '2025-04-22 15:00']),
        'Contact': ['Alice', 'Bob', 'Alice', 'Charlie', 'Bob'],
        'MessageLength': [20, 150, 35, 80, 10]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_dataframe_missing_cols():
    """Sample DataFrame with missing columns needed for feature extraction."""
    data = {
        'Contact': ['Alice', 'Bob'],
        'SomeOtherCol': [1, 2]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_features(sample_dataframe):
    """Sample features extracted from the dataframe."""
    return extract_features(sample_dataframe)

@pytest.fixture
def sample_labels():
    """Sample labels (e.g., for a supervised task)."""
    return pd.Series([0, 1, 0, 1, 0]) # Example binary labels

# --- Test Cases ---

@pytest.mark.unit
def test_base_ml_model_creation():
    """Test creating a base MLModel."""
    model = MLModel()
    assert model is not None
    assert model.model is None
    assert model.last_error is None
    assert not model.is_trained
    # Base model methods should raise NotImplementedError
    with pytest.raises(NotImplementedError):
        model._train_model(pd.DataFrame())
    with pytest.raises(NotImplementedError):
        model._predict_model(pd.DataFrame())
    with pytest.raises(NotImplementedError):
        model._evaluate_model(pd.DataFrame(), pd.Series())

@pytest.mark.unit
def test_model_predict_evaluate_before_train():
    """Test calling predict/evaluate before training."""
    model = TimePatternModel() # Use a subclass
    assert model.predict(pd.DataFrame()) is None
    assert model.last_error == "Model not trained"
    assert model.evaluate(pd.DataFrame(), pd.Series()) == {}
    assert model.last_error == "Model not trained"


@pytest.mark.unit
def test_time_pattern_model(sample_features, sample_labels):
    """Test the TimePatternModel implementation."""
    model = TimePatternModel()
    assert not model.is_trained
    # Test training
    model.train(sample_features, sample_labels)
    assert model.is_trained
    assert model.model == "trained_time_model_placeholder"
    assert model.last_error is None
    # Test prediction
    preds = model.predict(sample_features)
    assert isinstance(preds, list)
    assert len(preds) == len(sample_features)
    assert all(p.startswith("hour_pattern_") for p in preds)
    # Test evaluation
    metrics = model.evaluate(sample_features, sample_labels)
    assert metrics == {'placeholder_accuracy': 0.9}

@pytest.mark.unit
def test_contact_pattern_model(sample_features):
    """Test the ContactPatternModel implementation (unsupervised)."""
    model = ContactPatternModel()
    assert not model.is_trained
    model.train(sample_features) # No labels needed for unsupervised learning
    assert model.is_trained
    assert model.model == "trained_contact_model_placeholder"
    preds = model.predict(sample_features)
    assert isinstance(preds, list)
    assert len(preds) == len(sample_features)
    assert all(p in ['groupA', 'groupB'] for p in preds)
    
    # Test evaluation with both None and empty series for labels
    # This tests the model's ability to handle unsupervised evaluation
    metrics = model.evaluate(sample_features, None)
    assert metrics == {'placeholder_silhouette_score': 0.7}
    metrics_empty_series = model.evaluate(sample_features, pd.Series(dtype=int))
    assert metrics_empty_series == {'placeholder_silhouette_score': 0.7}


@pytest.mark.unit
def test_anomaly_detection_model(sample_features):
    """Test the AnomalyDetectionModel implementation (unsupervised)."""
    model = AnomalyDetectionModel()
    assert not model.is_trained
    model.train(sample_features)
    assert model.is_trained
    assert model.model == "trained_anomaly_model_placeholder"
    anomalies = model.predict(sample_features)
    assert isinstance(anomalies, pd.Series) 
    assert len(anomalies) == len(sample_features)
    assert anomalies.isin([0, 1]).all() # Should contain only 0s and 1s
    
    # Test evaluation with unsupervised metrics
    metrics = model.evaluate(sample_features, None)
    assert 'num_anomalies_detected' in metrics
    assert isinstance(metrics['num_anomalies_detected'], float)


@pytest.mark.unit
def test_feature_extraction(sample_dataframe):
    """Test feature extraction function."""
    features = extract_features(sample_dataframe)
    assert isinstance(features, pd.DataFrame)
    assert not features.empty
    assert 'hour' in features.columns
    assert 'dayofweek' in features.columns
    assert 'is_weekend' in features.columns
    assert 'message_length' in features.columns
    assert features.shape[0] == sample_dataframe.shape[0]
    assert not features.isnull().any().any() # Check for NaNs after fillna(0)
    
    # Check dtypes
    assert features['hour'].dtype == int
    assert features['dayofweek'].dtype == int
    assert features['is_weekend'].dtype == int # Boolean becomes int after fillna(0).astype(int)
    # Message length can be either int or float depending on whether NaNs were present
    assert features['message_length'].dtype in (int, float, np.int64, np.float64)


@pytest.mark.unit
def test_feature_extraction_missing_cols(sample_dataframe_missing_cols, caplog):
    """Test feature extraction with missing essential columns."""
    features = extract_features(sample_dataframe_missing_cols)
    assert features.empty # Should return empty if essential columns are missing
    assert "Feature extraction resulted in an empty DataFrame" in caplog.text

@pytest.mark.unit
def test_feature_extraction_empty_df():
    """Test feature extraction with an empty DataFrame."""
    features = extract_features(pd.DataFrame())
    assert features.empty
