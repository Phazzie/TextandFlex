#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Visualization View

This module implements the visualization display view.
It displays analysis results as charts and graphs using matplotlib.
"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QFormLayout, QToolBar, QFileDialog,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Import UI constants
from ..stylesheets.constants import Colors, Dimensions, Typography


class MatplotlibCanvas(FigureCanvas):
    """
    Matplotlib canvas for embedding in Qt applications.

    This class provides a canvas for matplotlib figures that can be embedded
    in Qt applications.
    """

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """
        Initialize the canvas.

        Args:
            parent (QWidget, optional): The parent widget
            width (float, optional): The width of the figure in inches
            height (float, optional): The height of the figure in inches
            dpi (int, optional): The resolution of the figure in dots per inch
        """
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        super().__init__(self.fig)
        self.setParent(parent)

        # Set up the figure
        self.fig.tight_layout()

        # Make the canvas expandable
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

    def clear(self):
        """Clear the figure."""
        self.axes.clear()
        self.draw()


class VisualizationView(QWidget):
    """
    Visualization display view.

    This class implements a view for displaying analysis results as charts and graphs.
    It supports different types of visualizations and export options.
    """

    # Signals
    export_requested = Signal(str, str)  # Emitted when export is requested (format, path)

    def __init__(self, parent=None):
        """Initialize the visualization view."""
        super().__init__(parent)

        # Initialize UI components
        self._init_ui()

        # Current data
        self.current_data = None
        self.current_type = None
        self.current_title = None
        self.current_x_label = None
        self.current_y_label = None

    def _init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            Dimensions.SPACING_MEDIUM,
            Dimensions.SPACING_MEDIUM,
            Dimensions.SPACING_MEDIUM,
            Dimensions.SPACING_MEDIUM
        )
        main_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(Dimensions.ICON_SMALL)

        # Visualization type combo
        type_label = QLabel("Chart Type:")
        toolbar.addWidget(type_label)

        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItem("Bar Chart", "bar")
        self.chart_type_combo.addItem("Line Chart", "line")
        self.chart_type_combo.addItem("Pie Chart", "pie")
        self.chart_type_combo.addItem("Scatter Plot", "scatter")
        self.chart_type_combo.setToolTip("Select the type of chart to display")
        self.chart_type_combo.currentIndexChanged.connect(self._on_chart_type_changed)
        toolbar.addWidget(self.chart_type_combo)

        toolbar.addSeparator()

        # Export button
        self.export_button = QPushButton("Export")
        self.export_button.setToolTip("Export the visualization to a file")
        self.export_button.clicked.connect(self._on_export_button_clicked)
        toolbar.addWidget(self.export_button)

        # Export format combo
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItem("PNG", "png")
        self.export_format_combo.addItem("PDF", "pdf")
        self.export_format_combo.addItem("SVG", "svg")
        toolbar.addWidget(self.export_format_combo)

        main_layout.addWidget(toolbar)

        # Matplotlib canvas
        self.canvas = MatplotlibCanvas(self)
        main_layout.addWidget(self.canvas)

        # Matplotlib toolbar
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        main_layout.addWidget(self.mpl_toolbar)

        # Status bar
        self.status_label = QLabel("No data to display")
        main_layout.addWidget(self.status_label)

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

        # Update the visualization
        self._update_visualization()

    def _update_visualization(self):
        """Update the visualization based on the current data and chart type."""
        if self.current_data is None:
            self.status_label.setText("No data to display")
            return

        # Clear the canvas
        self.canvas.clear()

        # Get the chart type
        chart_type = self.chart_type_combo.currentData()

        try:
            # Create the chart based on the type
            if chart_type == "bar":
                self._create_bar_chart()
            elif chart_type == "line":
                self._create_line_chart()
            elif chart_type == "pie":
                self._create_pie_chart()
            elif chart_type == "scatter":
                self._create_scatter_chart()

            # Update the status
            self.status_label.setText(f"Displaying {chart_type} chart")

        except Exception as e:
            self.status_label.setText(f"Error creating chart: {str(e)}")
            # Clear the canvas
            self.canvas.clear()

    def _set_chart_labels(self, labels=None):
        """Set the chart title and axis labels."""
        # Set the title and labels
        if self.current_title:
            self.canvas.axes.set_title(self.current_title)
        if self.current_x_label:
            self.canvas.axes.set_xlabel(self.current_x_label)
        if self.current_y_label:
            self.canvas.axes.set_ylabel(self.current_y_label)

        # Rotate the x-axis labels if there are many and labels are provided
        if labels and len(labels) > 5:
            self.canvas.axes.set_xticklabels(labels, rotation=45, ha="right")

    def _create_bar_chart(self):
        """Create a bar chart."""
        # Extract the data
        labels = list(self.current_data.keys())
        values = list(self.current_data.values())

        # Create the chart
        self.canvas.axes.bar(labels, values)

        # Set the chart labels
        self._set_chart_labels(labels)

        # Adjust the layout
        self.canvas.fig.tight_layout()

        # Draw the canvas
        self.canvas.draw()

    def _create_line_chart(self):
        """Create a line chart."""
        # Extract the data
        labels = list(self.current_data.keys())
        values = list(self.current_data.values())

        # Create the chart
        self.canvas.axes.plot(labels, values, marker='o')

        # Set the chart labels
        self._set_chart_labels(labels)

        # Adjust the layout
        self.canvas.fig.tight_layout()

        # Draw the canvas
        self.canvas.draw()

    def _create_pie_chart(self):
        """Create a pie chart."""
        # Extract the data
        labels = list(self.current_data.keys())
        values = list(self.current_data.values())

        # Create the chart
        self.canvas.axes.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90
        )

        # Set the title (only title for pie charts, no axis labels)
        if self.current_title:
            self.canvas.axes.set_title(self.current_title)

        # Equal aspect ratio ensures that pie is drawn as a circle
        self.canvas.axes.axis('equal')

        # Adjust the layout
        self.canvas.fig.tight_layout()

        # Draw the canvas
        self.canvas.draw()

    def _create_scatter_chart(self):
        """Create a scatter chart."""
        # Extract the data
        labels = list(self.current_data.keys())
        values = list(self.current_data.values())

        # Create the chart
        self.canvas.axes.scatter(range(len(labels)), values)

        # Set the x-axis ticks and labels
        self.canvas.axes.set_xticks(range(len(labels)))
        self.canvas.axes.set_xticklabels(labels)

        # Set the chart labels
        self._set_chart_labels(labels)

        # Adjust the layout
        self.canvas.fig.tight_layout()

        # Draw the canvas
        self.canvas.draw()

    @Slot(int)
    def _on_chart_type_changed(self, _):
        """
        Handle chart type changes.

        Args:
            _ (int): The index of the selected chart type (unused)
        """
        self._update_visualization()

    @Slot()
    def _on_export_button_clicked(self):
        """Handle export button click."""
        if self.current_data is None:
            QMessageBox.warning(
                self,
                "No Data",
                "There is no data to export."
            )
            return

        # Get the export format
        export_format = self.export_format_combo.currentData()

        # Get the file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Visualization",
            "",
            f"{export_format.upper()} Files (*.{export_format});;All Files (*)"
        )

        if file_path:
            # Ensure the file has the correct extension
            if not file_path.lower().endswith(f".{export_format}"):
                file_path += f".{export_format}"

            try:
                # Save the figure
                self.canvas.fig.savefig(
                    file_path,
                    format=export_format,
                    dpi=300,
                    bbox_inches='tight'
                )

                # Show success message
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Visualization exported to {file_path}"
                )

            except Exception as e:
                # Show error message
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export visualization: {str(e)}"
                )


# For testing purposes
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    view = VisualizationView()

    # Set some test data
    data = {
        "Category 1": 10,
        "Category 2": 25,
        "Category 3": 15,
        "Category 4": 30,
        "Category 5": 20
    }
    view.set_data(data, "Test Chart", "Categories", "Values")

    view.show()
    sys.exit(app.exec())
