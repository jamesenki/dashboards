# Environment-Based Configuration System

## Overview

The IoTSphere application now supports an environment-based configuration system that allows different settings for development, staging, and production environments. This system provides:

1. **Centralized Configuration**: All application settings in one place
2. **Environment-Specific Overrides**: Different settings for development, staging, and production
3. **Database Fallback Mechanism**: Automatic fallback to mock data when database is unavailable
4. **Configuration Validation**: Type-safe access to configuration values
5. **Environment Variable Substitution**: Use environment variables for sensitive information

## Configuration Files

The configuration is structured across several YAML files:

- **`config/config.yaml`**: Base configuration shared across environments
- **`config/development.yaml`**: Development environment overrides
- **`config/production.yaml`**: Production environment overrides

## Starting the Application with Environment Selection

To specify the environment when starting the application:

```bash
# Development environment (default)
python -m src.main --env=development

# Production environment
python -m src.main --env=production

# With additional options
python -m src.main --env=production --host=0.0.0.0 --port=8000
```

## Environment Variables

The application will use the `APP_ENV` environment variable if the `--env` flag is not provided:

```bash
export APP_ENV=production
python -m src.main
```

## Database Fallback Mechanism

The system will automatically try to use the configured database first and will fall back to mock data in these cases:

1. If the database connection fails AND `database.fallback_to_mock` is set to `true`
2. If a service-specific setting is explicitly set to use mock data:
   - `services.water_heater.use_mock_data` is set to `true`
   - `services.monitoring.use_mock_data` is set to `true`
   
Additionally, each service can have its own fallback configuration:
   - `services.monitoring.fallback_to_mock` controls whether the model monitoring service should fall back to mock data when database access fails

For backward compatibility, the system also checks the `USE_MOCK_DATA` environment variable.

## Using the Configuration in Code

Access configuration values from anywhere in the code:

```python
from src.config import config

# Get a configuration value with an optional default
db_type = config.get("database.type", "sqlite")
use_mock_data = config.get("services.water_heater.use_mock_data", False)

# Type-specific getters
debug_mode = config.get_bool("app.debug", False)
log_level = config.get_str("app.log_level", "INFO")
```

## Configuration Structure

### Database Configuration

```yaml
database:
  type: "postgres"  # postgres, sqlite
  host: "${AZURE_DB_HOST}"  # Environment variable substitution
  port: 5432
  name: "iotsphere"
  credentials:
    username: "${AZURE_DB_USER}"
    password: "${AZURE_DB_PASSWORD}"
  fallback_to_mock: false  # Whether to fallback to mock data
```

### Services Configuration

```yaml
services:
  water_heater:
    use_mock_data: false
    data_retention_days: 90
    
  predictions:
    model_cache_ttl: 3600
    enable_development_models: false
```

## Advanced Configuration

### Environment Variable Substitution

The configuration system supports environment variable substitution with default values:

```yaml
database:
  host: "${DB_HOST|localhost}"  # Use DB_HOST env var or default to "localhost"
  credentials:
    password: "${DB_PASSWORD}"  # Must be provided as env var
```

### Adding New Configuration Options

When adding new configuration options:

1. Add the default value to `config/config.yaml`
2. Add environment-specific overrides to the relevant environment files
3. Access the configuration in code using the `config.get()` method

## Service-Specific Configuration

### Water Heater Service

The Water Heater service supports the following configuration options:

- **`services.water_heater.use_mock_data`**: If true, will always use mock data. If false, will try the database first.
- **`services.water_heater.data_retention_days`**: Number of days to retain water heater readings data.
- **`services.water_heater.default_temperature`**: Default temperature setting for new water heaters.
- **`services.water_heater.alert_threshold_high`**: Temperature threshold for high temperature alerts.
- **`services.water_heater.alert_threshold_low`**: Temperature threshold for low temperature alerts.

### Model Monitoring Service

The Model Monitoring service supports the following configuration options:

- **`services.monitoring.use_mock_data`**: If true, will always use mock data instead of the database.
- **`services.monitoring.fallback_to_mock`**: If true, will fall back to mock data when database access fails.
- **`services.monitoring.metrics_retention_days`**: Number of days to retain model metrics data.
- **`services.monitoring.enabled`**: Global toggle for enabling/disabling the monitoring service.
- **`services.monitoring.model_health`**:
  - **`drift_threshold`**: Maximum acceptable drift score before alerting (0.0-1.0).
  - **`accuracy_threshold`**: Minimum acceptable accuracy score before alerting (0.0-1.0).
  - **`enabled`**: Toggle for model health monitoring specifically.
- **`services.monitoring.alerts`**:
  - **`enabled`**: Toggle for enabling alert generation.
  - **`check_interval`**: Interval in seconds between alert checks.
  - **`notification_channels`**: Configuration for notification destinations (email, slack, webhook).

## Integration with Prediction Endpoints

The configuration system works seamlessly with the prediction API endpoints (`/api/predictions/water-heaters/{device_id}/{prediction-type}`). The prediction service will use the configured database settings and fall back to mock data if necessary, ensuring that the prediction endpoints remain operational even when the database is unavailable.
