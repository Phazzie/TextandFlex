"""
ML Model Service Module
-------------------
Provides a service layer for ML model operations.
"""
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd
import os
from pathlib import Path

from ..presentation_layer.services.logging_service import LoggingService
from .ml_exceptions import (
    MLError, ModelError, TrainingError, 
    PredictionError, FeatureExtractionError, ModelPersistenceError
)
from .ml_models import (
    MLModel, TimePatternModel, ContactPatternModel, 
    AnomalyDetectionModel, extract_advanced_features
)


class MLModelService:
    """
    Service for managing ML model operations.
    
    This service provides a unified interface for ML model operations,
    including training, prediction, and persistence.
    """
    
    def __init__(self, 
                 logging_service: Optional[LoggingService] = None,
                 config_manager = None,
                 models_dir: str = None):
        """
        Initialize the ML model service.
        
        Args:
            logging_service: Optional logging service
            config_manager: Optional configuration manager for feature flags
            models_dir: Optional directory for model persistence
        """
        self.logging_service = logging_service
        self.config_manager = config_manager
        self.models_dir = models_dir or os.path.join(os.path.dirname(__file__), "..", "..", "models")
        self.models = {}
        
        # Initialize default models
        self._initialize_models()
        
        # Log initialization
        if self.logging_service:
            self.logging_service.info(
                "MLModelService initialized",
                component="MLModelService",
                models_dir=self.models_dir
            )
    
    def _initialize_models(self):
        """Initialize the default models."""
        try:
            # Ensure models directory exists
            Path(self.models_dir).mkdir(parents=True, exist_ok=True)
            
            # Create default model instances
            self.models["TimePatternModel"] = TimePatternModel(name="TimePatternModel")
            self.models["ContactPatternModel"] = ContactPatternModel(name="ContactPatternModel")
            self.models["AnomalyDetectionModel"] = AnomalyDetectionModel(name="AnomalyDetectionModel")
            
            # Try to load pre-trained models if available
            self._load_models()
            
        except Exception as e:
            if self.logging_service:
                self.logging_service.error(
                    f"Error initializing models: {str(e)}",
                    component="MLModelService",
                    error=str(e)
                )
            raise ModelError(f"Error initializing models: {str(e)}")
    
    def _load_models(self):
        """Load pre-trained models if available."""
        try:
            for model_name, model in self.models.items():
                model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
                if os.path.exists(model_path):
                    success = model.load(model_path)
                    if success and self.logging_service:
                        self.logging_service.info(
                            f"Loaded {model_name} model",
                            component="MLModelService",
                            model=model_name,
                            version=model.version
                        )
        except Exception as e:
            if self.logging_service:
                self.logging_service.warning(
                    f"Error loading models: {str(e)}",
                    component="MLModelService",
                    error=str(e)
                )
    
    def _save_models(self):
        """Save trained models."""
        try:
            Path(self.models_dir).mkdir(parents=True, exist_ok=True)
            
            for model_name, model in self.models.items():
                if model.is_trained:
                    model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
                    success = model.save(model_path)
                    if success and self.logging_service:
                        self.logging_service.info(
                            f"Saved {model_name} model",
                            component="MLModelService",
                            model=model_name,
                            version=model.version
                        )
        except Exception as e:
            if self.logging_service:
                self.logging_service.error(
                    f"Error saving models: {str(e)}",
                    component="MLModelService",
                    error=str(e)
                )
            raise ModelPersistenceError(f"Error saving models: {str(e)}")
    
    def get_model(self, model_name: str) -> MLModel:
        """
        Get a model by name.
        
        Args:
            model_name: Name of the model
            
        Returns:
            The requested model
            
        Raises:
            ModelError: If the model is not found
        """
        if model_name not in self.models:
            error_msg = f"Model '{model_name}' not found"
            if self.logging_service:
                self.logging_service.error(
                    error_msg,
                    component="MLModelService",
                    model=model_name
                )
            raise ModelError(error_msg)
            
        return self.models[model_name]
    
    def extract_features(self, df: pd.DataFrame, column_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Extract features from a dataframe.
        
        Args:
            df: DataFrame to extract features from
            column_mapping: Optional column mapping
            
        Returns:
            DataFrame with extracted features
            
        Raises:
            FeatureExtractionError: If feature extraction fails
        """
        try:
            # Check if advanced feature extraction is enabled
            use_advanced = True
            if self.config_manager and hasattr(self.config_manager, "is_feature_enabled"):
                use_advanced = self.config_manager.is_feature_enabled("advanced_feature_extraction", default=True)
                
            if use_advanced:
                features = extract_advanced_features(df, column_mapping)
                if self.logging_service:
                    self.logging_service.debug(
                        "Extracted advanced features",
                        component="MLModelService",
                        feature_count=features.shape[1],
                        row_count=features.shape[0]
                    )
            else:
                # Fall back to basic feature extraction
                from .ml_models import extract_features
                features = extract_features(df, column_mapping)
                if self.logging_service:
                    self.logging_service.debug(
                        "Extracted basic features",
                        component="MLModelService",
                        feature_count=features.shape[1],
                        row_count=features.shape[0]
                    )
                
            return features
            
        except Exception as e:
            error_msg = f"Error extracting features: {str(e)}"
            if self.logging_service:
                self.logging_service.error(
                    error_msg,
                    component="MLModelService",
                    error=str(e)
                )
            raise FeatureExtractionError(error_msg, details=str(e))
    
    def train_models(self, df: pd.DataFrame, 
                     column_mapping: Optional[Dict[str, str]] = None,
                     models_to_train: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Train selected models on the data.
        
        Args:
            df: DataFrame with the training data
            column_mapping: Optional column mapping
            models_to_train: Optional list of model names to train (default: all)
            
        Returns:
            Dictionary mapping model names to training success status
            
        Raises:
            TrainingError: If training fails
        """
        results = {}
        
        try:
            # Extract features
            features = self.extract_features(df, column_mapping)
            
            # Determine which models to train
            if models_to_train is None:
                models_to_train = list(self.models.keys())
                
            # Train each model
            for model_name in models_to_train:
                if model_name not in self.models:
                    if self.logging_service:
                        self.logging_service.warning(
                            f"Model '{model_name}' not found, skipping training",
                            component="MLModelService",
                            model=model_name
                        )
                    results[model_name] = False
                    continue
                
                model = self.models[model_name]
                
                # Log training start
                if self.logging_service:
                    self.logging_service.info(
                        f"Training {model_name} model",
                        component="MLModelService",
                        model=model_name
                    )
                
                # Train the model
                success = model.train(features)
                results[model_name] = success
                
                # Log training result
                if self.logging_service:
                    if success:
                        self.logging_service.info(
                            f"Successfully trained {model_name} model",
                            component="MLModelService",
                            model=model_name,
                            version=model.version
                        )
                    else:
                        self.logging_service.error(
                            f"Failed to train {model_name} model",
                            component="MLModelService",
                            model=model_name,
                            error=model._last_error
                        )
            
            # Save trained models
            self._save_models()
            
            return results
            
        except Exception as e:
            error_msg = f"Error training models: {str(e)}"
            if self.logging_service:
                self.logging_service.error(
                    error_msg,
                    component="MLModelService",
                    error=str(e)
                )
            raise TrainingError(error_msg, details=str(e))
    
    def update_models(self, df: pd.DataFrame, 
                     column_mapping: Optional[Dict[str, str]] = None,
                     models_to_update: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Update selected models with new data (incremental learning).
        
        Args:
            df: DataFrame with the update data
            column_mapping: Optional column mapping
            models_to_update: Optional list of model names to update (default: all)
            
        Returns:
            Dictionary mapping model names to update success status
            
        Raises:
            TrainingError: If update fails
        """
        results = {}
        
        try:
            # Extract features
            features = self.extract_features(df, column_mapping)
            
            # Determine which models to update
            if models_to_update is None:
                models_to_update = list(self.models.keys())
                
            # Update each model
            for model_name in models_to_update:
                if model_name not in self.models:
                    if self.logging_service:
                        self.logging_service.warning(
                            f"Model '{model_name}' not found, skipping update",
                            component="MLModelService",
                            model=model_name
                        )
                    results[model_name] = False
                    continue
                
                model = self.models[model_name]
                
                # Check if model is trained
                if not model.is_trained:
                    if self.logging_service:
                        self.logging_service.info(
                            f"{model_name} model is not trained, performing full training instead of update",
                            component="MLModelService",
                            model=model_name
                        )
                    success = model.train(features)
                else:
                    # Log update start
                    if self.logging_service:
                        self.logging_service.info(
                            f"Updating {model_name} model",
                            component="MLModelService",
                            model=model_name,
                            current_version=model.version
                        )
                    
                    # Update the model
                    success = model.partial_fit(features)
                
                results[model_name] = success
                
                # Log update result
                if self.logging_service:
                    if success:
                        self.logging_service.info(
                            f"Successfully updated {model_name} model to version {model.version}",
                            component="MLModelService",
                            model=model_name,
                            version=model.version
                        )
                    else:
                        self.logging_service.error(
                            f"Failed to update {model_name} model",
                            component="MLModelService",
                            model=model_name,
                            error=model._last_error
                        )
            
            # Save updated models
            self._save_models()
            
            return results
            
        except Exception as e:
            error_msg = f"Error updating models: {str(e)}"
            if self.logging_service:
                self.logging_service.error(
                    error_msg,
                    component="MLModelService",
                    error=str(e)
                )
            raise TrainingError(error_msg, details=str(e))
    
    def predict(self, model_name: str, df: pd.DataFrame, 
                 column_mapping: Optional[Dict[str, str]] = None,
                 use_cache: bool = True) -> Dict[str, Any]:
        """
        Generate predictions using the specified model.
        
        Args:
            model_name: Name of the model to use
            df: DataFrame to generate predictions for
            column_mapping: Optional column mapping
            use_cache: Whether to use cached results if available
            
        Returns:
            Dictionary containing predictions and metadata
            
        Raises:
            PredictionError: If prediction fails
            ModelError: If the model is not found or not trained
        """
        try:
            # Get the model
            model = self.get_model(model_name)
            
            # Check if model is trained
            if not model.is_trained:
                error_msg = f"Model '{model_name}' is not trained"
                if self.logging_service:
                    self.logging_service.error(
                        error_msg,
                        component="MLModelService",
                        model=model_name
                    )
                raise ModelError(error_msg)
            
            # Generate a cache key if caching is enabled
            cache_key = None
            if use_cache:
                # Simple cache key based on data hash and model version
                from hashlib import md5
                data_hash = md5(pd.util.hash_pandas_object(df).values).hexdigest()
                cache_key = f"{model_name}_{model.version}_{data_hash}"
            
                # Check if we have cached results
                from .statistical_utils import get_cached_result
                cached_result = get_cached_result(cache_key)
                if cached_result is not None:
                    if self.logging_service:
                        self.logging_service.debug(
                            f"Using cached predictions for {model_name}",
                            component="MLModelService",
                            model=model_name,
                            cache_key=cache_key
                        )
                    return cached_result
            
            # Extract features
            features = self.extract_features(df, column_mapping)
            
            # Log prediction start
            if self.logging_service:
                self.logging_service.debug(
                    f"Generating predictions with {model_name}",
                    component="MLModelService",
                    model=model_name,
                    data_size=len(df)
                )
            
            # Generate predictions
            predictions = model.predict(features)
            
            # Format the result
            result = {
                "predictions": predictions,
                "model_name": model_name,
                "model_version": model.version,
                "timestamp": pd.Timestamp.now(),
                "data_size": len(df)
            }
            
            # Cache the result if caching is enabled
            if use_cache and cache_key:
                from .statistical_utils import cache_result
                cache_result(cache_key, result)
                
            return result
            
        except MLError:
            # Re-raise ML errors
            raise
        except Exception as e:
            error_msg = f"Error generating predictions with {model_name}: {str(e)}"
            if self.logging_service:
                self.logging_service.error(
                    error_msg,
                    component="MLModelService",
                    model=model_name,
                    error=str(e)
                )
            raise PredictionError(error_msg, details=str(e))
    
    def evaluate_model(self, model_name: str, df: pd.DataFrame, 
                     target: pd.Series = None,
                     column_mapping: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        Evaluate a model on test data.
        
        Args:
            model_name: Name of the model to evaluate
            df: DataFrame with the test data
            target: Optional target values for supervised models
            column_mapping: Optional column mapping
            
        Returns:
            Dictionary with evaluation metrics
            
        Raises:
            ModelError: If evaluation fails
        """
        try:
            # Get the model
            model = self.get_model(model_name)
            
            # Check if model is trained
            if not model.is_trained:
                error_msg = f"Model '{model_name}' is not trained"
                if self.logging_service:
                    self.logging_service.error(
                        error_msg,
                        component="MLModelService",
                        model=model_name
                    )
                raise ModelError(error_msg)
            
            # Extract features
            features = self.extract_features(df, column_mapping)
            
            # Log evaluation start
            if self.logging_service:
                self.logging_service.info(
                    f"Evaluating {model_name} model",
                    component="MLModelService",
                    model=model_name,
                    version=model.version
                )
            
            # Evaluate the model
            metrics = model.evaluate(features, target)
            
            # Log evaluation result
            if self.logging_service:
                self.logging_service.info(
                    f"Evaluated {model_name} model: {metrics}",
                    component="MLModelService",
                    model=model_name,
                    metrics=metrics
                )
            
            return metrics
            
        except MLError:
            # Re-raise ML errors
            raise
        except Exception as e:
            error_msg = f"Error evaluating '{model_name}' model: {str(e)}"
            if self.logging_service:
                self.logging_service.error(
                    error_msg,
                    component="MLModelService",
                    model=model_name,
                    error=str(e)
                )
            raise ModelError(error_msg, details=str(e))
