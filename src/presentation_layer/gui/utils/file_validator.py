# File validation system for GUI core functionality
import os
import pandas as pd
from typing import List
from src.utils.validators import validate_dataframe_columns
from src.utils.data_utils import detect_excel_format

ALLOWED_EXTENSIONS = {".xlsx", ".csv"}
MAX_FILE_SIZE_MB = 10

REQUIRED_COLUMNS = [
    'timestamp',
    'phone_number',
    'message_type'
    # 'message_content' is now optional
]

class FileValidationError(Exception):
    pass

def validate_file_path(file_path: str):
    if not os.path.isfile(file_path):
        raise FileValidationError("File does not exist.")
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError("Unsupported file extension. Only .xlsx and .csv are allowed.")
    if os.path.getsize(file_path) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise FileValidationError("File size exceeds 10MB limit.")
    if ".." in os.path.normpath(file_path).split(os.sep):
        raise FileValidationError("Invalid file path (possible traversal attack).")
    return True

def validate_file_content(file_path: str, required_columns: List[str] = None):
    """
    Validate file content for required columns (headers).
    Only supports .xlsx and .csv files.
    Raises FileValidationError with a specific message if validation fails.
    """
    required_columns = required_columns or REQUIRED_COLUMNS
    ext = file_path.lower().split('.')[-1]
    try:
        if ext == 'xlsx':
            df = pd.read_excel(file_path, nrows=1)
        elif ext == 'csv':
            df = pd.read_csv(file_path, nrows=1)
        else:
            raise FileValidationError("Unsupported file extension for content validation.")
    except Exception as exc:
        raise FileValidationError(f"Failed to read file: {exc}") from exc

    try:
        # This will automatically handle Excel-specific format
        validate_dataframe_columns(df, required_columns)
    except Exception as exc:
        raise FileValidationError(f"Missing required columns: {exc}") from exc
    return True
