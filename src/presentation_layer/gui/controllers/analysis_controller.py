from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
from typing import Dict, Optional, Any, Union
import pandas as pd

from src.presentation_layer.gui.utils.error_handler import ErrorHandler, ErrorSeverity
from src.presentation_layer.gui.models.analysis_model import (
    AnalysisResult, AnalysisType, BasicAnalysisData,
    ContactAnalysisData, TimeAnalysisData, PatternAnalysisData
)
from src.analysis_layer.basic_statistics import BasicStatisticsAnalyzer
from src.analysis_layer.contact_analysis import ContactAnalyzer
from src.analysis_layer.time_analysis import TimeAnalyzer
from src.analysis_layer.pattern_detector import PatternDetector

class AnalysisController(QObject):
    analysis_started = Signal(str)
    analysis_progress = Signal(int)  # 0-100 percent
    analysis_completed = Signal(object)  # Emits AnalysisResult
    analysis_failed = Signal(str)

    def __init__(self, basic_analyzer: Optional[BasicStatisticsAnalyzer] = None,
                 contact_analyzer: Optional[ContactAnalyzer] = None,
                 time_analyzer: Optional[TimeAnalyzer] = None,
                 pattern_detector: Optional[PatternDetector] = None,
                 component_name="AnalysisController"):
        super().__init__()
        # Dependency injection for testability
        self.basic_analyzer = basic_analyzer or BasicStatisticsAnalyzer()
        self.contact_analyzer = contact_analyzer or ContactAnalyzer()
        self.time_analyzer = time_analyzer or TimeAnalyzer()
        self.pattern_detector = pattern_detector or PatternDetector()

        self.error_handler = ErrorHandler(component_name)
        self.thread_pool = QThreadPool.globalInstance()
        self.current_analysis_type = None

    def run_analysis(self, analysis_type: str, file_model, options: Optional[Dict[str, Any]] = None):
        """Run an analysis on the given file model.

        Args:
            analysis_type: Type of analysis to run ("basic", "contact", "time", "pattern")
            file_model: FileModel containing the data to analyze
            options: Optional dictionary of analysis options
        """
        self.current_analysis_type = analysis_type
        self.analysis_started.emit(f"{analysis_type.capitalize()} analysis started")

        # Map string analysis type to enum
        analysis_type_enum = {
            "basic": AnalysisType.BASIC,
            "contact": AnalysisType.CONTACT,
            "time": AnalysisType.TIME,
            "pattern": AnalysisType.PATTERN
        }.get(analysis_type.lower(), AnalysisType.CUSTOM)

        # Create and start the analysis task
        runnable = _AnalysisTask(
            analysis_type=analysis_type,
            analysis_type_enum=analysis_type_enum,
            analyzers={
                "basic": self.basic_analyzer,
                "contact": self.contact_analyzer,
                "time": self.time_analyzer,
                "pattern": self.pattern_detector
            },
            file_model=file_model,
            options=options or {},
            controller=self
        )
        self.thread_pool.start(runnable)

    def cancel_analysis(self):
        """Cancel the current analysis."""
        # This is a placeholder - actual implementation would depend on how
        # the analyzers support cancellation
        self.analysis_failed.emit("Analysis cancelled by user")

class _AnalysisTask(QRunnable):
    def __init__(self, analysis_type: str, analysis_type_enum: AnalysisType,
                 analyzers: Dict[str, Any], file_model, options: Dict[str, Any], controller):
        super().__init__()
        self.analysis_type = analysis_type
        self.analysis_type_enum = analysis_type_enum
        self.analyzers = analyzers
        self.file_model = file_model
        self.options = options
        self.controller = controller

    def run(self):
        try:
            # Get the appropriate analyzer
            analyzer = self.analyzers.get(self.analysis_type)
            if not analyzer:
                raise ValueError(f"Unknown analysis type: {self.analysis_type}")

            # Get the dataframe from the file model
            df = self.file_model.dataframe

            # Report progress
            self.controller.analysis_progress.emit(10)

            # Run the analysis based on type
            if self.analysis_type == "basic":
                stats, error = analyzer.analyze(df, column_mapping=None)
                if error:
                    raise ValueError(f"Analysis failed: {error}")

                # Convert stats to BasicAnalysisData
                specific_data = BasicAnalysisData(
                    total_records=stats.total_records,
                    date_range=stats.date_range.to_dict() if stats.date_range else None,
                    top_contacts=[contact.to_dict() for contact in stats.top_contacts] if stats.top_contacts else None,
                    message_types={t.name: t.count for t in stats.type_stats.types} if stats.type_stats else None,
                    duration_stats=stats.duration_stats.to_dict() if stats.duration_stats else None
                )

                # Create result dataframe
                result_df = pd.DataFrame({
                    "Metric": ["Total Records", "Date Range", "Top Contact", "Message Types"],
                    "Value": [
                        stats.total_records,
                        f"{stats.date_range.start} to {stats.date_range.end}" if stats.date_range else "N/A",
                        f"{stats.top_contacts[0].number} ({stats.top_contacts[0].count} records)" if stats.top_contacts else "N/A",
                        ", ".join([f"{t.name}: {t.count}" for t in stats.type_stats.types]) if stats.type_stats else "N/A"
                    ]
                })

            elif self.analysis_type == "contact":
                # Run contact analysis
                contact_data = analyzer.analyze_all(df)
                if not contact_data:
                    raise ValueError(f"Contact analysis failed: {analyzer.last_error}")

                # Convert to ContactAnalysisData
                specific_data = ContactAnalysisData(
                    contact_count=len(contact_data.get('contact_relationships', [])),
                    contact_relationships=contact_data.get('contact_relationships'),
                    conversation_flow=contact_data.get('conversation_flow'),
                    contact_importance=contact_data.get('contact_importance')
                )

                # Create result dataframe
                result_df = pd.DataFrame({
                    "Contact": [r['contact'] for r in contact_data.get('contact_relationships', [])],
                    "Frequency": [r['frequency'] for r in contact_data.get('contact_relationships', [])],
                    "Importance": [r.get('importance', 'N/A') for r in contact_data.get('contact_relationships', [])]
                }) if contact_data.get('contact_relationships') else pd.DataFrame()

            elif self.analysis_type == "time":
                # Run time analysis
                time_data = analyzer.analyze_all(df)
                if not time_data:
                    raise ValueError(f"Time analysis failed: {analyzer.last_error}")

                # Convert to TimeAnalysisData
                specific_data = TimeAnalysisData(
                    time_distribution=time_data.get('time_distribution'),
                    hourly_patterns=time_data.get('hourly_patterns'),
                    daily_patterns=time_data.get('daily_patterns'),
                    monthly_patterns=time_data.get('monthly_patterns'),
                    response_times=time_data.get('response_times')
                )

                # Create result dataframe
                if time_data.get('hourly_patterns'):
                    result_df = pd.DataFrame({
                        "Hour": list(time_data['hourly_patterns'].keys()),
                        "Count": list(time_data['hourly_patterns'].values())
                    })
                else:
                    result_df = pd.DataFrame()

            elif self.analysis_type == "pattern":
                # Run pattern detection
                pattern_data = analyzer.detect_all_patterns(df)
                if not pattern_data:
                    raise ValueError(f"Pattern detection failed: {analyzer.last_error}")

                # Convert to PatternAnalysisData
                specific_data = PatternAnalysisData(
                    detected_patterns=pattern_data.get('detected_patterns'),
                    anomalies=pattern_data.get('anomalies'),
                    predictions=pattern_data.get('predictions')
                )

                # Create result dataframe
                if pattern_data.get('detected_patterns'):
                    result_df = pd.DataFrame({
                        "Pattern": [p['pattern_name'] for p in pattern_data['detected_patterns']],
                        "Confidence": [p['confidence'] for p in pattern_data['detected_patterns']],
                        "Description": [p['description'] for p in pattern_data['detected_patterns']]
                    })
                else:
                    result_df = pd.DataFrame()
            else:
                raise ValueError(f"Unknown analysis type: {self.analysis_type}")

            # Report progress
            self.controller.analysis_progress.emit(90)

            # Create the analysis result
            result = AnalysisResult(
                result_type=self.analysis_type_enum,
                data=result_df,
                specific_data=specific_data
            )

            # Report completion
            self.controller.analysis_progress.emit(100)
            self.controller.analysis_completed.emit(result)

        except Exception as exc:
            self.controller.error_handler.log(
                ErrorSeverity.ERROR,
                "analysis_execution",
                str(exc),
                user_message="Analysis failed. Please check your input file and try again."
            )
            self.controller.analysis_failed.emit(str(exc))
