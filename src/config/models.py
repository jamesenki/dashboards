"""
Configuration models for the IoTSphere configuration system.

These Pydantic models define the structure and validation rules
for different parts of the configuration.
"""
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator, AnyHttpUrl


class DatabaseCredentials(BaseModel):
    """Database credentials configuration."""
    username: str
    password: str

    @validator('password')
    def password_not_empty(cls, v):
        if not v:
            raise ValueError('Password cannot be empty')
        return v


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    name: str = "iotsphere"
    pool_size: int = 5
    max_overflow: int = 10
    credentials: DatabaseCredentials

    class Config:
        env_prefix = "DB_"


class CorsConfig(BaseModel):
    """CORS configuration for API."""
    allowed_origins: List[str] = ["*"]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]
    allow_credentials: bool = False
    max_age: int = 600


class ApiEndpointsConfig(BaseModel):
    """API endpoint path configuration."""
    base: str = "/api"
    docs: str = "/docs"
    redoc: str = "/redoc"
    openapi: str = "/openapi.json"


class ApiConfig(BaseModel):
    """API configuration."""
    title: str = "IoTSphere API"
    version: str = "v1"
    endpoints: ApiEndpointsConfig = ApiEndpointsConfig()
    cors: CorsConfig = CorsConfig()

    class Config:
        env_prefix = "API_"


class MonitoringConfig(BaseModel):
    """Monitoring service configuration."""
    enabled: bool = True
    metrics_retention_days: int = 30
    base_path: str = "/api/monitoring"
    alerts_path: str = "/alerts"
    metrics_path: str = "/metrics"


class PredictionsConfig(BaseModel):
    """Predictions service configuration."""
    enabled: bool = True
    model_path: str = "./models"
    base_path: str = "/api/predictions"
    forecast_path: str = "/forecast"
    batch_path: str = "/batch"


class MocksConfig(BaseModel):
    """Mock data configuration."""
    enabled: bool = False
    data_path: str = "./mocks"
    response_delay_ms: int = 0


class ServicesConfig(BaseModel):
    """Combined services configuration."""
    monitoring: MonitoringConfig = MonitoringConfig()
    predictions: PredictionsConfig = PredictionsConfig()


class AppConfig(BaseModel):
    """Top-level application configuration."""
    name: str = "IoTSphere"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api: ApiConfig = ApiConfig()
    database: DatabaseConfig
    services: ServicesConfig = ServicesConfig()
    mocks: MocksConfig = MocksConfig()

    class Config:
        env_file = ".env"
        case_sensitive = True
