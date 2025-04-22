"""
Analysis Service Module
----------------------
Service for abstracting analysis operations for GUI controllers.
"""
from typing import Dict, List, Optional, Any, Union
import pandas as pd

from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
from src.analysis_layer.contact_analysis import ContactAnalyzer
from src.analysis_layer.time_analysis import TimeAnalyzer
from src.analysis_layer.pattern_detector import PatternDetector
from src.presentation_layer.gui.models.analysis_model import (
    AnalysisResult, AnalysisType, BasicAnalysisData,
    ContactAnalysisData, TimeAnalysisData, PatternAnalysisData
)


class AnalysisService:
    """
    Service for abstracting analysis operations.
    
    This class provides a simplified interface for GUI controllers to interact
    with the analysis components, handling exceptions and data transformations.
    """
    
    def __init__(self, 
                basic_analyzer: Optional[BasicStatisticsAnalyzer] = None,
                contact_analyzer: Optional[ContactAnalyzer] = None,
                time_analyzer: Optional[TimeAnalyzer] = None,
                pattern_detector: Optional[PatternDetector] = None):
        """
        Initialize the analysis service.
        
        Args:
            basic_analyzer: Optional basic statistics analyzer (for testing)
            contact_analyzer: Optional contact analyzer (for testing)
            time_analyzer: Optional time analyzer (for testing)
            pattern_detector: Optional pattern detector (for testing)
        """
        self.basic_analyzer = basic_analyzer or BasicStatisticsAnalyzer()
        self.contact_analyzer = contact_analyzer or ContactAnalyzer()
        self.time_analyzer = time_analyzer or TimeAnalyzer()
        self.pattern_detector = pattern_detector or PatternDetector()
    
    def run_analysis(self, analysis_type: str, dataframe: pd.DataFrame, 
                    options: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Run an analysis on the given dataframe.
        
        Args:
            analysis_type: Type of analysis to run ("basic", "contact", "time", "pattern")
            dataframe: DataFrame containing the data to analyze
            options: Optional dictionary of analysis options
            
        Returns:
            AnalysisResult containing the analysis results
            
        Raises:
            ValueError: If the analysis type is invalid or analysis fails
        """
        # Validate inputs
        if dataframe is None or dataframe.empty:
            raise ValueError("Empty dataframe provided for analysis")
        
        # Ensure we have a copy of the dataframe to prevent modifications
        df = dataframe.copy()
        
        # Map string analysis type to enum
        analysis_type_enum = {
            "basic": AnalysisType.BASIC,
            "contact": AnalysisType.CONTACT,
            "time": AnalysisType.TIME,
            "pattern": AnalysisType.PATTERN
        }.get(analysis_type.lower())
        
        if analysis_type_enum is None:
            raise ValueError(f"Invalid analysis type: {analysis_type}")
        
        # Map analysis types to their dedicated handler methods
        handlers = {
            "basic": self._handle_basic_analysis,
            "contact": self._handle_contact_analysis,
            "time": self._handle_time_analysis,
            "pattern": self._handle_pattern_analysis
        }
        
        handler = handlers.get(analysis_type.lower())
        if not handler:
            raise ValueError(f"No handler for analysis type: {analysis_type}")
        
        try:
            # Call the handler to get the specific data and result dataframe
            specific_data, result_df = handler(df, options or {})
            
            # Create the analysis result
            result = AnalysisResult(
                result_type=analysis_type_enum,
                data=result_df,
                specific_data=specific_data
            )
            
            return result
        except Exception as e:
            raise ValueError(f"Analysis failed: {str(e)}")
    
    def _handle_basic_analysis(self, df: pd.DataFrame, options: Dict[str, Any]) -> tuple:
        """
        Handle basic statistics analysis.
        
        Args:
            df: DataFrame to analyze
            options: Analysis options
            
        Returns:
            tuple: (specific_data, result_df)
            
        Raises:
            ValueError: If analysis fails
        """
        # Run basic analysis
        stats = self.basic_analyzer.analyze(df, options=options)
        if not stats:
            error_msg = "Basic analysis failed"
            if hasattr(self.basic_analyzer, 'last_error'):
                error_msg = self.basic_analyzer.last_error or error_msg
            raise ValueError(error_msg)
        
        # Convert to BasicAnalysisData
        specific_data = BasicAnalysisData(
            total_records=stats.get('total_records', 0),
            date_range=stats.get('date_range'),
            top_contacts=stats.get('top_contacts'),
            message_types=stats.get('message_types'),
            duration_stats=stats.get('duration_stats')
        )
        
        # Create a result dataframe
        # This is a simplified representation of the data for display
        result_data = []
        
        # Add top contacts to result data
        if stats.get('top_contacts'):
            for contact in stats['top_contacts']:
                result_data.append({
                    'type': 'contact',
                    'value': contact.get('number', ''),
                    'count': contact.get('count', 0),
                    'percentage': contact.get('percentage', 0)
                })
        
        # Add message types to result data
        if stats.get('message_types'):
            for msg_type, count in stats['message_types'].items():
                result_data.append({
                    'type': 'message_type',
                    'value': msg_type,
                    'count': count,
                    'percentage': count / stats.get('total_records', 1) * 100
                })
        
        result_df = pd.DataFrame(result_data) if result_data else df.head(10)
        
        return specific_data, result_df
    
    def _handle_contact_analysis(self, df: pd.DataFrame, options: Dict[str, Any]) -> tuple:
        """
        Handle contact analysis.
        
        Args:
            df: DataFrame to analyze
            options: Analysis options
            
        Returns:
            tuple: (specific_data, result_df)
            
        Raises:
            ValueError: If analysis fails
        """
        # Run contact analysis
        contact_data = self.contact_analyzer.analyze_all(df, options=options)
        if not contact_data:
            error_msg = "Contact analysis failed"
            if hasattr(self.contact_analyzer, 'last_error'):
                error_msg = self.contact_analyzer.last_error or error_msg
            raise ValueError(error_msg)
        
        # Convert to ContactAnalysisData
        specific_data = ContactAnalysisData(
            contact_count=contact_data.get('contact_count', 0),
            contact_relationships=contact_data.get('contact_relationships', []),
            conversation_flow=contact_data.get('conversation_flow', {}),
            contact_importance=contact_data.get('contact_importance', [])
        )
        
        # Create a result dataframe
        result_data = []
        
        # Add contact relationships to result data
        if contact_data.get('contact_relationships'):
            for relationship in contact_data['contact_relationships']:
                result_data.append({
                    'contact': relationship.get('contact', ''),
                    'relationship': relationship.get('relationship', ''),
                    'strength': relationship.get('strength', 0),
                    'last_contact': relationship.get('last_contact', '')
                })
        
        result_df = pd.DataFrame(result_data) if result_data else df.head(10)
        
        return specific_data, result_df
    
    def _handle_time_analysis(self, df: pd.DataFrame, options: Dict[str, Any]) -> tuple:
        """
        Handle time analysis.
        
        Args:
            df: DataFrame to analyze
            options: Analysis options
            
        Returns:
            tuple: (specific_data, result_df)
            
        Raises:
            ValueError: If analysis fails
        """
        # Run time analysis
        time_data = self.time_analyzer.analyze_time_patterns(df, options=options)
        if not time_data:
            error_msg = "Time analysis failed"
            if hasattr(self.time_analyzer, 'last_error'):
                error_msg = self.time_analyzer.last_error or error_msg
            raise ValueError(error_msg)
        
        # Convert to TimeAnalysisData
        specific_data = TimeAnalysisData(
            time_patterns=time_data,
            activity_periods=time_data.get('activity_periods', []),
            response_times=time_data.get('response_times', {})
        )
        
        # Create a result dataframe
        result_data = []
        
        # Add hourly distribution to result data
        if time_data.get('hourly_distribution'):
            for hour, count in time_data['hourly_distribution'].items():
                result_data.append({
                    'period_type': 'hour',
                    'period': hour,
                    'count': count
                })
        
        # Add daily distribution to result data
        if time_data.get('daily_distribution'):
            for day, count in time_data['daily_distribution'].items():
                result_data.append({
                    'period_type': 'day',
                    'period': day,
                    'count': count
                })
        
        # Add monthly distribution to result data
        if time_data.get('monthly_distribution'):
            for month, count in time_data['monthly_distribution'].items():
                result_data.append({
                    'period_type': 'month',
                    'period': month,
                    'count': count
                })
        
        result_df = pd.DataFrame(result_data) if result_data else df.head(10)
        
        return specific_data, result_df
    
    def _handle_pattern_analysis(self, df: pd.DataFrame, options: Dict[str, Any]) -> tuple:
        """
        Handle pattern analysis.
        
        Args:
            df: DataFrame to analyze
            options: Analysis options
            
        Returns:
            tuple: (specific_data, result_df)
            
        Raises:
            ValueError: If analysis fails
        """
        # Run pattern detection
        pattern_data = self.pattern_detector.detect_patterns(df, options=options)
        if not pattern_data:
            error_msg = "Pattern detection failed"
            if hasattr(self.pattern_detector, 'last_error'):
                error_msg = self.pattern_detector.last_error or error_msg
            raise ValueError(error_msg)
        
        # Convert to PatternAnalysisData
        specific_data = PatternAnalysisData(
            patterns=pattern_data.get('patterns', []),
            anomalies=pattern_data.get('anomalies', []),
            insights=pattern_data.get('insights', [])
        )
        
        # Create a result dataframe
        result_data = []
        
        # Add patterns to result data
        if pattern_data.get('patterns'):
            for pattern in pattern_data['patterns']:
                result_data.append({
                    'type': 'pattern',
                    'description': pattern.get('description', ''),
                    'confidence': pattern.get('confidence', 0),
                    'details': str(pattern.get('supporting_data', {}))
                })
        
        # Add anomalies to result data
        if pattern_data.get('anomalies'):
            for anomaly in pattern_data['anomalies']:
                result_data.append({
                    'type': 'anomaly',
                    'description': anomaly.get('description', ''),
                    'severity': anomaly.get('severity', 0),
                    'details': str(anomaly.get('details', {}))
                })
        
        result_df = pd.DataFrame(result_data) if result_data else df.head(10)
        
        return specific_data, result_df
