#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Results View

This module implements the results display view.
It displays analysis results in a tabular format with sorting and filtering.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableView, QHeaderView, QAbstractItemView, QComboBox,
    QLineEdit, QGroupBox, QFormLayout, QSpinBox, QToolBar,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem

# Import UI constants
from ..stylesheets.constants import Colors, Dimensions, Typography


class ResultsView(QWidget):
    """
    Results display view.

    This class implements a view for displaying analysis results in a tabular format.
    It supports sorting, filtering, and pagination of results.
    """

    # Signals
    export_requested = Signal(str, str)  # Emitted when export is requested (format, path)

    def __init__(self, parent=None):
        """Initialize the results view."""
        super().__init__(parent)

        # Initialize UI components
        self._init_ui()

        # Current page and page size
        self.current_page = 0
        self.page_size = 50
        self.total_rows = 0

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

        # Export button
        self.export_button = QPushButton("Export")
        self.export_button.setToolTip("Export the results to a file")
        self.export_button.clicked.connect(self._on_export_button_clicked)
        toolbar.addWidget(self.export_button)

        # Export format combo
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItem("CSV", "csv")
        self.export_format_combo.addItem("Excel", "xlsx")
        self.export_format_combo.addItem("JSON", "json")
        toolbar.addWidget(self.export_format_combo)

        toolbar.addSeparator()

        # Filter label
        filter_label = QLabel("Filter:")
        toolbar.addWidget(filter_label)

        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Enter filter text...")
        self.filter_input.setToolTip("Filter the results by text")
        self.filter_input.textChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.filter_input)

        # Filter column combo
        self.filter_column_combo = QComboBox()
        self.filter_column_combo.addItem("All Columns", -1)
        self.filter_column_combo.currentIndexChanged.connect(self._on_filter_column_changed)
        toolbar.addWidget(self.filter_column_combo)

        main_layout.addWidget(toolbar)

        # Results table
        self.results_table = QTableView()
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_table.setSortingEnabled(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.verticalHeader().setVisible(False)

        # Create the model and proxy model
        self.model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.results_table.setModel(self.proxy_model)

        main_layout.addWidget(self.results_table)

        # Pagination controls
        pagination_layout = QHBoxLayout()

        # Page size
        page_size_layout = QHBoxLayout()
        page_size_layout.addWidget(QLabel("Page Size:"))

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItem("10", 10)
        self.page_size_combo.addItem("25", 25)
        self.page_size_combo.addItem("50", 50)
        self.page_size_combo.addItem("100", 100)
        self.page_size_combo.addItem("All", -1)
        self.page_size_combo.setCurrentIndex(2)  # Default to 50
        self.page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)
        page_size_layout.addWidget(self.page_size_combo)

        pagination_layout.addLayout(page_size_layout)

        pagination_layout.addStretch()

        # Page navigation
        nav_layout = QHBoxLayout()

        self.first_page_button = QPushButton("<<")
        self.first_page_button.clicked.connect(self._on_first_page_clicked)
        nav_layout.addWidget(self.first_page_button)

        self.prev_page_button = QPushButton("<")
        self.prev_page_button.clicked.connect(self._on_prev_page_clicked)
        nav_layout.addWidget(self.prev_page_button)

        self.page_label = QLabel("Page 1 of 1")
        nav_layout.addWidget(self.page_label)

        self.next_page_button = QPushButton(">")
        self.next_page_button.clicked.connect(self._on_next_page_clicked)
        nav_layout.addWidget(self.next_page_button)

        self.last_page_button = QPushButton(">>")
        self.last_page_button.clicked.connect(self._on_last_page_clicked)
        nav_layout.addWidget(self.last_page_button)

        pagination_layout.addLayout(nav_layout)

        main_layout.addLayout(pagination_layout)

        # Status bar
        self.status_label = QLabel("No results to display")
        main_layout.addWidget(self.status_label)

    def set_results(self, headers, data):
        """
        Set the results data.

        Args:
            headers (list): The column headers
            data (list): The data rows (list of lists)
        """
        # Clear the model
        self.model.clear()

        # Set the headers
        self.model.setHorizontalHeaderLabels(headers)

        # Update the filter column combo
        self.filter_column_combo.clear()
        self.filter_column_combo.addItem("All Columns", -1)
        for i, header in enumerate(headers):
            self.filter_column_combo.addItem(header, i)

        # Add the data
        self.total_rows = len(data)

        for row_data in data:
            row = []
            for item in row_data:
                std_item = QStandardItem(str(item))
                std_item.setEditable(False)
                row.append(std_item)
            self.model.appendRow(row)

        # Reset pagination
        self.current_page = 0
        self._update_pagination()

        # Update status
        self.status_label.setText(f"Displaying {min(self.page_size, self.total_rows)} of {self.total_rows} results")

        # Resize columns to contents
        self.results_table.resizeColumnsToContents()

    def _on_filter_changed(self, text):
        """
        Handle filter text changes.

        Args:
            text (str): The new filter text
        """
        self.proxy_model.setFilterFixedString(text)
        self._update_pagination()

    def _on_filter_column_changed(self, index):
        """
        Handle filter column changes.

        Args:
            index (int): The index of the selected column
        """
        column = self.filter_column_combo.currentData()
        self.proxy_model.setFilterKeyColumn(column)
        self._update_pagination()

    def _on_page_size_changed(self, index):
        """
        Handle page size changes.

        Args:
            index (int): The index of the selected page size
        """
        self.page_size = self.page_size_combo.currentData()
        self.current_page = 0
        self._update_pagination()

    def _on_first_page_clicked(self):
        """Handle first page button click."""
        self.current_page = 0
        self._update_pagination()

    def _on_prev_page_clicked(self):
        """Handle previous page button click."""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_pagination()

    def _on_next_page_clicked(self):
        """Handle next page button click."""
        if self.page_size > 0:
            max_page = (self.proxy_model.rowCount() - 1) // self.page_size
            if self.current_page < max_page:
                self.current_page += 1
                self._update_pagination()

    def _on_last_page_clicked(self):
        """Handle last page button click."""
        if self.page_size > 0:
            self.current_page = (self.proxy_model.rowCount() - 1) // self.page_size
            self._update_pagination()

    def _update_pagination(self):
        """Update the pagination controls and visible rows."""
        row_count = self.proxy_model.rowCount()

        # Update the page label
        if self.page_size <= 0:
            # Show all rows
            self.page_label.setText("Showing all results")
            self.first_page_button.setEnabled(False)
            self.prev_page_button.setEnabled(False)
            self.next_page_button.setEnabled(False)
            self.last_page_button.setEnabled(False)
        else:
            # Calculate the total number of pages
            total_pages = (row_count + self.page_size - 1) // self.page_size

            # Ensure current_page is valid
            if total_pages == 0:
                self.current_page = 0
            elif self.current_page >= total_pages:
                self.current_page = total_pages - 1

            # Update the page label
            self.page_label.setText(f"Page {self.current_page + 1} of {max(1, total_pages)}")

            # Enable/disable navigation buttons
            self.first_page_button.setEnabled(self.current_page > 0)
            self.prev_page_button.setEnabled(self.current_page > 0)
            self.next_page_button.setEnabled(self.current_page < total_pages - 1)
            self.last_page_button.setEnabled(self.current_page < total_pages - 1)

        # Update the status label
        if row_count == 0:
            self.status_label.setText("No results to display")
        elif self.page_size <= 0:
            self.status_label.setText(f"Displaying all {row_count} results")
        else:
            start = self.current_page * self.page_size + 1
            end = min(start + self.page_size - 1, row_count)
            self.status_label.setText(f"Displaying {start}-{end} of {row_count} results")

    def _on_export_button_clicked(self):
        """Handle export button click."""
        # Get the export format
        export_format = self.export_format_combo.currentData()

        # Get the file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "",
            f"{export_format.upper()} Files (*.{export_format});;All Files (*)"
        )

        if file_path:
            # Ensure the file has the correct extension
            if not file_path.lower().endswith(f".{export_format}"):
                file_path += f".{export_format}"

            # Emit the export_requested signal
            self.export_requested.emit(export_format, file_path)


# For testing purposes
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    view = ResultsView()

    # Set some test data
    headers = ["Name", "Value", "Type", "Description"]
    data = [
        ["Item 1", "100", "Type A", "Description for item 1"],
        ["Item 2", "200", "Type B", "Description for item 2"],
        ["Item 3", "300", "Type A", "Description for item 3"],
        ["Item 4", "400", "Type C", "Description for item 4"],
        ["Item 5", "500", "Type B", "Description for item 5"],
    ]
    view.set_results(headers, data)

    view.show()
    sys.exit(app.exec())
