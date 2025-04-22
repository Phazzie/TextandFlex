#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Resource Compiler Script

This script compiles Qt resource files (.qrc) to Python modules.
It can be run directly to compile all .qrc files in the resources directory,
or imported and used programmatically.
"""

import os
import sys
import subprocess
from pathlib import Path

# Get the absolute path to the resources directory
SCRIPT_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = SCRIPT_DIR


def compile_resource_file(qrc_file, py_file=None):
    """
    Compile a .qrc file to a Python file.
    
    Args:
        qrc_file (str): Path to the .qrc file
        py_file (str, optional): Path to the output Python file. If None, 
                                 it will be derived from the qrc_file.
    
    Returns:
        str: Path to the generated Python file
    """
    qrc_path = Path(qrc_file)
    
    if py_file is None:
        py_file = qrc_path.with_name(f"{qrc_path.stem}_rc.py")
    else:
        py_file = Path(py_file)
    
    # Create the output directory if it doesn't exist
    py_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Compiling {qrc_path} to {py_file}")
    
    # Try PySide6 first, then PyQt6
    try:
        # PySide6 approach
        from PySide6.QtCore import QDir
        result = subprocess.run(
            ["pyside6-rcc", str(qrc_path), "-o", str(py_file)],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return str(py_file)
    except (ImportError, subprocess.CalledProcessError) as e:
        print(f"PySide6 compilation failed: {e}")
        try:
            # PyQt6 approach
            result = subprocess.run(
                ["pyrcc6", str(qrc_path), "-o", str(py_file)],
                check=True,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            return str(py_file)
        except (ImportError, subprocess.CalledProcessError) as e:
            print(f"PyQt6 compilation failed: {e}")
            print("Error: Failed to compile resource file. Make sure PySide6 or PyQt6 is installed.")
            return None


def compile_all_resource_files(resources_dir=RESOURCES_DIR):
    """
    Compile all .qrc files in the given directory to Python files.
    
    Args:
        resources_dir (str or Path): Directory containing .qrc files
    
    Returns:
        list: List of generated Python files
    """
    resources_dir = Path(resources_dir)
    
    generated_files = []
    for qrc_file in resources_dir.glob("*.qrc"):
        py_file = compile_resource_file(qrc_file)
        if py_file:
            generated_files.append(py_file)
    
    return generated_files


def create_default_resource_file(resources_dir=RESOURCES_DIR):
    """
    Create a default resource file if none exists.
    
    Args:
        resources_dir (str or Path): Directory to create the resource file in
    
    Returns:
        str: Path to the created resource file
    """
    resources_dir = Path(resources_dir)
    qrc_file = resources_dir / "app_resources.qrc"
    
    if qrc_file.exists():
        print(f"Resource file {qrc_file} already exists.")
        return str(qrc_file)
    
    # Create the icons directory if it doesn't exist
    icons_dir = resources_dir / "icons"
    icons_dir.mkdir(exist_ok=True)
    
    # Create the images directory if it doesn't exist
    images_dir = resources_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    # Create a default resource file
    with open(qrc_file, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE RCC>
<RCC version="1.0">
    <qresource prefix="/icons">
        <!-- Add your icons here -->
        <!-- Example: <file>icons/app_icon.png</file> -->
    </qresource>
    <qresource prefix="/images">
        <!-- Add your images here -->
        <!-- Example: <file>images/splash.png</file> -->
    </qresource>
    <qresource prefix="/styles">
        <!-- Add your stylesheets here -->
        <!-- Example: <file>../stylesheets/dark_theme.qss</file> -->
    </qresource>
</RCC>
""")
    
    print(f"Created default resource file: {qrc_file}")
    return str(qrc_file)


if __name__ == "__main__":
    # If run directly, create a default resource file if none exists
    # and compile all .qrc files in the resources directory
    create_default_resource_file()
    generated_files = compile_all_resource_files()
    print(f"Generated {len(generated_files)} Python files:")
    for file in generated_files:
        print(f"  {file}")
