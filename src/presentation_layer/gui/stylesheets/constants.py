#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI Constants

This module defines constants for the UI, including colors, dimensions, and typography.
These constants are used throughout the application to ensure a consistent look and feel.
"""

from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, QSize

# Color Palette
class Colors:
    """Color constants for the application."""

    # Primary colors
    PRIMARY = QColor(25, 118, 210)  # Blue
    PRIMARY_LIGHT = QColor(64, 196, 255)
    PRIMARY_DARK = QColor(0, 60, 143)

    # Secondary colors
    SECONDARY = QColor(245, 124, 0)  # Orange
    SECONDARY_LIGHT = QColor(255, 175, 64)
    SECONDARY_DARK = QColor(192, 77, 0)

    # Background colors
    BACKGROUND_LIGHT = QColor(250, 250, 250)
    BACKGROUND_DARK = QColor(33, 33, 33)

    # Surface colors (cards, dialogs, etc.)
    SURFACE_LIGHT = QColor(255, 255, 255)
    SURFACE_DARK = QColor(66, 66, 66)

    # Text colors
    TEXT_PRIMARY_LIGHT = QColor(33, 33, 33)
    TEXT_SECONDARY_LIGHT = QColor(117, 117, 117)
    TEXT_DISABLED_LIGHT = QColor(189, 189, 189)

    TEXT_PRIMARY_DARK = QColor(255, 255, 255)
    TEXT_SECONDARY_DARK = QColor(178, 178, 178)
    TEXT_DISABLED_DARK = QColor(97, 97, 97)

    # Error colors
    ERROR = QColor(211, 47, 47)
    ERROR_LIGHT = QColor(244, 67, 54)
    ERROR_DARK = QColor(183, 28, 28)

    # Warning colors
    WARNING = QColor(245, 124, 0)
    WARNING_LIGHT = QColor(255, 152, 0)
    WARNING_DARK = QColor(230, 81, 0)

    # Success colors
    SUCCESS = QColor(46, 125, 50)
    SUCCESS_LIGHT = QColor(76, 175, 80)
    SUCCESS_DARK = QColor(27, 94, 32)

    # Info colors
    INFO = QColor(2, 136, 209)
    INFO_LIGHT = QColor(3, 169, 244)
    INFO_DARK = QColor(1, 87, 155)

    # Divider colors
    DIVIDER_LIGHT = QColor(224, 224, 224)
    DIVIDER_DARK = QColor(97, 97, 97)

    # Chart colors (for data visualization)
    CHART_COLORS = [
        QColor(25, 118, 210),   # Blue
        QColor(245, 124, 0),    # Orange
        QColor(46, 125, 50),    # Green
        QColor(211, 47, 47),    # Red
        QColor(123, 31, 162),   # Purple
        QColor(0, 150, 136),    # Teal
        QColor(255, 193, 7),    # Amber
        QColor(158, 158, 158),  # Grey
    ]


# Dimensions
class Dimensions:
    """Dimension constants for the application."""

    # Spacing
    SPACING_TINY = 4
    SPACING_SMALL = 8
    SPACING_MEDIUM = 16
    SPACING_LARGE = 24
    SPACING_XLARGE = 32

    # Icon sizes
    ICON_TINY = QSize(16, 16)
    ICON_SMALL = QSize(24, 24)
    ICON_MEDIUM = QSize(32, 32)
    ICON_LARGE = QSize(48, 48)
    ICON_XLARGE = QSize(64, 64)

    # Border radius
    BORDER_RADIUS_SMALL = 4
    BORDER_RADIUS_MEDIUM = 8
    BORDER_RADIUS_LARGE = 12

    # Component sizes
    BUTTON_HEIGHT = 36
    INPUT_HEIGHT = 36
    TOOLBAR_HEIGHT = 48
    STATUSBAR_HEIGHT = 24

    # Default window size
    DEFAULT_WINDOW_WIDTH = 1024
    DEFAULT_WINDOW_HEIGHT = 768

    # Minimum window size
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600


# Typography
class Typography:
    """Typography constants for the application."""

    # Font families
    FONT_FAMILY_PRIMARY = "Segoe UI"
    FONT_FAMILY_SECONDARY = "Arial"
    FONT_FAMILY_MONOSPACE = "Consolas"

    # Font sizes
    FONT_SIZE_TINY = 10
    FONT_SIZE_SMALL = 12
    FONT_SIZE_MEDIUM = 14
    FONT_SIZE_LARGE = 16
    FONT_SIZE_XLARGE = 20
    FONT_SIZE_XXLARGE = 24

    # Font weights
    FONT_WEIGHT_LIGHT = QFont.Light
    FONT_WEIGHT_NORMAL = QFont.Normal
    FONT_WEIGHT_MEDIUM = QFont.Medium
    FONT_WEIGHT_BOLD = QFont.Bold

    # Standard fonts
    @staticmethod
    def get_default_font(size=FONT_SIZE_MEDIUM, weight=FONT_WEIGHT_NORMAL):
        """Get the default font with the specified size and weight."""
        font = QFont(Typography.FONT_FAMILY_PRIMARY, size)
        font.setWeight(weight)
        return font

    @staticmethod
    def get_monospace_font(size=FONT_SIZE_MEDIUM):
        """Get a monospace font with the specified size."""
        font = QFont(Typography.FONT_FAMILY_MONOSPACE, size)
        return font

    @staticmethod
    def get_heading_font(level=1):
        """Get a heading font for the specified level (1-6)."""
        sizes = {
            1: Typography.FONT_SIZE_XXLARGE,
            2: Typography.FONT_SIZE_XLARGE,
            3: Typography.FONT_SIZE_LARGE,
            4: Typography.FONT_SIZE_MEDIUM,
            5: Typography.FONT_SIZE_SMALL,
            6: Typography.FONT_SIZE_TINY
        }
        size = sizes.get(level, Typography.FONT_SIZE_MEDIUM)
        font = QFont(Typography.FONT_FAMILY_PRIMARY, size)
        font.setWeight(Typography.FONT_WEIGHT_BOLD)
        return font


# Animation
class Animation:
    """Animation constants for the application."""

    # Duration in milliseconds
    DURATION_FAST = 150
    DURATION_MEDIUM = 300
    DURATION_SLOW = 500

    # Easing curves - using integers for compatibility
    EASING_STANDARD = 2  # Qt.OutCubic
    EASING_ACCELERATE = 0  # Qt.Linear
    EASING_DECELERATE = 0  # Qt.Linear


# Z-Index (for stacking elements)
class ZIndex:
    """Z-index constants for the application."""

    BACKGROUND = -1
    DEFAULT = 0
    CARD = 1
    APPBAR = 10
    DIALOG = 100
    POPUP = 200
    TOOLTIP = 300
    MODAL = 1000
