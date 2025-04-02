# Water Heater Configuration Management

This guide explains how to use and extend the configuration management system for water heaters in the IoTSphere application.

## Overview

The water heater configuration management system provides a flexible way to:

1. Configure data sources (mock vs. database)
2. Manage health status thresholds and indicators
3. Define alert rules for monitoring water heater conditions
4. Access water heater data through a unified API

## Architecture

The system follows the repository pattern with these key components:

```
┌─────────────┐      ┌──────────────────────────┐      ┌───────────────────┐
│  API Router │─────▶│ConfigurableWaterHeater   │─────▶│WaterHeater        │
│             │      │Service                    │      │Repository         │
└─────────────┘      └──────────────────────────┘      │(Interface)        │
                                                       └─────────┬─────────┘
                                                                 │
                     ┌──────────────────────────┐               │
                     │                          │◀──────────────┘
                     ▼                          ▼
          ┌────────────────────┐    ┌────────────────────┐
          │MockWaterHeater     │    │SQLiteWaterHeater   │
          │Repository          │    │Repository          │
          └────────────────────┘    └────────────────────┘
```

## Database Schema

The SQLite implementation uses these tables:

### Main Tables

1. **water_heaters**: Stores basic water heater information
   - id (PRIMARY KEY)
   - name, model, manufacturer
   - target_temperature, current_temperature
   - status, mode
   - installation_date, warranty_expiry, last_maintenance
   - health_status

2. **water_heater_readings**: Stores temperature and sensor readings
   - id (PRIMARY KEY)
   - water_heater_id (FOREIGN KEY)
   - temperature, pressure, energy_usage, flow_rate
   - timestamp
  
3. **water_heater_diagnostic_codes**: Stores error codes and diagnostic information
   - id (PRIMARY KEY)
   - water_heater_id (FOREIGN KEY)
   - code, description, severity
   - timestamp, resolved, resolved_at

### Configuration Tables

4. **water_heater_health_config**: Defines health status thresholds
   - id (PRIMARY KEY)
   - metric (e.g., "temperature_high")
   - threshold (numeric value)
   - status (GREEN, YELLOW, RED)
   - description
   - created_at, updated_at

5. **water_heater_alert_rules**: Defines rules for alerts
   - id (PRIMARY KEY)
   - name
   - condition (e.g., "temperature > 75")
   - severity
   - message
   - enabled
   - created_at, updated_at

## Usage Examples

### Switching Between Mock and Database

The service automatically chooses the repository based on the environment variable:

```python
# Set this environment variable to choose the data source
os.environ["USE_MOCK_DATA"] = "False"  # Use SQLite instead of mock data
```

Or explicitly specify the repository:

```python
from src.repositories.water_heater_repository import SQLiteWaterHeaterRepository
from src.services.configurable_water_heater_service import ConfigurableWaterHeaterService

# Use SQLite repository
repository = SQLiteWaterHeaterRepository()
service = ConfigurableWaterHeaterService(repository=repository)
```

### Configuring Health Status Thresholds

```python
# Get current configuration
config = await repository.get_health_configuration()

# Set new configuration
new_config = {
    "temperature_high": {"threshold": 70.0, "status": "RED", "description": "Temperature critically high"},
    "temperature_warning": {"threshold": 65.0, "status": "YELLOW", "description": "Temperature elevated"},
    "pressure_high": {"threshold": 6.0, "status": "RED", "description": "Pressure exceeds safe limit"},
    "energy_usage_high": {"threshold": 3000.0, "status": "YELLOW", "description": "High energy consumption"}
}
await repository.set_health_configuration(new_config)
```

### Managing Alert Rules

```python
# Add a new alert rule
rule = {
    "name": "High Temperature Alert",
    "condition": "temperature > 75",
    "severity": "HIGH",
    "message": "Water heater temperature exceeds safe level",
    "enabled": True
}
await repository.add_alert_rule(rule)

# Get all alert rules
rules = await repository.get_alert_rules()

# Update an existing rule
rule_update = {**rule, "severity": "CRITICAL", "enabled": False}
await repository.update_alert_rule(rule["id"], rule_update)

# Delete a rule
await repository.delete_alert_rule(rule["id"])
```

## API Endpoints

The water heater API provides these endpoints:

### Basic Operations

- `GET /api/v1/water-heaters` - Get all water heaters
- `GET /api/v1/water-heaters/{device_id}` - Get a specific water heater
- `POST /api/v1/water-heaters` - Create a new water heater
- `PATCH /api/v1/water-heaters/{device_id}/temperature` - Update target temperature
- `PATCH /api/v1/water-heaters/{device_id}/mode` - Update operational mode

### Readings and Diagnostics

- `POST /api/v1/water-heaters/{device_id}/readings` - Add a new reading
- `GET /api/v1/water-heaters/{device_id}/readings` - Get recent readings
- `GET /api/v1/water-heaters/{device_id}/thresholds` - Check threshold violations
- `GET /api/v1/water-heaters/{device_id}/maintenance` - Perform maintenance check

### Configuration Management

- `GET /api/v1/water-heaters/health-configuration` - Get health configuration
- `POST /api/v1/water-heaters/health-configuration` - Set health configuration
- `GET /api/v1/water-heaters/alert-rules` - Get alert rules
- `POST /api/v1/water-heaters/alert-rules` - Add a new alert rule
- `PUT /api/v1/water-heaters/alert-rules/{rule_id}` - Update an alert rule
- `DELETE /api/v1/water-heaters/alert-rules/{rule_id}` - Delete an alert rule

## Testing

The system follows Test-Driven Development (TDD) principles with these test suites:

1. **Repository Tests**: Test the SQLite implementation against the interface
2. **Service Tests**: Test service methods with mocked repositories
3. **API Tests**: Test API endpoints with mocked services
4. **Integration Tests**: Test full stack with in-memory SQLite database

Run tests with:

```bash
pytest -xvs tests/repositories/test_sqlite_water_heater_repository.py
pytest -xvs tests/api/test_configurable_water_heater_router.py
```

## Troubleshooting

### Common Issues

1. **Data Source Configuration**
   - Check the `USE_MOCK_DATA` environment variable if you're not seeing expected data sources.
   - For local development, the default is to use mock data.

2. **Database Connectivity**
   - Ensure the database path in `SQLiteWaterHeaterRepository` exists and is writable.
   - Default path is `data/iotsphere.db`.

3. **Health Status Configuration**
   - If water heaters show "UNKNOWN" health status, verify the health configuration exists.
   - Health statuses should be one of: "GREEN", "YELLOW", "RED".

4. **Alert Rules**
   - Alert rules use simple string conditions, not full Python expressions.
   - Supported comparisons: `>`, `<`, `>=`, `<=`, `==`, `!=`
   - Example: `"temperature > 75"` or `"pressure >= 6.0"`

### Debugging

Use logging to debug issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("water_heater_config")
```

Logs are output to help trace database operations, configuration changes, and API calls.
