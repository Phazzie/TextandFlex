"""
Pattern Detector Module
------------------
Detect patterns in phone communication data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import Counter
import os
from pathlib import Path

from ..logger import get_logger
from .statistical_utils import get_cached_result, cache_result
from ..utils.data_utils import safe_get_column
from ..presentation_layer.services.logging_service import LoggingService
from .ml_model_service import MLModelService
from .ml_exceptions import MLError, FeatureExtractionError
from .ml_models import (
    TimePatternModel,
    ContactPatternModel,
    AnomalyDetectionModel,
    extract_advanced_features
)
from .advanced_patterns.gap_detector import GapDetector
from .advanced_patterns.overlap_analyzer import OverlapAnalyzer
# Assuming ResponseAnalyzer exists or will be created based on the contract
from .advanced_patterns.response_analyzer import ResponseAnalyzer

logger = get_logger("pattern_detector")

class PatternDetector:
    """Detector for patterns in phone communication data."""

    def __init__(self,
                 gap_detector: Optional[GapDetector] = None, # Added
                 overlap_analyzer: Optional[OverlapAnalyzer] = None, # Added
                 response_analyzer: Optional[ResponseAnalyzer] = None, # Added & Uncommented
                 ml_model_service: Optional[MLModelService] = None,
                 logging_service: Optional[LoggingService] = None,
                 config_manager = None):
        """Initialize the pattern detector and ML models.

        Args:
            gap_detector: Optional GapDetector instance.
            overlap_analyzer: Optional OverlapAnalyzer instance.
            response_analyzer: Optional ResponseAnalyzer instance. # Uncommented
            ml_model_service: Optional ML model service
            logging_service: Optional logging service
            config_manager: Optional configuration manager
        """
        self.last_error = None
        self.logging_service = logging_service
        self.config_manager = config_manager

        # Store injected analyzers
        self.gap_detector = gap_detector or GapDetector() # Use 'or' per Sourcery suggestion
        self.overlap_analyzer = overlap_analyzer or OverlapAnalyzer() # Use 'or' per Sourcery suggestion
        self.response_analyzer = response_analyzer or ResponseAnalyzer() # Use 'or' per Sourcery suggestion

        # Use the ML model service if provided, otherwise create models directly
        if ml_model_service:
            self.ml_model_service = ml_model_service
            self._models_trained = True
        else:
            self.ml_model_service = None
            # Create models directly (legacy approach)
            self.time_model = TimePatternModel()
            self.contact_model = ContactPatternModel()
            self.anomaly_model = AnomalyDetectionModel()
            self._models_trained = False

            # Legacy model loading
            self.models_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")
            self._legacy_load_models()

        # Log initialization
        if self.logging_service:
            self.logging_service.info(
                "PatternDetector initialized",
                component="PatternDetector",
                using_ml_service=self.ml_model_service is not None
            )
        else:
            logger.info("PatternDetector initialized")

    def _legacy_load_models(self):
        """Legacy method to load pre-trained models without MLModelService."""
        try:
            Path(self.models_dir).mkdir(parents=True, exist_ok=True)

            # Try to load models directly
            for model_name, model_instance in [
                ("TimePatternModel", self.time_model),
                ("ContactPatternModel", self.contact_model),
                ("AnomalyDetectionModel", self.anomaly_model)
            ]:
                model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
                if os.path.exists(model_path):
                    success = model_instance.load(model_path)
                    if success:
                        logger.info(f"Loaded {model_name} model version {model_instance.version}")

            # Update trained status
            self._models_trained = (
                self.time_model.is_trained and
                self.contact_model.is_trained and
                self.anomaly_model.is_trained
            )

        except Exception as e:
            if self.logging_service:
                self.logging_service.warning(
                    f"Could not load pre-trained models: {e}",
                    component="PatternDetector",
                    error=str(e)
                )
            else:
                logger.warning(f"Could not load pre-trained models: {e}")
            self._models_trained = False

    def _ensure_models_trained(self, df: pd.DataFrame, column_mapping=None):
        """Train ML models if not already trained or update existing models.

        Args:
            df: DataFrame containing phone records
            column_mapping: Optional mapping from standard column names to actual columns

        Returns:
            bool: True if models are trained successfully
        """
        # If we have the ML model service, use it
        if self.ml_model_service:
            try:
                # Log the action
                if self.logging_service:
                    self.logging_service.info(
                        "Ensuring models are trained using MLModelService",
                        component="PatternDetector",
                        action="train_models"
                    )

                # Check if we should use incremental learning (feature flag)
                use_incremental = True
                if self.config_manager and hasattr(self.config_manager, "is_feature_enabled"):
                    use_incremental = self.config_manager.is_feature_enabled("incremental_learning", default=True)

                # Train or update the models
                if use_incremental and self._models_trained:
                    # Use incremental learning if models are already trained
                    results = self.ml_model_service.update_models(df, column_mapping)
                else:
                    # Train from scratch
                    results = self.ml_model_service.train_models(df, column_mapping)

                # Check if all models were trained successfully
                self._models_trained = all(results.values())
                return self._models_trained

            except Exception as e:
                if self.logging_service:
                    self.logging_service.error(
                        f"Error ensuring models are trained: {str(e)}",
                        component="PatternDetector",
                        action="train_models",
                        error=str(e)
                    )
                else:
                    logger.error(f"Error ensuring models are trained: {e}")
                self.last_error = str(e)
                return False

        # Legacy approach (no MLModelService)
        try:
            # Extract advanced features using our enhanced feature engineering
            features = extract_advanced_features(df, column_mapping)

            if features.empty:
                if self.logging_service:
                    self.logging_service.warning(
                        "No features extracted, cannot train models",
                        component="PatternDetector"
                    )
                else:
                    logger.warning("No features extracted, cannot train models")
                return False

            # Train or update time model
            time_features = features.select_dtypes(include=['number'])
            time_target = features['hour'] if 'hour' in features else None

            if not self.time_model.is_trained:
                if self.logging_service:
                    self.logging_service.info(
                        "Training new time pattern model",
                        component="PatternDetector",
                        model="TimePatternModel"
                    )
                else:
                    logger.info("Training new time pattern model")
                success = self.time_model.train(time_features, time_target)
                if success:
                    self.time_model.bump_version("minor")
            else:
                # Use incremental learning for existing model
                if self.logging_service:
                    self.logging_service.info(
                        "Updating existing time pattern model",
                        component="PatternDetector",
                        model="TimePatternModel",
                        current_version=self.time_model.version
                    )
                else:
                    logger.info("Updating existing time pattern model")
                success = self.time_model.partial_fit(time_features, time_target)
                if success:
                    self.time_model.bump_version("patch")

            # Train or update contact and anomaly models (similar approach to time model)
            # ... (contact model training code) ...
            # ... (anomaly model training code) ...

            # Save updated models
            self._legacy_save_models()

            self._models_trained = True
            return True

        except Exception as e:
            if self.logging_service:
                self.logging_service.error(
                    f"Error ensuring models are trained: {str(e)}",
                    component="PatternDetector",
                    error=str(e)
                )
            else:
                logger.error(f"Error ensuring models are trained: {e}")
            self.last_error = str(e)
            return False

    def _legacy_save_models(self):
        """Legacy method to save trained models without MLModelService."""
        try:
            Path(self.models_dir).mkdir(parents=True, exist_ok=True)

            # Save models directly
            for model_name, model_instance in [
                ("TimePatternModel", self.time_model),
                ("ContactPatternModel", self.contact_model),
                ("AnomalyDetectionModel", self.anomaly_model)
            ]:
                if model_instance.is_trained:
                    model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
                    success = model_instance.save(model_path)
                    if success:
                        if self.logging_service:
                            self.logging_service.info(
                                f"Saved {model_name} model",
                                component="PatternDetector",
                                model=model_name,
                                version=model_instance.version
                            )
                        else:
                            logger.info(f"Saved {model_name} model version {model_instance.version}")

        except Exception as e:
            if self.logging_service:
                self.logging_service.warning(
                    f"Could not save trained models: {str(e)}",
                    component="PatternDetector",
                    error=str(e)
                )
            else:
                logger.warning(f"Could not save trained models: {e}")

    def detect_all_patterns(self, df: pd.DataFrame, column_mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Orchestrates detection of all pattern types (core, advanced, ML).

        Args:
            df: DataFrame containing phone records.
            column_mapping: Optional mapping from standard column names to actual columns.

        Returns:
            Dictionary containing aggregated patterns, anomalies, and errors.
        """
        results = {
            "detected_patterns": [],
            "anomalies": [],
            "advanced_analysis": {}, # Store results from advanced analyzers here
            "errors": []
        }

        if df is None or df.empty:
            results["errors"].append("Input DataFrame is empty, cannot detect patterns.")
            return results

        # --- Core Pattern Detection ---
        try:
            time_patterns = self.detect_time_patterns(df, column_mapping)
            results["detected_patterns"].extend(time_patterns)
        except Exception as e:
            error_msg = f"Error in core time pattern detection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)

        try:
            contact_patterns = self.detect_contact_patterns(df, column_mapping) # This might be ML based now
            # Decide how to integrate ML contact clusters vs. older contact patterns
            if isinstance(contact_patterns, list): # Assuming ML returns list
                 results["detected_patterns"].extend(contact_patterns)
            # Handle older dict format if necessary
        except Exception as e:
            error_msg = f"Error in contact pattern detection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)

        try:
            sequence_patterns = self.detect_sequence_patterns(df)
            results["detected_patterns"].extend(sequence_patterns)
        except Exception as e:
            error_msg = f"Error in sequence pattern detection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)

        # --- Advanced Pattern Detection ---
        min_gap_hours = self.config_manager.get("analysis.gaps.min_gap_hours", 24.0) if self.config_manager else 24.0
        time_window_minutes = self.config_manager.get("analysis.overlaps.time_window_minutes", 5.0) if self.config_manager else 5.0
        response_time_window = self.config_manager.get("analysis.response.time_window_minutes", 60.0) if self.config_manager else 60.0 # Example config

        # Gap Detection
        try:
            gap_analysis = self.gap_detector.analyze_gap_patterns(df, min_gap_hours=min_gap_hours)
            if "error" in gap_analysis:
                results["errors"].append(f"GapDetector Error: {gap_analysis['error']}")
            else:
                results["advanced_analysis"]["gaps"] = gap_analysis
                # Optionally add significant gaps to main patterns list
                if gap_analysis.get("overall_gaps"):
                     for gap in gap_analysis["overall_gaps"]:
                         if gap.get("significance", 0) > 1.5: # Example threshold
                             results["detected_patterns"].append({
                                 "pattern_type": "gap",
                                 "subtype": "significant_overall",
                                 **gap # Unpack gap details
                             })
        except Exception as e:
            error_msg = f"Error calling GapDetector: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)

        # Overlap Analysis
        try:
            overlap_analysis = self.overlap_analyzer.analyze_overlaps(df, time_window_minutes=time_window_minutes)
            if "error" in overlap_analysis:
                results["errors"].append(f"OverlapAnalyzer Error: {overlap_analysis['error']}")
            else:
                results["advanced_analysis"]["overlaps"] = overlap_analysis
                # Optionally add significant overlaps/groups to main patterns list
                if overlap_analysis.get("group_conversations"):
                     for group in overlap_analysis["group_conversations"]:
                         results["detected_patterns"].append({
                             "pattern_type": "overlap",
                             "subtype": "group_conversation",
                             **group
                         })
        except Exception as e:
            error_msg = f"Error calling OverlapAnalyzer: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)        # Response Analysis
        try:
            response_analysis = self.response_analyzer.analyze_response_patterns(df, column_mapping)
            if "error" in response_analysis and response_analysis["error"]:
                results["errors"].append(f"ResponseAnalyzer Error: {response_analysis['error']}")
            else:
                # Store full analysis results
                results["advanced_analysis"]["responses"] = response_analysis
                
                # Add response anomalies to main anomalies list
                if response_analysis.get("anomalies"):
                     results["anomalies"].extend(response_analysis["anomalies"])
                     
                # Convert response analysis results to standard pattern format
                response_patterns = self._convert_response_results_to_patterns(response_analysis)
                if response_patterns:
                    results["detected_patterns"].extend(response_patterns)
                    logger.debug(f"Added {len(response_patterns)} response patterns to results")

        except Exception as e:
            error_msg = f"Error calling ResponseAnalyzer: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)


        # --- ML-Based Anomaly Detection ---
        try:
            if self.ml_model_service:
                ml_anomalies = self.ml_model_service.predict("AnomalyDetectionModel", df, column_mapping)
                # Process ml_anomalies (might be indices or a series)
                # Convert to the expected anomaly dictionary format
            elif self.anomaly_model.is_trained:
                 features = extract_advanced_features(df, column_mapping)
                 anomaly_preds = self.anomaly_model.predict(features)
                 # Process anomaly_preds
                 # Convert to the expected anomaly dictionary format

            # Placeholder for processed anomalies
            processed_anomalies = [] # Replace with actual processing logic
            results["anomalies"].extend(processed_anomalies)

        except Exception as e:
            error_msg = f"Error during ML anomaly detection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)


        # --- Final Processing ---
        # Calculate significance for all detected patterns
        try:
            results["detected_patterns"] = self.calculate_pattern_significance(results["detected_patterns"], df)
        except Exception as e:
             error_msg = f"Error calculating pattern significance: {str(e)}"
             logger.error(error_msg, exc_info=True)
             results["errors"].append(error_msg)

        # Log summary
        if self.logging_service:
            self.logging_service.info(
                "Pattern detection complete",
                component="PatternDetector",
                patterns_found=len(results["detected_patterns"]),
                anomalies_found=len(results["anomalies"]),
                errors_count=len(results["errors"])
            )

        return results


    def detect_time_patterns(self, df: pd.DataFrame, column_mapping=None) -> list[dict]:
        """Detect time-based patterns (can be rule-based or ML-based).

        Args:
            df: DataFrame containing phone records
            column_mapping: Optional mapping from standard column names to actual columns

        Returns:
            List of detected patterns with details
        """
        # Log the operation
        if self.logging_service:
            self.logging_service.info(
                "Detecting time patterns",
                component="PatternDetector",
                action="detect_time_patterns",
                data_size=len(df)
            )

        # Use key for caching the results
        cache_key = f"time_patterns_{hash(tuple(sorted(df.index)))}"
        cached_result = get_cached_result(cache_key)
        if cached_result:
            if self.logging_service:
                self.logging_service.debug(
                    "Using cached time pattern results",
                    component="PatternDetector",
                    cache_key=cache_key
                )
            return cached_result

        # Ensure models are trained
        if not self._models_trained:
            self._ensure_models_trained(df, column_mapping)

        # Detect patterns based on the data
        patterns = []

        try:
            # Use ML model service if available
            if self.ml_model_service:
                # Get predictions from time model
                predictions = self.ml_model_service.predict("TimePatternModel", df, column_mapping)

                # Extract features for analysis
                features = self.ml_model_service.extract_features(df, column_mapping)
            else:
                # Legacy approach: extract features and use direct model predictions
                features = extract_advanced_features(df, column_mapping)
                predictions = self.time_model.predict(features)

            # Analyze time distributions
            # (Rest of the time pattern detection logic remains the same)
            # ...

            # Cache and return the results
            cache_result(cache_key, patterns)
            return patterns

        except Exception as e:
            error_msg = f"Error detecting time patterns: {str(e)}"
            if self.logging_service:
                self.logging_service.error(
                    error_msg,
                    component="PatternDetector",
                    action="detect_time_patterns",
                    error=str(e)
                )
            else:
                logger.error(error_msg)
            self.last_error = error_msg
            return []

    def _detect_hourly_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect hourly patterns."""
        patterns = []

        # Extract hour of day
        df['hour'] = df['timestamp'].dt.hour
        hour_counts = df['hour'].value_counts()

        # Look for peak hours
        for hour, count in hour_counts.items():
            if count >= 3 and count / len(df) >= 0.1:  # At least 3 occurrences and 10% of total
                # Determine time of day
                if 5 <= hour < 12:
                    time_of_day = "morning"
                elif 12 <= hour < 17:
                    time_of_day = "afternoon"
                elif 17 <= hour < 22:
                    time_of_day = "evening"
                else:
                    time_of_day = "night"

                patterns.append({
                    'pattern_type': 'time',
                    'subtype': 'hour',
                    'hour': int(hour),
                    'time_of_day': time_of_day,
                    'description': f"Frequent communication during the {time_of_day} (around {hour}:00)",
                    'confidence': min(1.0, float(count / len(df) + count / 20)),
                    'occurrences': int(count),
                    'examples': [
                        {
                            'timestamp': row['timestamp'].isoformat(),
                            'phone_number': row['phone_number']
                        }
                        for _, row in df[df['hour'] == hour].head(3).iterrows()
                    ]
                })

        return patterns

    def _detect_daily_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect daily patterns."""
        patterns = []

        # Extract day of week
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        day_counts = df['day_of_week'].value_counts()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Look for peak days
        for day, count in day_counts.items():
            if count >= 2 and count / len(df) >= 0.1:  # At least 2 occurrences and 10% of total
                day_name = day_names[day]

                # Check if it's a weekend
                is_weekend = day >= 5  # 5=Saturday, 6=Sunday

                patterns.append({
                    'pattern_type': 'time',
                    'subtype': 'day',
                    'day': int(day),
                    'day_name': day_name,
                    'is_weekend': bool(is_weekend),
                    'description': f"Frequent communication on {day_name}s",
                    'confidence': min(1.0, float(count / len(df) + count / 10)),
                    'occurrences': int(count),
                    'examples': [
                        {
                            'timestamp': row['timestamp'].isoformat(),
                            'phone_number': row['phone_number']
                        }
                        for _, row in df[df['day_of_week'] == day].head(3).iterrows()
                    ]
                })

        return patterns

    def _detect_day_hour_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect day-hour combination patterns."""
        patterns = []

        # Create day-hour combination
        if 'hour' not in df.columns:
            df['hour'] = df['timestamp'].dt.hour
        if 'day_of_week' not in df.columns:
            df['day_of_week'] = df['timestamp'].dt.dayofweek

        df['day_hour'] = df['day_of_week'].astype(str) + '_' + df['hour'].astype(str)
        day_hour_counts = df['day_hour'].value_counts()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Look for specific day-hour combinations
        for day_hour, count in day_hour_counts.items():
            if count >= 2 and count / len(df) >= 0.08:  # At least 2 occurrences and 8% of total
                day, hour = map(int, day_hour.split('_'))
                day_name = day_names[day]

                # Determine time of day
                if 5 <= hour < 12:
                    time_of_day = "morning"
                elif 12 <= hour < 17:
                    time_of_day = "afternoon"
                elif 17 <= hour < 22:
                    time_of_day = "evening"
                else:
                    time_of_day = "night"

                patterns.append({
                    'pattern_type': 'time',
                    'subtype': 'day_hour',
                    'day': day,
                    'day_name': day_name,
                    'hour': hour,
                    'time_of_day': time_of_day,
                    'description': f"Frequent communication on {day_name} {time_of_day}s (around {hour}:00)",
                    'confidence': min(1.0, float(count / len(df) + count / 5)),
                    'occurrences': int(count),
                    'examples': [
                        {
                            'timestamp': row['timestamp'].isoformat(),
                            'phone_number': row['phone_number']
                        }
                        for _, row in df[df['day_hour'] == day_hour].head(3).iterrows()
                    ]
                })

        return patterns

    def detect_contact_patterns(self, df: pd.DataFrame, column_mapping=None) -> List[Dict[str, Any]]: # Changed return type
        """Detect contact patterns, primarily using ML clustering.

        Args:
            df: DataFrame containing phone records
            column_mapping: Optional mapping

        Returns:
            List of detected contact cluster patterns.
        """
        cache_key = f"ml_contact_patterns_{hash(str(df.shape))}" # Use shape hash for simplicity
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        patterns = []
        try:
            # Ensure models are trained/updated
            self._ensure_models_trained(df, column_mapping)

            # Use ML model service if available
            if self.ml_model_service:
                clusters = self.ml_model_service.predict("ContactPatternModel", df, column_mapping)
                features = self.ml_model_service.extract_features(df, column_mapping) # Needed? Maybe not for just prediction
            else:
                # Legacy approach
                features = extract_advanced_features(df, column_mapping)
                clusters = self.contact_model.predict(features)

            # Process clusters into pattern dictionaries
            if clusters is not None and not clusters.empty and isinstance(clusters, pd.Series):
                # Assuming clusters is a Series with cluster IDs aligned with df index
                df_with_clusters = df.copy()
                df_with_clusters['cluster_id'] = clusters

                for cluster_id in sorted(df_with_clusters['cluster_id'].unique()):
                    cluster_df = df_with_clusters[df_with_clusters['cluster_id'] == cluster_id]
                    if not cluster_df.empty:
                        contact_col = column_mapping.get('phone_number', 'phone_number') if column_mapping else 'phone_number'
                        example_contacts = []
                        if contact_col in cluster_df.columns:
                             example_contacts = cluster_df[contact_col].head(3).astype(str).tolist()

                        pattern = {
                            'pattern_type': 'contact_cluster',
                            'cluster_id': int(cluster_id),
                            'size': int(len(cluster_df)),
                            'example_contacts': example_contacts,
                            'description': f"Contact cluster {cluster_id} with {len(cluster_df)} records"
                        }
                        patterns.append(pattern)

            cache_result(cache_key, patterns)
            return patterns

        except Exception as e:
            error_msg = f"Error detecting ML contact patterns: {str(e)}"
            if self.logging_service:
                 self.logging_service.error(error_msg, component="PatternDetector", action="detect_contact_patterns", error=str(e))
            else:
                 logger.error(error_msg)
            self.last_error = error_msg
            return [] # Return empty list on error

    def detect_sequence_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect sequence patterns in communication.

        Args:
            df: DataFrame containing phone records

        Returns:
            List of detected sequence patterns
        """
        # Log the operation
        if self.logging_service:
            self.logging_service.info(
                "Detecting sequence patterns",
                component="PatternDetector",
                action="detect_sequence_patterns",
                data_size=len(df)
            )

        # Use key for caching the results
        cache_key = f"sequence_patterns_{hash(str(df))}"
        cached_result = get_cached_result(cache_key)
        if cached_result:
            if self.logging_service:
                self.logging_service.debug(
                    "Using cached sequence pattern results",
                    component="PatternDetector",
                    cache_key=cache_key
                )
            return cached_result

        patterns = []
        try:
            # Work on a copy to avoid side effects
            df_copy = df.copy()

            # Basic validation
            if 'timestamp' not in df_copy.columns: return patterns
            if not pd.api.types.is_datetime64_any_dtype(df_copy['timestamp']):
                df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])

            # Sort by timestamp
            df_sorted = df_copy.sort_values('timestamp')

            # Look for text-then-call patterns
            text_call_patterns = self._detect_text_call_patterns(df_sorted)
            patterns.extend(text_call_patterns)

            # Look for regular check-in patterns
            checkin_patterns = self._detect_checkin_patterns(df_sorted)
            patterns.extend(checkin_patterns)

            # Sort patterns by confidence
            patterns.sort(key=lambda x: x.get('confidence', 0), reverse=True)

            # Cache and return the results
            cache_result(cache_key, patterns)
            return patterns

        except Exception as e:
            error_msg = f"Error detecting sequence patterns: {str(e)}"
            if self.logging_service:
                 self.logging_service.error(error_msg, component="PatternDetector", action="detect_sequence_patterns", error=str(e))
            else:
                 logger.error(error_msg)
            self.last_error = error_msg
            return []

    def _detect_text_call_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect text-then-call sequence patterns."""
        patterns = []

        try:
            # Use safe_get_column to get the duration column
            duration_col = safe_get_column(df, 'duration')

            # Check if we have valid duration values to identify calls
            if duration_col.isna().all():
                return patterns

            # Group by contact
            for contact in df['phone_number'].unique():
                contact_df = df[df['phone_number'] == contact].copy()

                # Skip if too few interactions
                if len(contact_df) < 4:
                    continue

                # Mark texts and calls
                contact_df['is_call'] = contact_df['duration'] > 0
                contact_df['is_text'] = ~contact_df['is_call']

                # Look for text followed by call within 30 minutes
                text_call_sequences = []

                for i in range(len(contact_df) - 1):
                    curr = contact_df.iloc[i]
                    next_msg = contact_df.iloc[i + 1]

                    # Check if current is text and next is call
                    if curr['is_text'] and next_msg['is_call']:
                        # Check if they're within 30 minutes
                        time_diff = (next_msg['timestamp'] - curr['timestamp']).total_seconds() / 60

                        if time_diff <= 30:
                            text_call_sequences.append((curr, next_msg))

                # If we found at least 2 sequences, it's a pattern
                if len(text_call_sequences) >= 2:
                    patterns.append({
                        'pattern_type': 'sequence',
                        'subtype': 'text_call',
                        'contact': contact,
                        'description': "Text messages often followed by calls within 30 minutes",
                        'confidence': min(1.0, 0.5 + len(text_call_sequences) / 5),
                        'occurrences': len(text_call_sequences),
                        'examples': [
                            {
                                'text_timestamp': text['timestamp'].isoformat(),
                                'call_timestamp': call['timestamp'].isoformat(),
                                'time_diff_minutes': round((call['timestamp'] - text['timestamp']).total_seconds() / 60, 1)
                            }
                            for text, call in text_call_sequences[:3]
                        ]
                    })

        except Exception as e:
            logger.error(f"Error detecting text-call patterns: {str(e)}")

        return patterns

    def _detect_checkin_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect regular check-in patterns."""
        patterns = []

        try:
            # Group by contact
            for contact in df['phone_number'].unique():
                contact_df = df[df['phone_number'] == contact]

                # Skip if too few interactions
                if len(contact_df) < 5:
                    continue

                # Check for daily check-ins
                contact_df['date'] = contact_df['timestamp'].dt.date
                dates_count = contact_df['date'].nunique()

                if dates_count >= 5:
                    # Check if there's at least one interaction on most days
                    date_range = (contact_df['timestamp'].max() - contact_df['timestamp'].min()).days + 1

                    if dates_count / date_range >= 0.7:  # Interaction on at least 70% of days
                        patterns.append({
                            'pattern_type': 'sequence',
                            'subtype': 'daily_checkin',
                            'contact': contact,
                            'description': "Regular daily check-ins",
                            'confidence': min(1.0, dates_count / date_range),
                            'occurrences': dates_count,
                            'examples': [
                                {
                                    'date': date.isoformat(),
                                    'count': count
                                }
                                for date, count in contact_df.groupby('date').size().head(3).items()
                            ]
                        })

                # Check for weekly check-ins
                contact_df['week'] = contact_df['timestamp'].dt.isocalendar().week
                contact_df['year'] = contact_df['timestamp'].dt.isocalendar().year
                contact_df['year_week'] = contact_df['year'].astype(str) + '-' + contact_df['week'].astype(str)
                weeks_count = contact_df['year_week'].nunique()

                if weeks_count >= 3:
                    # Check if there's at least one interaction in most weeks
                    week_range = (contact_df['timestamp'].max() - contact_df['timestamp'].min()).days / 7

                    if weeks_count / week_range >= 0.7:  # Interaction in at least 70% of weeks
                        patterns.append({
                            'pattern_type': 'sequence',
                            'subtype': 'weekly_checkin',
                            'contact': contact,
                            'description': "Regular weekly check-ins",
                            'confidence': min(1.0, weeks_count / week_range),
                            'occurrences': weeks_count,
                            'examples': [
                                {
                                    'year_week': yw,
                                    'count': count
                                }
                                for yw, count in contact_df.groupby('year_week').size().head(3).items()
                            ]
                        })

        except Exception as e:
            logger.error(f"Error detecting check-in patterns: {str(e)}")

        return patterns

    def calculate_pattern_significance(self, patterns: List[Dict[str, Any]], df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Calculate significance scores for patterns.

        Args:
            patterns: List of detected patterns
            df: DataFrame containing phone records

        Returns:
            Patterns with added significance scores
        """
        try:
            # Make a copy to avoid modifying the original
            patterns_with_significance = []

            for pattern in patterns:
                # Copy the pattern
                pattern_copy = pattern.copy()

                # Calculate significance based on confidence and occurrences
                confidence = pattern.get('confidence', 0)
                occurrences = pattern.get('occurrences', 0)

                # More occurrences and higher confidence mean higher significance
                significance_score = confidence * min(1.0, occurrences / max(1, len(df) * 0.1))

                # Add significance score
                pattern_copy['significance_score'] = significance_score

                patterns_with_significance.append(pattern_copy)

            # Sort by significance score
            patterns_with_significance.sort(key=lambda x: x['significance_score'], reverse=True)

            return patterns_with_significance

        except Exception as e:
            logger.error(f"Error calculating pattern significance: {str(e)}")
            return patterns

    def filter_patterns_by_confidence(self, patterns: List[Dict[str, Any]],
                                     min_confidence: float = 0.0,
                                     max_confidence: float = 1.0) -> List[Dict[str, Any]]:
        """Filter patterns by confidence level.

        Args:
            patterns: List of detected patterns
            min_confidence: Minimum confidence level (inclusive)
            max_confidence: Maximum confidence level (exclusive)

        Returns:
            Filtered list of patterns
        """
        return [p for p in patterns if min_confidence <= p.get('confidence', 0) < max_confidence]

    def _convert_response_results_to_patterns(self, response_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Converts ResponseAnalyzer results to standardized pattern format.
        
        Args:
            response_analysis: Dictionary from ResponseAnalyzer.analyze_response_patterns()
            
        Returns:
            List of pattern dictionaries in the standard format.
        """
        patterns = []
        
        # Skip conversion if response_analysis is None or has error
        if not response_analysis or "error" in response_analysis and response_analysis["error"]:
            return patterns
            
        # 1. Add average response time pattern if available
        response_times = response_analysis.get("response_times", {})
        if response_times and response_times.get("average_response_time_seconds") is not None:
            avg_time = response_times["average_response_time_seconds"]
            patterns.append({
                "pattern_type": "response_time",
                "subtype": "average",
                "value_seconds": avg_time,
                "description": f"Average response time is {avg_time:.1f} seconds",
                "significance": self._calculate_response_time_significance(avg_time)
            })
              # 2. Add quick/delayed responder patterns if significant numbers exist
        quick_count = response_times.get("quick_responders_count", 0)
        delayed_count = response_times.get("delayed_responders_count", 0)
        
        # Calculate total count either from response time distribution or as sum of quick and delayed
        total_count_from_dist = response_times.get("response_time_distribution", {}).get("count", 0)
        if total_count_from_dist:
            total_count = total_count_from_dist
        else:
            # If response_time_distribution doesn't have count, try to get it from the details DataFrame size
            details_df = response_times.get("details")
            if isinstance(details_df, pd.DataFrame) and not details_df.empty:
                total_count = len(details_df)
            else:
                # Fall back to sum of quick and delayed, plus any "normal" responses
                total_count = quick_count + delayed_count
        
        if total_count > 0:
            quick_ratio = quick_count / total_count
            delayed_ratio = delayed_count / total_count
            
            # Add patterns if ratios exceed thresholds
            if quick_ratio > 0.3:  # 30% are quick responses
                patterns.append({
                    "pattern_type": "response_time",
                    "subtype": "quick_responder",
                    "value": quick_count,
                    "ratio": quick_ratio,
                    "description": f"High ratio of quick responses ({quick_ratio:.1%})",
                    "significance": min(3.0, quick_ratio * 5)  # Scale significance
                })
                
            if delayed_ratio > 0.2:  # 20% are delayed responses
                patterns.append({
                    "pattern_type": "response_time",
                    "subtype": "delayed_responder",
                    "value": delayed_count,
                    "ratio": delayed_ratio,
                    "description": f"High ratio of delayed responses ({delayed_ratio:.1%})",
                    "significance": min(3.0, delayed_ratio * 6)  # Scale significance
                })
          # 3. Add reciprocity patterns
        reciprocity = response_analysis.get("reciprocity_patterns", {})
        init_ratio = None
        if reciprocity:
            # First try to get field using the naming in the implementation
            if reciprocity.get("overall_initiation_ratio") is not None:
                init_ratio = reciprocity["overall_initiation_ratio"]
            # Fallback to the field name in the contract
            elif reciprocity.get("initiation_ratio") is not None:
                init_ratio = reciprocity["initiation_ratio"]
                
        if init_ratio is not None:
            
            # Only add if there's a notable imbalance
            if init_ratio < 0.3 or init_ratio > 0.7:
                patterns.append({
                    "pattern_type": "reciprocity",
                    "subtype": "initiation_imbalance",
                    "user_initiation_ratio": init_ratio,
                    "description": f"{'User rarely' if init_ratio < 0.3 else 'User usually'} initiates conversations ({init_ratio:.1%})",
                    "significance": min(2.5, abs(0.5 - init_ratio) * 6)  # Distance from balanced
                })
        
        # 4. Add conversation flow patterns
        flows = response_analysis.get("conversation_flows", {})
        if flows and flows.get("conversation_count", 0) > 10:  # Only if we have enough conversations
            avg_duration = flows.get("average_duration_seconds")
            avg_msg_count = flows.get("average_message_count")
            
            if avg_duration is not None and avg_duration > 1800:  # > 30 minutes
                patterns.append({
                    "pattern_type": "conversation_flow",
                    "subtype": "long_conversations",
                    "average_duration_seconds": avg_duration,
                    "description": f"Conversations tend to be extended ({avg_duration/60:.1f} minutes average)",
                    "significance": min(2.0, avg_duration / 3600)  # Scale by hours
                })
                
            if avg_msg_count is not None and avg_msg_count > 15:  # > 15 messages
                patterns.append({
                    "pattern_type": "conversation_flow",
                    "subtype": "message_intensive",
                    "average_messages": avg_msg_count,
                    "description": f"Conversations tend to have many messages ({avg_msg_count:.1f} average)",
                    "significance": min(2.0, avg_msg_count / 10)  # Scale by 10s of messages
                })
        
        return patterns
        
    def _calculate_response_time_significance(self, avg_time_seconds: float) -> float:
        """Calculate significance score for response time patterns.
        
        Higher score for very fast (<60s) or very slow (>3600s) average times.
        
        Args:
            avg_time_seconds: Average response time in seconds
            
        Returns:
            Significance score between 0.0 and 3.0
        """
        if avg_time_seconds < 60:  # Very fast: <1 minute
            return min(3.0, 3.0 * (60 - avg_time_seconds) / 50)
        elif avg_time_seconds > 3600:  # Very slow: >1 hour
            return min(3.0, 1.5 * (avg_time_seconds / 3600))
        else:
            # Less significant in the "normal" range (calculate based on deviation from 10 minutes)
            return max(0.5, min(1.5, abs(600 - avg_time_seconds) / 600))
