# IoTSphere API Documentation

## Overview

The IoTSphere API provides a comprehensive set of RESTful endpoints for interacting with IoT devices, user management, and data visualization. This document details the available endpoints, request/response formats, and authentication requirements.

## Base URL

All API URLs referenced in this documentation have the following base:

```
http://localhost:8006/api/v1
```

For production environments, replace with your production domain.

## Authentication

Most API endpoints require authentication using JSON Web Tokens (JWT).

### Obtaining a Token

```
POST /auth/login
```

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2025-04-26T16:00:00Z",
  "user_id": "user-123",
  "role": "admin"
}
```

### Using a Token

Include the token in the Authorization header of subsequent requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## API Endpoints

### Vending Machines

#### List All Vending Machines

```
GET /vending-machines
```

**Query Parameters:**
- `status` (optional): Filter by status (e.g., "ONLINE", "OFFLINE")
- `location` (optional): Filter by location
- `page` (optional): Page number for pagination (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response:**
```json
{
  "machines": [
    {
      "id": "vm-123",
      "name": "Ice Cream Machine 1",
      "location": "Main Floor",
      "status": "ONLINE",
      "last_connection": "2025-03-26T11:30:00Z"
    },
    ...
  ],
  "pagination": {
    "total": 45,
    "page": 1,
    "per_page": 20,
    "pages": 3
  }
}
```

#### Get Vending Machine Details

```
GET /vending-machines/{machine_id}
```

**Response:**
```json
{
  "id": "vm-123",
  "name": "Ice Cream Machine 1",
  "location": "Main Floor",
  "status": "ONLINE",
  "model": "PolarDelight-3000",
  "firmware_version": "2.4.1",
  "installation_date": "2024-08-20",
  "last_maintenance": "2025-02-15",
  "last_connection": "2025-03-26T11:30:00Z",
  "readings": [
    {
      "timestamp": "2025-03-26T11:30:00Z",
      "temperature": -15.5,
      "door_status": "CLOSED"
    }
  ]
}
```

#### Update Vending Machine

```
PUT /vending-machines/{machine_id}
```

**Request Body:**
```json
{
  "name": "Ice Cream Machine 1 - Updated",
  "location": "Front Lobby"
}
```

**Response:**
```json
{
  "id": "vm-123",
  "name": "Ice Cream Machine 1 - Updated",
  "location": "Front Lobby",
  "status": "ONLINE"
}
```

### Operations Data

#### Get Real-time Operations Data

```
GET /vending-machines/{machine_id}/operations-realtime
```

**Response:**
```json
{
  "machine_id": "vm-123",
  "machine_status": "Online",
  "pod_code": "12345",
  "cup_detect": "Yes",
  "customer_door": "Closed",
  "dispense_pressure": {
    "dispensePressure": "35.5",
    "min": "10",
    "max": "50"
  },
  "freezer_temperature": {
    "freezerTemperature": "-15.2",
    "min": "-20",
    "max": "0"
  },
  "cycle_time": {
    "cycleTime": "18.3",
    "min": "15",
    "max": "25"
  },
  "ice_cream_inventory": [
    {
      "name": "Vanilla",
      "level": 75,
      "max_capacity": 100
    },
    {
      "name": "Chocolate",
      "level": 60,
      "max_capacity": 100
    },
    {
      "name": "Strawberry",
      "level": 30,
      "max_capacity": 100
    },
    {
      "name": "Mint",
      "level": 85,
      "max_capacity": 100
    }
  ]
}
```

#### Get Historical Operations Data

```
GET /vending-machines/{machine_id}/operations
```

**Query Parameters:**
- `start_date` (optional): Start date for data (format: YYYY-MM-DD)
- `end_date` (optional): End date for data (format: YYYY-MM-DD)

**Response:**
```json
{
  "machine_id": "vm-123",
  "period": {
    "start": "2025-03-19",
    "end": "2025-03-26"
  },
  "sales_data": {
    "total_sales": 1250.50,
    "units_sold": 350,
    "average_transaction": 3.57
  },
  "usage_patterns": [
    {
      "day": "Monday",
      "transactions": 45,
      "peak_hour": "12:00"
    },
    ...
  ],
  "maintenance_history": [
    {
      "date": "2025-03-20",
      "type": "Scheduled",
      "description": "Filter replacement"
    }
  ],
  "temperature_trends": {
    "average": -15.5,
    "min": -18.2,
    "max": -12.1,
    "readings": [
      {
        "timestamp": "2025-03-20T00:00:00Z",
        "value": -15.5
      },
      ...
    ]
  }
}
```

### Users and Authentication

#### List Users

```
GET /users
```

**Response:**
```json
{
  "users": [
    {
      "id": "user-123",
      "username": "admin@example.com",
      "role": "admin",
      "last_login": "2025-03-26T10:15:00Z"
    },
    ...
  ]
}
```

#### Get User Details

```
GET /users/{user_id}
```

**Response:**
```json
{
  "id": "user-123",
  "username": "admin@example.com",
  "role": "admin",
  "first_name": "Admin",
  "last_name": "User",
  "email": "admin@example.com",
  "created_at": "2024-09-15T00:00:00Z",
  "last_login": "2025-03-26T10:15:00Z"
}
```

#### Create User

```
POST /users
```

**Request Body:**
```json
{
  "username": "new.user@example.com",
  "password": "secure-password",
  "role": "operator",
  "first_name": "New",
  "last_name": "User",
  "email": "new.user@example.com"
}
```

**Response:**
```json
{
  "id": "user-456",
  "username": "new.user@example.com",
  "role": "operator",
  "created_at": "2025-03-26T12:00:00Z"
}
```

#### Update User

```
PUT /users/{user_id}
```

**Request Body:**
```json
{
  "role": "admin",
  "first_name": "Updated",
  "last_name": "User"
}
```

**Response:**
```json
{
  "id": "user-456",
  "username": "new.user@example.com",
  "role": "admin",
  "first_name": "Updated",
  "last_name": "User",
  "updated_at": "2025-03-26T12:30:00Z"
}
```

#### Delete User

```
DELETE /users/{user_id}
```

**Response:**
```
204 No Content
```

### Alerts and Notifications

#### List Alerts

```
GET /alerts
```

**Query Parameters:**
- `status` (optional): Filter by status (e.g., "ACTIVE", "RESOLVED")
- `severity` (optional): Filter by severity (e.g., "HIGH", "MEDIUM", "LOW")
- `machine_id` (optional): Filter by machine ID

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert-123",
      "machine_id": "vm-123",
      "type": "TEMPERATURE",
      "message": "Freezer temperature above threshold",
      "severity": "HIGH",
      "status": "ACTIVE",
      "created_at": "2025-03-26T09:15:00Z"
    },
    ...
  ]
}
```

#### Update Alert Status

```
PUT /alerts/{alert_id}
```

**Request Body:**
```json
{
  "status": "RESOLVED",
  "resolution_notes": "Technician adjusted freezer settings"
}
```

**Response:**
```json
{
  "id": "alert-123",
  "status": "RESOLVED",
  "resolved_at": "2025-03-26T13:45:00Z",
  "resolved_by": "user-123",
  "resolution_notes": "Technician adjusted freezer settings"
}
```

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `204 No Content`: Request succeeded (no response body)
- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Authentication valid but insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Request validation error
- `500 Internal Server Error`: Server-side error

Error responses follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

## Rate Limiting

The API employs rate limiting to prevent abuse:

- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1616669600
```

## Pagination

List endpoints support pagination with the following parameters:

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

Pagination information is included in the response:

```json
{
  "items": [...],
  "pagination": {
    "total": 45,
    "page": 1,
    "per_page": 20,
    "pages": 3
  }
}
```

## Versioning

The API is versioned through the URL path (`/api/v1/`). When breaking changes are introduced, a new version will be created (e.g., `/api/v2/`).

## WebSocket API

For real-time updates, the API provides WebSocket endpoints:

### Connection

```
ws://localhost:8006/ws/v1
```

Include the JWT token as a query parameter:

```
ws://localhost:8006/ws/v1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Event Types

The WebSocket API sends the following event types:

1. **machine_status**: Machine status changes
2. **alert**: New alerts
3. **reading**: New sensor readings

Example message:

```json
{
  "type": "machine_status",
  "data": {
    "machine_id": "vm-123",
    "status": "OFFLINE",
    "timestamp": "2025-03-26T14:15:00Z"
  }
}
```

## Further Assistance

For additional support with the API:

- Check the developer documentation
- Contact the API team at api-support@iotsphere.example.com
- Submit issues through the internal ticket system
