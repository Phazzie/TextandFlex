"""
Trend Analyzer Module
------------------
Analyze communication trends over extended periods.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from ...logger import get_logger
from ..statistical_utils import get_cached_result, cache_result

logger = get_logger("trend_analyzer")

class TrendAnalyzer:
    """Analyzer for communication trends over time."""

    def __init__(self):
        """Initialize the trend analyzer."""
        self.last_error = None

    def analyze_trends(self, dataframes: Dict[str, pd.DataFrame], 
                      time_unit: str = 'month') -> Dict[str, Any]:
        """Analyze trends across multiple time periods.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames
            time_unit: Time unit for aggregation ('day', 'week', 'month')

        Returns:
            Dictionary of trend analysis results
        """
        if not dataframes:
            error = "Cannot analyze trends with empty data"
            self.last_error = error
            logger.error(error)
            return {"error": error}

        try:
            # Create a cache key based on the dataframes
            cache_key = f"trend_analysis_{hash(str(list(dataframes.keys())))}"
            cached = get_cached_result(cache_key)
            if cached is not None:
                return cached

            # Validate all dataframes have timestamp column
            for period, df in dataframes.items():
                if 'timestamp' not in df.columns:
                    error = f"DataFrame for period {period} missing timestamp column"
                    self.last_error = error
                    logger.error(error)
                    return {"error": error}

            # Analyze volume trends
            volume_trends = self._analyze_volume_trends(dataframes, time_unit)
            
            # Analyze contact trends
            contact_trends = self._analyze_contact_trends(dataframes)
            
            # Analyze time of day trends
            time_trends = self._analyze_time_trends(dataframes)
            
            # Combine results
            results = {
                "volume_trends": volume_trends,
                "contact_trends": contact_trends,
                "time_trends": time_trends
            }
            
            # Cache results
            cache_result(cache_key, results)
            
            return results
            
        except Exception as e:
            error = f"Error analyzing trends: {str(e)}"
            self.last_error = error
            logger.error(error, exc_info=True)
            return {"error": error}

    def _analyze_volume_trends(self, dataframes: Dict[str, pd.DataFrame], 
                              time_unit: str) -> Dict[str, Any]:
        """Analyze message volume trends over time.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames
            time_unit: Time unit for aggregation ('day', 'week', 'month')

        Returns:
            Dictionary of volume trend analysis
        """
        # Initialize results
        volume_data = {}
        total_counts = {}
        daily_averages = {}
        growth_rates = {}
        
        # Sort periods chronologically if they are date strings
        try:
            sorted_periods = sorted(dataframes.keys(), 
                                   key=lambda x: pd.to_datetime(x))
        except:
            # If periods can't be parsed as dates, use original order
            sorted_periods = list(dataframes.keys())
        
        # Calculate volume metrics for each period
        for period in sorted_periods:
            df = dataframes[period]
            
            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Calculate total message count
            total_count = len(df)
            total_counts[period] = total_count
            
            # Calculate daily average
            min_date = df['timestamp'].min().date()
            max_date = df['timestamp'].max().date()
            days = (max_date - min_date).days + 1  # Add 1 to include both start and end days
            daily_avg = total_count / max(1, days)  # Avoid division by zero
            daily_averages[period] = daily_avg
            
            # Calculate volume by time unit
            if time_unit == 'day':
                df['time_unit'] = df['timestamp'].dt.date
            elif time_unit == 'week':
                df['time_unit'] = df['timestamp'].dt.isocalendar().week
            else:  # Default to month
                df['time_unit'] = df['timestamp'].dt.to_period('M')
                
            volume_by_unit = df.groupby('time_unit').size().to_dict()
            volume_data[period] = volume_by_unit
        
        # Calculate growth rates between consecutive periods
        for i in range(1, len(sorted_periods)):
            prev_period = sorted_periods[i-1]
            curr_period = sorted_periods[i]
            
            prev_count = total_counts[prev_period]
            curr_count = total_counts[curr_period]
            
            if prev_count > 0:
                growth_rate = ((curr_count - prev_count) / prev_count) * 100
            else:
                growth_rate = float('inf')  # Infinite growth from zero
                
            growth_rates[f"{prev_period}_to_{curr_period}"] = growth_rate
        
        return {
            "total_counts": total_counts,
            "daily_averages": daily_averages,
            "growth_rates": growth_rates,
            "volume_by_time_unit": volume_data
        }

    def _analyze_contact_trends(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze contact-related trends over time.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames

        Returns:
            Dictionary of contact trend analysis
        """
        # Initialize results
        unique_contacts = {}
        contact_frequencies = {}
        new_contacts = {}
        discontinued_contacts = {}
        consistent_contacts = set()
        
        # Sort periods chronologically if they are date strings
        try:
            sorted_periods = sorted(dataframes.keys(), 
                                   key=lambda x: pd.to_datetime(x))
        except:
            # If periods can't be parsed as dates, use original order
            sorted_periods = list(dataframes.keys())
        
        # Track all contacts seen across all periods
        all_contacts = set()
        period_contacts = {}
        
        # Analyze contacts for each period
        for period in sorted_periods:
            df = dataframes[period]
            
            # Get unique contacts for this period
            if 'phone_number' in df.columns:
                contacts = set(df['phone_number'].unique())
            else:
                contacts = set()
                
            period_contacts[period] = contacts
            all_contacts.update(contacts)
            
            # Count unique contacts
            unique_contacts[period] = len(contacts)
            
            # Calculate contact frequencies
            if 'phone_number' in df.columns:
                freq = df['phone_number'].value_counts().to_dict()
                contact_frequencies[period] = freq
            else:
                contact_frequencies[period] = {}
        
        # Find new and discontinued contacts between consecutive periods
        for i in range(1, len(sorted_periods)):
            prev_period = sorted_periods[i-1]
            curr_period = sorted_periods[i]
            
            prev_contacts = period_contacts[prev_period]
            curr_contacts = period_contacts[curr_period]
            
            # New contacts are in current but not in previous
            new = curr_contacts - prev_contacts
            new_contacts[curr_period] = list(new)
            
            # Discontinued contacts are in previous but not in current
            discontinued = prev_contacts - curr_contacts
            discontinued_contacts[curr_period] = list(discontinued)
        
        # Find contacts that appear in all periods
        if sorted_periods:
            consistent_contacts = set.intersection(*[period_contacts[p] for p in sorted_periods])
        
        return {
            "unique_contacts": unique_contacts,
            "contact_frequencies": contact_frequencies,
            "new_contacts": new_contacts,
            "discontinued_contacts": discontinued_contacts,
            "consistent_contacts": list(consistent_contacts),
            "total_unique_contacts": len(all_contacts)
        }

    def _analyze_time_trends(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze time-of-day trends over time.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames

        Returns:
            Dictionary of time trend analysis
        """
        # Initialize results
        hourly_distributions = {}
        daily_distributions = {}
        peak_hours = {}
        peak_days = {}
        
        # Sort periods chronologically if they are date strings
        try:
            sorted_periods = sorted(dataframes.keys(), 
                                   key=lambda x: pd.to_datetime(x))
        except:
            # If periods can't be parsed as dates, use original order
            sorted_periods = list(dataframes.keys())
        
        # Analyze time patterns for each period
        for period in sorted_periods:
            df = dataframes[period]
            
            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Calculate hourly distribution
            hourly_dist = df['timestamp'].dt.hour.value_counts().sort_index().to_dict()
            hourly_distributions[period] = hourly_dist
            
            # Find peak hour
            if hourly_dist:
                peak_hour = max(hourly_dist.items(), key=lambda x: x[1])[0]
                peak_hours[period] = peak_hour
            
            # Calculate daily distribution
            daily_dist = df['timestamp'].dt.day_name().value_counts().to_dict()
            daily_distributions[period] = daily_dist
            
            # Find peak day
            if daily_dist:
                peak_day = max(daily_dist.items(), key=lambda x: x[1])[0]
                peak_days[period] = peak_day
        
        # Analyze shifts in peak hours and days
        hour_shifts = {}
        day_shifts = {}
        
        for i in range(1, len(sorted_periods)):
            prev_period = sorted_periods[i-1]
            curr_period = sorted_periods[i]
            
            # Check if peak hour changed
            if prev_period in peak_hours and curr_period in peak_hours:
                prev_peak = peak_hours[prev_period]
                curr_peak = peak_hours[curr_period]
                
                if prev_peak != curr_peak:
                    hour_shifts[f"{prev_period}_to_{curr_period}"] = {
                        "from": prev_peak,
                        "to": curr_peak
                    }
            
            # Check if peak day changed
            if prev_period in peak_days and curr_period in peak_days:
                prev_peak = peak_days[prev_period]
                curr_peak = peak_days[curr_period]
                
                if prev_peak != curr_peak:
                    day_shifts[f"{prev_period}_to_{curr_period}"] = {
                        "from": prev_peak,
                        "to": curr_peak
                    }
        
        return {
            "hourly_distributions": hourly_distributions,
            "daily_distributions": daily_distributions,
            "peak_hours": peak_hours,
            "peak_days": peak_days,
            "hour_shifts": hour_shifts,
            "day_shifts": day_shifts
        }

    def detect_significant_changes(self, dataframes: Dict[str, pd.DataFrame], 
                                 threshold: float = 20.0) -> List[Dict[str, Any]]:
        """Detect significant changes in communication patterns over time.

        Args:
            dataframes: Dictionary mapping time period labels to DataFrames
            threshold: Percentage threshold for significant change (default: 20%)

        Returns:
            List of significant changes detected
        """
        try:
            # Analyze trends
            trends = self.analyze_trends(dataframes)
            
            # Check for errors
            if "error" in trends:
                return [{"error": trends["error"]}]
            
            # Initialize list of significant changes
            significant_changes = []
            
            # Check volume changes
            if "volume_trends" in trends and "growth_rates" in trends["volume_trends"]:
                for period_pair, growth_rate in trends["volume_trends"]["growth_rates"].items():
                    if abs(growth_rate) >= threshold:
                        change_type = "increase" if growth_rate > 0 else "decrease"
                        significant_changes.append({
                            "type": "volume_change",
                            "period": period_pair,
                            "change_type": change_type,
                            "percentage": growth_rate,
                            "description": f"Message volume {change_type}d by {abs(growth_rate):.1f}% from {period_pair.split('_to_')[0]} to {period_pair.split('_to_')[1]}"
                        })
            
            # Check contact changes
            if "contact_trends" in trends and "new_contacts" in trends["contact_trends"]:
                for period, new_contacts in trends["contact_trends"]["new_contacts"].items():
                    if len(new_contacts) > 0:
                        significant_changes.append({
                            "type": "new_contacts",
                            "period": period,
                            "count": len(new_contacts),
                            "contacts": new_contacts[:5],  # Limit to first 5 for brevity
                            "description": f"{len(new_contacts)} new contacts in {period}"
                        })
            
            # Check time pattern changes
            if "time_trends" in trends and "hour_shifts" in trends["time_trends"]:
                for period_pair, shift in trends["time_trends"]["hour_shifts"].items():
                    significant_changes.append({
                        "type": "peak_hour_shift",
                        "period": period_pair,
                        "from_hour": shift["from"],
                        "to_hour": shift["to"],
                        "description": f"Peak communication hour shifted from {shift['from']}:00 to {shift['to']}:00 from {period_pair.split('_to_')[0]} to {period_pair.split('_to_')[1]}"
                    })
            
            return significant_changes
            
        except Exception as e:
            error = f"Error detecting significant changes: {str(e)}"
            self.last_error = error
            logger.error(error, exc_info=True)
            return [{"error": error}]
