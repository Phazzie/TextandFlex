import os
import tempfile
import pandas as pd
import pytest
from src.presentation_layer.gui.utils.file_validator import (
    validate_file_path,
    validate_file_content,
    FileValidationError,
    REQUIRED_COLUMNS
)

def test_validate_file_path_valid(tmp_path):
    # Create a valid dummy file
    file_path = tmp_path / "test.csv"
    file_path.write_text("header1,header2\nval1,val2\n")
    # Should not raise
    validate_file_path(str(file_path))

def test_validate_file_path_invalid_extension(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("foo")
    with pytest.raises(FileValidationError):
        validate_file_path(str(file_path))

def test_validate_file_path_too_large(tmp_path):
    file_path = tmp_path / "test.csv"
    file_path.write_bytes(b"0" * (10 * 1024 * 1024 + 1))
    with pytest.raises(FileValidationError):
        validate_file_path(str(file_path))

def test_validate_file_path_traversal(tmp_path):
    # Simulate traversal
    with pytest.raises(FileValidationError):
        validate_file_path("../test.csv")

def test_validate_file_content_valid_csv(tmp_path):
    file_path = tmp_path / "test.csv"
    df = pd.DataFrame({col: ["val"] for col in REQUIRED_COLUMNS})
    df.to_csv(file_path, index=False)
    assert validate_file_content(str(file_path))

def test_validate_file_content_missing_column(tmp_path):
    file_path = tmp_path / "test.csv"
    df = pd.DataFrame({"timestamp": ["val"]})
    df.to_csv(file_path, index=False)
    with pytest.raises(FileValidationError):
        validate_file_content(str(file_path))

def test_validate_file_content_invalid_file(tmp_path):
    file_path = tmp_path / "test.csv"
    file_path.write_text("")  # Empty file
    with pytest.raises(FileValidationError):
        validate_file_content(str(file_path))
