"""
Longitudinal Analysis Package
------------------
This package contains components for analyzing phone records data over time.

Components:
- trend_analyzer: Analyze communication trends over extended periods
- contact_evolution: Track how relationships with contacts change over time
- seasonality_detector: Identify seasonal patterns in communication

Usage:
    from src.analysis_layer.longitudinal.trend_analyzer import TrendAnalyzer
    from src.analysis_layer.longitudinal.contact_evolution import ContactEvolutionTracker
    from src.analysis_layer.longitudinal.seasonality_detector import SeasonalityDetector

    # Initialize analyzers
    trend_analyzer = TrendAnalyzer()
    evolution_tracker = ContactEvolutionTracker()
    seasonality_detector = SeasonalityDetector()

    # Analyze trends over time
    trends = trend_analyzer.analyze_trends(dataframes, time_periods)

    # Track contact evolution
    evolution = evolution_tracker.track_evolution(dataframes, contact_id)

    # Detect seasonality
    seasonality = seasonality_detector.detect_seasonality(dataframes)
"""

from .trend_analyzer import TrendAnalyzer
from .contact_evolution import ContactEvolutionTracker
from .seasonality_detector import SeasonalityDetector

__all__ = [
    'TrendAnalyzer',
    'ContactEvolutionTracker',
    'SeasonalityDetector'
]
