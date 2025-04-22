"""
Pattern Detector Module
------------------
Detect patterns in phone communication data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import Counter

from ..logger import get_logger
from .statistical_utils import get_cached_result, cache_result
from .ml_models import TimePatternModel, ContactPatternModel, extract_features

logger = get_logger("pattern_detector")

class PatternDetector:
    """Detector for patterns in phone communication data."""

    def __init__(self):
        """Initialize the pattern detector and ML models."""
        self.last_error = None
        self.time_model = TimePatternModel()
        self.contact_model = ContactPatternModel()
        self._models_trained = False

    def _ensure_models_trained(self, df: pd.DataFrame):
        """Train ML models if not already trained."""
        if not self._models_trained:
            features = extract_features(df)
            # Train time model on time features
            if not self.time_model.is_trained:
                time_features = features[['hour', 'dayofweek']]
                self.time_model.train(time_features)
            # Train contact model on message_length
            if not self.contact_model.is_trained:
                contact_features = features[['message_length']]
                self.contact_model.train(contact_features)
            self._models_trained = True

    def detect_time_patterns(self, df: pd.DataFrame) -> list[dict]:
        """Detect time-based patterns using ML model.

        Args:
            df: DataFrame containing phone records

        Returns:
            List of detected patterns with details
        """
        cache_key = f"ml_time_patterns_{hash(str(df))}"
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        try:
            features = extract_features(df)
            self._ensure_models_trained(df)
            time_features = features[['hour', 'dayofweek']]
            clusters = self.time_model.predict(time_features)
            patterns = []
            if clusters is not None and not clusters.empty:
                for cluster_id in sorted(clusters.unique()):
                    cluster_df = df.iloc[clusters[clusters == cluster_id].index]
                    if not cluster_df.empty:
                        pattern = {
                            'pattern_type': 'time_cluster',
                            'cluster_id': int(cluster_id),
                            'size': int(len(cluster_df)),
                            'example_timestamps': cluster_df['timestamp'].head(3).astype(str).tolist(),
                            'description': f"Cluster {cluster_id} with {len(cluster_df)} records"
                        }
                        patterns.append(pattern)

            cache_result(cache_key, patterns)
            return patterns

        except Exception as e:
            logger.error(f"Error detecting ML time patterns: {str(e)}")
            self.last_error = str(e)
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

    def detect_contact_patterns(self, df: pd.DataFrame) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Detect patterns for each contact.

        Args:
            df: DataFrame containing phone records

        Returns:
            Dictionary mapping contact phone numbers to pattern dictionaries
        """
        cache_key = f"ml_contact_patterns_{hash(str(df))}"
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        try:
            features = extract_features(df)
            self._ensure_models_trained(df)
            contact_features = features[['message_length']]
            clusters = self.contact_model.predict(contact_features)
            patterns = []
            if clusters is not None and not clusters.empty:
                for cluster_id in sorted(clusters.unique()):
                    cluster_df = df.iloc[clusters[clusters == cluster_id].index]
                    if not cluster_df.empty:
                        pattern = {
                            'pattern_type': 'contact_cluster',
                            'cluster_id': int(cluster_id),
                            'size': int(len(cluster_df)),
                            'example_contacts': cluster_df['Contact'].head(3).astype(str).tolist() if 'Contact' in cluster_df.columns else [],
                            'description': f"Contact cluster {cluster_id} with {len(cluster_df)} records"
                        }
                        patterns.append(pattern)

            cache_result(cache_key, patterns)
            return patterns

        except Exception as e:
            logger.error(f"Error detecting ML contact patterns: {str(e)}")
            self.last_error = str(e)
            return {}

    def _detect_content_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect content-based patterns."""
        # Content patterns are not supported as message_content is not available
        return []

    def _detect_interaction_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect interaction patterns."""
        patterns = []

        try:
            # Check for call duration patterns
            if 'duration' in df.columns:
                # Filter for calls (duration > 0)
                calls_df = df[df['duration'] > 0]

                if len(calls_df) >= 3:
                    avg_duration = calls_df['duration'].mean()

                    # Check for short calls
                    if avg_duration < 120:  # Less than 2 minutes
                        patterns.append({
                            'pattern_type': 'interaction',
                            'subtype': 'call_duration',
                            'description': "Typically has short calls (less than 2 minutes)",
                            'confidence': min(1.0, 0.5 + len(calls_df) / 10),
                            'occurrences': len(calls_df),
                            'examples': [
                                {
                                    'timestamp': row['timestamp'].isoformat(),
                                    'duration': row['duration']
                                }
                                for _, row in calls_df.head(3).iterrows()
                            ]
                        })

                    # Check for long calls
                    elif avg_duration > 600:  # More than 10 minutes
                        patterns.append({
                            'pattern_type': 'interaction',
                            'subtype': 'call_duration',
                            'description': "Typically has long calls (more than 10 minutes)",
                            'confidence': min(1.0, 0.5 + len(calls_df) / 10),
                            'occurrences': len(calls_df),
                            'examples': [
                                {
                                    'timestamp': row['timestamp'].isoformat(),
                                    'duration': row['duration']
                                }
                                for _, row in calls_df.head(3).iterrows()
                            ]
                        })

            # Check for message type patterns
            sent_count = len(df[df['message_type'] == 'sent'])
            received_count = len(df[df['message_type'] == 'received'])
            total_count = sent_count + received_count

            if total_count >= 5:
                # Check for mostly outgoing communication
                if sent_count / total_count >= 0.7:
                    patterns.append({
                        'pattern_type': 'interaction',
                        'subtype': 'direction',
                        'description': "Mostly outgoing communication",
                        'confidence': min(1.0, sent_count / total_count),
                        'occurrences': sent_count,
                        'examples': [
                            {
                                'timestamp': row['timestamp'].isoformat(),
                                'message_type': row['message_type']
                            }
                            for _, row in df[df['message_type'] == 'sent'].head(3).iterrows()
                        ]
                    })

                # Check for mostly incoming communication
                elif received_count / total_count >= 0.7:
                    patterns.append({
                        'pattern_type': 'interaction',
                        'subtype': 'direction',
                        'description': "Mostly incoming communication",
                        'confidence': min(1.0, received_count / total_count),
                        'occurrences': received_count,
                        'examples': [
                            {
                                'timestamp': row['timestamp'].isoformat(),
                                'message_type': row['message_type']
                            }
                            for _, row in df[df['message_type'] == 'received'].head(3).iterrows()
                        ]
                    })

        except Exception as e:
            logger.error(f"Error detecting interaction patterns: {str(e)}")

        return patterns

    def detect_content_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect content-based patterns in communication.

        Args:
            df: DataFrame containing phone records

        Returns:
            List of detected content patterns
        """
        # Content patterns are not supported as message_content is not available
        return []

    def detect_sequence_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect sequence patterns in communication.

        Args:
            df: DataFrame containing phone records

        Returns:
            List of detected sequence patterns
        """
        cache_key = f"sequence_patterns_{hash(str(df))}"
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        try:

            # Normal analysis for non-test data
            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Sort by timestamp
            df_sorted = df.sort_values('timestamp')

            patterns = []

            # Look for text-then-call patterns
            text_call_patterns = self._detect_text_call_patterns(df_sorted)
            patterns.extend(text_call_patterns)

            # Look for regular check-in patterns
            checkin_patterns = self._detect_checkin_patterns(df_sorted)
            patterns.extend(checkin_patterns)

            # Sort patterns by confidence
            patterns.sort(key=lambda x: x.get('confidence', 0), reverse=True)

            cache_result(cache_key, patterns)
            return patterns

        except Exception as e:
            logger.error(f"Error detecting sequence patterns: {str(e)}")
            self.last_error = str(e)
            return []

    def _detect_text_call_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect text-then-call sequence patterns."""
        patterns = []

        try:
            # Check if we have duration column to identify calls
            if 'duration' not in df.columns:
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
                        'description': f"Text messages often followed by calls within 30 minutes",
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
