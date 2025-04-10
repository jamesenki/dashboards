"""
Configuration settings module for the IoTSphere application.
Provides configuration settings for the application, including
database, API, and service settings.
"""

import logging
from functools import lru_cache
from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""

    # Environment Settings
    environment: str = "development"  # Options: development, testing, production
    logging_level: str = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    enable_diagnostics: bool = (
        False  # Enable diagnostic tools in non-production environments
    )
    enable_debuggers: bool = False  # Enable debuggers in development environment

    # API Settings
    api_version: str = "v1"
    api_prefix: str = "/api"
    debug: bool = False

    # Database Settings
    db_url: str = "sqlite:///iotsphere.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Water Heater Service Settings
    water_heater_default_target_temp: float = 50.0  # in Celsius
    water_heater_min_temp: float = 35.0
    water_heater_max_temp: float = 80.0

    # External API Settings
    external_api_timeout: int = 30  # in seconds
    weather_api_key: Optional[str] = None
    energy_rate_api_key: Optional[str] = None

    # Cache Settings
    cache_ttl: int = 300  # in seconds

    # Maintenance Settings
    maintenance_check_interval: int = 30  # in days

    # WebSocket Settings
    websocket_tracing_enabled: bool = False  # Disable WebSocket tracing by default
    websocket_debug_mode: bool = False  # Disable WebSocket debug mode by default
    websocket_port: int = 8912  # Default WebSocket port
    websocket_host: str = "0.0.0.0"  # Default WebSocket host

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "IOTSPHERE_"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings based on the current environment.

    Returns:
        Settings: Application settings with environment-specific overrides
    """
    import os

    try:
        # Get environment from environment variable or default to development
        env = os.environ.get("APP_ENV", "development").lower()

        # Create base settings
        settings = Settings(environment=env)

        # Apply environment-specific overrides
        if env == "production":
            # Production settings - optimize for performance
            settings.logging_level = "WARNING"
            settings.debug = False
            settings.enable_diagnostics = False
            settings.enable_debuggers = False
            settings.websocket_tracing_enabled = False
            settings.websocket_debug_mode = False
            logger.info("Loaded PRODUCTION settings - optimized for performance")
        elif env == "testing":
            # Testing settings - balance between debugging and performance
            settings.logging_level = "INFO"
            settings.debug = True
            settings.enable_diagnostics = False
            settings.enable_debuggers = False
            logger.info("Loaded TESTING settings")
        else:  # development is the default
            # Development settings - prioritize debugging capabilities
            settings.logging_level = "INFO"
            settings.debug = True
            settings.enable_diagnostics = False  # Disable for better performance
            settings.enable_debuggers = True
            logger.info("Loaded DEVELOPMENT settings")

        # Configure logging based on settings
        logging.basicConfig(level=getattr(logging, settings.logging_level))

        return settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        # In case of error, return default settings
        return Settings()
