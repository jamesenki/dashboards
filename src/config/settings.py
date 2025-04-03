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

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "IOTSPHERE_"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings: Application settings
    """
    try:
        logger.info("Loading application settings")
        return Settings()
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        # In case of error, return default settings
        return Settings()
