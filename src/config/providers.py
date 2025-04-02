"""
Configuration providers for the IoTSphere configuration system.

Providers are responsible for loading configuration from different sources
and making it available to the configuration service.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from src.config.exceptions import ConfigurationProviderError


class ConfigurationProvider:
    """Base class for all configuration providers."""

    def __init__(self):
        """Initialize the provider."""
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Dot-separated key path (e.g., 'database.host')
            default: Default value if key is not found

        Returns:
            The value if found, or default value
        """
        parts = key.split(".")
        config = self._get_config()

        # Navigate the nested dictionary
        current = config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def _get_config(self) -> Dict[str, Any]:
        """
        Get the full configuration from this provider.

        This method should be implemented by subclasses.

        Returns:
            Configuration dictionary
        """
        raise NotImplementedError("Subclasses must implement _get_config")


class DefaultProvider(ConfigurationProvider):
    """Provider for default configuration values."""

    def __init__(self, defaults: Dict[str, Any]):
        """
        Initialize with default values.

        Args:
            defaults: Dictionary of default configuration values
        """
        super().__init__()
        self._defaults = defaults

    def _get_config(self) -> Dict[str, Any]:
        """
        Get the default configuration.

        Returns:
            Default configuration dictionary
        """
        return self._defaults


class FileProvider(ConfigurationProvider):
    """Provider for configuration from YAML files."""

    def __init__(self, file_path: Union[str, Path]):
        """
        Initialize with a file path.

        Args:
            file_path: Path to the YAML configuration file

        Raises:
            ConfigurationProviderError: If the file doesn't exist or can't be read
        """
        super().__init__()
        self._file_path = Path(file_path)
        self._config = None

        # Load the configuration file
        self._load_config()

    def _load_config(self):
        """
        Load configuration from the file.

        Raises:
            ConfigurationProviderError: If the file doesn't exist or can't be read
        """
        try:
            if not self._file_path.exists():
                raise ConfigurationProviderError(
                    f"Configuration file not found: {self._file_path}"
                )

            with open(self._file_path, "r") as f:
                self._config = yaml.safe_load(f) or {}

        except Exception as e:
            raise ConfigurationProviderError(f"Error loading configuration file: {e}")

    def reload(self):
        """Reload the configuration from the file."""
        self._load_config()

    def _get_config(self) -> Dict[str, Any]:
        """
        Get the configuration from the file.

        Returns:
            Configuration dictionary from the file
        """
        return self._config


class EnvironmentProvider(ConfigurationProvider):
    """Provider for configuration from environment variables."""

    def __init__(self, prefix: str = "", separator: str = "_"):
        """
        Initialize with optional prefix and separator.

        Args:
            prefix: Prefix for environment variables to consider (e.g., 'IOTSPHERE_')
            separator: Separator for nested keys in environment variables (default: '_')
        """
        super().__init__()
        self._prefix = prefix
        self._separator = separator
        self._config_cache = None

    def _get_config(self) -> Dict[str, Any]:
        """
        Get configuration from environment variables.

        This method converts environment variables to a nested dictionary structure.
        For example, 'IOTSPHERE_DATABASE_HOST' becomes {'database': {'host': value}}.

        Returns:
            Configuration dictionary from environment variables
        """
        # Use cached config if available
        if self._config_cache is not None:
            return self._config_cache

        # Start with empty config
        config = {}

        # Process environment variables
        for key, value in os.environ.items():
            # Skip if doesn't start with prefix
            if self._prefix and not key.startswith(self._prefix):
                continue

            # Remove prefix if specified
            if self._prefix:
                key = key[len(self._prefix) :]

            # Convert key to nested path
            path = key.lower().split(self._separator)

            # Navigate to the correct nested dict
            current = config
            for i, part in enumerate(path):
                if i == len(path) - 1:
                    # Last part is the actual key
                    current[part] = value
                else:
                    # Create nested dict if it doesn't exist
                    if part not in current:
                        current[part] = {}
                    current = current[part]

        # Cache the result
        self._config_cache = config
        return config

    def reload(self):
        """Reload the configuration from environment variables."""
        self._config_cache = None
