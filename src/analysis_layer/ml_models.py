"""
Machine Learning Models Module
------------------
Contains ML models for pattern detection and analysis.
"""

import pandas as pd
from typing import Dict, List, Any, Union
# Import necessary ML libraries when implementing actual models
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest # Example for anomaly detection
from sklearn.cluster import KMeans # Example for clustering/patterns
from sklearn.metrics import silhouette_score, accuracy_score # Example metrics
import joblib # For saving/loading models
import os
from pathlib import Path
import numpy as np

from ..logger import get_logger
# Import file_io utilities (breaking into multiple lines for readability)
from ..utils.file_io import (
    ensure_directory_exists,
    save_pickle,
    load_pickle
)

logger = get_logger("ml_models")

# Default column mapping - adjust as needed based on actual data source
DEFAULT_COLUMN_MAPPING = {
    'timestamp': 'Timestamp',
    'contact': 'Contact',
    'message_length': 'MessageLength',
    # Add other columns if needed by features
}

class MLModel:
    """Base class for machine learning models."""

    def __init__(self):
        """Initialize the base model."""
        self.model = None
        self._last_error = None
        self._is_trained = False

    def train(self, features: pd.DataFrame, labels: pd.Series = None):
        \"\"\"Train the model. Labels are optional for unsupervised models.\"\"\"
        if features.empty:
            logger.warning(f"Cannot train {self.__class__.__name__}: features DataFrame is empty.")
            self._last_error = "Input features are empty"
            self._is_trained = False
            return
        try:
            self._train_model(features, labels)
            self._is_trained = True
            logger.info(f"{self.__class__.__name__} trained successfully.")
        except Exception as exception:
            logger.error(f"Error training {self.__class__.__name__}: {exception}")
            self._last_error = str(exception)
            self._is_trained = False

    def _train_model(self, features: pd.DataFrame, labels: pd.Series = None):
        """Internal training logic to be implemented by subclasses."""
        raise NotImplementedError("Train method must be implemented by subclasses.")

    def predict(self, features: pd.DataFrame) -> Any:
        """Make predictions using the trained model."""
        if not self._is_trained:
            logger.error(f"{self.__class__.__name__} is not trained. Cannot predict.")
            self._last_error = "Model not trained"
            return None
        try:
            predictions = self._predict_model(features)
            logger.info(f"Predictions made using {self.__class__.__name__}.")
            return predictions
        except Exception as exception:
            logger.error(f"Error predicting with {self.__class__.__name__}: {exception}")
            self._last_error = str(exception)
            return None

    def _predict_model(self, features: pd.DataFrame) -> Any:
        """Internal prediction logic to be implemented by subclasses."""
        raise NotImplementedError("Predict method must be implemented by subclasses.")

    def evaluate(self, test_features: pd.DataFrame, test_labels: pd.Series) -> Dict[str, float]:
        """Evaluate the model's performance."""
        if not self._is_trained:
            logger.error(f"{self.__class__.__name__} is not trained. Cannot evaluate.")
            self._last_error = "Model not trained"
            return {}
        try:
            metrics = self._evaluate_model(test_features, test_labels)
            logger.info(f"Evaluation complete for {self.__class__.__name__}: {metrics}")
            return metrics
        except Exception as exception:
            logger.error(f"Error evaluating {self.__class__.__name__}: {exception}")
            self._last_error = str(exception)
            return {}

    def _evaluate_model(self, test_features: pd.DataFrame, test_labels: pd.Series) -> Dict[str, float]:
        """Internal evaluation logic to be implemented by subclasses."""
        # Example: return {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0}
        raise NotImplementedError("Evaluate method must be implemented by subclasses.")

    @property
    def is_trained(self) -> bool:
        """Check if the model has been trained."""
        return self._is_trained

    @property
    def last_error(self) -> str | None:
        """Get the last error message."""
        return self._last_error

    def save(self, file_path: Union[str, Path]):
        \"\"\"Save the trained model to a file.\"\"\"
        if not self._is_trained or self.model is None:
            logger.error(f"Cannot save {self.__class__.__name__}: Model is not trained.")
            self._last_error = "Model not trained, cannot save."
            return False
        try:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            ensure_directory_exists(path.parent)
            joblib.dump(self.model, path)
            logger.info(f"Saved {self.__class__.__name__} model to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving {self.__class__.__name__} model to {file_path}: {e}")
            self._last_error = f"Failed to save model: {e}"
            return False

    def load(self, file_path: Union[str, Path]):
        \"\"\"Load a trained model from a file.\"\"\"
        try:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            if not path.exists():
                logger.error(f"Cannot load {self.__class__.__name__}: File not found at {path}")
                self._last_error = "Model file not found."
                self._is_trained = False
                return False
            self.model = joblib.load(path)
            self._is_trained = True
            self._last_error = None
            logger.info(f"Loaded {self.__class__.__name__} model from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading {self.__class__.__name__} model from {file_path}: {e}")
            self._last_error = f"Failed to load model: {e}"
            self._is_trained = False
            return False

    # TODO: Add methods for model versioning if needed
    # def get_version(self): -> str
    # def set_version(self, version: str):

    # TODO: Consider adding support for incremental learning (partial_fit)
    # if the underlying sklearn model supports it.


class TimePatternModel(MLModel):
    \"\"\"Model for predicting time-based patterns. (Example using simple classification)\"\"\"

    def _train_model(self, features: pd.DataFrame, labels: pd.Series = None):
        # Example: Using KMeans to find clusters in time features (hour, dayofweek)
        # This is unsupervised, so labels are ignored.
        if features.empty or features.shape[1] == 0:
             logger.warning("TimePatternModel training skipped: No features provided.")
             self.model = None
             return

        # Use relevant features like 'hour', 'dayofweek'
        time_features = features[['hour', 'dayofweek']]
        # Simple KMeans example
        self.model = KMeans(n_clusters=3, random_state=42, n_init=10) # Specify n_init
        self.model.fit(time_features)
        logger.info("TimePatternModel trained using KMeans.")


    def _predict_model(self, features: pd.DataFrame) -> Any:
        # Predict cluster labels based on time features
        if self.model is None or features.empty or features.shape[1] == 0:
             logger.warning("TimePatternModel prediction skipped: Model not trained or no features.")
             return pd.Series(dtype=int)

        time_features = features[['hour', 'dayofweek']]
        preds = self.model.predict(time_features)
        return pd.Series(preds, index=features.index)


    def _evaluate_model(self, test_features: pd.DataFrame, test_labels: pd.Series = None) -> Dict[str, float]:
        # Evaluate clustering using silhouette score (unsupervised metric)
        if self.model is None or test_features.empty or test_features.shape[1] < 2:
             logger.warning("TimePatternModel evaluation skipped: Model not trained or insufficient features.")
             return {}

        time_features = test_features[['hour', 'dayofweek']]
        if len(time_features) < 2: # Silhouette score requires at least 2 samples
            logger.warning("TimePatternModel evaluation skipped: Need at least 2 samples for silhouette score.")
            return {}

        labels = self.model.predict(time_features)
        try:
            score = silhouette_score(time_features, labels)
            return {'silhouette_score': score}
        except ValueError as ve:
            logger.warning(f"Could not calculate silhouette score: {ve}")
            return {'silhouette_score': np.nan} # Return NaN if score calculation fails


class ContactPatternModel(MLModel):
    \"\"\"Model for predicting contact-based patterns (e.g., grouping contacts).\"\"\"

    def _train_model(self, features: pd.DataFrame, labels: pd.Series = None):
        # Example: Using KMeans based on 'message_length' and maybe other contact-specific features
        if features.empty or 'message_length' not in features.columns:
             logger.warning("ContactPatternModel training skipped: No 'message_length' feature.")
             self.model = None
             return

        contact_features = features[['message_length']] # Add more features if available
        self.model = KMeans(n_clusters=2, random_state=42, n_init=10) # Example: 2 groups
        self.model.fit(contact_features)
        logger.info("ContactPatternModel trained using KMeans.")


    def _predict_model(self, features: pd.DataFrame) -> Any:
        if self.model is None or features.empty or 'message_length' not in features.columns:
             logger.warning("ContactPatternModel prediction skipped: Model not trained or no 'message_length' feature.")
             return pd.Series(dtype=int)

        contact_features = features[['message_length']]
        preds = self.model.predict(contact_features)
        return pd.Series(preds, index=features.index)


    def _evaluate_model(self, test_features: pd.DataFrame, test_labels: pd.Series = None) -> Dict[str, float]:
        if self.model is None or test_features.empty or 'message_length' not in test_features.columns:
             logger.warning("ContactPatternModel evaluation skipped: Model not trained or no 'message_length' feature.")
             return {}

        contact_features = test_features[['message_length']]
        if len(contact_features) < 2:
            logger.warning("ContactPatternModel evaluation skipped: Need at least 2 samples for silhouette score.")
            return {}

        labels = self.model.predict(contact_features)
        try:
            score = silhouette_score(contact_features, labels)
            return {'silhouette_score': score}
        except ValueError as ve:
            logger.warning(f"Could not calculate silhouette score: {ve}")
            return {'silhouette_score': np.nan}


class AnomalyDetectionModel(MLModel):
    \"\"\"Model for detecting anomalies (Unsupervised Example - IsolationForest).\"\""

    def _train_model(self, features: pd.DataFrame, labels: pd.Series = None):
        # Unsupervised model fits to the data
        if features.empty or features.shape[1] == 0:
             logger.warning("AnomalyDetectionModel training skipped: No features provided.")
             self.model = None
             return

        # Example: Use all available features
        self.model = IsolationForest(contamination='auto', random_state=42)
        self.model.fit(features)
        logger.info("AnomalyDetectionModel trained using IsolationForest.")


    def _predict_model(self, features: pd.DataFrame) -> Any:
        # Predict returns 1 for inliers, -1 for outliers (anomalies)
        if self.model is None or features.empty or features.shape[1] == 0:
             logger.warning("AnomalyDetectionModel prediction skipped: Model not trained or no features.")
             return pd.Series(dtype=int)

        # Convert predictions: 1 (normal) -> 0, -1 (anomaly) -> 1
        predictions = self.model.predict(features)
        anomaly_flags = pd.Series(np.where(predictions == -1, 1, 0), index=features.index)
        return anomaly_flags


    def _evaluate_model(self, test_features: pd.DataFrame, test_labels: pd.Series = None) -> Dict[str, float]:
        # Evaluation for unsupervised anomaly detection.
        # If true labels are available (test_labels indicate true anomalies as 1),
        # we can calculate precision/recall. Otherwise, just report anomaly count/percentage.
        if self.model is None or test_features.empty or test_features.shape[1] == 0:
             logger.warning("AnomalyDetectionModel evaluation skipped: Model not trained or no features.")
             return {}

        predictions = self.predict(test_features) # Returns 0 for normal, 1 for anomaly
        num_anomalies = predictions.sum()
        total_samples = len(predictions)
        anomaly_percentage = (num_anomalies / total_samples) * 100 if total_samples > 0 else 0

        metrics = {
            'num_anomalies_detected': float(num_anomalies),
            'percentage_anomalies': anomaly_percentage
        }

        # If true labels are provided (and not all NaN/None)
        if test_labels is not None and not test_labels.isnull().all() and len(test_labels) == len(predictions):
            try:
                # Ensure labels are binary (0 or 1)
                true_labels_binary = test_labels.fillna(0).astype(int)
                accuracy = accuracy_score(true_labels_binary, predictions)
                # Add more metrics like precision, recall, F1 if needed
                metrics['accuracy_if_labeled'] = accuracy
            except Exception as e:
                logger.warning(f"Could not calculate accuracy for anomaly detection (requires binary labels): {e}")

        return metrics


def extract_features(df: pd.DataFrame, column_mapping: Dict = None) -> pd.DataFrame:
    """
    Extract features for ML models from the raw data, using column mapping.
    
    Args:
        df: Input DataFrame with raw data
        column_mapping: Optional dictionary to map feature names to columns in df
                        (e.g., {'timestamp': 'message_date'})
    
    Returns:
        DataFrame with extracted features
    """
    # Make a copy to avoid modifying the original
    df_local = df.copy()
    features = pd.DataFrame(index=df_local.index)
    
    # Merge default mapping with user mapping
    mapping = {**DEFAULT_COLUMN_MAPPING, **(column_mapping or {})}
    
    # Build lowercase column lookup for case-insensitive matching
    col_lookup = {col.lower(): col for col in df_local.columns}
    
    # Helper function to find column using mapping or direct match
    def find_column(key):
        # Try mapped value first (case insensitive)
        mapped_val = mapping.get(key)
        if mapped_val and mapped_val.lower() in col_lookup:
            return col_lookup[mapped_val.lower()]
            
        # Try the key directly (case insensitive)
        if key.lower() in col_lookup:
            return col_lookup[key.lower()]
            
        # No match found
        return None

    try:
        ts_col = find_col('timestamp')
        contact_col = find_col('contact')
        len_col = find_col('message_length')

        # Extract time-based features
        if ts_col and ts_col in df_local.columns:
            df_local[ts_col] = pd.to_datetime(df_local[ts_col], errors='coerce')
            features['hour'] = df_local[ts_col].dt.hour
            features['dayofweek'] = df_local[ts_col].dt.dayofweek
            features['is_weekend'] = df_local[ts_col].dt.dayofweek >= 5
            features = features.dropna(subset=['hour', 'dayofweek', 'is_weekend'])
        else:
            logger.warning(f"Timestamp column '{ts_col}' not found in DataFrame. Time features skipped.")

        if len_col and len_col in df_local.columns:
            features['message_length'] = df_local.loc[features.index, len_col]
        else:
            logger.warning(f"Message length column '{len_col}' not found. Length feature skipped.")

        # TODO: Add more sophisticated features:
        # - Time since last message from same contact (requires sorting and grouping by contact_col)
        # - Rolling message count per contact/time window
        # - Sentiment score (if NLP is added)
        # - TF-IDF vectors for message content (if applicable)

        # Handle potential missing columns gracefully
        if features.empty and not df_local.empty:
             logger.warning("Feature extraction resulted in an empty DataFrame. Check input columns and mapping.")
        elif not features.empty:
             logger.info(f"Extracted features: {list(features.columns)}")

    except KeyError as key_error:
         logger.error(f"Missing expected column during feature extraction based on mapping: {key_error}")
         return pd.DataFrame() # Return empty DataFrame on critical error
    except Exception as exception:
        logger.error(f"Error during feature extraction: {exception}")
        return pd.DataFrame() # Return empty DataFrame on critical error

    # Basic imputation: Fill missing values with 0 or median/mean
    # Using median for message_length as 0 might be misleading
    if 'message_length' in features:
        median_len = features['message_length'].median()
        features['message_length'] = features['message_length'].fillna(median_len if not pd.isna(median_len) else 0)

    # Fill remaining NaNs (e.g., from timestamp coercion) with 0
    features = features.fillna(0)

    # Ensure appropriate dtypes (casting after fillna)
    for col in ['hour', 'dayofweek', 'is_weekend', 'message_length']:
        if col in features:
            features[col] = features[col].astype(int)

    return features


def evaluate_model(model: MLModel, test_features: pd.DataFrame, test_labels: pd.Series = None) -> Dict[str, float]:
    \"\"\"Evaluate a trained ML model using its own evaluate method.\"\"\"
    logger.info(f"Evaluating model {model.__class__.__name__}...")
    # Pass labels only if they are provided
    if test_labels is not None:
        return model.evaluate(test_features, test_labels)
    # Create an empty Series with the same index as test_features if labels are None
    # This ensures compatibility with evaluation methods that might expect a Series
    test_labels = pd.Series(index=test_features.index, dtype=float) # Use float to allow NaN

    return model.evaluate(test_features, test_labels)

# TODO: Add functions for model management (saving/loading multiple models)
# def save_all_models(models: Dict[str, MLModel], directory: str):
# def load_all_models(directory: str) -> Dict[str, MLModel]
