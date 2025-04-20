"""
Advanced tests for ML models with synthetic data patterns.
These tests simulate real-world usage with synthetic data containing clear patterns
that the models should be able to detect.
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

from src.analysis_layer.ml_models import (
    MLModel, 
    TimePatternModel, 
    ContactPatternModel, 
    AnomalyDetectionModel,
    extract_features, 
    evaluate_model
)

# ----- Test Fixtures -----

@pytest.fixture
def synthetic_time_pattern_data():
    """
    Create synthetic data with clear time patterns:
    - Morning weekday messages (6-9 AM, Mon-Fri)
    - Evening weekday messages (8-11 PM, Mon-Fri)
    - Weekend afternoon messages (1-5 PM, Sat-Sun)
    """
    # Generate 300 records with clear patterns
    np.random.seed(42)
    
    # Pattern 1: Morning weekday (100 records)
    morning_hours = np.random.randint(6, 10, 100)  # 6-9 AM
    morning_days = np.random.randint(0, 5, 100)    # Mon-Fri (0-4)
    
    # Pattern 2: Evening weekday (100 records)
    evening_hours = np.random.randint(20, 24, 100)  # 8-11 PM
    evening_days = np.random.randint(0, 5, 100)     # Mon-Fri (0-4)
    
    # Pattern 3: Weekend afternoon (100 records)
    weekend_hours = np.random.randint(13, 18, 100)  # 1-5 PM
    weekend_days = np.random.randint(5, 7, 100)     # Sat-Sun (5-6)
    
    # Combine patterns
    hours = np.concatenate([morning_hours, evening_hours, weekend_hours])
    days = np.concatenate([morning_days, evening_days, weekend_days])
    
    # Add message lengths (not pattern-specific)
    message_lengths = np.random.randint(10, 200, 300)
    
    # Create timestamps and DataFrame
    timestamps = pd.date_range(start='2023-01-01', periods=300, freq='H')
    np.random.shuffle(timestamps)  # Shuffle to avoid sequential ordering
    
    # Create DataFrame with the standard column names
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'hour': hours,
        'dayofweek': days,
        'MessageLength': message_lengths,
        'Contact': np.random.choice(['Alice', 'Bob', 'Charlie', 'Dave'], 300)
    })
    
    return df

@pytest.fixture
def synthetic_contact_pattern_data():
    """
    Create synthetic data with clear contact patterns:
    - Alice: short messages (5-20 chars)
    - Bob: medium messages (50-100 chars)
    - Charlie: long messages (150-300 chars)
    - Dave: mixed length messages (random)
    """
    np.random.seed(42)
    
    # 300 records with clear contact-based patterns
    contacts = np.random.choice(['Alice', 'Bob', 'Charlie', 'Dave'], 300)
    
    # Define message lengths based on contact
    message_lengths = []
    for contact in contacts:
        if contact == 'Alice':
            message_lengths.append(np.random.randint(5, 21))  # Short messages
        elif contact == 'Bob':
            message_lengths.append(np.random.randint(50, 101))  # Medium messages
        elif contact == 'Charlie':
            message_lengths.append(np.random.randint(150, 301))  # Long messages
        else:  # Dave
            message_lengths.append(np.random.randint(5, 301))  # Random lengths
    
    # Create DataFrame
    timestamps = pd.date_range(start='2023-01-01', periods=300, freq='H')
    np.random.shuffle(timestamps)  # Shuffle to avoid sequential ordering
    
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Contact': contacts,
        'MessageLength': message_lengths,
        'hour': pd.DatetimeIndex(timestamps).hour,
        'dayofweek': pd.DatetimeIndex(timestamps).dayofweek
    })
    
    return df

@pytest.fixture
def synthetic_anomaly_data():
    """
    Create synthetic data with clear anomalies:
    - Normal messages: 10-100 chars, within typical hours (7AM-11PM)
    - Anomalous messages: 
      - Very long messages (500-1000 chars)
      - Very late night messages (1AM-4AM)
    """
    np.random.seed(42)
    
    # 280 normal records
    normal_hours = np.random.randint(7, 24, 280)  # 7AM-11PM
    normal_lengths = np.random.randint(10, 101, 280)  # 10-100 chars
    normal_days = np.random.randint(0, 7, 280)
    normal_contacts = np.random.choice(['Alice', 'Bob', 'Charlie'], 280)
    
    # 20 anomalous records (both late night and long messages)
    anomaly_hours = np.random.randint(1, 5, 20)  # 1AM-4AM
    anomaly_lengths = np.random.randint(500, 1001, 20)  # 500-1000 chars
    anomaly_days = np.random.randint(0, 7, 20)
    anomaly_contacts = np.random.choice(['Unknown', 'Scammer'], 20)
    
    # Combine and create DataFrame
    hours = np.concatenate([normal_hours, anomaly_hours])
    message_lengths = np.concatenate([normal_lengths, anomaly_lengths])
    days = np.concatenate([normal_days, anomaly_days])
    contacts = np.concatenate([normal_contacts, anomaly_contacts])
    
    # Create anomaly labels (1 for anomalies, 0 for normal)
    anomaly_labels = np.concatenate([np.zeros(280), np.ones(20)])
    
    # Create timestamps for each record
    timestamps = pd.date_range(start='2023-01-01', periods=300, freq='H')
    np.random.shuffle(timestamps)  # Shuffle to mix normal and anomalous data
    
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Contact': contacts,
        'MessageLength': message_lengths,
        'hour': hours,
        'dayofweek': days,
        'is_anomaly': anomaly_labels
    })
    
    return df

# ----- Test Cases -----

def test_time_pattern_model_with_real_data(synthetic_time_pattern_data):
    """Test if TimePatternModel can identify clear time clusters"""
    # Extract features
    features = synthetic_time_pattern_data[['hour', 'dayofweek']]
    
    # Create and train model
    model = TimePatternModel()
    model.train(features)
    
    assert model.is_trained
    
    # Predict clusters
    predictions = model.predict(features)
    
    # We should get 3 clusters (roughly matching our 3 patterns)
    assert predictions is not None
    assert not predictions.empty
    
    # The model should identify at least 2 distinct clusters (morning/evening and weekend)
    # with silhouette score > 0.3
    metrics = model.evaluate(features)
    assert 'silhouette_score' in metrics
    assert metrics['silhouette_score'] > 0.3

def test_contact_pattern_model_with_real_data(synthetic_contact_pattern_data):
    """Test if ContactPatternModel can cluster contacts with similar behaviors"""
    # Extract features
    features = synthetic_contact_pattern_data[['message_length']]
    
    # Create and train model
    model = ContactPatternModel()
    model.train(features)
    
    assert model.is_trained
    
    # Predict clusters
    predictions = model.predict(features)
    
    assert predictions is not None
    assert not predictions.empty
    
    # The model should cluster contacts with similar behaviors
    metrics = model.evaluate(features)
    assert 'silhouette_score' in metrics
    assert metrics['silhouette_score'] > 0.3

def test_anomaly_detection_model_with_real_data(synthetic_anomaly_data):
    """Test if AnomalyDetectionModel can detect anomalous messages"""
    # Extract features (excluding the 'is_anomaly' label)
    features = synthetic_anomaly_data[['hour', 'dayofweek', 'message_length']]
    true_labels = synthetic_anomaly_data['is_anomaly']
    
    # Create and train model
    model = AnomalyDetectionModel()
    model.train(features)
    
    assert model.is_trained
    
    # Predict anomalies
    predictions = model.predict(features)
    
    assert predictions is not None
    assert not predictions.empty
    
    # Calculate accuracy (should be > 0.9 since we created clear anomalies)
    # 0:normal, 1:anomaly for both predictions and true_labels
    metrics = model.evaluate(features, true_labels)
    
    assert 'num_anomalies_detected' in metrics
    assert metrics['num_anomalies_detected'] > 0
    
    # We created 20 anomalies
    assert abs(metrics['num_anomalies_detected'] - 20) < 10  # Allow some error margin
    
    if 'accuracy_if_labeled' in metrics:
        assert metrics['accuracy_if_labeled'] > 0.85  # At least 85% accuracy

def test_feature_extraction_with_default_mapping(synthetic_time_pattern_data):
    """Test feature extraction with default column mapping"""
    features = extract_features(synthetic_time_pattern_data)
    
    # Expected columns should be present
    assert 'hour' in features.columns
    assert 'dayofweek' in features.columns
    assert 'is_weekend' in features.columns
    assert 'message_length' in features.columns
    
    # No missing values
    assert not features.isnull().any().any()
    
    # Correct data types
    assert features['hour'].dtype == int
    assert features['dayofweek'].dtype == int
    assert features['is_weekend'].dtype == int
    assert features['message_length'].dtype == int

def test_feature_extraction_with_custom_mapping():
    """Test feature extraction with custom column mapping"""
    # Create DataFrame with different column names
    df = pd.DataFrame({
        'msg_time': pd.date_range(start='2023-01-01', periods=50, freq='H'),
        'person': np.random.choice(['Alice', 'Bob', 'Charlie'], 50),
        'length': np.random.randint(10, 200, 50)
    })
    
    # Custom mapping
    custom_mapping = {
        'timestamp': 'msg_time',
        'contact': 'person',
        'message_length': 'length'
    }
    
    features = extract_features(df, custom_mapping)
    
    # Expected columns should be present
    assert 'hour' in features.columns
    assert 'dayofweek' in features.columns
    assert 'is_weekend' in features.columns
    assert 'message_length' in features.columns
    
    # No missing values
    assert not features.isnull().any().any()
    
    # Correct data types
    assert features['hour'].dtype == int
    assert features['dayofweek'].dtype == int
    assert features['is_weekend'].dtype == int
    assert features['message_length'].dtype == int

def test_model_persistence():
    """Test saving and loading ML models"""
    # Create a simple model
    model = TimePatternModel()
    
    # Create synthetic data
    df = pd.DataFrame({
        'hour': np.random.randint(0, 24, 100),
        'dayofweek': np.random.randint(0, 7, 100)
    })
    
    model.train(df)
    assert model.is_trained
    
    # Create a temporary directory for saving the model
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "time_model.joblib"
        
        # Save the model
        success = model.save(file_path)
        assert success
        assert file_path.exists()
        
        # Load into a new model instance
        new_model = TimePatternModel()
        success = new_model.load(file_path)
        
        assert success
        assert new_model.is_trained
        
        # Make predictions with both models and ensure they match
        orig_preds = model.predict(df)
        new_preds = new_model.predict(df)
        
        assert orig_preds.equals(new_preds)

def test_model_error_handling():
    """Test ML model error handling"""
    # Case 1: Empty features
    empty_df = pd.DataFrame()
    model = TimePatternModel()
    model.train(empty_df)
    
    assert not model.is_trained
    assert model.last_error is not None
    
    # Case 2: Missing required columns
    invalid_df = pd.DataFrame({
        'irrelevant': np.random.random(10)
    })
    
    model = ContactPatternModel()
    model.train(invalid_df)
    
    assert not model.is_trained
    assert model.model is None
