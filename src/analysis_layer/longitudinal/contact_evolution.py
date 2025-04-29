"""
Contact Evolution Module
------------------
Track how relationships with contacts change over time.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from ...logger import get_logger
from ..statistical_utils import get_cached_result, cache_result

logger = get_logger("contact_evolution")

class ContactEvolutionTracker:
    """Tracker for contact relationship evolution over time."""

    def __init__(self):
        """Initialize the contact evolution tracker."""
        self.last_error = None

    def track_evolution(self, dataframes: Dict[str, pd.DataFrame], 
                       contact: str) -> Dict[str, Any]:
        """Track the evolution of a specific contact over time.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames
            contact: Contact identifier (phone number) to track

        Returns:
            Dictionary of contact evolution metrics
        """
        if not dataframes:
            error = "Cannot track evolution with empty data"
            self.last_error = error
            logger.error(error)
            return {"error": error}

        try:
            # Create a cache key based on the dataframes and contact
            cache_key = f"contact_evolution_{contact}_{hash(str(list(dataframes.keys())))}"
            cached = get_cached_result(cache_key)
            if cached is not None:
                return cached

            # Validate all dataframes have required columns
            for period, df in dataframes.items():
                if 'timestamp' not in df.columns or 'phone_number' not in df.columns:
                    error = f"DataFrame for period {period} missing required columns"
                    self.last_error = error
                    logger.error(error)
                    return {"error": error}

            # Sort periods chronologically if they are date strings
            try:
                sorted_periods = sorted(dataframes.keys(), 
                                      key=lambda x: pd.to_datetime(x))
            except:
                # If periods can't be parsed as dates, use original order
                sorted_periods = list(dataframes.keys())
            
            # Track frequency evolution
            frequency_evolution = self._track_frequency_evolution(dataframes, sorted_periods, contact)
            
            # Track response time evolution
            response_evolution = self._track_response_evolution(dataframes, sorted_periods, contact)
            
            # Track time pattern evolution
            time_evolution = self._track_time_pattern_evolution(dataframes, sorted_periods, contact)
            
            # Track relationship strength evolution
            relationship_evolution = self._track_relationship_evolution(dataframes, sorted_periods, contact)
            
            # Combine results
            results = {
                "contact": contact,
                "periods": sorted_periods,
                "frequency_evolution": frequency_evolution,
                "response_evolution": response_evolution,
                "time_evolution": time_evolution,
                "relationship_evolution": relationship_evolution
            }
            
            # Cache results
            cache_result(cache_key, results)
            
            return results
            
        except Exception as e:
            error = f"Error tracking contact evolution: {str(e)}"
            self.last_error = error
            logger.error(error, exc_info=True)
            return {"error": error}

    def _track_frequency_evolution(self, dataframes: Dict[str, pd.DataFrame], 
                                 sorted_periods: List[str], 
                                 contact: str) -> Dict[str, Any]:
        """Track the evolution of communication frequency with a contact.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames
            sorted_periods: List of periods in chronological order
            contact: Contact identifier to track

        Returns:
            Dictionary of frequency evolution metrics
        """
        # Initialize results
        message_counts = {}
        message_percentages = {}
        relative_importance = {}
        
        # Calculate metrics for each period
        for period in sorted_periods:
            df = dataframes[period]
            
            # Filter for the specific contact
            contact_df = df[df['phone_number'] == contact]
            
            # Count messages
            message_count = len(contact_df)
            message_counts[period] = message_count
            
            # Calculate percentage of total messages
            total_messages = len(df)
            percentage = (message_count / total_messages * 100) if total_messages > 0 else 0
            message_percentages[period] = percentage
            
            # Calculate relative importance (rank among contacts)
            contact_counts = df['phone_number'].value_counts()
            if contact in contact_counts:
                rank = contact_counts.rank(method='min', ascending=False)[contact]
                relative_importance[period] = int(rank)
            else:
                relative_importance[period] = None
        
        # Calculate trends
        count_trend = self._calculate_trend([message_counts.get(p, 0) for p in sorted_periods])
        percentage_trend = self._calculate_trend([message_percentages.get(p, 0) for p in sorted_periods])
        
        return {
            "message_counts": message_counts,
            "message_percentages": message_percentages,
            "relative_importance": relative_importance,
            "count_trend": count_trend,
            "percentage_trend": percentage_trend
        }

    def _track_response_evolution(self, dataframes: Dict[str, pd.DataFrame], 
                                sorted_periods: List[str], 
                                contact: str) -> Dict[str, Any]:
        """Track the evolution of response patterns with a contact.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames
            sorted_periods: List of periods in chronological order
            contact: Contact identifier to track

        Returns:
            Dictionary of response evolution metrics
        """
        # Initialize results
        avg_response_times = {}
        response_rates = {}
        
        # Calculate metrics for each period
        for period in sorted_periods:
            df = dataframes[period]
            
            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter for the specific contact
            contact_df = df[df['phone_number'] == contact].sort_values('timestamp')
            
            # Skip if not enough messages
            if len(contact_df) < 2:
                avg_response_times[period] = None
                response_rates[period] = None
                continue
            
            # Calculate response times if direction column exists
            if 'direction' in contact_df.columns:
                # Calculate response times
                response_times = []
                
                # Group consecutive messages by direction
                direction_changes = contact_df['direction'].ne(contact_df['direction'].shift()).cumsum()
                message_groups = contact_df.groupby(direction_changes)
                
                # Calculate time between groups
                prev_group_end = None
                for _, group in message_groups:
                    if prev_group_end is not None:
                        group_start = group['timestamp'].min()
                        response_time = (group_start - prev_group_end).total_seconds() / 60  # in minutes
                        response_times.append(response_time)
                    prev_group_end = group['timestamp'].max()
                
                # Calculate average response time
                if response_times:
                    avg_response_times[period] = np.mean(response_times)
                else:
                    avg_response_times[period] = None
                
                # Calculate response rate (percentage of messages that got responses)
                sent_messages = contact_df[contact_df['direction'] == 'outgoing']
                received_messages = contact_df[contact_df['direction'] == 'incoming']
                
                if len(sent_messages) > 0:
                    response_rate = min(1.0, len(received_messages) / len(sent_messages)) * 100
                    response_rates[period] = response_rate
                else:
                    response_rates[period] = None
            else:
                # Can't calculate response metrics without direction
                avg_response_times[period] = None
                response_rates[period] = None
        
        # Calculate trends
        response_time_trend = self._calculate_trend([avg_response_times.get(p) for p in sorted_periods 
                                                  if avg_response_times.get(p) is not None])
        response_rate_trend = self._calculate_trend([response_rates.get(p) for p in sorted_periods 
                                                  if response_rates.get(p) is not None])
        
        return {
            "avg_response_times": avg_response_times,
            "response_rates": response_rates,
            "response_time_trend": response_time_trend,
            "response_rate_trend": response_rate_trend
        }

    def _track_time_pattern_evolution(self, dataframes: Dict[str, pd.DataFrame], 
                                    sorted_periods: List[str], 
                                    contact: str) -> Dict[str, Any]:
        """Track the evolution of communication time patterns with a contact.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames
            sorted_periods: List of periods in chronological order
            contact: Contact identifier to track

        Returns:
            Dictionary of time pattern evolution metrics
        """
        # Initialize results
        peak_hours = {}
        peak_days = {}
        time_consistency = {}
        
        # Calculate metrics for each period
        for period in sorted_periods:
            df = dataframes[period]
            
            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter for the specific contact
            contact_df = df[df['phone_number'] == contact]
            
            # Skip if not enough messages
            if len(contact_df) < 3:
                peak_hours[period] = None
                peak_days[period] = None
                time_consistency[period] = None
                continue
            
            # Calculate hourly distribution
            hourly_dist = contact_df['timestamp'].dt.hour.value_counts()
            if not hourly_dist.empty:
                peak_hour = hourly_dist.idxmax()
                peak_hours[period] = peak_hour
                
                # Calculate time consistency (percentage of messages in peak hour)
                peak_hour_count = hourly_dist.max()
                time_consistency[period] = (peak_hour_count / len(contact_df)) * 100
            else:
                peak_hours[period] = None
                time_consistency[period] = None
            
            # Calculate daily distribution
            daily_dist = contact_df['timestamp'].dt.day_name().value_counts()
            if not daily_dist.empty:
                peak_day = daily_dist.idxmax()
                peak_days[period] = peak_day
            else:
                peak_days[period] = None
        
        # Analyze shifts in peak hours and days
        hour_shifts = {}
        day_shifts = {}
        
        for i in range(1, len(sorted_periods)):
            prev_period = sorted_periods[i-1]
            curr_period = sorted_periods[i]
            
            # Check if peak hour changed
            if peak_hours.get(prev_period) is not None and peak_hours.get(curr_period) is not None:
                prev_peak = peak_hours[prev_period]
                curr_peak = peak_hours[curr_period]
                
                if prev_peak != curr_peak:
                    hour_shifts[f"{prev_period}_to_{curr_period}"] = {
                        "from": prev_peak,
                        "to": curr_peak
                    }
            
            # Check if peak day changed
            if peak_days.get(prev_period) is not None and peak_days.get(curr_period) is not None:
                prev_peak = peak_days[prev_period]
                curr_peak = peak_days[curr_period]
                
                if prev_peak != curr_peak:
                    day_shifts[f"{prev_period}_to_{curr_period}"] = {
                        "from": prev_peak,
                        "to": curr_peak
                    }
        
        # Calculate consistency trend
        consistency_trend = self._calculate_trend([time_consistency.get(p) for p in sorted_periods 
                                                if time_consistency.get(p) is not None])
        
        return {
            "peak_hours": peak_hours,
            "peak_days": peak_days,
            "time_consistency": time_consistency,
            "hour_shifts": hour_shifts,
            "day_shifts": day_shifts,
            "consistency_trend": consistency_trend
        }

    def _track_relationship_evolution(self, dataframes: Dict[str, pd.DataFrame], 
                                    sorted_periods: List[str], 
                                    contact: str) -> Dict[str, Any]:
        """Track the evolution of relationship strength with a contact.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames
            sorted_periods: List of periods in chronological order
            contact: Contact identifier to track

        Returns:
            Dictionary of relationship evolution metrics
        """
        # Initialize results
        relationship_scores = {}
        conversation_counts = {}
        avg_conversation_lengths = {}
        
        # Calculate metrics for each period
        for period in sorted_periods:
            df = dataframes[period]
            
            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter for the specific contact
            contact_df = df[df['phone_number'] == contact].sort_values('timestamp')
            
            # Skip if not enough messages
            if len(contact_df) < 3:
                relationship_scores[period] = None
                conversation_counts[period] = None
                avg_conversation_lengths[period] = None
                continue
            
            # Calculate relationship score based on multiple factors
            score_components = []
            
            # Factor 1: Message frequency (normalized by total messages)
            total_messages = len(df)
            contact_messages = len(contact_df)
            frequency_score = min(1.0, (contact_messages / total_messages) * 10) if total_messages > 0 else 0
            score_components.append(frequency_score)
            
            # Factor 2: Conversation detection
            conversations = []
            current_conversation = []
            
            for i, (_, row) in enumerate(contact_df.iterrows()):
                if i == 0:
                    current_conversation = [row]
                else:
                    prev_time = contact_df.iloc[i-1]['timestamp']
                    curr_time = row['timestamp']
                    time_diff = (curr_time - prev_time).total_seconds() / 60  # in minutes
                    
                    # If messages are within 30 minutes, consider them part of the same conversation
                    if time_diff <= 30:
                        current_conversation.append(row)
                    else:
                        # End of conversation
                        if len(current_conversation) > 0:
                            conversations.append(current_conversation)
                        current_conversation = [row]
            
            # Add the last conversation if it exists
            if current_conversation:
                conversations.append(current_conversation)
            
            # Calculate conversation metrics
            conversation_counts[period] = len(conversations)
            
            if conversations:
                conversation_lengths = [len(conv) for conv in conversations]
                avg_conversation_lengths[period] = np.mean(conversation_lengths)
                
                # Factor 2: Conversation depth
                max_length = max(conversation_lengths)
                conversation_score = min(1.0, max_length / 10)  # Normalize to 0-1
                score_components.append(conversation_score)
            else:
                avg_conversation_lengths[period] = None
                score_components.append(0)
            
            # Factor 3: Consistency (if contact appears in multiple periods)
            periods_with_contact = sum(1 for p in sorted_periods[:sorted_periods.index(period)+1] 
                                     if contact in dataframes[p]['phone_number'].values)
            consistency_score = min(1.0, periods_with_contact / len(sorted_periods[:sorted_periods.index(period)+1]))
            score_components.append(consistency_score)
            
            # Calculate final relationship score (average of components)
            relationship_scores[period] = np.mean(score_components) * 10  # Scale to 0-10
        
        # Calculate relationship score trend
        score_trend = self._calculate_trend([relationship_scores.get(p) for p in sorted_periods 
                                          if relationship_scores.get(p) is not None])
        
        return {
            "relationship_scores": relationship_scores,
            "conversation_counts": conversation_counts,
            "avg_conversation_lengths": avg_conversation_lengths,
            "score_trend": score_trend
        }

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend metrics for a series of values.

        Args:
            values: List of values to analyze

        Returns:
            Dictionary of trend metrics
        """
        # Remove None values
        values = [v for v in values if v is not None]
        
        # Need at least two values to calculate a trend
        if len(values) < 2:
            return {
                "direction": "unknown",
                "percentage_change": None,
                "is_significant": False
            }
        
        # Calculate percentage change from first to last value
        first_value = values[0]
        last_value = values[-1]
        
        if first_value == 0:
            percentage_change = float('inf') if last_value > 0 else 0
        else:
            percentage_change = ((last_value - first_value) / first_value) * 100
        
        # Determine trend direction
        if percentage_change > 5:
            direction = "increasing"
        elif percentage_change < -5:
            direction = "decreasing"
        else:
            direction = "stable"
        
        # Determine if trend is significant (more than 20% change)
        is_significant = abs(percentage_change) >= 20
        
        return {
            "direction": direction,
            "percentage_change": percentage_change,
            "is_significant": is_significant
        }

    def analyze_all_contacts(self, dataframes: Dict[str, pd.DataFrame], 
                           min_messages: int = 5) -> Dict[str, Any]:
        """Analyze evolution for all contacts with sufficient data.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames
            min_messages: Minimum number of messages required for analysis

        Returns:
            Dictionary of contact evolution analysis for all relevant contacts
        """
        if not dataframes:
            error = "Cannot analyze contacts with empty data"
            self.last_error = error
            logger.error(error)
            return {"error": error}

        try:
            # Create a cache key based on the dataframes
            cache_key = f"all_contacts_evolution_{hash(str(list(dataframes.keys())))}"
            cached = get_cached_result(cache_key)
            if cached is not None:
                return cached

            # Find all contacts across all periods
            all_contacts = set()
            for df in dataframes.values():
                if 'phone_number' in df.columns:
                    all_contacts.update(df['phone_number'].unique())
            
            # Filter for contacts with sufficient data
            relevant_contacts = []
            for contact in all_contacts:
                total_messages = sum(len(df[df['phone_number'] == contact]) for df in dataframes.values())
                if total_messages >= min_messages:
                    relevant_contacts.append(contact)
            
            # Analyze each relevant contact
            contact_evolutions = {}
            for contact in relevant_contacts:
                evolution = self.track_evolution(dataframes, contact)
                if "error" not in evolution:
                    contact_evolutions[contact] = evolution
            
            # Identify contacts with significant changes
            significant_changes = []
            for contact, evolution in contact_evolutions.items():
                # Check relationship score trend
                if "relationship_evolution" in evolution and "score_trend" in evolution["relationship_evolution"]:
                    score_trend = evolution["relationship_evolution"]["score_trend"]
                    if score_trend.get("is_significant", False):
                        significant_changes.append({
                            "contact": contact,
                            "change_type": "relationship_score",
                            "direction": score_trend["direction"],
                            "percentage_change": score_trend["percentage_change"],
                            "description": f"Relationship with {contact} has {score_trend['direction']} by {abs(score_trend['percentage_change']):.1f}%"
                        })
            
            results = {
                "contact_count": len(relevant_contacts),
                "analyzed_contacts": len(contact_evolutions),
                "significant_changes": significant_changes,
                "contact_evolutions": contact_evolutions
            }
            
            # Cache results
            cache_result(cache_key, results)
            
            return results
            
        except Exception as e:
            error = f"Error analyzing all contacts: {str(e)}"
            self.last_error = error
            logger.error(error, exc_info=True)
            return {"error": error}
