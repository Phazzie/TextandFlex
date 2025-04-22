"""
Visualization Controller

This module implements the controller for the visualization display.
It handles the creation and export of visualizations.
"""

from PySide6.QtCore import QObject, Signal
import os

from src.presentation_layer.gui.utils.error_handler import ErrorHandler, ErrorSeverity


class VisualizationController(QObject):
    """
    Controller for the visualization display.
    
    This class handles the creation and export of visualizations.
    """
    
    # Signals
    export_started = Signal(str)  # Emitted when export is started
    export_completed = Signal(str)  # Emitted when export is completed
    export_failed = Signal(str)  # Emitted when export fails
    
    def __init__(self, component_name="VisualizationController"):
        """
        Initialize the visualization controller.
        
        Args:
            component_name (str): The name of the component for error handling
        """
        super().__init__()
        self.error_handler = ErrorHandler(component_name)
        self.current_data = None
        self.current_title = None
        self.current_x_label = None
        self.current_y_label = None
    
    def set_data(self, data, title=None, x_label=None, y_label=None):
        """
        Set the data for visualization.
        
        Args:
            data (dict): The data to visualize
            title (str, optional): The title of the visualization
            x_label (str, optional): The label for the x-axis
            y_label (str, optional): The label for the y-axis
        """
        self.current_data = data
        self.current_title = title
        self.current_x_label = x_label
        self.current_y_label = y_label
    
    def export_visualization(self, export_format, file_path, figure):
        """
        Export the visualization to a file.
        
        Args:
            export_format (str): The format to export to (png, pdf, svg)
            file_path (str): The path to export to
            figure: The matplotlib figure to export
        """
        try:
            # Emit the export_started signal
            self.export_started.emit(f"Exporting to {export_format}...")
            
            # Save the figure
            figure.savefig(
                file_path,
                format=export_format,
                dpi=300,
                bbox_inches='tight'
            )
            
            # Emit the export_completed signal
            self.export_completed.emit(f"Export to {file_path} completed")
            
        except Exception as exc:
            # Log the error
            self.error_handler.log(
                ErrorSeverity.ERROR,
                "export_visualization",
                str(exc),
                user_message=f"Failed to export visualization: {str(exc)}"
            )
            
            # Emit the export_failed signal
            self.export_failed.emit(str(exc))
