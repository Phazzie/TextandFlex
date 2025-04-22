"""
Configuration Manager Module
-------------------------
Manages feature flags and application configuration.
"""
import os
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path


class ConfigManager:
    """
    Configuration manager for feature flags and application settings.
    
    This class provides methods for managing feature flags and application
    configuration, with support for loading and saving to a JSON file.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Optional path to the configuration file
        """
        self.config_file = config_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config",
            "app_config.json"
        )
        self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get the default configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "features": {
                "advanced_analysis": True,
                "export_to_excel": True,
                "visualization": True,
                "experimental_ml": False,
                "disk_based_indices": False,
                "dataset_versioning": True
            },
            "ui": {
                "theme": "light",
                "font_size": 12,
                "show_toolbar": True,
                "show_statusbar": True,
                "show_sidebar": True
            },
            "analysis": {
                "cache_results": True,
                "max_top_contacts": 10,
                "max_patterns": 5,
                "confidence_threshold": 0.7
            },
            "export": {
                "default_format": "csv",
                "include_metadata": True,
                "auto_open_file": False
            }
        }
    
    def get_feature_flag(self, feature_name: str, default: bool = False) -> bool:
        """
        Get the value of a feature flag.
        
        Args:
            feature_name: Name of the feature flag
            default: Default value if the feature flag is not found
            
        Returns:
            Value of the feature flag
        """
        return self.config.get("features", {}).get(feature_name, default)
    
    def set_feature_flag(self, feature_name: str, value: bool) -> None:
        """
        Set the value of a feature flag.
        
        Args:
            feature_name: Name of the feature flag
            value: Value to set
        """
        if "features" not in self.config:
            self.config["features"] = {}
        
        self.config["features"][feature_name] = bool(value)
    
    def get_all_feature_flags(self) -> Dict[str, bool]:
        """
        Get all feature flags.
        
        Returns:
            Dictionary of all feature flags
        """
        return self.config.get("features", {}).copy()
    
    def get_config_value(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value by path.
        
        Args:
            path: Path to the configuration value (e.g., "ui.theme")
            default: Default value if the path is not found
            
        Returns:
            Configuration value
        """
        parts = path.split(".")
        value = self.config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def set_config_value(self, path: str, value: Any) -> None:
        """
        Set a configuration value by path.
        
        Args:
            path: Path to the configuration value (e.g., "ui.theme")
            value: Value to set
        """
        parts = path.split(".")
        config = self.config
        
        # Navigate to the parent of the target key
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]
        
        # Set the value
        config[parts[-1]] = value
    
    def load_config(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.config_file):
            return False
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
            
            # Update the configuration
            self.config.update(loaded_config)
            return True
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading configuration: {str(e)}")
            return False
    
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            
            return True
        except IOError as e:
            print(f"Error saving configuration: {str(e)}")
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = self._get_default_config()
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        This is an alias for get_feature_flag for more readable code.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            True if the feature is enabled, False otherwise
        """
        return self.get_feature_flag(feature_name, False)
