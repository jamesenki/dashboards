"""
IoTSphere configuration system.

This package provides a unified configuration system for the IoTSphere platform,
following the principles of Test-Driven Development (TDD).
"""
from src.config.exceptions import ConfigurationError, ConfigurationValidationError
from src.config.models import (
    ApiConfig,
    AppConfig,
    CorsConfig,
    DatabaseConfig,
    MocksConfig,
    MonitoringConfig,
    PredictionsConfig,
    ServicesConfig,
)
from src.config.providers import DefaultProvider, EnvironmentProvider, FileProvider
from src.config.service import ConfigurationService

# Singleton instance for global access
config = ConfigurationService.get_instance()
