#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File View

This module implements the file selection and display view.
It allows users to select files and displays file metadata.
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTableView, QHeaderView, QAbstractItemView,
    QGroupBox, QFormLayout, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent

# Import UI constants
from ..stylesheets.constants import Colors, Dimensions, Typography


class FileView(QWidget):
    """
    File selection and display view.

    This class implements a view for selecting files and displaying file metadata.
    It supports drag-and-drop file selection and displays basic file information.
    """

    # Signals
    file_selected = Signal(str)  # Emitted when a file is selected

    def __init__(self, file_controller=None, parent=None):
        """Initialize the file view.

        Args:
            file_controller: The file controller to use
            parent: The parent widget
        """
        super().__init__(parent)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Initialize UI components
        self._init_ui()

        # Current file path
        self.current_file_path = None

        # Set up the file controller
        self.file_controller = file_controller

        # Connect signals if controller is provided
        if self.file_controller:
            # Connect view signals to controller methods
            self.file_selected.connect(self.file_controller.load_file)

            # Connect controller signals to view methods
            self.file_controller.file_loaded.connect(self.on_file_loaded)
            self.file_controller.file_load_failed.connect(self.on_file_load_failed)

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

        # File selection section
        selection_group = QGroupBox("File Selection")
        selection_layout = QVBoxLayout(selection_group)

        # Instructions label
        instructions_label = QLabel(
            "Select a phone records file to analyze. "
            "You can click the button below or drag and drop a file here."
        )
        instructions_label.setWordWrap(True)
        selection_layout.addWidget(instructions_label)

        # File selection button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.select_file_button = QPushButton("Select File...")
        self.select_file_button.setMinimumWidth(150)
        self.select_file_button.setToolTip("Click to select a phone records file")
        self.select_file_button.clicked.connect(self.on_select_file_button_clicked)
        button_layout.addWidget(self.select_file_button)

        button_layout.addStretch()
        selection_layout.addLayout(button_layout)

        # Drop area
        self.drop_area = QLabel("Or drop files here")
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setMinimumHeight(100)
        self.drop_area.setStyleSheet(
            "QLabel { background-color: #f0f0f0; border: 2px dashed #cccccc; border-radius: 5px; }"
        )
        selection_layout.addWidget(self.drop_area)

        main_layout.addWidget(selection_group)

        # File information section
        info_group = QGroupBox("File Information")
        info_layout = QFormLayout(info_group)

        # File path
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        info_layout.addRow("File Path:", self.file_path_edit)

        # File size
        self.file_size_edit = QLineEdit()
        self.file_size_edit.setReadOnly(True)
        info_layout.addRow("File Size:", self.file_size_edit)

        # File type
        self.file_type_edit = QLineEdit()
        self.file_type_edit.setReadOnly(True)
        info_layout.addRow("File Type:", self.file_type_edit)

        # Record count (to be filled after loading)
        self.record_count_edit = QLineEdit()
        self.record_count_edit.setReadOnly(True)
        info_layout.addRow("Record Count:", self.record_count_edit)

        main_layout.addWidget(info_group)

        # Add a spacer at the bottom
        main_layout.addStretch()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Handle drag enter events.

        Args:
            event (QDragEnterEvent): The drag enter event
        """
        # Check if the dragged data has URLs (files)
        if event.mimeData().hasUrls():
            # Get the first URL
            url = event.mimeData().urls()[0]

            # Check if it's a local file
            if url.isLocalFile():
                file_path = url.toLocalFile()

                # Check if it's a valid file type
                if self._is_valid_file_type(file_path):
                    event.acceptProposedAction()
                    # Change the drop area appearance
                    self.drop_area.setStyleSheet(
                        "QLabel { background-color: #e0f7fa; border: 2px dashed #00acc1; border-radius: 5px; }"
                    )
                    return

        # If we get here, the drag is not accepted
        event.ignore()

    def dragLeaveEvent(self, event):
        """
        Handle drag leave events.

        Args:
            event: The drag leave event
        """
        # Reset the drop area appearance
        self.drop_area.setStyleSheet(
            "QLabel { background-color: #f0f0f0; border: 2px dashed #cccccc; border-radius: 5px; }"
        )
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        """
        Handle drop events.

        Args:
            event (QDropEvent): The drop event
        """
        # Reset the drop area appearance
        self.drop_area.setStyleSheet(
            "QLabel { background-color: #f0f0f0; border: 2px dashed #cccccc; border-radius: 5px; }"
        )

        # Get the first URL
        url = event.mimeData().urls()[0]

        # Check if it's a local file
        if url.isLocalFile():
            file_path = url.toLocalFile()

            # Check if it's a valid file type
            if self._is_valid_file_type(file_path):
                self._set_file(file_path)
                event.acceptProposedAction()

    @Slot()
    def on_select_file_button_clicked(self):
        """Handle the select file button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Phone Records File",
            "",
            "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            if self._is_valid_file_type(file_path):
                self._set_file(file_path)
            else:
                QMessageBox.warning(
                    self,
                    "Invalid File Type",
                    "Please select an Excel (.xlsx) or CSV (.csv) file."
                )

    def _is_valid_file_type(self, file_path):
        """
        Check if the file is a valid type.

        Args:
            file_path (str): The path to the file

        Returns:
            bool: True if the file is a valid type, False otherwise
        """
        # Get the file extension
        _, ext = os.path.splitext(file_path)

        # Check if it's a valid extension
        return ext.lower() in ['.xlsx', '.csv']

    def _set_file(self, file_path):
        """
        Set the current file.

        Args:
            file_path (str): The path to the file
        """
        self.current_file_path = file_path

        # Update the file information
        self.file_path_edit.setText(file_path)

        try:
            # Get file size
            file_size = os.path.getsize(file_path)
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            self.file_size_edit.setText(size_str)
        except (FileNotFoundError, OSError):
            # Handle non-existent files (for testing)
            self.file_size_edit.setText("Unknown")

        # Get file type
        _, ext = os.path.splitext(file_path)
        if ext.lower() == '.xlsx':
            self.file_type_edit.setText("Excel Spreadsheet")
        elif ext.lower() == '.csv':
            self.file_type_edit.setText("CSV File")
        else:
            self.file_type_edit.setText(ext)

        # Clear record count (will be updated after loading)
        self.record_count_edit.setText("Loading...")

        # Emit the file_selected signal
        self.file_selected.emit(file_path)

    def set_record_count(self, count):
        """
        Set the record count.

        Args:
            count (int): The number of records in the file
        """
        self.record_count_edit.setText(str(count))

    @Slot(object)
    def on_file_loaded(self, file_model):
        """
        Handle the file_loaded signal from the controller.

        Args:
            file_model: The loaded file model
        """
        # Update the file information
        self.file_path_edit.setText(file_model.file_path)
        self.file_size_edit.setText(file_model.file_size_formatted)
        self.file_type_edit.setText(file_model.file_type)
        self.record_count_edit.setText(str(file_model.record_count))

        # Show a success message
        QMessageBox.information(
            self,
            "File Loaded",
            f"File '{file_model.file_name}' loaded successfully with {file_model.record_count} records."
        )

    @Slot(str)
    def on_file_load_failed(self, error_message):
        """
        Handle the file_load_failed signal from the controller.

        Args:
            error_message: The error message
        """
        # Show an error message
        QMessageBox.critical(
            self,
            "File Load Error",
            f"Failed to load file: {error_message}"
        )

        # Clear the file information
        self.file_path_edit.clear()
        self.file_size_edit.clear()
        self.file_type_edit.clear()
        self.record_count_edit.clear()


# For testing purposes
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    view = FileView()
    view.show()
    sys.exit(app.exec())
