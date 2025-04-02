"""
Configuration service for the IoTSphere platform.

This service provides a centralized way to access configuration from multiple sources
with type safety and validation.
"""
import os
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError

from src.config.exceptions import (
    ConfigurationAccessError,
    ConfigurationError,
    ConfigurationValidationError,
)
from src.config.providers import ConfigurationProvider

# Generic type for configuration models
T = TypeVar("T", bound=BaseModel)


class ConfigurationService:
    """
    Central service for accessing configuration from multiple providers.

    This service:
    - Merges configuration from multiple providers
    - Caches configuration for performance
    - Provides type-safe access to configuration values
    - Validates configuration against schemas
    """

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of the configuration service.

        Returns:
            ConfigurationService: The singleton instance
        """
        if cls._instance is None:
            cls._instance = ConfigurationService()
        return cls._instance

    def __init__(self, initial_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the configuration service.

        Args:
            initial_config: Optional initial configuration dictionary
        """
        # List of (provider, priority) tuples
        self._providers: List[Tuple[ConfigurationProvider, int]] = []

        # Configuration cache
        self._config_cache: Optional[Dict[str, Any]] = (
            initial_config.copy() if initial_config else None
        )

    def register_provider(self, provider: ConfigurationProvider, priority: int = 0):
        """
        Register a configuration provider.

        Providers with higher priority values override those with lower priority.

        Args:
            provider: The configuration provider to register
            priority: Priority level (higher value = higher priority)
        """
        self._providers.append((provider, priority))

        # Sort by priority (descending)
        self._providers.sort(key=lambda p: p[1], reverse=True)

        # Invalidate cache
        self._config_cache = None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Dot-separated key path (e.g., 'database.host')
            default: Default value if key is not found

        Returns:
            The configuration value if found, or the default value
        """
        # Ensure config is loaded
        config = self._get_merged_config()

        # Navigate the nested dictionary
        parts = key.split(".")
        current = config

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """
        Get a boolean configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Boolean value, or default

        Raises:
            ConfigurationAccessError: If value cannot be converted to boolean
        """
        value = self.get(key, default)

        if value is None:
            return None

        if isinstance(value, bool):
            return value

        # Convert string values
        if isinstance(value, str):
            value = value.lower()
            if value in ("true", "yes", "1", "on", "y"):
                return True
            if value in ("false", "no", "0", "off", "n"):
                return False

        # Try to convert other values
        try:
            return bool(value)
        except ValueError:
            raise ConfigurationAccessError(f"Cannot convert value to boolean: {value}")

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """
        Get an integer configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Integer value, or default

        Raises:
            ConfigurationAccessError: If value cannot be converted to integer
        """
        value = self.get(key, default)

        if value is None:
            return None

        if isinstance(value, int) and not isinstance(value, bool):
            return value

        # Convert string values
        try:
            if isinstance(value, str):
                return int(value)
            return int(value)
        except (ValueError, TypeError):
            raise ConfigurationAccessError(f"Cannot convert value to integer: {value}")

    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """
        Get a float configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Float value, or default

        Raises:
            ConfigurationAccessError: If value cannot be converted to float
        """
        value = self.get(key, default)

        if value is None:
            return None

        if isinstance(value, float):
            return value

        # Convert string values
        try:
            if isinstance(value, str):
                return float(value)
            return float(value)
        except (ValueError, TypeError):
            raise ConfigurationAccessError(f"Cannot convert value to float: {value}")

    def get_list(
        self, key: str, default: Optional[List[Any]] = None
    ) -> Optional[List[Any]]:
        """
        Get a list configuration value.

        If the value is a comma-separated string, it will be split into a list.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            List value, or default

        Raises:
            ConfigurationAccessError: If value cannot be converted to list
        """
        value = self.get(key, default)

        if value is None:
            return None

        if isinstance(value, list):
            return value

        # Convert string values
        if isinstance(value, str):
            return [item.strip() for item in value.split(",")]

        # Try to convert other values
        try:
            return list(value)
        except (ValueError, TypeError):
            raise ConfigurationAccessError(f"Cannot convert value to list: {value}")

    def get_section(
        self, section: str, default: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get a configuration section as a dictionary.

        Args:
            section: Section key (e.g., 'database')
            default: Default value if section not found

        Returns:
            Dictionary of configuration values, or default
        """
        value = self.get(section)

        if value is None:
            return default if default is not None else {}

        if isinstance(value, dict):
            return value

        raise ConfigurationAccessError(
            f"Configuration section is not a dictionary: {section}"
        )

    def get_validated(self, section: str, model_class: Type[T]) -> T:
        """
        Get a validated configuration section.

        Args:
            section: Section key (e.g., 'database')
            model_class: Pydantic model class for validation

        Returns:
            Validated model instance

        Raises:
            ConfigurationValidationError: If validation fails
        """
        config_data = self.get_section(section)

        try:
            return model_class(**config_data)
        except ValidationError as e:
            raise ConfigurationValidationError(
                f"Configuration validation failed for {section}: {e}"
            )

    def reload(self):
        """
        Reload configuration from all providers.

        This method reloads all providers that support reloading and
        invalidates the configuration cache.
        """
        # Reload providers that support it
        for provider, _ in self._providers:
            if hasattr(provider, "reload"):
                provider.reload()

        # Invalidate cache
        self._config_cache = None

    def _get_merged_config(self) -> Dict[str, Any]:
        """
        Get the merged configuration from all providers.

        This method merges configuration from all registered providers,
        respecting their priority order.

        Returns:
            Merged configuration dictionary
        """
        # Return cached config if available
        if self._config_cache is not None:
            return self._config_cache

        # Start with empty config
        merged_config = {}

        # Merge from lowest to highest priority
        # Reverse the order since we sorted by descending priority
        for provider, _ in reversed(self._providers):
            provider_config = provider._get_config()
            self._deep_merge(merged_config, provider_config)

        # Cache the result
        self._config_cache = merged_config
        return merged_config

    @staticmethod
    def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively merge source dictionary into target dictionary.

        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dictionaries
                ConfigurationService._deep_merge(target[key], value)
            else:
                # Otherwise just overwrite
                target[key] = value

    def __repr__(self) -> str:
        """String representation of the configuration service."""
        provider_count = len(self._providers)
        return f"<ConfigurationService: {provider_count} providers>"
