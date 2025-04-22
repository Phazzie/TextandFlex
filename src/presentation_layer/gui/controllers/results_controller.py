"""
Results Controller

This module implements the controller for the results display.
It handles the display and export of analysis results.
"""

from PySide6.QtCore import QObject, Signal
import pandas as pd
import json
import os

from src.presentation_layer.gui.utils.error_handler import ErrorHandler, ErrorSeverity
from src.presentation_layer.gui.models.analysis_model import AnalysisResult


class ResultsController(QObject):
    """
    Controller for the results display.
    
    This class handles the display and export of analysis results.
    """
    
    # Signals
    export_started = Signal(str)  # Emitted when export is started
    export_completed = Signal(str)  # Emitted when export is completed
    export_failed = Signal(str)  # Emitted when export fails
    visualization_requested = Signal(dict, str, str, str)  # Emitted when visualization is requested
    
    def __init__(self, component_name="ResultsController"):
        """
        Initialize the results controller.
        
        Args:
            component_name (str): The name of the component for error handling
        """
        super().__init__()
        self.error_handler = ErrorHandler(component_name)
        self.current_result = None
    
    def set_result(self, result):
        """
        Set the current analysis result.
        
        Args:
            result (AnalysisResult): The analysis result to display
        """
        self.current_result = result
    
    def export_results(self, export_format, file_path):
        """
        Export the results to a file.
        
        Args:
            export_format (str): The format to export to (csv, xlsx, json)
            file_path (str): The path to export to
        """
        if not self.current_result:
            self.export_failed.emit("No results to export")
            return
        
        try:
            # Emit the export_started signal
            self.export_started.emit(f"Exporting to {export_format}...")
            
            # Get the data from the result
            data = self.current_result.data
            
            # Export based on the format
            if export_format == "csv":
                data.to_csv(file_path, index=False)
            elif export_format == "xlsx":
                data.to_excel(file_path, index=False)
            elif export_format == "json":
                # Convert to JSON
                json_data = data.to_json(orient="records")
                with open(file_path, "w") as f:
                    f.write(json_data)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            # Emit the export_completed signal
            self.export_completed.emit(f"Export to {file_path} completed")
            
        except Exception as exc:
            # Log the error
            self.error_handler.log(
                ErrorSeverity.ERROR,
                "export_results",
                str(exc),
                user_message=f"Failed to export results: {str(exc)}"
            )
            
            # Emit the export_failed signal
            self.export_failed.emit(str(exc))
    
    def request_visualization(self, chart_type="bar"):
        """
        Request a visualization of the results.
        
        Args:
            chart_type (str): The type of chart to create
        """
        if not self.current_result:
            self.error_handler.log(
                ErrorSeverity.WARNING,
                "request_visualization",
                "No results to visualize",
                user_message="No results to visualize"
            )
            return
        
        try:
            # Get the data from the result
            data = self.current_result.data
            
            # Prepare the data for visualization
            if chart_type == "bar" or chart_type == "pie":
                # For bar and pie charts, we need a dictionary of category -> value
                if len(data.columns) >= 2:
                    # Use the first column as categories and the second as values
                    categories = data.iloc[:, 0].tolist()
                    values = data.iloc[:, 1].tolist()
                    viz_data = dict(zip(categories, values))
                else:
                    # Use row indices as categories
                    viz_data = {f"Row {i+1}": data.iloc[i, 0] for i in range(len(data))}
            else:
                # For other chart types, just use the raw data
                viz_data = data.to_dict()
            
            # Get the title from the result
            title = f"{self.current_result.result_type.name} Analysis Results"
            
            # Get the axis labels from the data
            x_label = data.columns[0] if len(data.columns) > 0 else "Categories"
            y_label = data.columns[1] if len(data.columns) > 1 else "Values"
            
            # Emit the visualization_requested signal
            self.visualization_requested.emit(viz_data, title, x_label, y_label)
            
        except Exception as exc:
            # Log the error
            self.error_handler.log(
                ErrorSeverity.ERROR,
                "request_visualization",
                str(exc),
                user_message=f"Failed to create visualization: {str(exc)}"
            )
