"""
Advanced Pattern Detection Package
------------------
This package contains components for advanced pattern detection in phone records data.

Components:
- gap_detector: Detect significant gaps in communication
- overlap_analyzer: Analyze overlapping communication patterns
- response_analyzer: Advanced analysis of response patterns

Usage:
    from src.analysis_layer.advanced_patterns.gap_detector import GapDetector
    from src.analysis_layer.advanced_patterns.overlap_analyzer import OverlapAnalyzer
    from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer

    # Initialize detectors
    gap_detector = GapDetector()
    overlap_analyzer = OverlapAnalyzer()
    response_analyzer = ResponseAnalyzer()

    # Detect gaps in communication
    gaps = gap_detector.detect_gaps(dataframe)

    # Analyze overlapping patterns
    overlaps = overlap_analyzer.analyze_overlaps(dataframe)

    # Analyze response patterns
    responses = response_analyzer.analyze_responses(dataframe)
"""

from .gap_detector import GapDetector
from .overlap_analyzer import OverlapAnalyzer
from .response_analyzer import ResponseAnalyzer

__all__ = [
    'GapDetector',
    'OverlapAnalyzer',
    'ResponseAnalyzer'
]
