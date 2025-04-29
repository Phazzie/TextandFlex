"""
Machine Learning Models Module
------------------
Contains ML models for pattern detection and analysis.
"""

import pandas as pd
from typing import Dict, List, Any, Union, Callable, Optional, Iterator, Tuple
import os
from pathlib import Path
import concurrent.futures
import gc  # Garbage collector
import time
from functools import partial
import logging
import numpy as np  # Explicitly import numpy at the top level

# Try to import optional dependencies with fallbacks
try:
    import joblib  # For saving/loading models
except ImportError:
    import pickle as joblib
    logging.warning("joblib not found, using pickle for model serialization")

try:
    from tqdm import tqdm
except ImportError:
    # Create a simple fallback for tqdm if not installed
    def tqdm(iterable=None, **kwargs):
        if iterable is not None:
            return iterable
        return lambda x: x

# Import scikit-learn with error handling
try:
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import IsolationForest, RandomForestRegressor
    from sklearn.cluster import KMeans
    from sklearn.metrics import (
        silhouette_score,
        accuracy_score,
        mean_squared_error,
        r2_score,
        precision_score,
        recall_score,
        f1_score
    )
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not found. ML functionality will be limited.")

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
    'phone_number': 'To/From',
    # Add other columns if needed by features
}

class MLModel:
    """
    Base class for machine learning models.

    Provides a standard interface for training, batched training, prediction, evaluation,
    saving, and loading models. Subclasses should implement the _train_model, _predict_model,
    and _evaluate_model methods.

    Example usage:
        >>> model = TimePatternModel()
        >>> features = extract_features(df)
        >>> model.train(features, labels)
        >>> predictions = model.predict(features)
        >>> metrics = model.evaluate(test_features, test_labels)
        >>> model.save('model.pkl')
        >>> model.load('model.pkl')
    """

    def __init__(self):
        """Initialize the base model."""
        self.model = None
        self._last_error = None
        self._is_trained = False
        self._supports_partial_fit = False
        self._training_progress = 0.0
        self._version = "0.1.0"  # Semantic versioning: major.minor.patch

    def train(self, features: pd.DataFrame, labels: pd.Series = None):
        """Train the model. Labels are optional for unsupervised models."""
        if features.empty:
            logger.warning(f"Cannot train {self.__class__.__name__}: features DataFrame is empty.")
            self._last_error = "Input features are empty"
            self._is_trained = False
            return False
        try:
            self._train_model(features, labels)
            self._is_trained = True
            logger.info(f"{self.__class__.__name__} trained successfully.")
            return True
        except Exception as exception:
            logger.error(f"Error training {self.__class__.__name__}: {exception}")
            self._last_error = str(exception)
            self._is_trained = False
            return False

    def train_batched(self, features_iterator, labels_iterator=None,
                     batch_size=5000, progress_callback=None):
        """
        Train the model using batched data to handle large datasets efficiently.

        Args:
            features_iterator: Iterator yielding feature DataFrames or a DataFrame
            labels_iterator: Optional iterator yielding label Series or a Series
            batch_size: Size of batches to process (if input is not already batched)
            progress_callback: Optional function(progress_float, status_message)
                               to report progress

        Returns:
            bool: True if training succeeded, False otherwise
        """
        # If inputs are DataFrames/Series, convert to iterators
        if isinstance(features_iterator, pd.DataFrame):
            total_rows = len(features_iterator)
            def feature_batch_gen():
                for i in range(0, total_rows, batch_size):
                    yield features_iterator.iloc[i:i+batch_size]
            features_iterator = feature_batch_gen()

            if isinstance(labels_iterator, pd.Series):
                def label_batch_gen():
                    for i in range(0, total_rows, batch_size):
                        yield labels_iterator.iloc[i:i+batch_size]
                labels_iterator = label_batch_gen()

        # Determine if the model supports incremental learning
        supports_partial = self._supports_partial_fit

        if not supports_partial:
            # Fallback to collecting all data and training at once
            try:
                all_features = []
                all_labels = []
                total_rows = 0
                start_time = time.time()
                batch_count = 0

                # Collect all data from iterators
                for batch in features_iterator:
                    if batch.empty:
                        continue

                    all_features.append(batch)
                    total_rows += len(batch)
                    batch_count += 1

                    if labels_iterator:
                        try:
                            label_batch = next(labels_iterator)
                            all_labels.append(label_batch)
                        except StopIteration:
                            logger.warning("Labels iterator exhausted before features.")
                            break

                    if progress_callback:
                        # We can't know the total size, report based on batches
                        msg = f"Collected batch {batch_count}, {total_rows} rows total"
                        progress = 0.5 * (batch_count / (batch_count + 1))
                        progress_callback(progress, msg)

                # Combine all batches
                if all_features:
                    combined_features = pd.concat(all_features)
                    combined_labels = pd.concat(all_labels) if all_labels else None

                    if progress_callback:
                        progress_callback(0.5, f"Training on {len(combined_features)} total rows")

                    # Train on the combined dataset
                    if not combined_features.empty:
                        success = self.train(combined_features, combined_labels)
                        if progress_callback:
                            progress_callback(1.0, "Training complete")
                        return success

                logger.warning("No data collected for training")
                if progress_callback:
                    progress_callback(1.0, "No data to train on")
                return False

            except Exception as exc:
                logger.error(f"Error in batched training: {exc}")
                self._last_error = str(exc)
                if progress_callback:
                    progress_callback(1.0, f"Error: {exc}")
                return False
        else:
            # True incremental learning using partial_fit
            try:
                processed_batches = 0
                start_time = time.time()
                has_labels = labels_iterator is not None

                # Initialize with first batch to setup the model
                initialized = False

                for feature_batch in features_iterator:
                    if feature_batch.empty:
                        continue

                    label_batch = None
                    if has_labels:
                        try:
                            label_batch = next(labels_iterator)
                        except StopIteration:
                            has_labels = False

                    # On first batch, initialize the model
                    if not initialized:
                        self._init_partial_fit(feature_batch, label_batch)
                        initialized = True

                    # Perform incremental fit
                    self._partial_fit(feature_batch, label_batch)

                    processed_batches += 1

                    # Report progress
                    if progress_callback:
                        elapsed = time.time() - start_time
                        if processed_batches > 1:
                            # Can't predict total batches, so use a progress that approaches 1
                            # asymptotically as more batches are processed
                            progress = processed_batches / (processed_batches + 5)
                            msg = f"Processed batch {processed_batches}, {elapsed:.1f}s elapsed"
                        else:
                            progress = 0.1
                            msg = f"Processed batch {processed_batches}"

                        progress_callback(min(0.99, progress), msg)

                    # Clear memory occasionally
                    if processed_batches % 10 == 0:
                        gc.collect()

                if processed_batches > 0:
                    self._is_trained = True
                    if progress_callback:
                        progress_callback(1.0, "Training complete")
                    logger.info(f"{self.__class__.__name__} trained in {processed_batches} batches")
                    return True
                else:
                    logger.warning(f"{self.__class__.__name__}: No batches processed")
                    if progress_callback:
                        progress_callback(1.0, "No data to train on")
                    return False

            except Exception as exc:
                logger.error(f"Error during incremental training: {exc}")
                self._last_error = str(exc)
                if progress_callback:
                    progress_callback(1.0, f"Error: {exc}")
                return False

    def _init_partial_fit(self, features: pd.DataFrame, labels: pd.Series = None):
        """
        Initialize the model for partial fitting. To be overridden by subclasses
        that support incremental learning.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support incremental learning"
        )

    def _partial_fit(self, features: pd.DataFrame, labels: pd.Series = None):
        """
        Update the model with a batch of data. To be overridden by subclasses
        that support incremental learning.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support incremental learning"
        )

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

    @property
    def version(self) -> str:
        """Get the model version."""
        return self._version

    def bump_version(self, level="patch"):
        """Bump the model version according to semantic versioning.

        Args:
            level: The version level to bump ("major", "minor", or "patch")
        """
        major, minor, patch = map(int, self._version.split("."))

        if level == "major":
            major += 1
            minor = 0
            patch = 0
        elif level == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        self._version = f"{major}.{minor}.{patch}"
        logger.info(f"Bumped {self.__class__.__name__} version to {self._version}")
        return self._version

    def save(self, file_path: Union[str, Path]):
        """Save the trained model to a file."""
        if not self._is_trained or self.model is None:
            logger.error(f"Cannot save {self.__class__.__name__}: Model is not trained.")
            self._last_error = "Model not trained, cannot save."
            return False
        try:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            ensure_directory_exists(path.parent)
            # Save model and metadata
            model_data = {
                'model': self.model,
                'version': self._version,
                'class_name': self.__class__.__name__,
                'timestamp': datetime.now().isoformat()
            }
            joblib.dump(model_data, path)
            logger.info(f"Saved {self.__class__.__name__} model version {self._version} to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving {self.__class__.__name__} model to {file_path}: {e}")
            self._last_error = f"Failed to save model: {e}"
            return False

    def load(self, file_path: Union[str, Path]):
        """Load a trained model from a file."""
        try:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            if not path.exists():
                logger.error(f"Cannot load {self.__class__.__name__}: File not found at {path}")
                self._last_error = "Model file not found."
                self._is_trained = False
                return False

            # Load the model data
            model_data = joblib.load(path)

            # Handle both new format (with metadata) and old format (just the model)
            if isinstance(model_data, dict) and 'model' in model_data:
                self.model = model_data['model']
                # Load version if available
                if 'version' in model_data:
                    self._version = model_data['version']
            else:
                # Old format - just the model
                self.model = model_data

            self._is_trained = True
            self._last_error = None
            logger.info(f"Loaded {self.__class__.__name__} model version {self._version} from {path}")
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
    """
    Model for predicting time-based patterns using RandomForestRegressor.

    Example usage:
        >>> model = TimePatternModel()
        >>> features = extract_features(df)
        >>> model.train(features, labels)
        >>> predictions = model.predict(features)
        >>> metrics = model.evaluate(test_features, test_labels)
    """

    def _train_model(self, features: pd.DataFrame, labels: pd.Series = None):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for TimePatternModel but is not installed.")
        # Using RandomForestRegressor as specified in the checklist

        if features.empty or features.shape[1] == 0:
            logger.warning("TimePatternModel training skipped: No features provided.")
            self.model = None
            return

        # Make sure we have labels for supervised learning
        if labels is None or labels.empty:
            logger.warning("TimePatternModel requires labels for training. Using hour as target if available.")
            # Use hour as target if available, as it's a meaningful regression target for time analysis
            if 'hour' in features.columns:
                labels = features['hour']
                logger.info("Using 'hour' feature as the regression target.")
            else:
                logger.error("No suitable target variable found for TimePatternModel. Cannot train properly.")
                self._last_error = "Missing target variable for regression"
                self.model = None
                return

        # Use time-related features
        time_features = features.copy()

        # Create the model with reasonable defaults
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1  # Use all available cores
        )

        # Train the model
        self.model.fit(time_features, labels)
        logger.info("TimePatternModel trained using RandomForestRegressor.")


    def _predict_model(self, features: pd.DataFrame) -> Any:
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for TimePatternModel but is not installed.")
        if self.model is None or features.empty or features.shape[1] == 0:
            logger.warning("TimePatternModel prediction skipped: Model not trained or no features.")
            return pd.Series(dtype=float)

        # Make predictions
        predictions = self.model.predict(features)
        return pd.Series(predictions, index=features.index)


    def _evaluate_model(self, test_features: pd.DataFrame, test_labels: pd.Series = None) -> Dict[str, float]:
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for TimePatternModel but is not installed.")
        if self.model is None or test_features.empty or test_features.shape[1] == 0:
            logger.warning("TimePatternModel evaluation skipped: Model not trained or insufficient features.")
            return {}

        if test_labels is None or test_labels.empty:
            logger.warning("TimePatternModel evaluation requires labels. Skipping evaluation.")
            return {}

        # Make predictions
        predictions = self.predict(test_features)

        # Calculate regression metrics
        metrics = {
            'mean_squared_error': mean_squared_error(test_labels, predictions),
            'r2_score': r2_score(test_labels, predictions),
            'feature_importance': dict(zip(
                test_features.columns,
                self.model.feature_importances_
            ))
        }

        return metrics


class ContactPatternModel(MLModel):
    """
    Model for predicting contact-based patterns (e.g., grouping contacts) using KMeans clustering.

    Example usage:
        >>> model = ContactPatternModel()
        >>> features = extract_features(df)
        >>> model.train(features)
        >>> predictions = model.predict(features)
        >>> metrics = model.evaluate(test_features)
    """

    def _train_model(self, features: pd.DataFrame, labels: pd.Series = None):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ContactPatternModel but is not installed.")
        if features.empty:
            logger.warning("ContactPatternModel training skipped: Empty features.")
            self.model = None
            self._is_trained = False
            return

        # Ensure message_length exists (should be added by extract_features)
        if 'message_length' not in features.columns:
            logger.warning("ContactPatternModel: Adding missing 'message_length' feature with default value 0.")
            features['message_length'] = 0

        contact_features = features[['message_length']].copy()
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(contact_features)
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        kmeans.fit(scaled_features)
        self.model = {'kmeans': kmeans, 'scaler': scaler}
        self._is_trained = True
        logger.info("ContactPatternModel trained using KMeans with StandardScaler.")

    def _predict_model(self, features: pd.DataFrame) -> Any:
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ContactPatternModel but is not installed.")
        if self.model is None or features.empty:
            logger.warning("ContactPatternModel prediction skipped: Model not trained or empty features.")
            return pd.Series(dtype=int)

        # Ensure message_length exists
        if 'message_length' not in features.columns:
            logger.warning("ContactPatternModel: Adding missing 'message_length' feature with default value 0.")
            features = features.copy()
            features['message_length'] = 0

        contact_features = features[['message_length']].copy()
        scaled_features = self.model['scaler'].transform(contact_features)
        preds = self.model['kmeans'].predict(scaled_features)
        return pd.Series(preds, index=features.index)

    def _evaluate_model(self, test_features: pd.DataFrame, test_labels: pd.Series = None) -> Dict[str, float]:
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ContactPatternModel but is not installed.")
        if self.model is None or test_features.empty:
            logger.warning("ContactPatternModel evaluation skipped: Model not trained or empty features.")
            return {}

        # Ensure message_length exists
        if 'message_length' not in test_features.columns:
            logger.warning("ContactPatternModel: Adding missing 'message_length' feature with default value 0.")
            test_features = test_features.copy()
            test_features['message_length'] = 0

        contact_features = test_features[['message_length']].copy()
        scaled_features = self.model['scaler'].transform(contact_features)
        if len(scaled_features) < 2:
            logger.warning("ContactPatternModel evaluation skipped: Need at least 2 samples for silhouette score.")
            return {}
        labels = self.model['kmeans'].predict(scaled_features)
        try:
            score = silhouette_score(scaled_features, labels)
            return {'silhouette_score': score}
        except ValueError as ve:
            logger.warning(f"Could not calculate silhouette score: {ve}")
            return {'silhouette_score': np.nan}


class AnomalyDetectionModel(MLModel):
    """
    Model for detecting anomalies using IsolationForest.
    Supports incremental learning via partial_fit.

    Example usage:
        >>> model = AnomalyDetectionModel()
        >>> features = extract_features(df)
        >>> model.train(features)
        >>> # For incremental learning:
        >>> for batch in extract_features_batched(df, batch_size=1000):
        ...     model._partial_fit(batch)
        >>> predictions = model.predict(features)
        >>> metrics = model.evaluate(test_features, test_labels)
    """

    def __init__(self):
        """Initialize the model with incremental learning support."""
        super().__init__()
        self._supports_partial_fit = True  # Enable incremental learning

    def _init_partial_fit(self, features: pd.DataFrame, labels: pd.Series = None):
        """Initialize the model for incremental learning."""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for AnomalyDetectionModel but is not installed.")
        if features.empty:
            raise ValueError("Cannot initialize model with empty features")

        # Initialize the scaler with the first batch of data
        self._scaler = StandardScaler()
        self._scaler.fit(features)

        # Create the IsolationForest model
        self._isolation_forest = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination='auto',
            random_state=42,
            n_jobs=-1
        )

        # Perform the first partial fit
        scaled_features = self._scaler.transform(features)
        self._isolation_forest.fit(scaled_features)

        # Store in the model dict
        self.model = {
            "isolation_forest": self._isolation_forest,
            "scaler": self._scaler
        }

        logger.info("AnomalyDetectionModel initialized for incremental learning")

    def _partial_fit(self, features: pd.DataFrame, labels: pd.Series = None):
        """Update the model with a new batch of data."""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for AnomalyDetectionModel but is not installed.")
        if self.model is None:
            raise ValueError("Model not initialized. Call _init_partial_fit first.")

        if features.empty:
            logger.warning("Skipping empty batch in partial_fit")
            return

        # Get existing model components
        isolation_forest = self.model["isolation_forest"]
        scaler = self.model["scaler"]

        # Scale features with the existing scaler
        scaled_features = scaler.transform(features)

        # For IsolationForest which doesn't natively support partial_fit, we have two options:
        # 1. Train a separate forest and combine estimators (faster but less accurate)
        # 2. Retain a subset of original data and retrain (slower but more accurate)

        # Option 1: Train a new forest on this batch and combine estimators
        batch_forest = IsolationForest(
            n_estimators=max(10, isolation_forest.n_estimators // 5),  # Proportional to main forest
            max_samples='auto',
            contamination=isolation_forest.contamination,  # Use same contamination value
            random_state=42,
            n_jobs=-1
        )
        batch_forest.fit(scaled_features)

        # Update the estimators
        original_n_estimators = isolation_forest.n_estimators
        batch_n_estimators = batch_forest.n_estimators

        # Add the new estimators to the existing ones
        isolation_forest.estimators_ += batch_forest.estimators_
        isolation_forest.estimators_samples_ += batch_forest.estimators_samples_

        # Update total estimator count and recalculate offsets
        isolation_forest.n_estimators = original_n_estimators + batch_n_estimators

        # For more accurate anomaly threshold, we could recalculate:
        # if hasattr(isolation_forest, '_compute_score_samples'):
        #    isolation_forest.offset_ = isolation_forest._compute_score_samples(...)

        # Update the stored model
        self.model.update({
            "isolation_forest": isolation_forest
        })

        self._is_trained = True
        logger.debug(f"Partial fit completed with {len(features)} samples, forest now has {isolation_forest.n_estimators} trees")

    def _train_model(self, features: pd.DataFrame, labels: pd.Series = None):
        """Standard training method for when not using incremental learning."""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for AnomalyDetectionModel but is not installed.")
        if features.empty or features.shape[1] == 0:
            logger.warning("AnomalyDetectionModel training skipped: No features provided.")
            self.model = None
            return

        # Make a copy of features to avoid modifying the original
        anomaly_features = features.copy()

        # Apply standard scaling for better anomaly detection
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(anomaly_features)

        # Create the IsolationForest model with reasonable defaults
        # The 'contamination' parameter is an estimate of the proportion of outliers in the data
        isolation_forest = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination='auto',  # Let the algorithm decide based on data
            random_state=42,
            n_jobs=-1  # Use all available cores
        )

        # Train the model
        isolation_forest.fit(scaled_features)

        # Store both the model and scaler for prediction
        self.model = {
            "isolation_forest": isolation_forest,
            "scaler": scaler
        }

        logger.info("AnomalyDetectionModel trained using IsolationForest.")

    def _predict_model(self, features: pd.DataFrame) -> Any:
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for AnomalyDetectionModel but is not installed.")
        if self.model is None or features.empty:
            logger.warning("AnomalyDetectionModel prediction skipped: Model not trained or no features.")
            return pd.Series(dtype=int)

        # Scale the features
        scaled_features = self.model["scaler"].transform(features)

        # Get predictions: 1 for inliers, -1 for outliers
        raw_predictions = self.model["isolation_forest"].predict(scaled_features)

        # Convert predictions: -1 (anomaly) → 1 (flag it as anomaly), 1 (normal) → 0 (not anomaly)
        anomaly_flags = pd.Series(np.where(raw_predictions == -1, 1, 0), index=features.index)
        return anomaly_flags

    def _evaluate_model(self, test_features: pd.DataFrame, test_labels: pd.Series = None) -> Dict[str, float]:
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for AnomalyDetectionModel but is not installed.")
        if self.model is None or test_features.empty:
            logger.warning("scikit-learn is required for AnomalyDetectionModel but is not installed.")
            return {}

        # Get anomaly predictions
        anomaly_predictions = self.predict(test_features)

        # Calculate basic statistics
        anomaly_count = anomaly_predictions.sum()
        total_samples = len(anomaly_predictions)
        anomaly_percentage = (anomaly_count / total_samples) * 100 if total_samples > 0 else 0

        metrics = {
            "anomaly_count": float(anomaly_count),
            "total_samples": float(total_samples),
            "anomaly_percentage": float(anomaly_percentage)
        }

        # If labeled data is provided (ground truth about anomalies), compute accuracy metrics
        if test_labels is not None and not test_labels.isnull().all() and len(test_labels) == len(anomaly_predictions):
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

            try:
                # Check if labels are actually binary (0 or 1)
                unique_values = test_labels.unique()
                if not all(val in [0, 1] for val in unique_values if not pd.isna(val)):
                    logger.warning("Test labels must be binary (0 or 1) for anomaly detection evaluation. "
                                  f"Found values: {unique_values}. Converting to binary.")

                # Ensure test_labels are binary for metric calculation
                binary_labels = test_labels.astype(bool).astype(int)

                metrics.update({
                    "accuracy": accuracy_score(binary_labels, anomaly_predictions),
                    "precision": precision_score(binary_labels, anomaly_predictions, zero_division=0),
                    "recall": recall_score(binary_labels, anomaly_predictions, zero_division=0),
                    "f1_score": f1_score(binary_labels, anomaly_predictions, zero_division=0)
                })
            except Exception as e:
                logger.warning(f"Could not calculate accuracy metrics: {e}")

        return metrics


def extract_features(df: pd.DataFrame, column_mapping: Dict = None) -> pd.DataFrame:
    """
    Extract features for ML models from the raw data, using column mapping.
    Ensures all output columns are int and robustly handles missing columns.

    Args:
        df: Input DataFrame with raw data.
        column_mapping: Optional mapping of logical column names to actual DataFrame columns.

    Returns:
        DataFrame with extracted features (hour, dayofweek, is_weekend, message_length).

    Example:
        >>> features = extract_features(df, column_mapping={'timestamp': 'Time', 'message_length': 'Len'})
    """
    df_local = df.copy()
    features = pd.DataFrame(index=df_local.index)
    mapping = {**DEFAULT_COLUMN_MAPPING, **(column_mapping or {})}
    col_lookup = {col.lower(): col for col in df_local.columns}
    def find_column(key):
        mapped_val = mapping.get(key)
        if mapped_val and mapped_val.lower() in col_lookup:
            return col_lookup[mapped_val.lower()]
        if key.lower() in col_lookup:
            return col_lookup[key.lower()]
        return None
    try:
        ts_col = find_column('timestamp')
        len_col = find_column('message_length')

        # Extract time-based features
        if ts_col and ts_col in df_local.columns:
            df_local[ts_col] = pd.to_datetime(df_local[ts_col], errors='coerce')
            features['hour'] = df_local[ts_col].dt.hour
            features['dayofweek'] = df_local[ts_col].dt.dayofweek
            features['is_weekend'] = (df_local[ts_col].dt.dayofweek >= 5).astype(int)
            features = features.dropna(subset=['hour', 'dayofweek', 'is_weekend'])
        else:
            logger.warning(f"Timestamp column '{ts_col}' not found in DataFrame. Time features skipped.")

        # Extract message length feature
        if len_col and len_col in df_local.columns:
            # Use existing message_length column
            features['message_length'] = df_local.loc[features.index, len_col]
        else:
            # Add a default message_length (we don't expect message_content)
            logger.info("No message_length column found. Using default value of 0.")
            features['message_length'] = 0
        # Convert all columns to int, drop rows with missing values
        for col in ['hour', 'dayofweek', 'is_weekend', 'message_length']:
            if col in features.columns:
                features[col] = pd.to_numeric(features[col], errors='coerce').astype('Int64')
        features = features.dropna().astype(int)
        if features.empty and not df_local.empty:
            logger.warning("Feature extraction resulted in an empty DataFrame. Check input columns and mapping.")
        elif not features.empty:
            logger.info(f"Extracted features: {list(features.columns)}")
    except KeyError as key_error:
        logger.error(f"Missing expected column during feature extraction based on mapping: {key_error}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error during feature extraction: {e}")
        return pd.DataFrame()
    return features


def extract_features_batched(df_iterator, batch_size=5000, column_mapping=None,
                        progress_callback=None, num_workers=1):
    """
    Extract features for ML models from large datasets in batches to optimize memory usage.

    Args:
        df_iterator: Iterator yielding pandas DataFrames or a DataFrame
        batch_size: Size of batches to process, ignored if df_iterator yields batches
        column_mapping: Optional mapping of column names
        progress_callback: Optional function(progress_float, status_message) to report progress
        num_workers: Number of parallel workers for processing (0 or 1 disables parallelism)

    Returns:
        Iterator yielding feature DataFrames in batches

    Example:
        >>> for features_batch in extract_features_batched(df, batch_size=1000):
        ...     # process features_batch
    """
    # Validate inputs
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")

    if not isinstance(num_workers, int) or num_workers < 0:
        raise ValueError("num_workers must be a non-negative integer")

    # If df_iterator is a DataFrame, convert it to a batched iterator
    if isinstance(df_iterator, pd.DataFrame):
        total_rows = len(df_iterator)
        if total_rows == 0:
            logger.warning("Empty DataFrame provided to extract_features_batched")
            return iter([])  # Return empty iterator

        batches = [(df_iterator.iloc[i:i+batch_size], i//batch_size, total_rows)
                  for i in range(0, total_rows, batch_size)]
        df_iterator = iter(batches)
        has_progress_info = True
    else:
        # Ensure it's an iterator
        try:
            df_iterator = iter(df_iterator)
        except TypeError:
            raise TypeError("df_iterator must be a DataFrame or an iterable of DataFrames")

        # If it's already an iterator, we don't know the total size upfront
        df_iterator = ((batch, idx, None) for idx, batch in enumerate(df_iterator))
        has_progress_info = False

    # Process batches - either serially or in parallel
    processed_batches = 0
    total_processed_rows = 0
    start_time = time.time()

    if num_workers <= 1:
        # Process serially
        for batch, batch_idx, total_rows in df_iterator:
            if batch.empty:
                if progress_callback:
                    progress_callback(processed_batches / (processed_batches + 1),
                                    f"Processed {processed_batches} batches, {total_processed_rows} rows")
                continue

            # Extract features for this batch
            try:
                features_batch = extract_features(batch, column_mapping)
                total_processed_rows += len(features_batch)
                processed_batches += 1
            except Exception as e:
                logger.error(f"Error extracting features from batch {batch_idx}: {e}")
                features_batch = pd.DataFrame()  # Return empty DataFrame for this batch

            # Report progress
            if progress_callback:
                progress = (batch_idx + 1) / total_rows if has_progress_info and total_rows else 0.5
                elapsed = time.time() - start_time

                if processed_batches > 1:
                    # If we have progress info, use it directly
                    if has_progress_info and total_rows:
                        remaining = (elapsed / progress) - elapsed if progress > 0 else 0
                    else:
                        # Otherwise estimate based on processed batches
                        remaining = (elapsed / processed_batches) * processed_batches

                    msg = f"Batch {processed_batches}, {total_processed_rows} rows processed, ~{remaining:.1f}s remaining"
                else:
                    msg = f"Batch {processed_batches}, {total_processed_rows} rows processed"

                progress_callback(min(0.99, progress), msg)

            # Free memory
            if processed_batches % 10 == 0:
                gc.collect()

            # Only yield non-empty feature batches
            if not features_batch.empty:
                yield features_batch
    else:
        # Process in parallel using a thread pool
        # Note: We're using threads not processes since the GIL isn't a bottleneck for pandas operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Process extract_features in parallel
            extract_fn = partial(extract_features, column_mapping=column_mapping)

            # Submit all batches to the executor
            future_to_batch = {}
            for batch, batch_idx, total_rows in df_iterator:
                if not batch.empty:
                    future = executor.submit(extract_fn, batch)
                    future_to_batch[future] = (batch_idx, len(batch))

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_idx, batch_size = future_to_batch[future]
                try:
                    features_batch = future.result()
                    if not features_batch.empty:
                        total_processed_rows += len(features_batch)
                        processed_batches += 1

                        # Report progress
                        if progress_callback:
                            progress = (batch_idx + 1) / total_rows if has_progress_info and total_rows else 0.5
                            progress_callback(min(0.99, progress),
                                            f"Batch {processed_batches}, {total_processed_rows} rows processed")

                        yield features_batch
                except Exception as e:
                    logger.error(f"Error processing batch {batch_idx}: {e}")

                # Free memory periodically
                if processed_batches % 10 == 0:
                    gc.collect()

    # Final progress update
    if progress_callback:
        progress_callback(1.0, f"Complete: {processed_batches} batches, {total_processed_rows} total rows")


def process_dataset_with_progress(df, feature_extraction_fn=None, model_training_fn=None,
                                batch_size=5000, progress_callback=None, column_mapping=None):
    """
    Process a large dataset with progress reporting.

    Args:
        df: Input DataFrame with raw data
        feature_extraction_fn: Function to extract features (defaults to extract_features)
        model_training_fn: Optional function to train model on each batch
        batch_size: Size of batches to process
        progress_callback: Function(progress_float, status_message) to report progress
        column_mapping: Optional mapping for column names

    Returns:
        Tuple of (features_df, trained_model) - model may be None if no training_fn provided
    """
    if feature_extraction_fn is None:
        feature_extraction_fn = extract_features

    total_rows = len(df)
    processed_rows = 0
    all_features = []
    model = None
    start_time = time.time()

    # Process in batches
    for i in range(0, total_rows, batch_size):
        # Extract batch
        end_idx = min(i + batch_size, total_rows)
        batch = df.iloc[i:end_idx]
        batch_size_actual = len(batch)

        # Extract features
        try:
            features = feature_extraction_fn(batch, column_mapping)
            if not features.empty:
                all_features.append(features)

                # Train model incrementally if function provided
                if model_training_fn is not None and callable(model_training_fn):
                    if model is None:
                        model = model_training_fn(features)
                    else:
                        model = model_training_fn(features, model)
        except Exception as exc:
            logger.error(f"Error processing batch {i//batch_size}: {exc}")

        # Update progress
        processed_rows += batch_size_actual
        progress = processed_rows / total_rows

        if progress_callback:
            elapsed = time.time() - start_time
            remaining = (elapsed / progress) - elapsed if progress > 0 else 0
            message = (f"Processed {processed_rows}/{total_rows} rows "
                      f"({progress:.1%}, ~{remaining:.1f}s remaining)")
            progress_callback(progress, message)

        # Periodically free memory
        if (i // batch_size) % 5 == 0:
            gc.collect()

    # Combine all features
    if all_features:
        combined_features = pd.concat(all_features)

        # Final progress update
        if progress_callback:
            progress_callback(1.0, f"Completed: {len(combined_features)} feature rows from {total_rows} input rows")

        return combined_features, model
    else:
        if progress_callback:
            progress_callback(1.0, "No features extracted")
        return pd.DataFrame(), model


def run_model_evaluation(model: MLModel, test_features: pd.DataFrame, test_labels: pd.Series = None) -> Dict[str, float]:
    """Run the evaluation method of a trained ML model and return its metrics.

    This is a wrapper function that calls the model's own evaluate method with appropriate parameters.

    Args:
        model: A trained MLModel instance
        test_features: Features to use for evaluation
        test_labels: Optional labels for supervised evaluation metrics

    Returns:
        Dictionary of evaluation metrics
    """
    logger.info(f"Running evaluation for {model.__class__.__name__}...")
    # Pass labels only if they are provided
    if test_labels is not None:
        return model.evaluate(test_features, test_labels)
    # Create an empty Series with the same index as test_features if labels are None
    # This ensures compatibility with evaluation methods that might expect a Series
    test_labels = pd.Series(index=test_features.index, dtype=float) # Use float to allow NaN

    return model.evaluate(test_features, test_labels)

# Keep backward compatibility with old function name
evaluate_model = run_model_evaluation

def extract_advanced_features(df: pd.DataFrame, column_mapping: Dict = None) -> pd.DataFrame:
    """
    Extract advanced features for ML models from the raw data, using column mapping.
    Extends the basic extract_features function with more sophisticated features.

    Args:
        df: Input DataFrame with raw data.
        column_mapping: Optional mapping of logical column names to actual DataFrame columns.

    Returns:
        DataFrame with extracted features including basic features plus advanced ones:
        - time_since_last: Time since last communication (in hours)
        - response_time: Response time for messages (in hours)
        - activity_density: Number of messages per day
        - contact_frequency: Frequency of communication with each contact
        - weekday_pattern: Pattern of activity across weekdays
        - hour_pattern: Pattern of activity across hours

    Example:
        >>> features = extract_advanced_features(df, column_mapping={'timestamp': 'Time', 'phone_number': 'Contact'})
    """
    # First get basic features
    features = extract_features(df, column_mapping)
    if features.empty:
        return features

    # Get column mappings
    mapping = {**DEFAULT_COLUMN_MAPPING, **(column_mapping or {})}
    col_lookup = {col.lower(): col for col in df.columns}

    def find_column(key):
        mapped_val = mapping.get(key)
        if mapped_val and mapped_val.lower() in col_lookup:
            return col_lookup[mapped_val.lower()]
        if key.lower() in col_lookup:
            return col_lookup[key.lower()]
        return None

    try:
        ts_col = find_column('timestamp')
        phone_col = find_column('phone_number')
        direction_col = find_column('direction')

        if ts_col and ts_col in df.columns:
            df_copy = df.copy()
            df_copy[ts_col] = pd.to_datetime(df_copy[ts_col], errors='coerce')

            # Sort by timestamp
            df_sorted = df_copy.sort_values(by=ts_col)

            # Calculate time since last communication (overall)
            df_sorted['prev_timestamp'] = df_sorted[ts_col].shift(1)
            df_sorted['time_diff'] = (df_sorted[ts_col] - df_sorted['prev_timestamp']).dt.total_seconds() / 3600  # hours
            features['time_since_last'] = df_sorted['time_diff'].fillna(0).astype(int)

            # Calculate response times if direction column exists
            if direction_col and direction_col in df.columns:
                # Group by conversation (direction changes)
                df_sorted['direction_changed'] = df_sorted[direction_col] != df_sorted[direction_col].shift(1)
                df_sorted['conversation_id'] = df_sorted['direction_changed'].cumsum()

                # Calculate response time within each conversation
                response_times = []
                for _, group in df_sorted.groupby('conversation_id'):
                    if len(group) > 1:
                        # First message in group has no response time
                        group_times = [0]
                        # For subsequent messages, calculate time since previous
                        for i in range(1, len(group)):
                            time_diff = (group.iloc[i][ts_col] - group.iloc[i-1][ts_col]).total_seconds() / 3600
                            group_times.append(time_diff)
                        response_times.extend(group_times)
                    else:
                        response_times.append(0)

                # Add to features
                features['response_time'] = pd.Series(response_times, index=df_sorted.index).fillna(0).astype(int)

            # Calculate activity density (messages per day)
            if len(df_sorted) > 1:
                date_counts = df_sorted.groupby(df_sorted[ts_col].dt.date).size()
                date_mapping = {date: count for date, count in date_counts.items()}
                features['activity_density'] = df_sorted[ts_col].dt.date.map(date_mapping).fillna(0).astype(int)
            else:
                features['activity_density'] = 1

            # Calculate weekday and hour patterns
            features['weekday_pattern'] = df_sorted[ts_col].dt.dayofweek
            features['hour_pattern'] = df_sorted[ts_col].dt.hour

            # Calculate contact frequency if phone_number column exists
            if phone_col and phone_col in df.columns:
                contact_counts = df_sorted.groupby(phone_col).size()
                contact_mapping = {contact: count for contact, count in contact_counts.items()}
                features['contact_frequency'] = df_sorted[phone_col].map(contact_mapping).fillna(0).astype(int)

        # Ensure all numeric columns are properly typed
        for col in features.columns:
            if col not in ['hour', 'dayofweek', 'is_weekend', 'message_length']:
                features[col] = pd.to_numeric(features[col], errors='coerce').fillna(0).astype(int)

        logger.info(f"Extracted advanced features: {list(features.columns)}")

    except Exception as e:
        logger.error(f"Error extracting advanced features: {e}")
        # Return basic features if advanced extraction fails
        return extract_features(df, column_mapping)

    return features


# TODO: Add functions for model management (saving/loading multiple models)
# def save_all_models(models: Dict[str, MLModel], directory: str):
# def load_all_models(directory: str) -> Dict[str, MLModel]
