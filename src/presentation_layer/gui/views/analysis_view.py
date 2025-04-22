#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Analysis View

This module implements the analysis options and control view.
It allows users to select and configure analysis options.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QGroupBox, QFormLayout, QSpinBox,
    QDateEdit, QProgressBar, QListWidget, QListWidgetItem,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, Slot, QDate

# Import UI constants
from ..stylesheets.constants import Colors, Dimensions, Typography


class AnalysisView(QWidget):
    """
    Analysis options and control view.

    This class implements a view for selecting and configuring analysis options.
    It provides controls for different types of analysis and their parameters.
    """

    # Signals
    analysis_requested = Signal(str, dict)  # Emitted when analysis is requested

    def __init__(self, analysis_controller=None, parent=None):
        """Initialize the analysis view.

        Args:
            analysis_controller: The analysis controller to use
            parent: The parent widget
        """
        super().__init__(parent)

        # Initialize UI components
        self._init_ui()

        # Analysis history
        self.analysis_history = []

        # Current file model
        self.current_file_model = None

        # Set up the analysis controller
        self.analysis_controller = analysis_controller

        # Connect signals if controller is provided
        if self.analysis_controller:
            # Connect view signals to controller methods
            self.analysis_requested.connect(lambda analysis_type, options:
                self.analysis_controller.run_analysis(analysis_type, self.current_file_model, options))
            self.cancel_button.clicked.connect(self.analysis_controller.cancel_analysis)

            # Connect controller signals to view methods
            self.analysis_controller.analysis_started.connect(self.on_analysis_started)
            self.analysis_controller.analysis_progress.connect(self.on_analysis_progress)
            self.analysis_controller.analysis_completed.connect(self.on_analysis_completed)
            self.analysis_controller.analysis_failed.connect(self.on_analysis_failed)

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

        # Analysis type section
        type_group = QGroupBox("Analysis Type")
        type_layout = QFormLayout(type_group)

        # Analysis type combo box
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItem("Basic Statistics", "basic")
        self.analysis_type_combo.addItem("Contact Analysis", "contact")
        self.analysis_type_combo.addItem("Time Analysis", "time")
        self.analysis_type_combo.currentIndexChanged.connect(self._on_analysis_type_changed)
        type_layout.addRow("Analysis Type:", self.analysis_type_combo)

        main_layout.addWidget(type_group)

        # Create a scroll area for options
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Container for options
        options_container = QWidget()
        self.options_layout = QVBoxLayout(options_container)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        scroll_area.setWidget(options_container)
        main_layout.addWidget(scroll_area)

        # Basic statistics options
        self.basic_options_group = QGroupBox("Basic Statistics Options")
        basic_options_layout = QFormLayout(self.basic_options_group)

        # Include call duration checkbox
        self.include_duration_check = QCheckBox("Include call duration statistics")
        self.include_duration_check.setChecked(True)
        basic_options_layout.addRow(self.include_duration_check)

        # Include message type checkbox
        self.include_message_type_check = QCheckBox("Include message type statistics")
        self.include_message_type_check.setChecked(True)
        basic_options_layout.addRow(self.include_message_type_check)

        # Group by options
        self.group_by_combo = QComboBox()
        self.group_by_combo.addItem("None", "none")
        self.group_by_combo.addItem("Day", "day")
        self.group_by_combo.addItem("Week", "week")
        self.group_by_combo.addItem("Month", "month")
        basic_options_layout.addRow("Group By:", self.group_by_combo)

        self.options_layout.addWidget(self.basic_options_group)

        # Contact analysis options
        self.contact_options_group = QGroupBox("Contact Analysis Options")
        contact_options_layout = QFormLayout(self.contact_options_group)

        # Top contacts count
        self.top_contacts_spin = QSpinBox()
        self.top_contacts_spin.setMinimum(1)
        self.top_contacts_spin.setMaximum(100)
        self.top_contacts_spin.setValue(10)
        contact_options_layout.addRow("Top Contacts:", self.top_contacts_spin)

        # Include incoming checkbox
        self.include_incoming_check = QCheckBox("Include incoming communications")
        self.include_incoming_check.setChecked(True)
        contact_options_layout.addRow(self.include_incoming_check)

        # Include outgoing checkbox
        self.include_outgoing_check = QCheckBox("Include outgoing communications")
        self.include_outgoing_check.setChecked(True)
        contact_options_layout.addRow(self.include_outgoing_check)

        self.options_layout.addWidget(self.contact_options_group)

        # Time analysis options
        self.time_options_group = QGroupBox("Time Analysis Options")
        time_options_layout = QFormLayout(self.time_options_group)

        # Date range
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        time_options_layout.addRow("Start Date:", self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        time_options_layout.addRow("End Date:", self.end_date_edit)

        # Time interval
        self.time_interval_combo = QComboBox()
        self.time_interval_combo.addItem("Hourly", "hour")
        self.time_interval_combo.addItem("Daily", "day")
        self.time_interval_combo.addItem("Weekly", "week")
        self.time_interval_combo.addItem("Monthly", "month")
        time_options_layout.addRow("Time Interval:", self.time_interval_combo)

        self.options_layout.addWidget(self.time_options_group)

        # Initially show only the basic options
        self.contact_options_group.hide()
        self.time_options_group.hide()

        # Progress section
        progress_group = QGroupBox("Analysis Progress")
        progress_layout = QVBoxLayout(progress_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)

        main_layout.addWidget(progress_group)

        # Analysis history section
        history_group = QGroupBox("Analysis History")
        history_layout = QVBoxLayout(history_group)

        # History list
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        history_layout.addWidget(self.history_list)

        main_layout.addWidget(history_group)

        # Button section
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Run analysis button
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setMinimumWidth(150)
        self.run_button.setToolTip("Run the selected analysis with the current options")
        self.run_button.clicked.connect(self._on_run_button_clicked)
        button_layout.addWidget(self.run_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(150)
        self.cancel_button.setToolTip("Cancel the current analysis")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._on_cancel_button_clicked)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    @Slot(int)
    def _on_analysis_type_changed(self, index):
        """
        Handle the analysis type change.

        Args:
            index (int): The index of the selected analysis type
        """
        analysis_type = self.analysis_type_combo.currentData()

        # Show/hide options based on the selected type
        self.basic_options_group.setVisible(analysis_type == "basic")
        self.contact_options_group.setVisible(analysis_type == "contact")
        self.time_options_group.setVisible(analysis_type == "time")

    @Slot()
    def _on_run_button_clicked(self):
        """Handle the run button click."""
        # Get the selected analysis type
        analysis_type = self.analysis_type_combo.currentData()

        # Collect options based on the analysis type
        options = {}

        if analysis_type == "basic":
            options["include_duration"] = self.include_duration_check.isChecked()
            options["include_message_type"] = self.include_message_type_check.isChecked()
            options["group_by"] = self.group_by_combo.currentData()

        elif analysis_type == "contact":
            options["top_contacts"] = self.top_contacts_spin.value()
            options["include_incoming"] = self.include_incoming_check.isChecked()
            options["include_outgoing"] = self.include_outgoing_check.isChecked()

        elif analysis_type == "time":
            options["start_date"] = self.start_date_edit.date().toString(Qt.ISODate)
            options["end_date"] = self.end_date_edit.date().toString(Qt.ISODate)
            options["time_interval"] = self.time_interval_combo.currentData()

        # Update UI
        self.run_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Running analysis...")

        # Add to history
        self._add_to_history(analysis_type, options)

        # Emit the analysis_requested signal
        self.analysis_requested.emit(analysis_type, options)

    @Slot()
    def _on_cancel_button_clicked(self):
        """Handle the cancel button click."""
        # Update UI
        self.run_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Cancelled")

    def _add_to_history(self, analysis_type, options):
        """
        Add an analysis to the history.

        Args:
            analysis_type (str): The type of analysis
            options (dict): The analysis options
        """
        # Create a description of the analysis
        if analysis_type == "basic":
            description = "Basic Statistics"
            if options.get("group_by") != "none":
                description += f" (Grouped by {options['group_by']})"

        elif analysis_type == "contact":
            description = f"Top {options['top_contacts']} Contacts"
            if options.get("include_incoming") and options.get("include_outgoing"):
                description += " (Incoming & Outgoing)"
            elif options.get("include_incoming"):
                description += " (Incoming Only)"
            elif options.get("include_outgoing"):
                description += " (Outgoing Only)"

        elif analysis_type == "time":
            description = f"Time Analysis ({options['time_interval']})"
            description += f" from {options['start_date']} to {options['end_date']}"

        else:
            description = f"Unknown Analysis: {analysis_type}"

        # Add to the history list
        item = QListWidgetItem(description)
        item.setData(Qt.UserRole, {"type": analysis_type, "options": options})
        self.history_list.insertItem(0, item)

        # Add to the history list
        self.analysis_history.insert(0, {"type": analysis_type, "options": options, "description": description})

        # Limit the history to 10 items
        if self.history_list.count() > 10:
            self.history_list.takeItem(10)
            self.analysis_history = self.analysis_history[:10]

    @Slot(QListWidgetItem)
    def _on_history_item_double_clicked(self, item):
        """
        Handle double-clicking a history item.

        Args:
            item (QListWidgetItem): The clicked item
        """
        # Get the analysis data
        data = item.data(Qt.UserRole)

        # Set the analysis type
        index = self.analysis_type_combo.findData(data["type"])
        if index >= 0:
            self.analysis_type_combo.setCurrentIndex(index)

        # Set the options
        options = data["options"]

        if data["type"] == "basic":
            self.include_duration_check.setChecked(options.get("include_duration", True))
            self.include_message_type_check.setChecked(options.get("include_message_type", True))
            index = self.group_by_combo.findData(options.get("group_by", "none"))
            if index >= 0:
                self.group_by_combo.setCurrentIndex(index)

        elif data["type"] == "contact":
            self.top_contacts_spin.setValue(options.get("top_contacts", 10))
            self.include_incoming_check.setChecked(options.get("include_incoming", True))
            self.include_outgoing_check.setChecked(options.get("include_outgoing", True))

        elif data["type"] == "time":
            if "start_date" in options:
                self.start_date_edit.setDate(QDate.fromString(options["start_date"], Qt.ISODate))
            if "end_date" in options:
                self.end_date_edit.setDate(QDate.fromString(options["end_date"], Qt.ISODate))
            index = self.time_interval_combo.findData(options.get("time_interval", "day"))
            if index >= 0:
                self.time_interval_combo.setCurrentIndex(index)

    def set_progress(self, value, status=None):
        """
        Set the progress value and status.

        Args:
            value (int): The progress value (0-100)
            status (str, optional): The status message
        """
        self.progress_bar.setValue(value)

        if status is not None:
            self.status_label.setText(status)

        # If the progress is 100%, enable the run button and disable the cancel button
        if value >= 100:
            self.run_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            if status is None:
                self.status_label.setText("Analysis complete")

    def set_progress_message(self, message):
        """
        Set the progress message.

        Args:
            message (str): The progress message
        """
        self.status_label.setText(message)

    def set_current_file_model(self, file_model):
        """
        Set the current file model.

        Args:
            file_model: The file model to use for analysis
        """
        self.current_file_model = file_model

    @Slot(str)
    def on_analysis_started(self, analysis_type):
        """
        Handle the analysis_started signal from the controller.

        Args:
            analysis_type (str): The type of analysis that was started
        """
        # Update UI
        self.run_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Running {analysis_type} analysis...")

    @Slot(int)
    def on_analysis_progress(self, percent):
        """
        Handle the analysis_progress signal from the controller.

        Args:
            percent (int): The progress percentage (0-100)
        """
        self.progress_bar.setValue(percent)

    @Slot(object)
    def on_analysis_completed(self, result):
        """
        Handle the analysis_completed signal from the controller.

        Args:
            result: The analysis result
        """
        # Update UI
        self.run_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("Analysis complete")

        # Add to history
        analysis_type = result.result_type.name.lower()
        options = {}
        self._add_to_history(analysis_type, options)

    @Slot(str)
    def on_analysis_failed(self, error_message):
        """
        Handle the analysis_failed signal from the controller.

        Args:
            error_message (str): The error message
        """
        # Update UI
        self.run_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Analysis failed")

        # Show error message
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"Analysis failed: {error_message}"
        )


# For testing purposes
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    view = AnalysisView()
    view.show()
    sys.exit(app.exec())
