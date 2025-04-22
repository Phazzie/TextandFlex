#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI Converter Script

This script converts Qt Designer .ui files to Python code.
It can be run directly to convert all .ui files in the ui directory,
or imported and used programmatically.
"""

import os
import sys
import glob
from pathlib import Path

# Determine if we're using PySide6 or PyQt6
try:
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtCore import QFile, QIODevice
    from PySide6 import QtCore
    USE_PYSIDE = True
except ImportError:
    try:
        from PyQt6.uic import compileUi
        USE_PYSIDE = False
    except ImportError:
        print("Error: Neither PySide6 nor PyQt6 is installed.")
        sys.exit(1)

# Get the absolute path to the ui directory
SCRIPT_DIR = Path(__file__).resolve().parent
UI_DIR = SCRIPT_DIR
PYTHON_DIR = SCRIPT_DIR.parent / "views"


def convert_ui_file(ui_file, py_file=None, use_pyside=USE_PYSIDE):
    """
    Convert a .ui file to a Python file.
    
    Args:
        ui_file (str): Path to the .ui file
        py_file (str, optional): Path to the output Python file. If None, 
                                 it will be derived from the ui_file.
        use_pyside (bool, optional): Whether to use PySide6 or PyQt6.
    
    Returns:
        str: Path to the generated Python file
    """
    ui_path = Path(ui_file)
    
    if py_file is None:
        py_file = PYTHON_DIR / f"ui_{ui_path.stem}.py"
    else:
        py_file = Path(py_file)
    
    # Create the output directory if it doesn't exist
    py_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Converting {ui_path} to {py_file}")
    
    if use_pyside:
        # PySide6 approach
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-

\"\"\"
This file was automatically generated from {ui_path.name}
DO NOT EDIT MANUALLY unless you know what you're doing!
\"\"\"

import os
from pathlib import Path
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice, QMetaObject

class Ui_{ui_path.stem}:
    \"\"\"
    UI class for {ui_path.stem}
    \"\"\"
    def __init__(self):
        # Get the directory where this script is located
        self.script_dir = Path(__file__).resolve().parent
        self.ui_file_path = self.script_dir.parent / "ui" / "{ui_path.name}"
        
    def setupUi(self, widget):
        \"\"\"
        Set up the UI for the given widget
        
        Args:
            widget: The widget to set up the UI for
        \"\"\"
        ui_file = QFile(str(self.ui_file_path))
        if not ui_file.open(QIODevice.ReadOnly):
            raise RuntimeError(f"Cannot open {{self.ui_file_path}}: {{ui_file.errorString()}}")
        
        loader = QUiLoader()
        self.ui = loader.load(ui_file, widget)
        ui_file.close()
        
        if not self.ui:
            raise RuntimeError(loader.errorString())
        
        # Set up any additional connections or customizations here
        self.connectSignalsSlots()
        
        return self.ui
    
    def connectSignalsSlots(self):
        \"\"\"
        Connect signals and slots for the UI
        \"\"\"
        pass  # Implement in subclasses
""")
    else:
        # PyQt6 approach
        with open(ui_file, 'r', encoding='utf-8') as ui_file_obj:
            with open(py_file, 'w', encoding='utf-8') as py_file_obj:
                py_file_obj.write(f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-

\"\"\"
This file was automatically generated from {ui_path.name}
DO NOT EDIT MANUALLY unless you know what you're doing!
\"\"\"

""")
                compileUi(ui_file_obj, py_file_obj, from_imports=True)
    
    return str(py_file)


def convert_all_ui_files(ui_dir=UI_DIR, python_dir=PYTHON_DIR, use_pyside=USE_PYSIDE):
    """
    Convert all .ui files in the given directory to Python files.
    
    Args:
        ui_dir (str or Path): Directory containing .ui files
        python_dir (str or Path): Directory to output Python files
        use_pyside (bool, optional): Whether to use PySide6 or PyQt6.
    
    Returns:
        list: List of generated Python files
    """
    ui_dir = Path(ui_dir)
    python_dir = Path(python_dir)
    
    # Create the output directory if it doesn't exist
    python_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    for ui_file in ui_dir.glob("*.ui"):
        py_file = python_dir / f"ui_{ui_file.stem}.py"
        generated_files.append(convert_ui_file(ui_file, py_file, use_pyside))
    
    return generated_files


if __name__ == "__main__":
    # If run directly, convert all .ui files in the ui directory
    generated_files = convert_all_ui_files()
    print(f"Generated {len(generated_files)} Python files:")
    for file in generated_files:
        print(f"  {file}")
