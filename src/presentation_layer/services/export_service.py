"""
Export Service Module
-------------------
Service for handling export operations for different formats.
"""
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from pathlib import Path
import json
import os

from src.presentation_layer.gui.models.analysis_model import AnalysisResult
from src.analysis_layer.result_formatter import format_as_text, format_as_json, format_as_csv


class ExportService:
    """
    Service for handling export operations.
    
    This class provides methods for exporting analysis results to different
    file formats and generating reports.
    """
    
    def __init__(self):
        """Initialize the export service."""
        self._supported_formats = ["csv", "excel", "json"]
    
    def export_to_file(self, analysis_result: AnalysisResult, 
                      export_format: str, file_path: str) -> bool:
        """
        Export analysis results to a file.
        
        Args:
            analysis_result: The analysis result to export
            export_format: The format to export to (csv, excel, json)
            file_path: The path to export to
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If the export format is unsupported or export fails
        """
        # Validate inputs
        if not analysis_result:
            raise ValueError("No analysis result provided")
        
        if not export_format:
            raise ValueError("No export format specified")
        
        if not file_path:
            raise ValueError("No file path specified")
        
        # Normalize export format
        export_format = export_format.lower()
        
        # Check if format is supported
        if export_format not in self._supported_formats:
            raise ValueError(f"Unsupported export format: {export_format}. "
                           f"Supported formats: {', '.join(self._supported_formats)}")
        
        try:
            # Get the data from the result
            data = analysis_result.data
            
            # Ensure the directory exists
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export based on the format
            if export_format == "csv":
                data.to_csv(file_path, index=False)
            elif export_format == "excel":
                data.to_excel(file_path, index=False)
            elif export_format == "json":
                # Convert to JSON
                json_data = data.to_json(orient="records")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(json_data)
            
            return True
        except Exception as e:
            raise ValueError(f"Error exporting to file: {str(e)}")
    
    def generate_report(self, analysis_result: AnalysisResult, file_path: str) -> bool:
        """
        Generate a text report from analysis results.
        
        Args:
            analysis_result: The analysis result to generate a report from
            file_path: The path to save the report to
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If report generation fails
        """
        # Validate inputs
        if not analysis_result:
            raise ValueError("No analysis result provided")
        
        if not file_path:
            raise ValueError("No file path specified")
        
        try:
            # Generate report content based on analysis type
            report_content = self._generate_report_content(analysis_result)
            
            # Ensure the directory exists
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            
            return True
        except Exception as e:
            raise ValueError(f"Error generating report: {str(e)}")
    
    def _generate_report_content(self, analysis_result: AnalysisResult) -> str:
        """
        Generate report content based on analysis type.
        
        Args:
            analysis_result: The analysis result to generate a report from
            
        Returns:
            Report content as a string
        """
        # Get the analysis type
        analysis_type = analysis_result.result_type
        
        # Generate report header
        header = f"Analysis Report: {analysis_type.name}\n"
        header += "=" * len(header) + "\n\n"
        
        # Generate report content based on analysis type
        content = ""
        
        if hasattr(analysis_result, "specific_data") and analysis_result.specific_data:
            specific_data = analysis_result.specific_data
            
            # Basic analysis
            if hasattr(specific_data, "total_records"):
                content += f"Total Records: {specific_data.total_records}\n\n"
            
            # Date range
            if hasattr(specific_data, "date_range") and specific_data.date_range:
                content += "Date Range:\n"
                content += f"  Start: {specific_data.date_range.get('start', 'N/A')}\n"
                content += f"  End: {specific_data.date_range.get('end', 'N/A')}\n"
                content += f"  Days: {specific_data.date_range.get('days', 'N/A')}\n\n"
            
            # Top contacts
            if hasattr(specific_data, "top_contacts") and specific_data.top_contacts:
                content += "Top Contacts:\n"
                for contact in specific_data.top_contacts:
                    content += f"  {contact.get('number', 'N/A')}: {contact.get('count', 0)} messages\n"
                content += "\n"
            
            # Message types
            if hasattr(specific_data, "message_types") and specific_data.message_types:
                content += "Message Types:\n"
                for msg_type, count in specific_data.message_types.items():
                    content += f"  {msg_type}: {count} messages\n"
                content += "\n"
            
            # Contact analysis
            if hasattr(specific_data, "contact_count"):
                content += f"Contact Count: {specific_data.contact_count}\n\n"
            
            # Contact relationships
            if hasattr(specific_data, "contact_relationships") and specific_data.contact_relationships:
                content += "Contact Relationships:\n"
                for relationship in specific_data.contact_relationships:
                    content += f"  {relationship.get('contact', 'N/A')}: {relationship.get('relationship', 'N/A')}\n"
                content += "\n"
            
            # Time patterns
            if hasattr(specific_data, "time_patterns") and specific_data.time_patterns:
                content += "Time Patterns:\n"
                
                # Hourly distribution
                if "hourly_distribution" in specific_data.time_patterns:
                    content += "  Hourly Distribution:\n"
                    for hour, count in specific_data.time_patterns["hourly_distribution"].items():
                        if count > 0:
                            content += f"    {hour}: {count} messages\n"
                    content += "\n"
                
                # Daily distribution
                if "daily_distribution" in specific_data.time_patterns:
                    content += "  Daily Distribution:\n"
                    for day, count in specific_data.time_patterns["daily_distribution"].items():
                        if count > 0:
                            content += f"    {day}: {count} messages\n"
                    content += "\n"
                
                # Monthly distribution
                if "monthly_distribution" in specific_data.time_patterns:
                    content += "  Monthly Distribution:\n"
                    for month, count in specific_data.time_patterns["monthly_distribution"].items():
                        if count > 0:
                            content += f"    {month}: {count} messages\n"
                    content += "\n"
            
            # Patterns
            if hasattr(specific_data, "patterns") and specific_data.patterns:
                content += "Detected Patterns:\n"
                for pattern in specific_data.patterns:
                    content += f"  {pattern.get('description', 'N/A')} (Confidence: {pattern.get('confidence', 0):.2f})\n"
                content += "\n"
            
            # Anomalies
            if hasattr(specific_data, "anomalies") and specific_data.anomalies:
                content += "Detected Anomalies:\n"
                for anomaly in specific_data.anomalies:
                    content += f"  {anomaly.get('description', 'N/A')} (Severity: {anomaly.get('severity', 0):.2f})\n"
                content += "\n"
        
        # Add data summary
        if hasattr(analysis_result, "data") and not analysis_result.data.empty:
            content += "Data Summary:\n"
            content += f"  Rows: {len(analysis_result.data)}\n"
            content += f"  Columns: {len(analysis_result.data.columns)}\n"
            
            # Add column names
            content += "  Columns: " + ", ".join(analysis_result.data.columns) + "\n\n"
            
            # Add first few rows
            content += "First 5 rows:\n"
            content += analysis_result.data.head(5).to_string() + "\n"
        
        return header + content
    
    def get_supported_formats(self) -> List[str]:
        """
        Get a list of supported export formats.
        
        Returns:
            List of supported export formats
        """
        return self._supported_formats.copy()
