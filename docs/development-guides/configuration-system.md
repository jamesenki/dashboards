# IoTSphere Configuration System Guide

## Overview

The IoTSphere platform uses a hierarchical configuration system that allows for flexible, environment-specific configuration while maintaining type safety and validation. This guide explains how to use the configuration system effectively.

## Configuration Structure

Configuration in IoTSphere follows a layered approach with multiple sources:

1. **Default Configuration** (`config/config.yaml`)
   - Base configuration with sensible defaults
   - Serves as documentation for all available settings

2. **Environment-Specific Configuration** (`config/config.<environment>.yaml`)
   - Overrides specific to development, testing, or production environments
   - Applied on top of the default configuration

3. **Environment Variables**
   - Highest priority, overrides file-based configuration
   - Used for sensitive information and deployment-specific settings

## Using the Configuration Service

The configuration service provides a centralized way to access configuration settings throughout the application.

### Importing the Service

```python
# Option 1: Import the global singleton
from src.config import config

# Option 2: Get the singleton instance directly
from src.config.service import ConfigurationService
config = ConfigurationService.get_instance()
```

### Basic Configuration Access

```python
# Simple key access
app_name = config.get("app.name")                  # Returns: "IoTSphere"
db_host = config.get("database.host")              # Returns: "localhost"

# Access with default values
debug_mode = config.get("app.debug", False)        # Returns configured value or False if not found
log_level = config.get("app.log_level", "INFO")    # Returns configured value or "INFO" if not found
```

### Typed Access

```python
# Boolean values
debug_enabled = config.get_bool("app.debug")              # Converts to boolean
metrics_enabled = config.get_bool("observability.metrics.enabled", False)

# Integer values
port = config.get_int("database.port", 5432)              # Converts to integer
pool_size = config.get_int("database.pool_size")          # Converts to integer

# Float values
drift_threshold = config.get_float("services.monitoring.model_health.drift_threshold")

# List values
origins = config.get_list("api.cors.allowed_origins")      # Returns as list
```

### Section Access

```python
# Get entire configuration sections as dictionaries
db_config = config.get_section("database")
monitoring_config = config.get_section("services.monitoring")

# With defaults if section doesn't exist
metrics_config = config.get_section("nonexistent", {"enabled": False})
```

### Validated Configuration

```python
# Get configuration validated against Pydantic models
from src.config.models import DatabaseConfig, ApiConfig

# Returns a validated DatabaseConfig object
db_config = config.get_validated("database", DatabaseConfig)
print(db_config.host)      # Access with type hints and validation
print(db_config.port)      # Integer with validation

# Get API configuration
api_config = config.get_validated("api", ApiConfig)
```

## Configuration Files

### Default Configuration

The default configuration file (`config/config.yaml`) contains all available settings with sensible defaults. It serves as both the base configuration and documentation of available settings.

This file should **never contain sensitive information** like passwords or API keys. Use environment variables for those.

### Environment-Specific Configuration

Environment-specific files (`config/config.<environment>.yaml`) contain overrides for specific environments:

- `config.development.yaml`: Development environment settings
- `config.testing.yaml`: Test environment settings
- `config.production.yaml`: Production environment settings

The appropriate file is loaded based on the `APP_ENVIRONMENT` environment variable.

## Environment Variables

Environment variables take precedence over file-based configuration. They follow a naming convention:

- Convert dot notation to uppercase with underscores
- Add the `IOTSPHERE_` prefix

Examples:
- `app.name` becomes `IOTSPHERE_APP_NAME`
- `database.host` becomes `IOTSPHERE_DATABASE_HOST`
- `api.cors.allowed_origins` becomes `IOTSPHERE_API_CORS_ALLOWED_ORIGINS`

For list values, use comma-separated strings:
```
IOTSPHERE_API_CORS_ALLOWED_ORIGINS=http://localhost:4200,http://example.com
```

## Sensitive Information

Never store sensitive information like passwords or API keys in configuration files, especially if these files are committed to version control. Instead:

1. Use environment variables for sensitive information
2. Use references to environment variables in configuration files:
   ```yaml
   database:
     credentials:
       password: "${DB_PASSWORD}"
   ```

## Best Practices

1. **Add New Settings to Default Configuration First**
   - Always add new settings to the default config file
   - Include comments explaining the purpose and valid values
   - Use Pydantic models to enforce validation

2. **Test with Different Configurations**
   - Write tests that verify system behavior with different configurations
   - Use parametrized tests to check boundary conditions

3. **Keep Environment-Specific Overrides Minimal**
   - Only override settings that truly need to differ between environments
   - Keep overrides to a minimum for maintainability

4. **Validate Configuration at Startup**
   - Validate critical configuration at application startup
   - Fail fast if required configuration is missing or invalid

5. **Reload Support**
   - For long-running services, use the `config.reload()` method to refresh configuration
   - Implement configuration change events if components need to react to changes

## Example: Configuration Usage Following TDD

Following our Test-Driven Development principles, configuration usage should be planned with testing in mind:

```python
# In your test
def test_database_connection_with_config(monkeypatch):
    # Arrange: Set up test configuration
    monkeypatch.setenv("IOTSPHERE_DATABASE_HOST", "testdb")
    monkeypatch.setenv("IOTSPHERE_DATABASE_PORT", "5433")
    
    # Force config reload to pick up environment changes
    from src.config import config
    config.reload()
    
    # Act: Create database connection using configuration
    db = create_database_connection(config)
    
    # Assert: Verify connection uses configured values
    assert db.host == "testdb"
    assert db.port == 5433
```

## Extending the Configuration System

The configuration system is designed to be extensible:

1. **Adding New Providers**
   - Create a new provider class implementing the `ConfigurationProvider` interface
   - Register the provider with the configuration service

2. **Adding New Models**
   - Create new Pydantic models in `src.config.models`
   - Use models for validation with `get_validated()`

3. **Adding Helper Methods**
   - Extend the `ConfigurationService` class with new helper methods as needed
