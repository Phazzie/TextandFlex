"""
Gap Detector Module
------------------
Detect significant gaps in communication.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta
import logging

from ...logger import get_logger
from ..statistical_utils import get_cached_result, cache_result

logger = get_logger("gap_detector")

class GapDetector:
    """Detector for significant gaps in communication."""

    def __init__(self):
        """Initialize the gap detector."""
        self.last_error = None

    def detect_gaps(self, df: pd.DataFrame, 
                   min_gap_hours: float = 24.0,
                   contact_specific: bool = False) -> Dict[str, Any]:
        """Detect significant gaps in communication.

        Args:
            df: DataFrame containing phone records
            min_gap_hours: Minimum gap duration in hours to be considered significant
            contact_specific: Whether to detect gaps for each contact separately

        Returns:
            Dictionary of detected gaps
        """
        if df is None or df.empty:
            error = "Cannot detect gaps with empty data"
            self.last_error = error
            logger.error(error)
            return {"error": error}

        try:
            # Create a cache key based on the dataframe
            cache_key = f"gaps_{hash(str(df.shape))}_{min_gap_hours}_{contact_specific}"
            cached = get_cached_result(cache_key)
            if cached is not None:
                return cached

            # Ensure timestamp is datetime
            if 'timestamp' not in df.columns:
                error = "DataFrame missing timestamp column"
                self.last_error = error
                logger.error(error)
                return {"error": error}
                
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Detect overall gaps
            overall_gaps = self._detect_overall_gaps(df, min_gap_hours)
            
            # Detect contact-specific gaps if requested
            contact_gaps = {}
            if contact_specific and 'phone_number' in df.columns:
                for contact in df['phone_number'].unique():
                    contact_df = df[df['phone_number'] == contact]
                    if len(contact_df) >= 2:  # Need at least 2 messages to have a gap
                        contact_gaps[contact] = self._detect_overall_gaps(contact_df, min_gap_hours)
            
            # Combine results
            results = {
                "overall_gaps": overall_gaps,
                "contact_gaps": contact_gaps if contact_specific else {}
            }
            
            # Cache results
            cache_result(cache_key, results)
            
            return results
            
        except Exception as e:
            error = f"Error detecting gaps: {str(e)}"
            self.last_error = error
            logger.error(error, exc_info=True)
            return {"error": error}

    def _detect_overall_gaps(self, df: pd.DataFrame, min_gap_hours: float) -> List[Dict[str, Any]]:
        """Detect gaps in the overall communication timeline.

        Args:
            df: DataFrame containing phone records
            min_gap_hours: Minimum gap duration in hours to be considered significant

        Returns:
            List of detected gaps
        """
        # Sort by timestamp
        df_sorted = df.sort_values('timestamp')
        
        # Calculate time differences between consecutive messages
        df_sorted['next_timestamp'] = df_sorted['timestamp'].shift(-1)
        df_sorted['time_diff'] = (df_sorted['next_timestamp'] - df_sorted['timestamp']).dt.total_seconds() / 3600  # in hours
        
        # Filter for significant gaps
        gap_df = df_sorted[df_sorted['time_diff'] >= min_gap_hours].copy()
        
        # Skip if no gaps found
        if gap_df.empty:
            return []
        
        # Calculate typical time between messages (median)
        typical_gap = df_sorted['time_diff'].median()
        
        # Calculate gap significance (how many times larger than typical)
        gap_df['significance'] = gap_df['time_diff'] / typical_gap
        
        # Create gap records
        gaps = []
        for _, row in gap_df.iterrows():
            gap = {
                "start_time": row['timestamp'],
                "end_time": row['next_timestamp'],
                "duration_hours": row['time_diff'],
                "significance": row['significance'],
                "description": f"Gap of {row['time_diff']:.1f} hours from {row['timestamp']} to {row['next_timestamp']}"
            }
            
            # Add contact information if available
            if 'phone_number' in row:
                gap["last_contact"] = row['phone_number']
            
            # Add next contact information if available
            next_idx = df_sorted.index.get_loc(row.name) + 1
            if next_idx < len(df_sorted) and 'phone_number' in df_sorted.iloc[next_idx]:
                gap["next_contact"] = df_sorted.iloc[next_idx]['phone_number']
            
            gaps.append(gap)
        
        # Sort gaps by duration (descending)
        gaps.sort(key=lambda x: x["duration_hours"], reverse=True)
        
        return gaps

    def analyze_gap_patterns(self, df: pd.DataFrame, 
                           min_gap_hours: float = 24.0) -> Dict[str, Any]:
        """Analyze patterns in communication gaps.

        Args:
            df: DataFrame containing phone records
            min_gap_hours: Minimum gap duration in hours to be considered significant

        Returns:
            Dictionary of gap pattern analysis
        """
        if df is None or df.empty:
            error = "Cannot analyze gap patterns with empty data"
            self.last_error = error
            logger.error(error)
            return {"error": error}

        try:
            # Create a cache key based on the dataframe
            cache_key = f"gap_patterns_{hash(str(df.shape))}_{min_gap_hours}"
            cached = get_cached_result(cache_key)
            if cached is not None:
                return cached

            # Detect gaps
            gaps_result = self.detect_gaps(df, min_gap_hours, contact_specific=True)
            
            # Check for errors
            if "error" in gaps_result:
                return gaps_result
            
            # Analyze overall gap patterns
            overall_gaps = gaps_result["overall_gaps"]
            overall_patterns = self._analyze_gap_timing(df, overall_gaps)
            
            # Analyze contact-specific gap patterns
            contact_patterns = {}
            for contact, contact_gaps in gaps_result["contact_gaps"].items():
                if contact_gaps:
                    contact_df = df[df['phone_number'] == contact]
                    contact_patterns[contact] = self._analyze_gap_timing(contact_df, contact_gaps)
            
            # Identify contacts with unusual gap patterns
            unusual_contacts = []
            if contact_patterns:
                # Calculate average gap duration for each contact
                avg_gap_durations = {
                    contact: np.mean([gap["duration_hours"] for gap in gaps]) 
                    for contact, gaps in gaps_result["contact_gaps"].items() 
                    if gaps
                }
                
                # Calculate overall average gap duration
                overall_avg_duration = np.mean([gap["duration_hours"] for gap in overall_gaps]) if overall_gaps else 0
                
                # Find contacts with significantly different gap patterns
                for contact, avg_duration in avg_gap_durations.items():
                    if overall_avg_duration > 0:
                        difference = ((avg_duration - overall_avg_duration) / overall_avg_duration) * 100
                        
                        if abs(difference) >= 50:  # 50% difference threshold
                            pattern_type = "longer" if difference > 0 else "shorter"
                            unusual_contacts.append({
                                "contact": contact,
                                "pattern_type": pattern_type,
                                "avg_gap_duration": avg_duration,
                                "difference_percentage": difference,
                                "description": f"Contact {contact} has {pattern_type} gaps than average (diff: {abs(difference):.1f}%)"
                            })
            
            # Combine results
            results = {
                "overall_patterns": overall_patterns,
                "contact_patterns": contact_patterns,
                "unusual_contacts": unusual_contacts
            }
            
            # Cache results
            cache_result(cache_key, results)
            
            return results
            
        except Exception as e:
            error = f"Error analyzing gap patterns: {str(e)}"
            self.last_error = error
            logger.error(error, exc_info=True)
            return {"error": error}

    def _analyze_gap_timing(self, df: pd.DataFrame, gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the timing of communication gaps.

        Args:
            df: DataFrame containing phone records
            gaps: List of detected gaps

        Returns:
            Dictionary of gap timing analysis
        """
        if not gaps:
            return {
                "gap_count": 0,
                "avg_gap_duration": 0,
                "max_gap_duration": 0,
                "day_of_week_distribution": {},
                "hour_of_day_distribution": {},
                "recurring_patterns": []
            }
        
        # Calculate basic statistics
        gap_durations = [gap["duration_hours"] for gap in gaps]
        avg_gap_duration = np.mean(gap_durations)
        max_gap_duration = np.max(gap_durations)
        
        # Analyze day of week distribution
        start_days = [gap["start_time"].day_name() for gap in gaps]
        day_counts = pd.Series(start_days).value_counts().to_dict()
        
        # Analyze hour of day distribution
        start_hours = [gap["start_time"].hour for gap in gaps]
        hour_counts = pd.Series(start_hours).value_counts().to_dict()
        
        # Detect recurring patterns
        recurring_patterns = self._detect_recurring_gap_patterns(gaps)
        
        return {
            "gap_count": len(gaps),
            "avg_gap_duration": avg_gap_duration,
            "max_gap_duration": max_gap_duration,
            "day_of_week_distribution": day_counts,
            "hour_of_day_distribution": hour_counts,
            "recurring_patterns": recurring_patterns
        }

    def _detect_recurring_gap_patterns(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect recurring patterns in communication gaps.

        Args:
            gaps: List of detected gaps

        Returns:
            List of recurring gap patterns
        """
        if len(gaps) < 3:  # Need at least 3 gaps to detect patterns
            return []
        
        # Sort gaps by start time
        sorted_gaps = sorted(gaps, key=lambda x: x["start_time"])
        
        # Calculate time between gap starts
        gap_intervals = []
        for i in range(1, len(sorted_gaps)):
            prev_gap = sorted_gaps[i-1]
            curr_gap = sorted_gaps[i]
            
            interval_hours = (curr_gap["start_time"] - prev_gap["start_time"]).total_seconds() / 3600
            gap_intervals.append(interval_hours)
        
        # Check for weekly patterns (168 ± 24 hours)
        weekly_pattern = self._check_interval_pattern(gap_intervals, 168, 24)
        
        # Check for monthly patterns (720 ± 72 hours, ~30 days)
        monthly_pattern = self._check_interval_pattern(gap_intervals, 720, 72)
        
        # Combine patterns
        patterns = []
        if weekly_pattern:
            patterns.append({
                "type": "weekly",
                "description": "Gaps tend to occur weekly",
                "confidence": weekly_pattern["confidence"],
                "matching_intervals": weekly_pattern["matching_intervals"]
            })
        
        if monthly_pattern:
            patterns.append({
                "type": "monthly",
                "description": "Gaps tend to occur monthly",
                "confidence": monthly_pattern["confidence"],
                "matching_intervals": monthly_pattern["matching_intervals"]
            })
        
        return patterns

    def _check_interval_pattern(self, intervals: List[float], 
                              target_hours: float, 
                              tolerance: float) -> Optional[Dict[str, Any]]:
        """Check if intervals match a specific pattern.

        Args:
            intervals: List of time intervals in hours
            target_hours: Target interval duration in hours
            tolerance: Acceptable deviation from target in hours

        Returns:
            Dictionary with pattern details or None if no pattern detected
        """
        if not intervals:
            return None
        
        # Count intervals that match the pattern
        matching_intervals = []
        for interval in intervals:
            if abs(interval - target_hours) <= tolerance:
                matching_intervals.append(interval)
        
        # Calculate confidence based on percentage of matching intervals
        match_percentage = (len(matching_intervals) / len(intervals)) * 100
        
        # Only return pattern if at least 30% of intervals match
        if match_percentage >= 30:
            return {
                "matching_intervals": len(matching_intervals),
                "total_intervals": len(intervals),
                "match_percentage": match_percentage,
                "confidence": min(100, match_percentage)
            }
        
        return None
