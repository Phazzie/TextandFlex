"""
Analysis Layer Package
------------------
This package contains components for analyzing phone records data.

Components:
- analysis_models: Data structures for analysis results
- basic_statistics: Core statistical functions for analyzing phone records
- contact_analysis: Analysis of contact relationships and patterns
- time_analysis: Analysis of time-based patterns
- pattern_detector: Detection of various communication patterns
- insight_generator: Generation of insights and summaries from analysis
- ml_models: Machine learning models for advanced analysis
- statistical_utils: Common statistical functions and utilities
- result_formatter: Output formatting for analysis results

Data Flow:
Repository → Contact Analysis → Pattern Detector → Insight Generator
Repository → Time Analysis → Pattern Detector → Insight Generator
                                    ↓
                                ML Models
                                    ↓
                                Basic Statistics → Statistical Utils → Analysis Models
                                    ↓
                                Result Formatter

Usage:
    from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
    from src.analysis_layer.contact_analysis import ContactAnalyzer
    from src.analysis_layer.time_analysis import TimeAnalyzer
    from src.analysis_layer.pattern_detector import PatternDetector
    from src.analysis_layer.insight_generator import InsightGenerator
    from src.analysis_layer.result_formatter import format_as_text

    # Initialize analyzers
    basic_analyzer = BasicStatisticsAnalyzer()
    contact_analyzer = ContactAnalyzer()
    time_analyzer = TimeAnalyzer()
    pattern_detector = PatternDetector()
    insight_generator = InsightGenerator()

    # Analyze data (example for basic stats)
    stats, error = basic_analyzer.analyze(dataframe, column_mapping)

    # Format results
    formatted_result = format_as_text(stats)
"""

from .analysis_models import AnalysisResult, StatisticalSummary
from .basic_statistics import BasicStatisticsAnalyzer
from .contact_analysis import ContactAnalyzer
from .time_analysis import TimeAnalyzer
from .pattern_detector import PatternDetector
from .insight_generator import InsightGenerator
from .ml_models import (
    MLModel, TimePatternModel, ContactPatternModel,
    AnomalyDetectionModel, extract_features, evaluate_model
)
from .statistical_utils import (
    calculate_time_distribution,
    calculate_message_frequency,
    calculate_response_times,
    calculate_conversation_gaps,
    calculate_contact_activity_periods,
    calculate_word_frequency,
    get_cached_result,
    cache_result
)
from .result_formatter import (
    format_as_text,
    format_as_json,
    format_as_csv,
    format_as_html,
    format_as_markdown
)

__all__ = [
    'AnalysisResult',
    'StatisticalSummary',
    'BasicStatisticsAnalyzer',
    'ContactAnalyzer',
    'TimeAnalyzer',
    'PatternDetector',
    'InsightGenerator',
    'MLModel',
    'TimePatternModel',
    'ContactPatternModel',
    'AnomalyDetectionModel',
    'extract_features',
    'evaluate_model',
    'calculate_time_distribution',
    'calculate_message_frequency',
    'calculate_response_times',
    'calculate_conversation_gaps',
    'calculate_contact_activity_periods',
    'calculate_word_frequency',
    'get_cached_result',
    'cache_result',
    'format_as_text',
    'format_as_json',
    'format_as_csv',
    'format_as_html',
    'format_as_markdown'
]
