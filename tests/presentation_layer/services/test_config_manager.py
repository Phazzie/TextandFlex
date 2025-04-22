"""
Tests for the configuration manager.
"""
import pytest
import os
import json
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from src.presentation_layer.services.config_manager import ConfigManager


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return {
        "features": {
            "advanced_analysis": True,
            "export_to_excel": True,
            "visualization": True,
            "experimental_ml": False
        },
        "ui": {
            "theme": "light",
            "font_size": 12,
            "show_toolbar": True
        },
        "analysis": {
            "cache_results": True,
            "max_top_contacts": 10
        }
    }


@pytest.fixture
def config_manager(sample_config):
    """Create a configuration manager with a sample configuration."""
    with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
        with patch('os.path.exists', return_value=True):
            manager = ConfigManager()
            manager.load_config()
            return manager


class TestConfigManager:
    """Tests for the ConfigManager class."""

    def test_get_feature_flag(self, config_manager):
        """Test getting a feature flag."""
        # Act
        result = config_manager.get_feature_flag("advanced_analysis")
        
        # Assert
        assert result is True

    def test_get_feature_flag_nonexistent(self, config_manager):
        """Test getting a nonexistent feature flag."""
        # Act
        result = config_manager.get_feature_flag("nonexistent_feature")
        
        # Assert
        assert result is False

    def test_get_feature_flag_with_default(self, config_manager):
        """Test getting a feature flag with a default value."""
        # Act
        result = config_manager.get_feature_flag("nonexistent_feature", default=True)
        
        # Assert
        assert result is True

    def test_set_feature_flag(self, config_manager):
        """Test setting a feature flag."""
        # Act
        config_manager.set_feature_flag("experimental_ml", True)
        
        # Assert
        assert config_manager.get_feature_flag("experimental_ml") is True

    def test_get_config_value(self, config_manager):
        """Test getting a configuration value."""
        # Act
        result = config_manager.get_config_value("ui.theme")
        
        # Assert
        assert result == "light"

    def test_get_config_value_nonexistent(self, config_manager):
        """Test getting a nonexistent configuration value."""
        # Act
        result = config_manager.get_config_value("ui.nonexistent")
        
        # Assert
        assert result is None

    def test_get_config_value_with_default(self, config_manager):
        """Test getting a configuration value with a default value."""
        # Act
        result = config_manager.get_config_value("ui.nonexistent", default="dark")
        
        # Assert
        assert result == "dark"

    def test_set_config_value(self, config_manager):
        """Test setting a configuration value."""
        # Act
        config_manager.set_config_value("ui.theme", "dark")
        
        # Assert
        assert config_manager.get_config_value("ui.theme") == "dark"

    def test_save_config(self, config_manager):
        """Test saving the configuration."""
        # Act
        with patch('builtins.open', mock_open()) as mock_file:
            result = config_manager.save_config()
        
        # Assert
        assert result is True
        mock_file.assert_called_once()

    def test_save_config_error(self, config_manager):
        """Test saving the configuration with an error."""
        # Act
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = config_manager.save_config()
        
        # Assert
        assert result is False

    def test_load_config(self):
        """Test loading the configuration."""
        # Arrange
        sample_config = {
            "features": {
                "advanced_analysis": True
            }
        }
        
        # Act
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
            with patch('os.path.exists', return_value=True):
                manager = ConfigManager()
                result = manager.load_config()
        
        # Assert
        assert result is True
        assert manager.get_feature_flag("advanced_analysis") is True

    def test_load_config_file_not_found(self):
        """Test loading the configuration when the file is not found."""
        # Act
        with patch('os.path.exists', return_value=False):
            manager = ConfigManager()
            result = manager.load_config()
        
        # Assert
        assert result is False

    def test_load_config_invalid_json(self):
        """Test loading the configuration with invalid JSON."""
        # Act
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch('os.path.exists', return_value=True):
                manager = ConfigManager()
                result = manager.load_config()
        
        # Assert
        assert result is False

    def test_get_all_feature_flags(self, config_manager):
        """Test getting all feature flags."""
        # Act
        result = config_manager.get_all_feature_flags()
        
        # Assert
        assert isinstance(result, dict)
        assert "advanced_analysis" in result
        assert "export_to_excel" in result
        assert "visualization" in result
        assert "experimental_ml" in result

    def test_reset_to_defaults(self, config_manager):
        """Test resetting to default configuration."""
        # Arrange
        config_manager.set_feature_flag("advanced_analysis", False)
        
        # Act
        config_manager.reset_to_defaults()
        
        # Assert
        assert config_manager.get_feature_flag("advanced_analysis") is True
