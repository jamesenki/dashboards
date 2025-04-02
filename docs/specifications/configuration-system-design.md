# IoTSphere Configuration System Design

## Overview

This document details the design and implementation plan for the IoTSphere unified configuration system. Following our Test-Driven Development approach, we'll define how configuration will be managed across the platform, ensuring flexibility, security, and maintainability.

## Architecture

The configuration system follows a layered architecture with clear separation of concerns:

```
┌───────────────────────────────────────┐
│           Application Code            │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│        Configuration Service          │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│      Configuration Providers          │
├───────────┬───────────┬───────────────┤
│  Default  │  Files    │  Environment  │
│  Values   │  (YAML)   │  Variables    │
└───────────┴───────────┴───────────────┘
```

### Components

1. **ConfigurationService**
   - Central service for accessing all configuration
   - Caches configuration for performance
   - Provides validation and type safety
   - Exposes configuration change events

2. **ConfigurationProviders**
   - Default Values Provider: Hardcoded defaults as a fallback
   - File Provider: YAML/JSON configuration files
   - Environment Provider: Environment variables
   - (Optional) Remote Provider: Configuration from a remote service

3. **Configuration Schema**
   - Pydantic models defining structure and validation
   - Separate models for different configuration domains
   - Documentation via schema comments

4. **Configuration Manager**
   - Handles merging configuration from different sources
   - Resolves conflicts using predefined priority
   - Manages configuration reloading

## Configuration Structure

Configuration will be organized in a hierarchical structure:

```yaml
app:
  name: "IoTSphere"
  environment: "development"
  debug: true

api:
  base_path: "/api"
  version: "v1"
  cors:
    allowed_origins: ["http://localhost:4200"]
    allowed_methods: ["GET", "POST", "PUT", "DELETE"]

database:
  type: "postgres"
  host: "localhost"
  port: 5432
  credentials:
    username: "iotsphere"
    password: "${DB_PASSWORD}" # Reference to environment variable

services:
  monitoring:
    enabled: true
    metrics_retention_days: 30
    endpoints:
      alerts: "/alerts"
      metrics: "/metrics"
  
  prediction:
    enabled: true
    model_path: "./models"
    api:
      base_path: "/api/predictions"

mocks:
  enabled: "${USE_MOCK_DATA}"
  data_path: "./mocks"
  response_delay_ms: 200
```

## Implementation Plan

Following our TDD approach, we'll implement the configuration system in these phases:

### Phase 1: Core Configuration Service (RED)

1. **Write Tests**:
   - Test loading configuration from different sources
   - Test configuration validation and type conversion
   - Test priority and overriding behavior
   - Test access patterns and performance

2. **Define Schemas**:
   - Create Pydantic models for all configuration sections
   - Document validation rules and default values
   - Define relationships between configuration sections

### Phase 2: Implementation (GREEN)

1. **Configuration Providers**:
   - Implement default values provider
   - Implement YAML/JSON file provider
   - Implement environment variable provider
   - Implement variable interpolation

2. **Configuration Service**:
   - Implement configuration loading and merging
   - Implement caching for performance
   - Implement validation using Pydantic models
   - Implement configuration change events

3. **Configuration CLI**:
   - Create command-line tools for configuration validation
   - Implement configuration generation from templates
   - Add commands for configuration inspection

### Phase 3: Integration (REFACTOR)

1. **Database Configuration**:
   - Refactor database connection to use configuration service
   - Update database migration scripts
   - Implement configuration-based connection pooling

2. **API Configuration**:
   - Refactor API router registration to use configuration
   - Implement dynamic API paths and versioning
   - Configure CORS using the configuration system

3. **Mock Data**:
   - Move hardcoded mock data to configuration files
   - Implement mock data provider using configuration
   - Add environment-specific mock data

4. **Service Configuration**:
   - Refactor service initialization to use configuration
   - Implement feature flags using configuration
   - Add service-specific configuration

### Phase 4: Documentation and Testing (VERIFY)

1. **Documentation**:
   - Update developer guides with configuration instructions
   - Document configuration schema and validation rules
   - Provide examples for common configuration scenarios

2. **Integration Testing**:
   - Create tests for configuration-dependent components
   - Verify system behavior with different configurations
   - Test deployment with different environment configurations

## Code Examples

### Configuration Schema Definition

```python
from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator

class DatabaseCredentials(BaseModel):
    username: str
    password: str
    
    @validator('password')
    def password_not_empty(cls, v):
        if not v:
            raise ValueError('Password cannot be empty')
        return v

class DatabaseConfig(BaseModel):
    type: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    name: str = "iotsphere"
    credentials: DatabaseCredentials
    
    class Config:
        env_prefix = "DB_"

class ApiConfig(BaseModel):
    base_path: str = "/api"
    version: str = "v1"
    cors: CorsConfig = CorsConfig()
    
    class Config:
        env_prefix = "API_"

class AppConfig(BaseModel):
    database: DatabaseConfig
    api: ApiConfig
    # Other configuration sections...
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

### Configuration Service Usage

```python
from src.config.service import ConfigurationService

# Get configuration instance
config = ConfigurationService.get_instance()

# Access configuration values with type safety
db_host = config.get('database.host')
api_version = config.get('api.version')

# Access with default values
debug_mode = config.get('app.debug', default=False)

# Access with type conversion
port = config.get_int('database.port', default=5432)

# Access complex objects
db_config = config.get_section('database')
```

### Configurable API Endpoint Example

```python
from fastapi import FastAPI, APIRouter
from src.config.service import ConfigurationService

config = ConfigurationService.get_instance()

# Create router with configuration
router = APIRouter(
    prefix=config.get('api.predictions.base_path', '/api/predictions'),
    tags=["Predictions"],
)

# Define endpoints using configuration
@router.get(
    config.get('api.predictions.endpoints.forecast', '/forecast'),
    summary="Get maintenance forecast prediction"
)
async def get_forecast():
    # Implementation...
    pass

# Use configuration for API creation
app = FastAPI(
    title=config.get('api.title', 'IoTSphere API'),
    version=config.get('api.version', 'v1'),
    docs_url=config.get('api.docs_url', '/docs'),
)
```

## Migration Strategy

To minimize disruption, we'll implement the configuration system in stages:

1. **Parallel Implementation**: Create the new configuration system alongside existing code
2. **Gradual Migration**: Move one component at a time to the new system
3. **Compatibility Layer**: Provide adapters for components that rely on the old approach
4. **Validation**: Extensive testing at each migration step
5. **Documentation**: Update documentation as components are migrated

## Conclusion

The unified configuration system will provide a flexible, maintainable approach to configuration management across the IoTSphere platform. By following our TDD principles, we'll ensure that the implementation is robust, tested, and meets the needs of the system. The phased implementation approach will minimize disruption while providing immediate benefits as components are migrated.

---

*Next Steps: Create the first set of tests for the configuration service following the RED phase of our TDD approach.*
