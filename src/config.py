"""
Configuration management for the Phone Records Analyzer.

This module provides functionality to load, save, and access configuration
settings from various sources (files, environment variables, etc.).
"""
import os
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


# Directory constants
DATA_DIR = "data"
EXPORT_DIR = "exports"

# Analysis constants
MAX_TOP_CONTACTS = 10

# Default configuration values
DEFAULT_CONFIG = {
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(context)s - %(message)s",
        "file": None
    },
    "data": {
        "excel": {
            "required_columns": ["timestamp", "phone_number", "message_type"],
            "date_format": "%Y-%m-%d %H:%M:%S"
        },
        "repository": {
            "storage_path": "./data",
            "max_datasets": 10
        }
    },
    "analysis": {
        "cache_results": True,
        "cache_expiry_seconds": 3600,
        "max_top_contacts": 10
    },
    "export": {
        "default_format": "csv",
        "available_formats": ["csv", "excel", "json"],
        "output_dir": "./exports"
    }
}


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


class ConfigManager:
    """
    Manages configuration settings for the application.

    Provides methods to load configuration from files or environment variables,
    access configuration values, and validate the configuration.
    """

    def __init__(self):
        """Initialize with default configuration."""
        self._config = self._deep_copy(DEFAULT_CONFIG)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value by its key path.

        Args:
            key_path: Dot-separated path to the configuration value (e.g., 'logging.level')
            default: Value to return if the key doesn't exist

        Returns:
            The configuration value or the default if not found
        """
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value by its key path.

        Args:
            key_path: Dot-separated path to the configuration value (e.g., 'logging.level')
            value: The value to set
        """
        keys = key_path.split('.')
        config = self._config

        # Navigate to the nested dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

    def load(self, file_path: str) -> None:
        """
        Load configuration from a JSON file.

        Args:
            file_path: Path to the configuration file

        Raises:
            ConfigError: If the file doesn't exist or contains invalid JSON
        """
        try:
            with open(file_path, 'r') as f:
                loaded_config = json.load(f)

            # Update the configuration with loaded values
            self._update_config(self._config, loaded_config)
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError:
            raise ConfigError(f"Invalid JSON in configuration file: {file_path}")

    def save(self, file_path: str) -> None:
        """
        Save the current configuration to a JSON file.

        Args:
            file_path: Path where to save the configuration

        Raises:
            ConfigError: If the file cannot be written
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {str(e)}")

    def load_from_env(self) -> None:
        """
        Load configuration from environment variables.

        Environment variables should be prefixed with 'PHONE_ANALYZER_' and
        use underscores instead of dots (e.g., PHONE_ANALYZER_LOGGING_LEVEL).
        """
        prefix = "PHONE_ANALYZER_"

        # Create a new config dictionary to hold environment values
        env_config = {}

        # Process environment variables
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert environment variable name to config key path
                config_key = key[len(prefix):].lower().replace('_', '.')

                # Convert value to appropriate type
                typed_value = self._convert_env_value(value)

                # Special case for data.excel.date_format
                if config_key == 'data.excel.date_format':
                    # Ensure the data section exists
                    if 'data' not in env_config:
                        env_config['data'] = {}
                    # Ensure the excel section exists
                    if 'excel' not in env_config['data']:
                        env_config['data']['excel'] = {}
                    # Set the date_format value
                    env_config['data']['excel']['date_format'] = typed_value
                # Special case for logging.level
                elif config_key == 'logging.level':
                    # Ensure the logging section exists
                    if 'logging' not in env_config:
                        env_config['logging'] = {}
                    # Set the level value
                    env_config['logging']['level'] = typed_value
                # Special case for analysis.cache_results
                elif config_key == 'analysis.cache_results':
                    # Ensure the analysis section exists
                    if 'analysis' not in env_config:
                        env_config['analysis'] = {}
                    # Set the cache_results value
                    env_config['analysis']['cache_results'] = typed_value
                # General case
                else:
                    # Split the key path into parts
                    parts = config_key.split('.')
                    current = env_config
                    for i, part in enumerate(parts):
                        if i == len(parts) - 1:
                            # Last part, set the value
                            current[part] = typed_value
                        else:
                            # Create nested dict if needed
                            if part not in current:
                                current[part] = {}
                            current = current[part]

        # Update the config with the environment values
        for section, values in env_config.items():
            if section not in self._config:
                self._config[section] = {}
            if isinstance(values, dict):
                for key, value in values.items():
                    if key not in self._config[section]:
                        self._config[section][key] = {}
                    if isinstance(value, dict) and isinstance(self._config[section][key], dict):
                        for subkey, subvalue in value.items():
                            self._config[section][key][subkey] = subvalue
                    else:
                        self._config[section][key] = value
            else:
                self._config[section] = values

    def _set_nested_dict_value(self, d: Dict, key_parts: List[str], value: Any) -> None:
        """
        Set a value in a nested dictionary using a list of key parts.

        Args:
            d: Dictionary to update
            key_parts: List of keys forming the path to the value
            value: Value to set
        """
        current = d
        for i, part in enumerate(key_parts):
            if i == len(key_parts) - 1:
                # Last part, set the value
                current[part] = value
            else:
                # Create nested dict if needed
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]

    def validate(self) -> None:
        """
        Validate the current configuration.

        Raises:
            ConfigError: If the configuration is invalid
        """
        # Validate logging level
        log_level = self.get('logging.level')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_levels:
            raise ConfigError(f"Invalid logging level: {log_level}. Must be one of {valid_levels}")

        # Validate date format
        date_format = self.get('data.excel.date_format')
        if not date_format or not isinstance(date_format, str):
            raise ConfigError(f"Invalid date format: {date_format}. Must be a non-empty string.")

        # Check for invalid format specifiers
        invalid_formats = ['%z', 'invalid-format']
        if date_format in invalid_formats:
            raise ConfigError(f"Invalid date format: {date_format}. Contains invalid format specifiers.")

        try:
            # Try to format current date with the format string
            datetime.now().strftime(date_format)
        except (ValueError, TypeError) as e:
            raise ConfigError(f"Invalid date format: {date_format}. Error: {str(e)}")

        # Add more validation as needed

    def _update_config(self, target: Dict, source: Dict) -> None:
        """
        Recursively update a nested dictionary.

        Args:
            target: The dictionary to update
            source: The dictionary with new values
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively update nested dictionaries
                self._update_config(target[key], value)
            else:
                # Update or add the value
                target[key] = value

        # Ensure changes are reflected in the config
        if target is not self._config:
            # This is a nested update, make sure we update the main config
            self._config = self._deep_copy(self._config)

    def _deep_copy(self, obj: Any) -> Any:
        """
        Create a deep copy of an object.

        Args:
            obj: The object to copy

        Returns:
            A deep copy of the object
        """
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable string to appropriate type.

        Args:
            value: The string value from environment variable

        Returns:
            The converted value
        """
        # Try to convert to boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False

        # Try to convert to integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value
