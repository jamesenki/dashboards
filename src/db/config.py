import os
from typing import Dict, Optional, Union

from pydantic_settings import BaseSettings


class DBSettings(BaseSettings):
    # Main database settings
    DB_TYPE: str = "postgres"  # postgres, sqlite, or memory
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "iotsphere"
    DB_PASSWORD: str = "iotsphere"
    DB_NAME: str = "iotsphere"
    
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


db_settings = DBSettings()


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
