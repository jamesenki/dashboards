# IoTSphere Water Heater API Documentation

## Overview

This document provides comprehensive documentation for the IoTSphere Water Heater APIs. These REST APIs enable developers to interact with water heaters in the IoTSphere platform programmatically.

> **Important:** The platform has transitioned to a manufacturer-agnostic API design. Legacy endpoints for specific manufacturers (including the `/api/water-heaters` endpoint) have been deprecated and are maintained only for backward compatibility.

## Manufacturer-Agnostic Water Heater API

### Base URL

All water heater API endpoints are relative to:

```
/api/manufacturer/water-heaters
```

### Authentication

All API requests require authentication using JWT (JSON Web Tokens).

### Available Endpoints

#### List Water Heaters

```
GET /api/manufacturer/water-heaters
```

Query Parameters:
- `manufacturer` (optional): Filter by manufacturer (e.g., "Rheem")
- `status` (optional): Filter by device status (active, inactive, maintenance)
- `limit` (optional): Number of results per page (default: 20)
- `offset` (optional): Pagination offset (default: 0)

Response:
```json
{
  "total": 6,
  "items": [
    {
      "id": "wh-d94a7707",
      "name": "Rheem Classic Tank",
      "manufacturer": "Rheem",
      "model": "Classic 50 Gallon",
      "type": "water-heater",
      "status": "online",
      "location": "Basement",
      "target_temperature": 120,
      "current_temperature": 118,
      "min_temperature": 90,
      "max_temperature": 140,
      "mode": "eco",
      "heater_status": "standby",
      "capacity": 50,
      "efficiency_rating": 0.92
    },
    ...
  ]
}
```

#### Get Water Heater Details

```
GET /api/manufacturer/water-heaters/{id}
```

Response:
```json
{
  "id": "wh-d94a7707",
  "name": "Rheem Classic Tank",
  "manufacturer": "Rheem",
  "model": "Classic 50 Gallon",
  "type": "water-heater",
  "status": "online",
  "location": "Basement",
  "target_temperature": 120,
  "current_temperature": 118,
  "min_temperature": 90,
  "max_temperature": 140,
  "mode": "eco",
  "heater_status": "standby",
  "capacity": 50,
  "efficiency_rating": 0.92,
  "last_maintenance": "2025-01-15T09:00:00Z",
  "installation_date": "2024-05-10T14:30:00Z",
  "warranty_expiration": "2034-05-10T00:00:00Z"
}
```

#### Update Water Heater Settings

```
PATCH /api/manufacturer/water-heaters/{id}/settings
```

Request:
```json
{
  "target_temperature": 122,
  "mode": "standard"
}
```

Response:
```json
{
  "success": true,
  "id": "wh-d94a7707",
  "updated_settings": {
    "target_temperature": 122,
    "mode": "standard"
  },
  "updated_at": "2025-04-05T14:22:33Z"
}
```

#### Get Water Heater Telemetry

```
GET /api/manufacturer/water-heaters/{id}/telemetry
```

Query Parameters:
- `metric` (optional): Specific metric to retrieve (temperature, pressure, etc.)
- `from` (optional): Start timestamp (ISO 8601)
- `to` (optional): End timestamp (ISO 8601)
- `interval` (optional): Aggregation interval (raw, 1m, 5m, 1h, 1d)

Response:
```json
{
  "id": "wh-d94a7707",
  "metrics": {
    "temperature": [
      {
        "timestamp": "2025-04-05T14:00:00Z",
        "value": 118.5
      },
      {
        "timestamp": "2025-04-05T14:05:00Z",
        "value": 119.2
      },
      ...
    ],
    "pressure": [
      {
        "timestamp": "2025-04-05T14:00:00Z",
        "value": 68.3
      },
      ...
    ]
  }
}
```

#### Get Water Heater Health Prediction

```
GET /api/manufacturer/water-heaters/{id}/health
```

Response:
```json
{
  "id": "wh-d94a7707",
  "health_score": 92,
  "predicted_issues": [],
  "estimated_lifespan": "12.5 years",
  "maintenance_recommendation": "No maintenance needed at this time",
  "next_maintenance_date": "2025-10-15T00:00:00Z",
  "component_health": {
    "heating_element": {
      "health": 95,
      "estimated_remaining_life": "5.2 years"
    },
    "thermostat": {
      "health": 98,
      "estimated_remaining_life": "6.8 years"
    },
    "pressure_relief_valve": {
      "health": 90,
      "estimated_remaining_life": "4.1 years"
    }
  }
}
```

## Deprecated APIs

The following API endpoints are deprecated and will be removed in a future release. Please migrate to the manufacturer-agnostic endpoints above.

### AquaTherm-Specific Endpoint (Deprecated)

```
GET /api/water-heaters
```

This endpoint returns mock AquaTherm water heaters and should not be used in production.

### Additional Deprecated Endpoints

- `GET /api/aquatherm/water-heaters` - Use `/api/manufacturer/water-heaters?manufacturer=Rheem` instead
- `GET /api/aquatherm/water-heaters/{id}` - Use `/api/manufacturer/water-heaters/{id}` instead
- `PATCH /api/aquatherm/water-heaters/{id}/settings` - Use `/api/manufacturer/water-heaters/{id}/settings` instead

## Future-Proof Integration

When integrating with the IoTSphere platform, always:

1. Use the manufacturer-agnostic endpoints
2. Include the manufacturer parameter when filtering is needed
3. Avoid hardcoding manufacturer-specific behaviors in your code
4. Be prepared to handle different attribute names across manufacturers (use the canonical model)
