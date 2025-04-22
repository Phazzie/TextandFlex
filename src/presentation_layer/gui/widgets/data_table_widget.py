#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Table Widget

This module implements a custom table widget for displaying data.
It extends QTableView with additional features for data display and interaction.
"""

from PySide6.QtWidgets import (
    QTableView, QAbstractItemView, QHeaderView, QMenu,
    QApplication
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, Slot, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem, QKeySequence

# Import UI constants
from ..stylesheets.constants import Colors, Dimensions, Typography


class DataTableWidget(QTableView):
    """
    Custom table widget for displaying data.

    This class extends QTableView with additional features for data display
    and interaction, such as copying selected cells and context menus.
    """

    # Signals
    cell_double_clicked = Signal(int, int, object)  # Row, column, data

    def __init__(self, parent=None):
        """Initialize the data table widget."""
        super().__init__(parent)

        # Set up the table view
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self.doubleClicked.connect(self._on_double_clicked)

        # Set up the header
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)

        # Create the model and proxy model
        self.source_model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setModel(self.proxy_model)

    def set_data(self, headers, data):
        """
        Set the table data.

        Args:
            headers (list): The column headers
            data (list): The data rows (list of lists)
        """
        # Clear the model
        self.source_model.clear()

        # Set the headers
        self.source_model.setHorizontalHeaderLabels(headers)

        # Add the data
        for row_data in data:
            row = []
            for item in row_data:
                std_item = QStandardItem(str(item))
                std_item.setEditable(False)
                row.append(std_item)
            self.source_model.appendRow(row)

        # Resize columns to contents
        self.resizeColumnsToContents()

    def set_filter(self, text, column=-1):
        """
        Set the filter for the table.

        Args:
            text (str): The filter text
            column (int, optional): The column to filter on (-1 for all columns)
        """
        self.proxy_model.setFilterFixedString(text)
        self.proxy_model.setFilterKeyColumn(column)

    def get_selected_rows(self):
        """
        Get the selected rows.

        Returns:
            list: The selected rows as a list of dictionaries
        """
        selected_rows = []

        # Get the selected indexes
        selection = self.selectionModel().selectedRows()

        # Get the headers
        headers = []
        for i in range(self.source_model.columnCount()):
            headers.append(self.source_model.headerData(i, Qt.Horizontal))

        # Get the data for each selected row
        for index in selection:
            row_data = {}
            source_row = self.proxy_model.mapToSource(index).row()

            for col in range(self.source_model.columnCount()):
                header = headers[col]
                value = self.source_model.data(self.source_model.index(source_row, col))
                row_data[header] = value

            selected_rows.append(row_data)

        return selected_rows

    def get_all_data(self):
        """
        Get all the data in the table.

        Returns:
            list: All rows as a list of dictionaries
        """
        all_rows = []

        # Get the headers
        headers = []
        for i in range(self.source_model.columnCount()):
            headers.append(self.source_model.headerData(i, Qt.Horizontal))

        # Get the data for each row
        for row in range(self.source_model.rowCount()):
            row_data = {}

            for col in range(self.source_model.columnCount()):
                header = headers[col]
                value = self.source_model.data(self.source_model.index(row, col))
                row_data[header] = value

            all_rows.append(row_data)

        return all_rows

    def copy_selected_to_clipboard(self):
        """Copy the selected cells to the clipboard."""
        selection = self.selectionModel().selection()
        if not selection:
            return

        # Get the selected ranges
        text = ""
        for range_idx in range(len(selection)):
            model_range = selection[range_idx]

            # Get the data for each cell in the range
            for row in range(model_range.top(), model_range.bottom() + 1):
                row_text = []
                for col in range(model_range.left(), model_range.right() + 1):
                    index = self.model().index(row, col)
                    cell_text = self.model().data(index)
                    row_text.append(str(cell_text))

                text += "\t".join(row_text) + "\n"

        # Copy to clipboard
        QApplication.clipboard().setText(text)

    def keyPressEvent(self, event):
        """
        Handle key press events.

        Args:
            event: The key press event
        """
        # Handle Ctrl+C to copy selected cells
        if event.matches(QKeySequence.Copy):
            self.copy_selected_to_clipboard()
        else:
            super().keyPressEvent(event)

    @Slot(object)
    def _on_context_menu(self, pos):
        """
        Handle context menu requests.

        Args:
            pos: The position of the context menu request
        """
        # Create the context menu
        menu = QMenu(self)

        # Add actions
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_selected_to_clipboard)
        menu.addAction(copy_action)

        # Show the menu
        menu.exec_(self.viewport().mapToGlobal(pos))

    @Slot(object)
    def _on_double_clicked(self, index):
        """
        Handle double-click events.

        Args:
            index: The index that was double-clicked
        """
        # Get the row and column
        row = index.row()
        column = index.column()

        # Get the data
        data = index.data()

        # Emit the signal
        self.cell_double_clicked.emit(row, column, data)


# For testing purposes
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    # Create a main window
    window = QMainWindow()
    window.setWindowTitle("Data Table Widget Test")
    window.resize(800, 600)

    # Create the data table widget
    table = DataTableWidget()

    # Set some test data
    headers = ["Name", "Value", "Type", "Description"]
    data = [
        ["Item 1", "100", "Type A", "Description for item 1"],
        ["Item 2", "200", "Type B", "Description for item 2"],
        ["Item 3", "300", "Type A", "Description for item 3"],
        ["Item 4", "400", "Type C", "Description for item 4"],
        ["Item 5", "500", "Type B", "Description for item 5"],
    ]
    table.set_data(headers, data)

    # Set the table as the central widget
    window.setCentralWidget(table)

    window.show()
    sys.exit(app.exec())
