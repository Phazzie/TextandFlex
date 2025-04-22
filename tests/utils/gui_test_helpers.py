"""
Helper utilities for GUI testing.
"""
import os
import sys
import time
import pytest
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, Union

from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QComboBox
from PySide6.QtTest import QTest


def wait_for(condition: Callable[[], bool], timeout: int = 5000, interval: int = 100) -> bool:
    """
    Wait for a condition to be true.
    
    Args:
        condition: A callable that returns a boolean
        timeout: Maximum time to wait in milliseconds
        interval: Check interval in milliseconds
        
    Returns:
        True if the condition was met, False if timeout occurred
    """
    elapsed = 0
    while elapsed < timeout:
        if condition():
            return True
        QTest.qWait(interval)
        elapsed += interval
    return False


def find_widget(parent: QWidget, widget_type: type, name: Optional[str] = None) -> Optional[QWidget]:
    """
    Find a widget of a specific type and optionally with a specific name.
    
    Args:
        parent: The parent widget to search in
        widget_type: The type of widget to find
        name: Optional object name of the widget
        
    Returns:
        The found widget or None if not found
    """
    for widget in parent.findChildren(widget_type):
        if name is None or widget.objectName() == name:
            return widget
    return None


def click_button(qtbot, button: QPushButton) -> None:
    """
    Click a button and wait for it to process.
    
    Args:
        qtbot: The qtbot fixture
        button: The button to click
    """
    qtbot.mouseClick(button, Qt.LeftButton)
    qtbot.wait(100)  # Wait for the click to be processed


def enter_text(qtbot, text_edit: QLineEdit, text: str) -> None:
    """
    Enter text into a QLineEdit.
    
    Args:
        qtbot: The qtbot fixture
        text_edit: The QLineEdit to enter text into
        text: The text to enter
    """
    text_edit.clear()
    qtbot.keyClicks(text_edit, text)
    qtbot.wait(100)  # Wait for the text to be processed


def select_combo_item(qtbot, combo_box: QComboBox, index: int) -> None:
    """
    Select an item in a QComboBox by index.
    
    Args:
        qtbot: The qtbot fixture
        combo_box: The QComboBox to select from
        index: The index of the item to select
    """
    combo_box.setCurrentIndex(index)
    qtbot.wait(100)  # Wait for the selection to be processed


def select_combo_text(qtbot, combo_box: QComboBox, text: str) -> None:
    """
    Select an item in a QComboBox by text.
    
    Args:
        qtbot: The qtbot fixture
        combo_box: The QComboBox to select from
        text: The text of the item to select
    """
    index = combo_box.findText(text)
    if index >= 0:
        combo_box.setCurrentIndex(index)
        qtbot.wait(100)  # Wait for the selection to be processed


def create_test_file(path: str, content: Any) -> str:
    """
    Create a test file with the given content.
    
    Args:
        path: The path to create the file at
        content: The content to write to the file
        
    Returns:
        The path to the created file
    """
    import pandas as pd
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Write the content to the file
    if isinstance(content, pd.DataFrame):
        content.to_excel(path, index=False)
    else:
        with open(path, 'w') as f:
            f.write(str(content))
            
    return path


def create_sample_dataframe() -> 'pd.DataFrame':
    """
    Create a sample dataframe for testing.
    
    Returns:
        A sample dataframe
    """
    import pandas as pd
    
    return pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00', '2023-01-01 12:30:00', '2023-01-01 13:00:00'],
        'phone_number': ['1234567890', '9876543210', '5551234567'],
        'message_type': ['sent', 'received', 'sent'],
        'message_content': ['Hello, world!', 'Hi there!', 'How are you?']
    })


def create_sample_excel_file(path: str) -> str:
    """
    Create a sample Excel file for testing.
    
    Args:
        path: The path to create the file at
        
    Returns:
        The path to the created file
    """
    df = create_sample_dataframe()
    return create_test_file(path, df)
