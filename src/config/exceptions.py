"""
Exception classes for the configuration system.
"""

class ConfigurationError(Exception):
    """Base exception for all configuration-related errors."""
    pass


class ConfigurationValidationError(ConfigurationError):
    """Raised when configuration validation fails."""
    pass


class ConfigurationProviderError(ConfigurationError):
    """Raised when a configuration provider encounters an error."""
    pass


class ConfigurationAccessError(ConfigurationError):
    """Raised when accessing configuration with incorrect types or paths."""
    pass
