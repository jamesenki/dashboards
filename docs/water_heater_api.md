# Water Heater API Documentation

## Overview

The IoTSphere Water Heater API is designed with a clear separation of concerns between mock data and real database implementations. This architecture ensures consistent behavior while providing transparency about which data source is being used at any time.

## Architecture

The API follows a layered architecture aligned with Test-Driven Development (TDD) principles:

1. **Interface Layer**: Defines the contract that both implementations must follow
2. **Implementation Layer**: Contains separate implementations for database and mock data
3. **Router Layer**: Exposes endpoints with consistent paths and behavior
4. **Service Layer**: Delegates requests to the appropriate repository
5. **Repository Layer**: Handles data access (mock or database)

```
┌────────────────┐    ┌────────────────┐
│   Mock API     │    │  Database API  │
│  (/api/mock/*) │    │   (/api/db/*)  │
└───────┬────────┘    └────────┬───────┘
        │                      │
        ▼                      ▼
┌────────────────┐    ┌────────────────┐
│  Mock Service  │    │   DB Service   │
└───────┬────────┘    └────────┬───────┘
        │                      │
        ▼                      ▼
┌────────────────┐    ┌────────────────┐
│Mock Repository │    │ DB Repository  │
└────────────────┘    └────────────────┘
```

## Available Endpoints

### Database API (`/api/db/water-heaters`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Get all water heaters from the database |
| GET | /{device_id} | Get a specific water heater by ID |
| POST | / | Create a new water heater in the database |
| GET | /data-source | Get information about the database data source |
| GET | /health | Check database health and connectivity |

### Mock API (`/api/mock/water-heaters`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Get all water heaters from mock data |
| GET | /{device_id} | Get a specific water heater by ID |
| POST | / | Create a new water heater in mock data |
| GET | /data-source | Get information about the mock data source |
| POST | /simulate/failure | Simulate a failure condition |
| GET | /simulation/status | Get current simulation status |

## Data Source Transparency

The API provides transparency about which data source is being used:

1. **Separate Base Paths**: `/api/db/*` vs `/api/mock/*`
2. **Data Source Info Endpoints**: Both implementations provide a `/data-source` endpoint
3. **Visual Indicators**: UI components show the active data source

## Mock API Simulation Controls

The mock API provides special endpoints for testing failure scenarios:

### Simulate Failure

```
POST /api/mock/water-heaters/simulate/failure?failure_type={type}
```

Available failure types:
- `network`: Simulates network connectivity issues
- `timeout`: Simulates slow responses or timeouts
- `validation`: Simulates validation errors
- `none`: Disables simulation

### Simulation Status

```
GET /api/mock/water-heaters/simulation/status
```

Returns the current simulation status including:
- Active simulation type
- Water heater count
- Timestamp

## Authentication and Authorization

The API currently doesn't require authentication. This will be addressed in future versions.

## Error Handling

All endpoints use standard HTTP status codes:

- `200`: Success
- `201`: Resource created successfully
- `400`: Bad request
- `404`: Resource not found
- `422`: Validation error
- `500`: Server error

## Data Models

The Water Heater model includes these key fields:

- `id`: Unique identifier
- `name`: Human-readable name
- `status`: Current operational status
- `type`: Always "WATER_HEATER"
- `target_temperature`: Target water temperature in Celsius
- `current_temperature`: Current water temperature in Celsius
- `min_temperature`: Minimum settable temperature
- `max_temperature`: Maximum settable temperature
- `mode`: Operational mode (ECO, BOOST, etc.)
- `heater_status`: Current heating status (HEATING, STANDBY)

## Versioning

API versioning is handled through the version control utility. The current version is 1.0.0.

## Database Implementation

The database implementation uses SQLite by default and creates these tables:
- water_heaters (main data)
- water_heater_readings (temperature, pressure, etc.)
- water_heater_diagnostic_codes (error codes)
- water_heater_health_config (thresholds)
- water_heater_alert_rules (monitoring rules)

## Mock Implementation

The mock implementation uses in-memory data structures with predefined sample data. It provides a consistent interface with the database implementation while allowing controlled testing of error scenarios.
