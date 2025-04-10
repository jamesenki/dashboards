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


import os
from pathlib import Path


def get_database_path(filename: str) -> str:
    """
    Get the path to a database file based on the current environment.

    Args:
        filename: The name of the database file

    Returns:
        Full path to the database file
    """
    # Get environment from configuration
    environment = config.get("environment", "development")

    # Base data directory
    base_dir = Path(os.environ.get("DATA_DIR", "data"))

    # Create environment-specific subdirectory
    db_dir = base_dir / environment / "db"

    # Ensure directory exists
    os.makedirs(db_dir, exist_ok=True)

    # Return full path
    return str(db_dir / filename)
