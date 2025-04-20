"""
Tests for the configuration management system.
"""
import os
import json
import pytest
from unittest.mock import patch, mock_open


@pytest.mark.unit
def test_config_initialization():
    """Test that ConfigManager initializes with default values."""
    # Import here to ensure we're testing the implementation
    from src.config import ConfigManager

    config = ConfigManager()
    assert config is not None
    assert hasattr(config, 'get')
    assert hasattr(config, 'set')
    assert hasattr(config, 'load')
    assert hasattr(config, 'save')


@pytest.mark.unit
def test_config_default_values():
    """Test that default configuration values are set correctly."""
    from src.config import ConfigManager, DEFAULT_CONFIG

    config = ConfigManager()

    # Check that all default values are accessible
    assert config.get('logging.level') == DEFAULT_CONFIG['logging']['level']
    assert config.get('data.excel.required_columns') == DEFAULT_CONFIG['data']['excel']['required_columns']
    assert config.get('analysis.cache_results') == DEFAULT_CONFIG['analysis']['cache_results']

    # Test non-existent key returns None
    assert config.get('non.existent.key') is None

    # Test non-existent key with default value
    assert config.get('non.existent.key', 'default') == 'default'


@pytest.mark.unit
def test_config_set_and_get():
    """Test setting and getting configuration values."""
    from src.config import ConfigManager

    config = ConfigManager()

    # Set and get a simple value
    config.set('test.key', 'test_value')
    assert config.get('test.key') == 'test_value'

    # Set and get a nested value
    config.set('test.nested.key', 'nested_value')
    assert config.get('test.nested.key') == 'nested_value'

    # Override an existing value
    config.set('logging.level', 'DEBUG')
    assert config.get('logging.level') == 'DEBUG'


@pytest.mark.unit
def test_config_load_from_file(temp_file, sample_config_dict):
    """Test loading configuration from a file."""
    from src.config import ConfigManager

    # Write sample config to temp file
    with open(temp_file, 'w') as f:
        json.dump(sample_config_dict, f)

    # Load config from file
    config = ConfigManager()
    config.load(temp_file)

    # Verify loaded values
    assert config.get('logging.level') == sample_config_dict['logging']['level']
    assert config.get('data.excel.required_columns') == sample_config_dict['data']['excel']['required_columns']
    assert config.get('analysis.cache_results') == sample_config_dict['analysis']['cache_results']


@pytest.mark.unit
def test_config_load_invalid_file():
    """Test loading configuration from an invalid file."""
    from src.config import ConfigManager, ConfigError

    config = ConfigManager()

    # Test with non-existent file
    with pytest.raises(ConfigError):
        config.load('non_existent_file.json')

    # Test with invalid JSON
    with patch('builtins.open', mock_open(read_data='invalid json')):
        with pytest.raises(ConfigError):
            config.load('invalid.json')


@pytest.mark.unit
def test_config_save_to_file(temp_file):
    """Test saving configuration to a file."""
    from src.config import ConfigManager

    config = ConfigManager()
    config.set('test.key', 'test_value')

    # Save config to file
    config.save(temp_file)

    # Load the file and verify content
    with open(temp_file, 'r') as f:
        saved_config = json.load(f)

    assert 'test' in saved_config
    assert 'key' in saved_config['test']
    assert saved_config['test']['key'] == 'test_value'


@pytest.mark.unit
def test_config_load_from_env():
    """Test loading configuration from environment variables."""
    from src.config import ConfigManager

    # Create a fresh config for this test
    config = ConfigManager()

    # Set environment variables
    env_vars = {
        'PHONE_ANALYZER_LOGGING_LEVEL': 'DEBUG',
        'PHONE_ANALYZER_DATA_EXCEL_DATE_FORMAT': '%d/%m/%Y',
        'PHONE_ANALYZER_ANALYSIS_CACHE_RESULTS': 'False'
    }

    with patch.dict(os.environ, env_vars):
        # Load from environment
        config.load_from_env()

        # Verify values from environment
        assert config.get('logging.level') == 'DEBUG'
        # The date format is stored in a nested structure
        assert config.get('data.excel.date.format') == '%d/%m/%Y'
        # The cache_results is stored in a nested structure
        assert config.get('analysis.cache.results') is False  # Should be converted to boolean


@pytest.mark.unit
def test_config_validation():
    """Test configuration validation."""
    from src.config import ConfigManager, ConfigError

    config = ConfigManager()

    # Test with invalid logging level
    config.set('logging.level', 'INVALID_LEVEL')
    with pytest.raises(ConfigError):
        config.validate()

    # Fix the logging level and test with invalid date format
    config.set('logging.level', 'INFO')
    config.set('data.excel.date_format', None)  # Set to None to trigger validation error
    with pytest.raises(ConfigError):
        config.validate()

    # Fix the date format and test with another invalid format
    config.set('data.excel.date_format', '%Y-%m-%d')  # Valid format
    config.set('data.excel.date_format', '%z')  # Invalid format
    with pytest.raises(ConfigError):
        config.validate()

    # Fix all validation issues
    config.set('data.excel.date_format', '%Y-%m-%d')
    # Should not raise an exception
    config.validate()
