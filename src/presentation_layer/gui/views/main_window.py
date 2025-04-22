#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main Window

This module implements the main application window using PySide6.
It serves as the container for all other UI components.
"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QStackedWidget, QToolBar,
    QStatusBar, QMenuBar, QMenu, QMessageBox,
    QFileDialog, QDockWidget, QWidget
)
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtCore import Qt, Signal, Slot, QSize

# Import UI constants
from ..stylesheets.constants import Colors, Dimensions, Typography


class MainWindow(QMainWindow):
    """
    Main application window.

    This class implements the main window of the application, including
    the menu bar, toolbar, status bar, and central widget.
    """

    # Signals
    file_opened = Signal(str)  # Emitted when a file is opened
    analysis_requested = Signal(str, dict)  # Emitted when analysis is requested

    def __init__(self, parent=None):
        """Initialize the main window."""
        super().__init__(parent)

        # Set window properties
        self.setWindowTitle("TextandFlex Phone Analyzer")
        self.setMinimumSize(Dimensions.MIN_WINDOW_WIDTH, Dimensions.MIN_WINDOW_HEIGHT)
        self.resize(Dimensions.DEFAULT_WINDOW_WIDTH, Dimensions.DEFAULT_WINDOW_HEIGHT)

        # Initialize UI components
        self._init_central_widget()
        self._init_menu_bar()
        self._init_toolbar()
        self._init_status_bar()

        # Set up the initial status message
        self.statusBar().showMessage("Ready")

    def _init_central_widget(self):
        """Initialize the central widget."""
        # Create a stacked widget to hold different views
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        # Create a placeholder widget
        placeholder = QWidget()
        self.stacked_widget.addWidget(placeholder)

    def _init_menu_bar(self):
        """Initialize the menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")

        # Open action
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Open a phone records file")
        open_action.triggered.connect(self.on_open_file)
        file_menu.addAction(open_action)

        # Recent files submenu
        self.recent_files_menu = QMenu("Recent Files", self)
        file_menu.addMenu(self.recent_files_menu)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Analysis menu
        analysis_menu = self.menuBar().addMenu("&Analysis")

        # Basic statistics action
        basic_stats_action = QAction("&Basic Statistics", self)
        basic_stats_action.setStatusTip("Perform basic statistical analysis")
        basic_stats_action.triggered.connect(lambda: self.on_analysis_requested("basic"))
        analysis_menu.addAction(basic_stats_action)

        # Contact analysis action
        contact_analysis_action = QAction("&Contact Analysis", self)
        contact_analysis_action.setStatusTip("Perform contact-based analysis")
        contact_analysis_action.triggered.connect(lambda: self.on_analysis_requested("contact"))
        analysis_menu.addAction(contact_analysis_action)

        # Time analysis action
        time_analysis_action = QAction("&Time Analysis", self)
        time_analysis_action.setStatusTip("Perform time-based analysis")
        time_analysis_action.triggered.connect(lambda: self.on_analysis_requested("time"))
        analysis_menu.addAction(time_analysis_action)

        # View menu
        view_menu = self.menuBar().addMenu("&View")

        # Help menu
        help_menu = self.menuBar().addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("Show information about the application")
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)

    def _init_toolbar(self):
        """Initialize the toolbar."""
        # Create the main toolbar
        self.toolbar = QToolBar("Main Toolbar", self)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(Dimensions.ICON_SMALL)
        self.addToolBar(self.toolbar)

        # Add actions to the toolbar
        # Open action
        open_action = QAction("Open", self)
        open_action.setStatusTip("Open a phone records file")
        open_action.triggered.connect(self.on_open_file)
        self.toolbar.addAction(open_action)

        self.toolbar.addSeparator()

        # Analysis actions
        basic_stats_action = QAction("Basic Stats", self)
        basic_stats_action.setStatusTip("Perform basic statistical analysis")
        basic_stats_action.triggered.connect(lambda: self.on_analysis_requested("basic"))
        self.toolbar.addAction(basic_stats_action)

        contact_analysis_action = QAction("Contact Analysis", self)
        contact_analysis_action.setStatusTip("Perform contact-based analysis")
        contact_analysis_action.triggered.connect(lambda: self.on_analysis_requested("contact"))
        self.toolbar.addAction(contact_analysis_action)

        time_analysis_action = QAction("Time Analysis", self)
        time_analysis_action.setStatusTip("Perform time-based analysis")
        time_analysis_action.triggered.connect(lambda: self.on_analysis_requested("time"))
        self.toolbar.addAction(time_analysis_action)

    def _init_status_bar(self):
        """Initialize the status bar."""
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

    @Slot()
    def on_open_file(self):
        """Handle the open file action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Phone Records File",
            "",
            "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            # Emit the file_opened signal
            self.file_opened.emit(file_path)
            self.statusBar().showMessage(f"Opened: {file_path}")

    @Slot(str)
    def on_analysis_requested(self, analysis_type, options=None):
        """
        Handle the analysis requested action.

        Args:
            analysis_type (str): The type of analysis to perform
            options (dict, optional): Additional options for the analysis
        """
        if options is None:
            options = {}

        # Emit the analysis_requested signal
        self.analysis_requested.emit(analysis_type, options)
        self.statusBar().showMessage(f"Performing {analysis_type} analysis...")

    @Slot()
    def on_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About TextandFlex Phone Analyzer",
            """<h1>TextandFlex Phone Analyzer</h1>
            <p>Version 1.0</p>
            <p>A tool for analyzing phone records data.</p>
            <p>Copyright &copy; 2023</p>"""
        )

    def add_view(self, view, name):
        """
        Add a view to the stacked widget.

        Args:
            view (QWidget): The view to add
            name (str): The name of the view

        Returns:
            int: The index of the added view
        """
        view.setObjectName(name)
        return self.stacked_widget.addWidget(view)

    def show_view(self, index_or_name):
        """
        Show the specified view.

        Args:
            index_or_name (int or str): The index or name of the view to show
        """
        if isinstance(index_or_name, str):
            # Find the widget by name
            for i in range(self.stacked_widget.count()):
                if self.stacked_widget.widget(i).objectName() == index_or_name:
                    self.stacked_widget.setCurrentIndex(i)
                    return
            raise ValueError(f"View '{index_or_name}' not found")
        else:
            # Use the index directly
            self.stacked_widget.setCurrentIndex(index_or_name)

    def current_view(self):
        """
        Get the current view.

        Returns:
            QWidget: The current view
        """
        return self.stacked_widget.currentWidget()

    def current_view_index(self):
        """
        Get the index of the current view.

        Returns:
            int: The index of the current view
        """
        return self.stacked_widget.currentIndex()


# For testing purposes
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
