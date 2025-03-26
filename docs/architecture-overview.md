# IoTSphere Architecture Overview

## Introduction

IoTSphere is built on a modern, maintainable architecture that separates backend data processing from frontend presentation. This document provides a comprehensive overview of the system architecture, component interactions, and design patterns.

## System Architecture

### High-Level Architecture

The IoTSphere application follows a client-server architecture with a clear separation of concerns:

```
┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
│                   │      │                   │      │                   │
│    Web Browser    │◄────►│   Python Server   │◄────►│     Database      │
│                   │      │                   │      │                   │
└───────────────────┘      └───────────────────┘      └───────────────────┘
       Frontend                  Backend                 Data Storage
```

- **Frontend**: HTML/CSS/JavaScript that runs in the browser
- **Backend**: Python Flask application providing API endpoints and business logic
- **Database**: SQL database storing application data

### Component Architecture

#### Backend Components

```
┌─────────────────────────────────────────────────────────────────┐
│                       Python Backend                            │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │             │    │             │    │                     │  │
│  │  API Layer  │───►│  Services   │───►│  Data Access Layer  │  │
│  │             │    │             │    │                     │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│         │                                        │              │
│         │                                        │              │
│  ┌─────────────┐                       ┌─────────────────────┐  │
│  │             │                       │                     │  │
│  │   Models    │◄──────────────────────┤      Database      │  │
│  │             │                       │                     │  │
│  └─────────────┘                       └─────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

1. **API Layer**: Defines the REST endpoints and handles HTTP requests and responses
2. **Services Layer**: Contains the business logic and orchestrates operations
3. **Data Access Layer**: Manages database interactions
4. **Models**: Defines data structures and validation rules

#### Frontend Components

```
┌─────────────────────────────────────────────────────────────────┐
│                       Frontend                                  │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │             │    │             │    │                     │  │
│  │  Templates  │───►│   JS Core   │───►│      API Client     │  │
│  │             │    │             │    │                     │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│         │                 │                      │              │
│         ▼                 ▼                      │              │
│  ┌─────────────┐    ┌─────────────┐              │              │
│  │             │    │             │              │              │
│  │    CSS      │    │  Components │◄─────────────┘              │
│  │             │    │             │                             │
│  └─────────────┘    └─────────────┘                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

1. **Templates**: HTML templates for rendering pages
2. **JS Core**: Core JavaScript functionality and utilities
3. **CSS**: Styling and visual presentation
4. **Components**: Reusable UI components
5. **API Client**: Handles communication with the backend API

## Key Design Patterns

### Backend

1. **Repository Pattern**: Abstracts data access logic
2. **Service Layer Pattern**: Centralizes business logic
3. **Factory Pattern**: Creates complex objects
4. **Dependency Injection**: Makes services and dependencies more testable

### Frontend

1. **Module Pattern**: Organizes JavaScript code
2. **Observer Pattern**: Enables event-driven UI updates
3. **Template Pattern**: Standardizes UI component rendering

## Communication Flow

### Request-Response Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│         │     │         │     │         │     │         │     │         │
│  Browser│────►│API Layer│────►│ Service │────►│Data Layer────►│Database │
│         │     │         │     │         │     │         │     │         │
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
     ▲               │               │               │               │
     │               │               │               │               │
     └───────────────┴───────────────┴───────────────┴───────────────┘
                             Response Flow
```

1. Browser sends HTTP request to API Layer
2. API Layer validates request and routes to appropriate Service
3. Service executes business logic, possibly using Data Layer
4. Data Layer interacts with the database
5. Response travels back through the layers to the browser

## Authentication & Authorization

IoTSphere uses JWT (JSON Web Tokens) for authentication:

1. **Authentication Flow**:
   - User submits credentials
   - Server validates credentials and issues a JWT
   - JWT is stored client-side
   - JWT is sent with subsequent requests

2. **Authorization Model**:
   - Role-based access control (RBAC)
   - Multiple user roles (Admin, Operator, Viewer)
   - Feature-based permissions

## Data Models

See [Data Models Documentation](./data-models.md) for detailed information.

## Scalability Considerations

IoTSphere is designed with scalability in mind:

1. **Horizontal Scaling**:
   - Stateless backend allows multiple server instances
   - Database connection pooling

2. **Performance Optimization**:
   - Data caching
   - Optimized database queries
   - Browser caching for static assets

## Deployment Architecture

### Production Deployment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│  Load Balancer  │───►│ Application     │───►│   Database      │
│                 │    │ Servers         │    │   Cluster       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Development Deployment

```
┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │
│  Python Server  │───►│  Local Database │
│                 │    │                 │
└─────────────────┘    └─────────────────┘
```

## Security Considerations

1. **Data Protection**:
   - TLS for all communications
   - Password hashing
   - Input validation and sanitization

2. **Application Security**:
   - CSRF protection
   - XSS prevention
   - Regular dependency updates

## Monitoring & Logging

1. **Application Monitoring**:
   - Performance metrics
   - Error tracking
   - User activity logs

2. **System Monitoring**:
   - Server health
   - Database performance
   - Network metrics

## Device Dashboards

### Water Heater Dashboard

The Water Heater Dashboard follows a tabbed interface pattern with three main views:

1. **Details Tab**: Displays basic water heater information including current temperature, target temperature, mode, and status. Provides controls for adjusting settings.

2. **Operations Tab**: Focused on real-time operational monitoring with:
   - Status cards showing current operational state
   - Asset health indicators
   - Gauge visualizations for temperature, pressure, flow rate, and energy usage
   - Real-time operational metrics

3. **History Tab**: Provides historical analytics through time-series charts:
   - Temperature history (actual vs. target)
   - Energy usage patterns
   - Pressure and flow rate trends
   - Customizable time ranges (7, 14, or 30 days)

#### Architecture Implementation

- **Backend**: Separate services handle device details, operations data, and historical metrics
- **APIs**: RESTful endpoints for each dashboard component (details, operations, history)
- **Frontend**: JavaScript modules leverage Chart.js for data visualization
- **Testing**: End-to-end tests verify data consistency across all three views

## Conclusion

This architecture provides a solid foundation for IoTSphere's current functionality while allowing for future growth and enhancements. The separation of concerns and modular design facilitate maintainability and scalability.
