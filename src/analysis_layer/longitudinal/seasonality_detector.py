"""
Seasonality Detector Module
------------------
Identify seasonal patterns in communication data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from ...logger import get_logger
from ..statistical_utils import get_cached_result, cache_result

logger = get_logger("seasonality_detector")

class SeasonalityDetector:
    """Detector for seasonal patterns in communication data."""

    def __init__(self):
        """Initialize the seasonality detector."""
        self.last_error = None

    def detect_seasonality(self, df: pd.DataFrame, min_cycles: int = 2) -> Dict[str, Any]:
        """Detect seasonal patterns in communication data.

        Args:
            df: DataFrame containing phone records
            min_cycles: Minimum number of cycles required to confirm seasonality

        Returns:
            Dictionary of detected seasonal patterns
        """
        if df is None or df.empty:
            error = "Cannot detect seasonality with empty data"
            self.last_error = error
            logger.error(error)
            return {"error": error}

        try:
            # Create a cache key based on the dataframe
            cache_key = f"seasonality_{hash(str(df.shape))}"
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
            
            # Detect daily patterns
            daily_patterns = self._detect_daily_patterns(df, min_cycles)
            
            # Detect weekly patterns
            weekly_patterns = self._detect_weekly_patterns(df, min_cycles)
            
            # Detect monthly patterns
            monthly_patterns = self._detect_monthly_patterns(df, min_cycles)
            
            # Detect yearly patterns
            yearly_patterns = self._detect_yearly_patterns(df, min_cycles)
            
            # Combine results
            results = {
                "daily_patterns": daily_patterns,
                "weekly_patterns": weekly_patterns,
                "monthly_patterns": monthly_patterns,
                "yearly_patterns": yearly_patterns
            }
            
            # Cache results
            cache_result(cache_key, results)
            
            return results
            
        except Exception as e:
            error = f"Error detecting seasonality: {str(e)}"
            self.last_error = error
            logger.error(error, exc_info=True)
            return {"error": error}

    def _detect_daily_patterns(self, df: pd.DataFrame, min_cycles: int) -> List[Dict[str, Any]]:
        """Detect daily patterns in communication data.

        Args:
            df: DataFrame containing phone records
            min_cycles: Minimum number of cycles required to confirm seasonality

        Returns:
            List of detected daily patterns
        """
        # Group by hour of day
        hourly_counts = df['timestamp'].dt.hour.value_counts().sort_index()
        
        # Need at least 24 hours of data
        if len(df['timestamp'].dt.date.unique()) < 1:
            return []
        
        # Find peak hours (local maxima)
        peak_hours = []
        for hour in range(24):
            # Get counts for this hour and adjacent hours
            prev_hour = (hour - 1) % 24
            next_hour = (hour + 1) % 24
            
            current_count = hourly_counts.get(hour, 0)
            prev_count = hourly_counts.get(prev_hour, 0)
            next_count = hourly_counts.get(next_hour, 0)
            
            # Check if this is a local maximum
            if current_count > prev_count and current_count > next_count and current_count > 0:
                peak_hours.append({
                    "hour": hour,
                    "count": current_count,
                    "percentage": (current_count / hourly_counts.sum()) * 100 if hourly_counts.sum() > 0 else 0
                })
        
        # Sort peak hours by count (descending)
        peak_hours.sort(key=lambda x: x["count"], reverse=True)
        
        # Check if peak hours repeat across multiple days
        patterns = []
        for peak in peak_hours:
            hour = peak["hour"]
            
            # Count occurrences by date
            dates_with_peak = set()
            for date in df['timestamp'].dt.date.unique():
                date_df = df[df['timestamp'].dt.date == date]
                hour_counts = date_df['timestamp'].dt.hour.value_counts()
                
                if hour in hour_counts and hour_counts[hour] > 0:
                    dates_with_peak.add(date)
            
            # Calculate consistency
            total_dates = len(df['timestamp'].dt.date.unique())
            consistency = (len(dates_with_peak) / total_dates) * 100 if total_dates > 0 else 0
            
            # Only include if pattern appears in multiple days
            if len(dates_with_peak) >= min_cycles and consistency >= 30:
                patterns.append({
                    "type": "daily",
                    "hour": hour,
                    "description": f"Communication peak at {hour}:00",
                    "occurrences": len(dates_with_peak),
                    "consistency": consistency,
                    "confidence": min(100, consistency)
                })
        
        return patterns

    def _detect_weekly_patterns(self, df: pd.DataFrame, min_cycles: int) -> List[Dict[str, Any]]:
        """Detect weekly patterns in communication data.

        Args:
            df: DataFrame containing phone records
            min_cycles: Minimum number of cycles required to confirm seasonality

        Returns:
            List of detected weekly patterns
        """
        # Need at least 2 weeks of data
        min_date = df['timestamp'].min().date()
        max_date = df['timestamp'].max().date()
        date_range = (max_date - min_date).days
        
        if date_range < 14:  # Need at least 2 weeks
            return []
        
        # Group by day of week
        day_counts = df['timestamp'].dt.dayofweek.value_counts().sort_index()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Find peak days (local maxima)
        peak_days = []
        for day in range(7):
            # Get counts for this day and adjacent days
            prev_day = (day - 1) % 7
            next_day = (day + 1) % 7
            
            current_count = day_counts.get(day, 0)
            prev_count = day_counts.get(prev_day, 0)
            next_count = day_counts.get(next_day, 0)
            
            # Check if this is a local maximum
            if current_count > prev_count and current_count > next_count and current_count > 0:
                peak_days.append({
                    "day": day,
                    "day_name": day_names[day],
                    "count": current_count,
                    "percentage": (current_count / day_counts.sum()) * 100 if day_counts.sum() > 0 else 0
                })
        
        # Sort peak days by count (descending)
        peak_days.sort(key=lambda x: x["count"], reverse=True)
        
        # Check if peak days repeat across multiple weeks
        patterns = []
        for peak in peak_days:
            day = peak["day"]
            day_name = peak["day_name"]
            
            # Group by week and count occurrences
            df['week'] = df['timestamp'].dt.isocalendar().week
            weeks_with_peak = set()
            
            for week in df['week'].unique():
                week_df = df[df['week'] == week]
                day_counts = week_df['timestamp'].dt.dayofweek.value_counts()
                
                if day in day_counts and day_counts[day] > 0:
                    weeks_with_peak.add(week)
            
            # Calculate consistency
            total_weeks = len(df['week'].unique())
            consistency = (len(weeks_with_peak) / total_weeks) * 100 if total_weeks > 0 else 0
            
            # Only include if pattern appears in multiple weeks
            if len(weeks_with_peak) >= min_cycles and consistency >= 30:
                patterns.append({
                    "type": "weekly",
                    "day": day,
                    "day_name": day_name,
                    "description": f"Communication peak on {day_name}s",
                    "occurrences": len(weeks_with_peak),
                    "consistency": consistency,
                    "confidence": min(100, consistency)
                })
        
        return patterns

    def _detect_monthly_patterns(self, df: pd.DataFrame, min_cycles: int) -> List[Dict[str, Any]]:
        """Detect monthly patterns in communication data.

        Args:
            df: DataFrame containing phone records
            min_cycles: Minimum number of cycles required to confirm seasonality

        Returns:
            List of detected monthly patterns
        """
        # Need at least 2 months of data
        min_date = df['timestamp'].min().date()
        max_date = df['timestamp'].max().date()
        
        min_month = min_date.month + min_date.year * 12
        max_month = max_date.month + max_date.year * 12
        month_range = max_month - min_month
        
        if month_range < 2:  # Need at least 2 months
            return []
        
        # Group by day of month
        day_of_month_counts = df['timestamp'].dt.day.value_counts().sort_index()
        
        # Find peak days (local maxima)
        peak_days = []
        for day in range(1, 29):  # Use 1-28 to avoid month length issues
            # Get counts for this day and adjacent days
            prev_day = day - 1 if day > 1 else None
            next_day = day + 1 if day < 28 else None
            
            current_count = day_of_month_counts.get(day, 0)
            prev_count = day_of_month_counts.get(prev_day, 0) if prev_day else 0
            next_count = day_of_month_counts.get(next_day, 0) if next_day else 0
            
            # Check if this is a local maximum
            if current_count > prev_count and current_count > next_count and current_count > 0:
                peak_days.append({
                    "day": day,
                    "count": current_count,
                    "percentage": (current_count / day_of_month_counts.sum()) * 100 if day_of_month_counts.sum() > 0 else 0
                })
        
        # Sort peak days by count (descending)
        peak_days.sort(key=lambda x: x["count"], reverse=True)
        
        # Check if peak days repeat across multiple months
        patterns = []
        for peak in peak_days:
            day = peak["day"]
            
            # Group by month and count occurrences
            df['month'] = df['timestamp'].dt.month + df['timestamp'].dt.year * 12
            months_with_peak = set()
            
            for month in df['month'].unique():
                month_df = df[df['month'] == month]
                day_counts = month_df['timestamp'].dt.day.value_counts()
                
                if day in day_counts and day_counts[day] > 0:
                    months_with_peak.add(month)
            
            # Calculate consistency
            total_months = len(df['month'].unique())
            consistency = (len(months_with_peak) / total_months) * 100 if total_months > 0 else 0
            
            # Only include if pattern appears in multiple months
            if len(months_with_peak) >= min_cycles and consistency >= 30:
                patterns.append({
                    "type": "monthly",
                    "day": day,
                    "description": f"Communication peak on day {day} of each month",
                    "occurrences": len(months_with_peak),
                    "consistency": consistency,
                    "confidence": min(100, consistency)
                })
        
        return patterns

    def _detect_yearly_patterns(self, df: pd.DataFrame, min_cycles: int) -> List[Dict[str, Any]]:
        """Detect yearly patterns in communication data.

        Args:
            df: DataFrame containing phone records
            min_cycles: Minimum number of cycles required to confirm seasonality

        Returns:
            List of detected yearly patterns
        """
        # Need at least 2 years of data
        min_date = df['timestamp'].min().date()
        max_date = df['timestamp'].max().date()
        
        min_year = min_date.year
        max_year = max_date.year
        year_range = max_year - min_year
        
        if year_range < 2:  # Need at least 2 years
            return []
        
        # Group by month of year
        month_counts = df['timestamp'].dt.month.value_counts().sort_index()
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        # Find peak months (local maxima)
        peak_months = []
        for month in range(1, 13):
            # Get counts for this month and adjacent months
            prev_month = month - 1 if month > 1 else 12
            next_month = month + 1 if month < 12 else 1
            
            current_count = month_counts.get(month, 0)
            prev_count = month_counts.get(prev_month, 0)
            next_count = month_counts.get(next_month, 0)
            
            # Check if this is a local maximum
            if current_count > prev_count and current_count > next_count and current_count > 0:
                peak_months.append({
                    "month": month,
                    "month_name": month_names[month-1],
                    "count": current_count,
                    "percentage": (current_count / month_counts.sum()) * 100 if month_counts.sum() > 0 else 0
                })
        
        # Sort peak months by count (descending)
        peak_months.sort(key=lambda x: x["count"], reverse=True)
        
        # Check if peak months repeat across multiple years
        patterns = []
        for peak in peak_months:
            month = peak["month"]
            month_name = peak["month_name"]
            
            # Group by year and count occurrences
            years_with_peak = set()
            
            for year in df['timestamp'].dt.year.unique():
                year_df = df[df['timestamp'].dt.year == year]
                month_counts = year_df['timestamp'].dt.month.value_counts()
                
                if month in month_counts and month_counts[month] > 0:
                    years_with_peak.add(year)
            
            # Calculate consistency
            total_years = len(df['timestamp'].dt.year.unique())
            consistency = (len(years_with_peak) / total_years) * 100 if total_years > 0 else 0
            
            # Only include if pattern appears in multiple years
            if len(years_with_peak) >= min_cycles and consistency >= 50:
                patterns.append({
                    "type": "yearly",
                    "month": month,
                    "month_name": month_name,
                    "description": f"Communication peak in {month_name}",
                    "occurrences": len(years_with_peak),
                    "consistency": consistency,
                    "confidence": min(100, consistency)
                })
        
        return patterns

    def detect_holiday_patterns(self, df: pd.DataFrame, 
                              holidays: Dict[str, List[datetime]] = None) -> List[Dict[str, Any]]:
        """Detect patterns related to holidays.

        Args:
            df: DataFrame containing phone records
            holidays: Dictionary mapping holiday names to lists of dates

        Returns:
            List of detected holiday patterns
        """
        if df is None or df.empty:
            error = "Cannot detect holiday patterns with empty data"
            self.last_error = error
            logger.error(error)
            return []

        try:
            # Create a cache key based on the dataframe
            cache_key = f"holiday_patterns_{hash(str(df.shape))}"
            cached = get_cached_result(cache_key)
            if cached is not None:
                return cached

            # Ensure timestamp is datetime
            if 'timestamp' not in df.columns:
                error = "DataFrame missing timestamp column"
                self.last_error = error
                logger.error(error)
                return []
                
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df = df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Use default holidays if none provided
            if holidays is None:
                holidays = self._get_default_holidays(df['timestamp'].min().year, 
                                                    df['timestamp'].max().year)
            
            # Detect patterns for each holiday
            patterns = []
            for holiday_name, dates in holidays.items():
                holiday_pattern = self._detect_holiday_pattern(df, holiday_name, dates)
                if holiday_pattern:
                    patterns.append(holiday_pattern)
            
            # Cache results
            cache_result(cache_key, patterns)
            
            return patterns
            
        except Exception as e:
            error = f"Error detecting holiday patterns: {str(e)}"
            self.last_error = error
            logger.error(error, exc_info=True)
            return []

    def _detect_holiday_pattern(self, df: pd.DataFrame, 
                              holiday_name: str, 
                              dates: List[datetime]) -> Optional[Dict[str, Any]]:
        """Detect pattern for a specific holiday.

        Args:
            df: DataFrame containing phone records
            holiday_name: Name of the holiday
            dates: List of dates for the holiday

        Returns:
            Dictionary of holiday pattern or None if no pattern detected
        """
        # Convert dates to date objects if they're datetime
        dates = [d.date() if hasattr(d, 'date') else d for d in dates]
        
        # Count messages on holiday dates and adjacent days
        holiday_counts = []
        before_counts = []
        after_counts = []
        
        for date in dates:
            # Get messages on the holiday
            holiday_df = df[df['timestamp'].dt.date == date]
            holiday_count = len(holiday_df)
            holiday_counts.append(holiday_count)
            
            # Get messages on the day before
            before_date = date - timedelta(days=1)
            before_df = df[df['timestamp'].dt.date == before_date]
            before_count = len(before_df)
            before_counts.append(before_count)
            
            # Get messages on the day after
            after_date = date + timedelta(days=1)
            after_df = df[df['timestamp'].dt.date == after_date]
            after_count = len(after_df)
            after_counts.append(after_count)
        
        # Calculate averages
        avg_holiday = np.mean(holiday_counts) if holiday_counts else 0
        avg_before = np.mean(before_counts) if before_counts else 0
        avg_after = np.mean(after_counts) if after_counts else 0
        
        # Calculate average messages per day for comparison
        total_days = len(df['timestamp'].dt.date.unique())
        avg_daily = len(df) / total_days if total_days > 0 else 0
        
        # Calculate percentage differences
        holiday_diff = ((avg_holiday - avg_daily) / avg_daily) * 100 if avg_daily > 0 else 0
        before_diff = ((avg_before - avg_daily) / avg_daily) * 100 if avg_daily > 0 else 0
        after_diff = ((avg_after - avg_daily) / avg_daily) * 100 if avg_daily > 0 else 0
        
        # Determine if there's a significant pattern
        significant_threshold = 30  # 30% difference
        
        if abs(holiday_diff) >= significant_threshold:
            pattern_type = "increase" if holiday_diff > 0 else "decrease"
            confidence = min(100, abs(holiday_diff))
            
            return {
                "type": "holiday",
                "holiday": holiday_name,
                "pattern": f"{pattern_type} on {holiday_name}",
                "description": f"Communication {pattern_type}s by {abs(holiday_diff):.1f}% on {holiday_name}",
                "percentage_change": holiday_diff,
                "confidence": confidence,
                "dates": [str(d) for d in dates]
            }
        
        # Check for patterns before or after the holiday
        elif abs(before_diff) >= significant_threshold:
            pattern_type = "increase" if before_diff > 0 else "decrease"
            confidence = min(100, abs(before_diff))
            
            return {
                "type": "holiday_adjacent",
                "holiday": holiday_name,
                "pattern": f"{pattern_type} before {holiday_name}",
                "description": f"Communication {pattern_type}s by {abs(before_diff):.1f}% the day before {holiday_name}",
                "percentage_change": before_diff,
                "confidence": confidence,
                "dates": [str(d) for d in dates]
            }
        
        elif abs(after_diff) >= significant_threshold:
            pattern_type = "increase" if after_diff > 0 else "decrease"
            confidence = min(100, abs(after_diff))
            
            return {
                "type": "holiday_adjacent",
                "holiday": holiday_name,
                "pattern": f"{pattern_type} after {holiday_name}",
                "description": f"Communication {pattern_type}s by {abs(after_diff):.1f}% the day after {holiday_name}",
                "percentage_change": after_diff,
                "confidence": confidence,
                "dates": [str(d) for d in dates]
            }
        
        return None

    def _get_default_holidays(self, start_year: int, end_year: int) -> Dict[str, List[datetime]]:
        """Get default holidays for the given year range.

        Args:
            start_year: Start year
            end_year: End year

        Returns:
            Dictionary mapping holiday names to lists of dates
        """
        holidays = defaultdict(list)
        
        for year in range(start_year, end_year + 1):
            # New Year's Day
            holidays["New Year's Day"].append(datetime(year, 1, 1).date())
            
            # Valentine's Day
            holidays["Valentine's Day"].append(datetime(year, 2, 14).date())
            
            # Independence Day (US)
            holidays["Independence Day"].append(datetime(year, 7, 4).date())
            
            # Halloween
            holidays["Halloween"].append(datetime(year, 10, 31).date())
            
            # Christmas
            holidays["Christmas"].append(datetime(year, 12, 25).date())
            
            # New Year's Eve
            holidays["New Year's Eve"].append(datetime(year, 12, 31).date())
        
        return holidays
