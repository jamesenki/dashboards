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
│         ▼                 ▼                      ▼              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │             │    │             │    │                     │  │
│  │    CSS      │    │ TabManager  │───►│ Dashboard Components │  │
│  │             │    │             │    │                     │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                │                │
│                                                ▼                │
│                     ┌──────────────────────────────────────┐    │
│                     │           Dashboard Modules          │    │
│                     │                                      │    │
│                     │ ┌────────────┐  ┌────────────┐       │    │
│                     │ │            │  │            │       │    │
│                     │ │ Operations │  │ Predictions│       │    │
│                     │ │            │  │            │       │    │
│                     │ └────────────┘  └────────────┘       │    │
│                     │                                      │    │
│                     │ ┌────────────┐  ┌────────────┐       │    │
│                     │ │            │  │            │       │    │
│                     │ │  History   │  │  Details   │       │    │
│                     │ │            │  │            │       │    │
│                     │ └────────────┘  └────────────┘       │    │
│                     └──────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

1. **Templates**: HTML templates for rendering pages
2. **JS Core**: Core JavaScript functionality and utilities
3. **CSS**: Styling and visual presentation
4. **TabManager**: Centralized tab navigation and component lifecycle management system
5. **Dashboard Components**: Reusable dashboard UI components that implement the TabManager interface
6. **Dashboard Modules**:
   - **Operations**: Real-time operational monitoring with status cards and metrics
   - **Predictions**: Predictive analytics with action recommendations
   - **History**: Historical data visualization and analysis
   - **Details**: Basic device information and configuration

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

## Model Monitoring Dashboard

The Model Monitoring Dashboard provides comprehensive tools for tracking ML model performance and health over time. The dashboard follows a tabbed interface pattern with specialized views:

1. **Models Tab**: Displays all deployed models with filtering options for both active and archived models. Shows key performance indicators and model metadata.

2. **Performance Tab**: Focuses on ML model performance metrics:
   - Accuracy, precision, recall, and F1 scores over time
   - Performance trend visualizations
   - Threshold configuration for acceptable performance
   - Comparison between models

3. **Drift Tab**: Monitors data and concept drift to identify when models need retraining:
   - Feature drift visualization and metrics
   - Distribution comparisons between training and production data
   - Statistical measures of drift (PSI, JSI)
   - Drift alerts and thresholds

4. **Alerts Tab**: Centralized view of all model-related alerts:
   - Severity-based alert categorization (critical, high, medium, low)
   - Alert filtering by model, metric, and status
   - Alert management workflow (acknowledge, resolve)
   - Historical alert patterns

5. **Reports Tab**: Generates comprehensive model monitoring reports:
   - Template-based report generation (performance, drift, alerts)
   - Customizable date ranges and models
   - Export functionality for PDF and CSV formats
   - Visual representations of key metrics

### Export Functionality Architecture

The report export system uses a server-side generation approach for reliability and consistency:

- **Backend**: 
  - FastAPI endpoints (`/reports/export/pdf` and `/reports/export/csv`) handle export requests
  - ReportLab library generates professionally formatted PDF reports with charts and tables
  - Python's CSV module creates structured data exports
  - Mock data generation during development follows TDD principles

- **Frontend**:
  - JavaScript functions initiate export requests via fetch API
  - Proper MIME types and Content-Disposition headers enable browser download
  - UI provides clear feedback during export process

- **Testing**:
  - Integration tests verify API endpoints for exports
  - Unit tests confirm client-side export functions
  - Test-driven development approach ensures functionality meets requirements

### Architecture Implementation

- **Backend**: Dashboard API module handles data aggregation and export generation
- **APIs**: RESTful endpoints for each monitoring component with standardized response formats
- **Frontend**: JavaScript modules use Chart.js for interactive visualizations
- **Testing**: Comprehensive test suite validates both frontend and backend components
- **Design**: Dark theme UI with minimalist, clean interface following IoTSphere design principles

## Conclusion

This architecture provides a solid foundation for IoTSphere's current functionality while allowing for future growth and enhancements. The separation of concerns and modular design facilitate maintainability and scalability.
