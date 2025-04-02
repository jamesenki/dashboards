"""
IoTSphere configuration system.

This package provides a unified configuration system for the IoTSphere platform,
following the principles of Test-Driven Development (TDD).
"""
from src.config.service import ConfigurationService
from src.config.providers import DefaultProvider, FileProvider, EnvironmentProvider
from src.config.models import (
    AppConfig,
    DatabaseConfig,
    ApiConfig,
    CorsConfig,
    ServicesConfig,
    MonitoringConfig,
    PredictionsConfig,
    MocksConfig
)
from src.config.exceptions import ConfigurationError, ConfigurationValidationError

# Singleton instance for global access
config = ConfigurationService.get_instance()
