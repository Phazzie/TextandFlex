"""
Tests for the file I/O utilities.
"""
import os
import pytest
import json
import pickle
from unittest.mock import patch, mock_open
import tempfile
from pathlib import Path

@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name

    yield temp_path

    # Clean up after the test
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after the test
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {
        "name": "test_dataset",
        "metadata": {
            "created_at": "2023-01-01T12:00:00",
            "record_count": 3
        },
        "column_mapping": {
            "timestamp": "date",
            "phone_number": "contact"
        }
    }

@pytest.mark.unit
def test_ensure_directory_exists(temp_dir):
    """Test ensuring a directory exists."""
    from src.utils.file_io import ensure_directory_exists

    # Test with an existing directory
    result = ensure_directory_exists(temp_dir)
    assert result is True
    assert os.path.exists(temp_dir)

    # Test with a new directory
    new_dir = os.path.join(temp_dir, "new_dir")
    result = ensure_directory_exists(new_dir)
    assert result is True
    assert os.path.exists(new_dir)

@pytest.mark.unit
def test_ensure_directory_exists_error():
    """Test ensuring a directory exists with an error."""
    from src.utils.file_io import ensure_directory_exists

    # Mock os.makedirs to raise an exception
    with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
        result = ensure_directory_exists("/invalid/path")
        assert result is False

@pytest.mark.unit
def test_save_json(temp_file, sample_data):
    """Test saving data to a JSON file."""
    from src.utils.file_io import save_json

    # Save data to file
    result = save_json(sample_data, temp_file)

    # Verify the result
    assert result is True

    # Verify the file was created
    assert os.path.exists(temp_file)

    # Verify the file contents
    with open(temp_file, 'r') as f:
        loaded_data = json.load(f)
        assert loaded_data == sample_data

@pytest.mark.unit
def test_save_json_error(sample_data):
    """Test saving data to a JSON file with an error."""
    from src.utils.file_io import save_json

    # Mock open to raise an exception
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        result = save_json(sample_data, "/invalid/path")
        assert result is False

@pytest.mark.unit
def test_load_json(temp_file, sample_data):
    """Test loading data from a JSON file."""
    from src.utils.file_io import load_json

    # Save data to file
    with open(temp_file, 'w') as f:
        json.dump(sample_data, f)

    # Load data from file
    result = load_json(temp_file)

    # Verify the result
    assert result == sample_data

@pytest.mark.unit
def test_load_json_file_not_found():
    """Test loading data from a non-existent JSON file."""
    from src.utils.file_io import load_json

    # Load data from a non-existent file
    result = load_json("/non/existent/file.json")

    # Verify the result
    assert result is None

@pytest.mark.unit
def test_load_json_error():
    """Test loading data from a JSON file with an error."""
    from src.utils.file_io import load_json

    # Mock open to raise an exception
    with patch('builtins.open', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
        result = load_json("/invalid/file.json")
        assert result is None

@pytest.mark.unit
def test_save_pickle(temp_file, sample_data):
    """Test saving data to a pickle file."""
    from src.utils.file_io import save_pickle

    # Save data to file
    result = save_pickle(sample_data, temp_file)

    # Verify the result
    assert result is True

    # Verify the file was created
    assert os.path.exists(temp_file)

    # Verify the file contents
    with open(temp_file, 'rb') as f:
        loaded_data = pickle.load(f)
        assert loaded_data == sample_data

@pytest.mark.unit
def test_save_pickle_error(sample_data):
    """Test saving data to a pickle file with an error."""
    from src.utils.file_io import save_pickle

    # Mock open to raise an exception
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        result = save_pickle(sample_data, "/invalid/path")
        assert result is False

@pytest.mark.unit
def test_load_pickle(temp_file, sample_data):
    """Test loading data from a pickle file."""
    from src.utils.file_io import load_pickle

    # Save data to file
    with open(temp_file, 'wb') as f:
        pickle.dump(sample_data, f)

    # Load data from file
    result = load_pickle(temp_file)

    # Verify the result
    assert result == sample_data

@pytest.mark.unit
def test_load_pickle_file_not_found():
    """Test loading data from a non-existent pickle file."""
    from src.utils.file_io import load_pickle

    # Load data from a non-existent file
    result = load_pickle("/non/existent/file.pkl")

    # Verify the result
    assert result is None

@pytest.mark.unit
def test_load_pickle_error():
    """Test loading data from a pickle file with an error."""
    from src.utils.file_io import load_pickle

    # Mock open to raise an exception
    with patch('builtins.open', side_effect=pickle.UnpicklingError("Invalid pickle")):
        result = load_pickle("/invalid/file.pkl")
        assert result is None

@pytest.mark.unit
def test_save_compressed_pickle(temp_file, sample_data):
    """Test saving data to a compressed pickle file."""
    from src.utils.file_io import save_compressed_pickle

    # Save data to file
    result = save_compressed_pickle(sample_data, temp_file)

    # Verify the result
    assert result is True

    # Verify the file was created
    assert os.path.exists(temp_file)

@pytest.mark.unit
def test_load_compressed_pickle(temp_file, sample_data):
    """Test loading data from a compressed pickle file."""
    from src.utils.file_io import save_compressed_pickle, load_compressed_pickle

    # Save data to file
    save_compressed_pickle(sample_data, temp_file)

    # Load data from file
    result = load_compressed_pickle(temp_file)

    # Verify the result
    assert result == sample_data
