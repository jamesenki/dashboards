import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

# Import dotenv utilities
from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings

# Environment constants
ENV_DEVELOPMENT = "development"
ENV_TESTING = "testing"


def get_environment() -> str:
    """Determine the current environment based on environment variables."""
    env = os.environ.get("IOTSPHERE_ENV", ENV_DEVELOPMENT).lower()

    if env not in [ENV_DEVELOPMENT, ENV_TESTING]:
        print(f"Warning: Unknown environment '{env}'. Defaulting to {ENV_DEVELOPMENT}")
        return ENV_DEVELOPMENT

    return env


def load_yaml_config() -> Dict[str, Any]:
    """Load environment-specific configuration from YAML file."""
    # Load environment variables from .env file if it exists
    env_file = find_dotenv()
    if env_file:
        load_dotenv(env_file)

    # Default config with development settings - using environment variables when available
    default_config = {
        "development": {
            "type": "postgres",
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", "5432")),
            "name": os.environ.get("DB_NAME", "iotsphere"),
            "user": os.environ.get("DB_USER", "iotsphere"),
            "password": os.environ.get("DB_PASSWORD", "iotsphere"),
            "fallback_to_mock": True,
        },
        "testing": {
            "type": "memory",
            "fallback_to_mock": True,
        },
    }

    # Attempt to load from config file
    config_path = Path(__file__).parent.parent.parent / "config" / "database.yaml"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    return yaml_config
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")

    return default_config


class DBSettings(BaseSettings):
    # Environment settings
    IOTSPHERE_ENV: str = ENV_DEVELOPMENT
    USE_MOCK_DATA: bool = False

    # These will be set based on environment config
    DB_TYPE: str = "postgres"  # Default to postgres
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "iotsphere"
    DB_PASSWORD: str = "iotsphere"
    DB_NAME: str = "iotsphere"

    # Control database behavior
    FALLBACK_TO_MOCK: bool = True
    SUPPRESS_DB_CONNECTION_ERRORS: bool = False

    # Redis cache settings
    REDIS_ENABLED: bool = True
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Connection pool settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields to be set from environment variables


# Load environment-specific configuration
def configure_db_settings() -> DBSettings:
    """Configure DB settings based on environment."""
    # Create default settings object
    settings = DBSettings()

    # Get environment
    env = get_environment()
    print(f"Configuring database for environment: {env}")

    # Load configuration from YAML
    config = load_yaml_config()

    # Get environment-specific settings
    if env in config:
        env_config = config[env]

        # Update settings from config
        settings.DB_TYPE = env_config.get("type", settings.DB_TYPE)
        settings.DB_HOST = env_config.get("host", settings.DB_HOST)
        settings.DB_PORT = env_config.get("port", settings.DB_PORT)
        settings.DB_USER = env_config.get("user", settings.DB_USER)
        settings.DB_NAME = env_config.get("name", settings.DB_NAME)
        settings.FALLBACK_TO_MOCK = env_config.get(
            "fallback_to_mock", settings.FALLBACK_TO_MOCK
        )

        # For password, prioritize environment variable for security
        env_password = os.environ.get("DB_PASSWORD")
        if env_password:
            settings.DB_PASSWORD = env_password
        else:
            settings.DB_PASSWORD = env_config.get("password", settings.DB_PASSWORD)

    return settings


# Initialize db_settings with environment-specific configuration
db_settings = configure_db_settings()


def get_db_url() -> str:
    """Generate database URL based on settings."""
    if db_settings.DB_TYPE == "memory":
        return "sqlite+aiosqlite:///:memory:"
    elif db_settings.DB_TYPE == "sqlite":
        return f"sqlite+aiosqlite:///{db_settings.DB_NAME}.db"
    elif db_settings.DB_TYPE == "postgres":
        # Note the postgresql+asyncpg:// for async driver
        return (
            f"postgresql+asyncpg://{db_settings.DB_USER}:{db_settings.DB_PASSWORD}@"
            f"{db_settings.DB_HOST}:{db_settings.DB_PORT}/{db_settings.DB_NAME}"
        )
    else:
        raise ValueError(f"Unsupported database type: {db_settings.DB_TYPE}")
