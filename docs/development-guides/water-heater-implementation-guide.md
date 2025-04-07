# Water Heater Implementation Guide

## Overview

This guide documents the current implementation of the water heater functionality in IoTSphere. It serves as a reference for developers working on water heater features or using the platform as a starting point for implementing new device types.

## Key Components

### Data Model

The water heater data model is defined in `src/models/water_heater.py`:

```python
class WaterHeater(BaseModel):
    id: str
    name: str
    manufacturer: str
    model: str
    type: DeviceType = DeviceType.WATER_HEATER
    status: DeviceStatus = DeviceStatus.ONLINE
    location: Optional[str] = None
    target_temperature: float
    current_temperature: float
    min_temperature: float
    max_temperature: float
    mode: WaterHeaterMode = WaterHeaterMode.STANDARD
    heater_status: WaterHeaterStatus = WaterHeaterStatus.STANDBY
    capacity: Optional[float] = None
    efficiency_rating: Optional[float] = None
```

### API Endpoints

The manufacturer-agnostic water heater API is defined in `src/api/routes/manufacturer_water_heaters.py`. Key endpoints include:

- `GET /api/manufacturer/water-heaters` - List water heaters with optional filtering
- `GET /api/manufacturer/water-heaters/{id}` - Get details for a specific water heater
- `PATCH /api/manufacturer/water-heaters/{id}/settings` - Update water heater settings
- `GET /api/manufacturer/water-heaters/{id}/telemetry` - Get water heater telemetry data
- `GET /api/manufacturer/water-heaters/{id}/health` - Get health predictions for a water heater

### Service Layer

The `ConfigurableWaterHeaterService` in `src/services/configurable_water_heater_service.py` provides the business logic for water heater operations. This service:

1. Selects the appropriate repository based on environment configuration
2. Normalizes data from different sources into a consistent format
3. Handles fallback logic when the primary data source is unavailable
4. Implements caching for improved performance

### Database Schema

The water heater database schema in PostgreSQL includes these key tables:

```sql
-- Main water heater table
CREATE TABLE water_heaters (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    manufacturer VARCHAR NOT NULL,
    model VARCHAR,
    status VARCHAR,
    location VARCHAR,
    target_temperature FLOAT,
    current_temperature FLOAT,
    min_temperature FLOAT,
    max_temperature FLOAT,
    mode VARCHAR,
    heater_status VARCHAR,
    capacity FLOAT,
    efficiency_rating FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Telemetry data with time-series optimization
CREATE TABLE water_heater_readings (
    id SERIAL PRIMARY KEY,
    water_heater_id VARCHAR REFERENCES water_heaters(id),
    temperature FLOAT,
    pressure FLOAT,
    flow_rate FLOAT,
    power_consumption FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Diagnostics and error information
CREATE TABLE water_heater_diagnostic_codes (
    id SERIAL PRIMARY KEY,
    water_heater_id VARCHAR REFERENCES water_heaters(id),
    code VARCHAR,
    description TEXT,
    severity VARCHAR,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);
```

### Frontend Implementation

The frontend water heater implementation consists of:

1. **HTML Templates**: `frontend/templates/water-heater/list.html` and `frontend/templates/water-heater/detail.html`
2. **JavaScript Modules**:
   - `frontend/static/js/water-heater-new.js` - Core water heater functionality
   - `frontend/static/js/api.js` - API client for water heater endpoints
3. **CSS Styling**: `frontend/static/css/water-heater.css`

## Implementation Notes

### Manufacturer Compatibility

The current implementation focuses on Rheem water heaters but has been designed to be manufacturer-agnostic:

1. The API accepts a `manufacturer` parameter to filter devices
2. Device attributes follow a standardized model regardless of manufacturer
3. Manufacturer-specific details are stored in the metadata JSON field when needed

### Database Fallback Strategy

The system includes fallback mechanisms when the database is unavailable:

1. ConnectionCheck service monitors database health
2. Environment variables control fallback behavior:
   - `USE_MOCK_DATA=false` - Disables using mock data by default
   - `FALLBACK_TO_MOCK=false` - Disables fallback to mock data when database is unavailable

### Cache Management

To ensure consistent data across different clients and networks:

1. API responses include appropriate cache headers
2. Frontend JavaScript files include cache-busting parameters (`?v=20250405`)
3. AJAX requests include timestamp parameters to prevent browser caching

## Testing

The water heater implementation includes several test types:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Verify interactions between components
3. **UI Validation**: Confirm proper data display in the frontend
4. **End-to-End Tests**: Test complete user flows

## Extending the Implementation

When extending the water heater implementation:

1. Follow the manufacturer-agnostic approach
2. Use the repository pattern for data access
3. Keep business logic in the service layer
4. Ensure frontend components properly handle different manufacturers
5. Add appropriate tests for new functionality
