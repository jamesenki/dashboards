# IoTSphere API Documentation

## Overview

This document provides comprehensive documentation for the IoTSphere platform APIs. These REST APIs enable developers to interact with the IoTSphere platform programmatically, allowing for device management, data retrieval, and platform configuration.

> **Note:** This document reflects the current manufacturer-agnostic API design. Legacy endpoints for specific manufacturers have been deprecated.

## Base URL

All API endpoints are relative to the base URL:

```
https://api.iotsphere.example.com/v1
```

## Authentication

All API requests require authentication using JWT (JSON Web Tokens). To authenticate:

1. Obtain a token via the `/auth/token` endpoint
2. Include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## API Endpoints

### Device Management

#### List Devices

```
GET /devices
```

Query Parameters:
- `status` (optional): Filter by device status (active, inactive, maintenance)
- `type` (optional): Filter by device type
- `limit` (optional): Number of results per page (default: 20)
- `offset` (optional): Pagination offset (default: 0)

Response:
```json
{
  "total": 125,
  "limit": 20,
  "offset": 0,
  "devices": [
    {
      "id": "device-001",
      "name": "Water Heater 1",
      "type": "water-heater",
      "status": "active",
      "lastSeen": "2025-03-15T14:32:10Z",
      "firmware": "v2.1.0",
      "metrics": {
        "temperature": 68.5,
        "pressure": 42.1,
        "energyConsumption": 1.2
      }
    },
    ...
  ]
}
```

#### Get Device Details

```
GET /devices/{deviceId}
```

Response:
```json
{
  "id": "device-001",
  "name": "Water Heater 1",
  "type": "water-heater",
  "status": "active",
  "lastSeen": "2025-03-15T14:32:10Z",
  "firmware": "v2.1.0",
  "location": {
    "building": "Main Office",
    "floor": 3,
    "room": "Kitchen"
  },
  "configuration": {
    "targetTemperature": 70,
    "operationMode": "standard",
    "scheduleEnabled": true
  },
  "metrics": {
    "temperature": 68.5,
    "pressure": 42.1,
    "energyConsumption": 1.2,
    "flowRate": 5.3,
    "totalEnergyUsed": 128.5
  },
  "maintenance": {
    "lastServiced": "2025-01-10T09:00:00Z",
    "nextScheduled": "2025-07-10T09:00:00Z",
    "components": [
      {
        "name": "heating_element",
        "status": "good",
        "estimatedLifespan": "450 days"
      },
      {
        "name": "pressure_valve",
        "status": "attention",
        "estimatedLifespan": "120 days"
      }
    ]
  }
}
```

#### Update Device Configuration

```
PATCH /devices/{deviceId}/configuration
```

Request:
```json
{
  "targetTemperature": 72,
  "operationMode": "eco",
  "scheduleEnabled": true
}
```

Response:
```json
{
  "success": true,
  "deviceId": "device-001",
  "configuration": {
    "targetTemperature": 72,
    "operationMode": "eco",
    "scheduleEnabled": true
  },
  "appliedAt": "2025-04-02T14:15:22Z"
}
```

### Telemetry Data

#### Get Historical Telemetry

```
GET /devices/{deviceId}/telemetry
```

Query Parameters:
- `metric` (required): Metric name (temperature, pressure, etc.)
- `from` (required): Start timestamp (ISO 8601)
- `to` (required): End timestamp (ISO 8601)
- `interval` (optional): Aggregation interval (raw, 1m, 5m, 1h, 1d)

Response:
```json
{
  "deviceId": "device-001",
  "metric": "temperature",
  "from": "2025-03-01T00:00:00Z",
  "to": "2025-03-02T00:00:00Z",
  "interval": "1h",
  "data": [
    {
      "timestamp": "2025-03-01T00:00:00Z",
      "value": 68.2,
      "min": 67.8,
      "max": 68.5,
      "avg": 68.1
    },
    ...
  ]
}
```

### Alerts

#### List Alerts

```
GET /alerts
```

Query Parameters:
- `deviceId` (optional): Filter by device
- `severity` (optional): Filter by severity (info, warning, critical)
- `status` (optional): Filter by status (active, acknowledged, resolved)
- `from` (optional): Start timestamp (ISO 8601)
- `to` (optional): End timestamp (ISO 8601)

Response:
```json
{
  "total": 5,
  "alerts": [
    {
      "id": "alert-001",
      "deviceId": "device-001",
      "timestamp": "2025-03-15T08:12:45Z",
      "type": "high_temperature",
      "severity": "warning",
      "message": "Temperature exceeded threshold: 85°C",
      "status": "active",
      "metrics": {
        "temperature": 85.2,
        "threshold": 80.0
      }
    },
    ...
  ]
}
```

#### Acknowledge Alert

```
POST /alerts/{alertId}/acknowledge
```

Response:
```json
{
  "success": true,
  "alertId": "alert-001",
  "status": "acknowledged",
  "acknowledgedAt": "2025-04-02T14:20:15Z",
  "acknowledgedBy": "user@example.com"
}
```

### Maintenance Predictions

#### Get Maintenance Predictions

```
GET /devices/{deviceId}/maintenance/predictions
```

Response:
```json
{
  "deviceId": "device-001",
  "lastUpdated": "2025-04-01T12:00:00Z",
  "overallHealth": 82,
  "estimatedNextMaintenance": "2025-07-10T00:00:00Z",
  "components": [
    {
      "name": "heating_element",
      "health": 90,
      "predictionConfidence": "high",
      "estimatedRemainingLife": "450 days",
      "recommendedAction": "none"
    },
    {
      "name": "pressure_valve",
      "health": 60,
      "predictionConfidence": "medium",
      "estimatedRemainingLife": "120 days",
      "recommendedAction": "inspect"
    }
  ],
  "factors": [
    {
      "name": "operation_cycles",
      "impact": "medium",
      "details": "Device has completed 1,200 heating cycles"
    },
    {
      "name": "water_quality",
      "impact": "high",
      "details": "High mineral content detected"
    }
  ]
}
```

## Error Handling

All API endpoints return standard HTTP status codes. In case of an error, the response body will include details:

```json
{
  "error": {
    "code": "invalid_parameter",
    "message": "Invalid date range specified",
    "details": "The 'from' date must be before the 'to' date"
  }
}
```

Common error codes:
- `invalid_parameter`: One or more request parameters are invalid
- `not_found`: Requested resource does not exist
- `unauthorized`: Authentication failure
- `forbidden`: Insufficient permissions
- `internal_error`: Unexpected server error

## Rate Limiting

API requests are rate-limited to 100 requests per minute per API key. Rate limit headers are included in each response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1617394980
```

When the rate limit is exceeded, a 429 (Too Many Requests) status code is returned.

## Versioning

The API version is included in the URL path (e.g., `/v1/devices`). When breaking changes are introduced, the version number will be incremented.

## Real-time Device Shadow Service (WebSocket API)

The Device Shadow Service provides real-time state synchronization for IoT devices using WebSockets and Change Data Capture (CDC) with MongoDB Change Streams. This enables efficient push-based updates instead of polling.

### WebSocket Base URL

```
wss://api.iotsphere.example.com/ws/v1
```

### Authentication

WebSocket connections use the same JWT authentication as REST APIs. Send the token in the connection handshake:

```javascript
// Example WebSocket connection with authentication
const ws = new WebSocket('wss://api.iotsphere.example.com/ws/v1/shadows?token=YOUR_JWT_TOKEN');
```

### Shadow Service WebSocket Endpoints

#### Subscribe to Device Shadows

Endpoint: `wss://api.iotsphere.example.com/ws/v1/shadows`

After establishing a WebSocket connection, subscribe to device shadow updates:

```json
{
  "type": "subscribe",
  "target": "shadow",
  "deviceIds": ["device-001", "device-002"],
  "operations": ["reported", "desired", "delta"]
}
```

Parameters:
- `deviceIds`: Array of device IDs to subscribe to (required)
- `operations`: Array of shadow operations to subscribe to (optional, defaults to all)
  - `reported`: Device-reported state changes
  - `desired`: Application-desired state changes
  - `delta`: Difference between reported and desired states

#### Shadow Update Messages

Shadow updates are pushed to clients in the following format:

```json
{
  "type": "shadow_update",
  "deviceId": "device-001",
  "timestamp": "2025-04-10T12:34:56Z",
  "operation": "reported",
  "version": 423,
  "data": {
    "temperature": 68.5,
    "humidity": 42,
    "status": "normal"
  }
}
```

#### Update Device Shadow

To update a device shadow's desired state:

```json
{
  "type": "update_shadow",
  "deviceId": "device-001",
  "operation": "desired",
  "data": {
    "targetTemperature": 72
  }
}
```

#### Shadow Error Messages

```json
{
  "type": "error",
  "code": "SHADOW_NOT_FOUND",
  "message": "Device shadow not found",
  "deviceId": "device-001"
}
```

### Telemetry WebSocket Streaming

For real-time telemetry data, use the telemetry WebSocket endpoint:

```
wss://api.iotsphere.example.com/ws/v1/telemetry
```

#### Subscribe to Telemetry Stream

```json
{
  "type": "subscribe",
  "metrics": ["temperature", "pressure"],
  "deviceIds": ["device-001", "device-002"],
  "aggregation": "raw"
}
```

Parameters:
- `metrics`: Array of metrics to subscribe to (required)
- `deviceIds`: Array of device IDs to subscribe to (required)
- `aggregation`: Data aggregation level (optional, defaults to "raw")
  - Options: "raw", "1m", "5m", "1h"

#### Telemetry Stream Messages

```json
{
  "type": "telemetry",
  "deviceId": "device-001",
  "timestamp": "2025-04-10T12:34:56.789Z",
  "metric": "temperature",
  "value": 68.5,
  "unit": "F"
}
```

#### WebSocket Error Handling

WebSocket errors follow a similar pattern to REST API errors:

```json
{
  "type": "error",
  "code": "SUBSCRIPTION_FAILED",
  "message": "Failed to subscribe to device updates",
  "details": "Maximum subscription limit reached"
}
```

## Testing

Following Test-Driven Development principles, every API endpoint (both REST and WebSocket) has corresponding automated tests to verify functionality, security, and performance. Tests are organized according to the TDD phases:

- **RED Phase**: Tests that define expected behavior
- **GREEN Phase**: Tests that verify implementation meets requirements
- **REFACTOR Phase**: Tests that ensure quality improvements maintain functionality

API test cases are available in the IoTSphere repository and can be used as additional reference for API behavior.
