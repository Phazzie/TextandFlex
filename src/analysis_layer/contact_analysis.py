"""
Contact Analysis Module
------------------
Analyze contact relationships and communication patterns.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from ..logger import get_logger
from ..utils.data_utils import safe_get_column
from .statistical_utils import (
    calculate_response_times,
    calculate_conversation_gaps,
    calculate_contact_activity_periods,
    get_cached_result,
    cache_result
)

logger = get_logger("contact_analysis")

class ContactAnalyzer:
    """Analyzer for contact relationships and communication patterns."""

    def __init__(self):
        """Initialize the contact analyzer."""
        self.last_error = None

    def _compute_confidence(self, count: int, total: int, divisor: float) -> float:
        """Compute confidence score based on count and total interactions."""
        return min(1.0, float(count / total + count / divisor))

    def analyze_contact_frequency(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze contact frequency.

        Args:
            df: DataFrame containing phone records

        Returns:
            Dictionary mapping contact phone numbers to frequency scores
        """
        cache_key = f"contact_frequency_{hash(str(df))}"
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        try:
            # Count interactions by contact
            contact_counts = df['phone_number'].value_counts().to_dict()

            # Calculate total interactions
            total_interactions = sum(contact_counts.values())

            # Calculate frequency scores (normalized by total interactions)
            frequency_scores = {
                phone: count / total_interactions
                for phone, count in contact_counts.items()
            }

            cache_result(cache_key, frequency_scores)
            return frequency_scores

        except Exception as e:
            error_msg = f"Error analyzing contact frequency: {str(e)}"
            logger.error(error_msg)
            self.last_error = error_msg
            return {}

    def categorize_contacts(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Categorize contacts by frequency.

        Args:
            df: DataFrame containing phone records

        Returns:
            Dictionary with categories (frequent, moderate, infrequent) mapping to lists of contact phone numbers
        """
        cache_key = f"contact_categories_{hash(str(df))}"
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        try:
            # Get contact frequency scores
            frequency_scores = self.analyze_contact_frequency(df)

            if not frequency_scores:
                return {'frequent': [], 'moderate': [], 'infrequent': []}

            # Sort contacts by frequency
            sorted_contacts = sorted(
                frequency_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Note: Removed hard-coded special case for exactly three contacts to avoid overfitting

            # Determine thresholds for categories
            # Top 20% are frequent, next 30% are moderate, rest are infrequent
            num_contacts = len(sorted_contacts)
            frequent_threshold = max(1, int(num_contacts * 0.2))
            moderate_threshold = max(frequent_threshold, int(num_contacts * 0.5))

            # Categorize contacts
            categories = {
                'frequent': [contact for contact, _ in sorted_contacts[:frequent_threshold]],
                'moderate': [contact for contact, _ in sorted_contacts[frequent_threshold:moderate_threshold]],
                'infrequent': [contact for contact, _ in sorted_contacts[moderate_threshold:]]
            }

            cache_result(cache_key, categories)
            return categories

        except Exception as e:
            error_msg = f"Error categorizing contacts: {str(e)}"
            logger.error(error_msg)
            self.last_error = error_msg
            return {'frequent': [], 'moderate': [], 'infrequent': []}

    def analyze_contact_relationships(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Analyze contact relationships.

        Args:
            df: DataFrame containing phone records

        Returns:
            Dictionary mapping contact phone numbers to relationship metrics
        """
        cache_key = f"contact_relationships_{hash(str(df))}"
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        try:
            # Use safe_get_column to get the timestamp column
            timestamp_col = safe_get_column(df, 'timestamp')

            # Check if we got valid timestamps
            if timestamp_col.isna().all():
                return {}

            # Ensure timestamp is datetime
            df = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(timestamp_col):
                df['timestamp'] = pd.to_datetime(timestamp_col)

            # Get unique contacts
            contacts = df['phone_number'].unique()

            # Initialize results
            relationships = {}

            for contact in contacts:
                # Filter data for this contact
                contact_df = df[df['phone_number'] == contact]

                # Get first and last interaction
                first_interaction = contact_df['timestamp'].min()
                last_interaction = contact_df['timestamp'].max()

                # Calculate interaction count
                interaction_count = len(contact_df)

                # Calculate average response time
                response_times = calculate_response_times(
                    contact_df,
                    'timestamp',
                    'message_type',
                    'phone_number'
                )
                avg_response_time = response_times.get('average_response_time', 0)

                # Calculate relationship duration in days
                relationship_duration = (last_interaction - first_interaction).total_seconds() / (24 * 3600)

                # Calculate interaction frequency (interactions per day)
                interaction_frequency = interaction_count / max(1, relationship_duration)

                # Calculate sent vs received ratio
                sent_count = len(contact_df[contact_df['message_type'] == 'sent'])
                received_count = len(contact_df[contact_df['message_type'] == 'received'])
                sent_received_ratio = sent_count / max(1, received_count)

                # Calculate relationship score (simple weighted formula)
                # Higher score means stronger relationship
                relationship_score = (
                    0.4 * interaction_frequency +
                    0.3 * (1 / (1 + avg_response_time / 3600)) +  # Normalize to hours and invert
                    0.3 * (1 / (1 + abs(1 - sent_received_ratio)))  # Closer to 1:1 ratio is better
                )

                # Normalize score to 0-1 range
                relationship_score = min(1.0, relationship_score)

                # Store results
                relationships[contact] = {
                    'interaction_count': interaction_count,
                    'first_interaction': first_interaction,
                    'last_interaction': last_interaction,
                    'relationship_duration_days': relationship_duration,
                    'interaction_frequency': interaction_frequency,
                    'sent_count': sent_count,
                    'received_count': received_count,
                    'sent_received_ratio': sent_received_ratio,
                    'avg_response_time': avg_response_time,
                    'relationship_score': relationship_score
                }

            cache_result(cache_key, relationships)
            return relationships

        except Exception as e:
            error_msg = f"Error analyzing contact relationships: {str(e)}"
            logger.error(error_msg)
            self.last_error = error_msg
            return {}

    def detect_contact_patterns(self, df: pd.DataFrame) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Detect patterns in contact communication.

        Args:
            df: DataFrame containing phone records

        Returns:
            Dictionary mapping contact phone numbers to pattern dictionaries
        """
        cache_key = f"contact_patterns_{hash(str(df))}"
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        try:
            # Use safe_get_column to get the timestamp column
            timestamp_col = safe_get_column(df, 'timestamp')

            # Check if we got valid timestamps
            if timestamp_col.isna().all():
                return {}

            # Ensure timestamp is datetime
            df = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(timestamp_col):
                df['timestamp'] = pd.to_datetime(timestamp_col)

            # Get unique contacts
            contacts = df['phone_number'].unique()

            # Initialize results
            patterns = {}

            for contact in contacts:
                # Filter data for this contact
                contact_df = df[df['phone_number'] == contact]

                # Skip if too few interactions
                if len(contact_df) < 3:
                    patterns[contact] = {
                        'time_patterns': [],
                        'content_patterns': [],
                        'response_patterns': []
                    }
                    continue

                # Detect time patterns
                time_patterns = self._detect_time_patterns(contact_df)

                # Detect content patterns
                content_patterns = self._detect_content_patterns(contact_df)

                # Detect response patterns
                response_patterns = self._detect_response_patterns(contact_df)

                # Store results
                patterns[contact] = {
                    'time_patterns': time_patterns,
                    'content_patterns': content_patterns,
                    'response_patterns': response_patterns
                }

            cache_result(cache_key, patterns)
            return patterns

        except Exception as e:
            error_msg = f"Error detecting contact patterns: {str(e)}"
            logger.error(error_msg)
            self.last_error = error_msg
            return {}

    def _detect_time_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect time-based patterns for a contact.

        Args:
            df: DataFrame containing phone records for a single contact

        Returns:
            List of time pattern dictionaries
        """
        patterns = []

        try:
            # Extract hour of day
            hours = df['timestamp'].dt.hour
            hour_counts = hours.value_counts()

            # Extract day of week
            days = df['timestamp'].dt.dayofweek
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_counts = days.value_counts()

            # Check for hour patterns (peak hours)
            for hour, count in hour_counts.items():
                if count >= 3 and count / len(df) >= 0.2:  # At least 3 occurrences and 20% of interactions
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
                        'type': 'hour',
                        'hour': int(hour),
                        'time_of_day': time_of_day,
                        'count': int(count),
                        'percentage': float(count / len(df)),
                        'description': f"Frequently communicates during the {time_of_day} (around {hour}:00)",
                        'confidence': self._compute_confidence(count, len(df), 10)  # Higher confidence with more occurrences
                    })

            # Check for day patterns
            for day, count in day_counts.items():
                if count >= 2 and count / len(df) >= 0.2:  # At least 2 occurrences and 20% of interactions
                    day_name = day_names[day]

                    # Check if it's a weekend
                    is_weekend = day >= 5  # 5=Saturday, 6=Sunday

                    patterns.append({
                        'type': 'day',
                        'day': int(day),
                        'day_name': day_name,
                        'is_weekend': bool(is_weekend),
                        'count': int(count),
                        'percentage': float(count / len(df)),
                        'description': f"Frequently communicates on {day_name}s",
                        'confidence': self._compute_confidence(count, len(df), 5)  # Higher confidence with more occurrences
                    })

            # Check for specific day-hour combinations
            # Using .loc to avoid SettingWithCopyWarning
            df.loc[:, 'day_hour'] = df['timestamp'].dt.dayofweek.astype(str) + '_' + df['timestamp'].dt.hour.astype(str)
            day_hour_counts = df['day_hour'].value_counts()

            for day_hour, count in day_hour_counts.items():
                if count >= 2 and count / len(df) >= 0.15:  # At least 2 occurrences and 15% of interactions
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
                        'type': 'day_hour',
                        'day': day,
                        'day_name': day_name,
                        'hour': hour,
                        'time_of_day': time_of_day,
                        'count': int(count),
                        'percentage': float(count / len(df)),
                        'description': f"Frequently communicates on {day_name} {time_of_day}s (around {hour}:00)",
                        'confidence': self._compute_confidence(count, len(df), 5)  # Higher confidence with more occurrences
                    })

        except Exception as e:
            logger.error(f"Error detecting time patterns: {str(e)}")

        return patterns

    def _detect_content_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect content-based patterns for a contact.

        Args:
            df: DataFrame containing phone records for a single contact

        Returns:
            List of content pattern dictionaries
        """
        patterns = []

        try:
            # Content patterns are not supported as message_content is not available
            return patterns

            # Skip if too many missing values
            if df['message_content'].isna().sum() / len(df) > 0.5:
                return patterns

            # Extract common words/phrases
            all_content = ' '.join(df['message_content'].fillna('').astype(str))

            # Simple word frequency analysis
            words = all_content.lower().split()
            word_counts = Counter(words)

            # Filter out common words and words shorter than 3 characters
            common_words = {'the', 'and', 'to', 'a', 'of', 'in', 'is', 'it', 'you', 'that', 'was', 'for', 'on', 'are', 'with', 'as', 'i', 'his', 'they', 'be', 'at', 'one', 'have', 'this', 'from'}
            filtered_words = {word: count for word, count in word_counts.items()
                             if word not in common_words and len(word) > 2 and count >= 3}

            # Add word patterns
            for word, count in filtered_words.items():
                if count / len(df) >= 0.2:  # Word appears in at least 20% of messages
                    patterns.append({
                        'type': 'word',
                        'word': word,
                        'count': count,
                        'percentage': float(count / len(df)),
                        'description': f"Frequently uses the word '{word}'",
                        'confidence': self._compute_confidence(count, len(df), 10)  # Higher confidence with more occurrences
                    })

            # Check for greeting patterns
            greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
            for greeting in greetings:
                if greeting in all_content.lower():
                    # Count messages containing this greeting
                    greeting_count = df['message_content'].str.contains(greeting, case=False, na=False).sum()
                    if greeting_count >= 3 and greeting_count / len(df) >= 0.2:
                        patterns.append({
                            'type': 'greeting',
                            'greeting': greeting,
                            'count': int(greeting_count),
                            'percentage': float(greeting_count / len(df)),
                            'description': f"Frequently starts messages with '{greeting.title()}'",
                            'confidence': self._compute_confidence(greeting_count, len(df), 10)
                        })

            # Check for question patterns
            question_count = df['message_content'].str.contains(r'\?', regex=True, na=False).sum()
            if question_count >= 3 and question_count / len(df) >= 0.2:
                patterns.append({
                    'type': 'question',
                    'count': int(question_count),
                    'percentage': float(question_count / len(df)),
                    'description': "Frequently asks questions",
                    'confidence': self._compute_confidence(question_count, len(df), 10)
                })

        except Exception as e:
            logger.error(f"Error detecting content patterns: {str(e)}")

        return patterns

    def _detect_response_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect response patterns for a contact.

        Args:
            df: DataFrame containing phone records for a single contact

        Returns:
            List of response pattern dictionaries
        """
        patterns = []

        try:
            # Ensure we have both sent and received messages
            sent_count = len(df[df['message_type'] == 'sent'])
            received_count = len(df[df['message_type'] == 'received'])

            if sent_count == 0 or received_count == 0:
                return patterns

            # Calculate response times
            response_times_dict = calculate_response_times(
                df,
                'timestamp',
                'message_type',
                'phone_number'
            )

            avg_response_time = response_times_dict.get('average_response_time', 0)

            # Check for quick responder pattern
            if avg_response_time <= 300 and received_count >= 3:  # Responds within 5 minutes on average
                patterns.append({
                    'type': 'quick_responder',
                    'avg_response_time': float(avg_response_time),
                    'description': "Typically responds quickly (within 5 minutes)",
                    'confidence': self._compute_confidence(received_count, len(df), 10)  # Higher confidence with more responses
                })

            # Check for slow responder pattern
            elif avg_response_time >= 3600 and received_count >= 3:  # Takes over an hour to respond on average
                patterns.append({
                    'type': 'slow_responder',
                    'avg_response_time': float(avg_response_time),
                    'description': "Typically responds slowly (over an hour)",
                    'confidence': self._compute_confidence(received_count, len(df), 10)  # Higher confidence with more responses
                })

            # Check for conversation initiator pattern
            # Count how often this contact initiates conversations
            df_sorted = df.sort_values('timestamp')

            # Group by day to identify separate conversations
            df_sorted['date'] = df_sorted['timestamp'].dt.date

            initiator_count = 0
            for date, group in df_sorted.groupby('date'):
                if len(group) >= 2:  # At least 2 messages to be a conversation
                    first_message = group.iloc[0]
                    if first_message['message_type'] == 'received':
                        initiator_count += 1

            # Check if they initiate conversations frequently
            conversation_days = len(df_sorted['date'].unique())
            if initiator_count >= 2 and initiator_count / conversation_days >= 0.5:
                patterns.append({
                    'type': 'initiator',
                    'initiator_count': int(initiator_count),
                    'conversation_days': int(conversation_days),
                    'percentage': float(initiator_count / conversation_days),
                    'description': "Frequently initiates conversations",
                    'confidence': self._compute_confidence(initiator_count, len(df), 5)  # Higher confidence with more initiations
                })

        except Exception as e:
            logger.error(f"Error detecting response patterns: {str(e)}")

        return patterns

    def analyze_conversation_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze conversation flow.

        Args:
            df: DataFrame containing phone records

        Returns:
            Dictionary with conversation flow metrics
        """
        cache_key = f"conversation_flow_{hash(str(df))}"
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        try:
            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Sort by timestamp
            df_sorted = df.sort_values('timestamp')

            # Calculate conversation gaps
            gaps = calculate_conversation_gaps(df_sorted, 'timestamp', 'phone_number', gap_threshold=3600)

            # Use gaps to identify conversations
            conversation_boundaries = gaps['gap_indices']

            # Calculate number of conversations
            conversation_count = len(conversation_boundaries) + 1

            # Calculate conversation lengths
            conversation_lengths = []
            conversation_message_counts = []
            conversation_initiators = []
            conversation_closers = []

            start_idx = 0
            for end_idx in conversation_boundaries:
                # Get conversation slice
                conversation = df_sorted.iloc[start_idx:end_idx+1]

                # Calculate length in seconds
                if len(conversation) >= 2:
                    length = (conversation['timestamp'].iloc[-1] - conversation['timestamp'].iloc[0]).total_seconds()
                    conversation_lengths.append(length)

                # Count messages
                conversation_message_counts.append(len(conversation))

                # Record initiator and closer
                if len(conversation) > 0:
                    initiator = conversation['phone_number'].iloc[0]
                    conversation_initiators.append(initiator)

                    closer = conversation['phone_number'].iloc[-1]
                    conversation_closers.append(closer)

                # Update start index for next conversation
                start_idx = end_idx + 1

            # Handle the last conversation
            if start_idx < len(df_sorted):
                conversation = df_sorted.iloc[start_idx:]

                # Calculate length in seconds
                if len(conversation) >= 2:
                    length = (conversation['timestamp'].iloc[-1] - conversation['timestamp'].iloc[0]).total_seconds()
                    conversation_lengths.append(length)

                # Count messages
                conversation_message_counts.append(len(conversation))

                # Record initiator and closer
                if len(conversation) > 0:
                    initiator = conversation['phone_number'].iloc[0]
                    conversation_initiators.append(initiator)

                    closer = conversation['phone_number'].iloc[-1]
                    conversation_closers.append(closer)

            # Calculate average conversation length
            avg_conversation_length = np.mean(conversation_lengths) if conversation_lengths else 0

            # Calculate average messages per conversation
            avg_messages_per_conversation = np.mean(conversation_message_counts) if conversation_message_counts else 0

            # Count initiators and closers
            initiator_counts = Counter(conversation_initiators)
            closer_counts = Counter(conversation_closers)

            # Prepare results
            results = {
                'conversation_count': conversation_count,
                'avg_conversation_length': float(avg_conversation_length),
                'avg_messages_per_conversation': float(avg_messages_per_conversation),
                'conversation_initiators': dict(initiator_counts),
                'conversation_closers': dict(closer_counts)
            }

            cache_result(cache_key, results)
            return results

        except Exception as e:
            error_msg = f"Error analyzing conversation flow: {str(e)}"
            logger.error(error_msg)
            self.last_error = error_msg
            return {}

    def analyze_contact_importance(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze contact importance.

        Args:
            df: DataFrame containing phone records

        Returns:
            List of contacts with importance metrics, sorted by importance
        """
        cache_key = f"contact_importance_{hash(str(df))}"
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        try:
            # Get contact relationships
            relationships = self.analyze_contact_relationships(df)

            # Get conversation flow
            conversation_flow = self.analyze_conversation_flow(df)

            # Calculate importance for each contact
            importance_list = []

            for contact, metrics in relationships.items():
                # Extract metrics
                interaction_count = metrics['interaction_count']
                relationship_score = metrics['relationship_score']
                avg_response_time = metrics['avg_response_time']
                sent_received_ratio = metrics['sent_received_ratio']

                # Calculate response rate (how often you respond to this contact)
                response_rate = 0.5  # Default to neutral
                if contact in conversation_flow.get('conversation_initiators', {}):
                    # If they initiate conversations, calculate how often you respond
                    they_initiate = conversation_flow['conversation_initiators'].get(contact, 0)
                    you_respond = sum(1 for msg in df[(df['phone_number'] == contact) & (df['message_type'] == 'sent')].itertuples()
                                     if any(prev.phone_number == contact and prev.message_type == 'received'
                                           for prev in df[df['timestamp'] < msg.timestamp].itertuples()))

                    if they_initiate > 0:
                        response_rate = min(1.0, you_respond / they_initiate)

                # Calculate importance score (weighted formula)
                importance_score = (
                    0.35 * relationship_score +
                    0.25 * (interaction_count / max(1, df['phone_number'].value_counts().max())) +
                    0.20 * response_rate +
                    0.20 * (1 / (1 + avg_response_time / 3600))  # Normalize to hours and invert
                )

                # Add to list
                importance_list.append({
                    'phone_number': contact,
                    'importance_score': float(importance_score),
                    'interaction_count': int(interaction_count),
                    'relationship_score': float(relationship_score),
                    'response_rate': float(response_rate),
                    'avg_response_time': float(avg_response_time)
                })

            # Sort by importance score (descending)
            importance_list.sort(key=lambda x: x['importance_score'], reverse=True)

            cache_result(cache_key, importance_list)
            return importance_list

        except Exception as e:
            error_msg = f"Error analyzing contact importance: {str(e)}"
            logger.error(error_msg)
            self.last_error = error_msg
            return []
