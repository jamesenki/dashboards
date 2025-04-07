# IoTSphere Current Architecture

## Overview

This document outlines the current architecture of the IoTSphere platform following recent refactoring efforts. The platform has been redesigned to support a manufacturer-agnostic approach for water heaters, with a vision toward supporting multiple device types in the future.

## Current Architecture

The current architecture follows a layered approach with clean separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ HTML/CSS    │  │ JavaScript  │  │ UI          │         │
│  │ Templates   │  │ Modules     │  │ Components  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  ┌─────────────────────┐  ┌───────────────────────────┐    │
│  │ Manufacturer-       │  │ Device Management APIs    │    │
│  │ Agnostic APIs       │  │                           │    │
│  └─────────────────────┘  └───────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Water Heater│  │ User        │  │ Analytics   │         │
│  │ Service     │  │ Service     │  │ Service     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Repository Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PostgreSQL  │  │ SQLite      │  │ Mock Data   │         │
│  │ Repository  │  │ Repository  │  │ Repository  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     Database Layer                          │
│  ┌─────────────────────┐  ┌───────────────────────────┐    │
│  │ PostgreSQL          │  │ SQLite (Development/Test) │    │
│  │ TimescaleDB         │  │                           │    │
│  └─────────────────────┘  └───────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Frontend Layer

The frontend uses a lightweight JavaScript/HTML approach instead of the previous Angular framework:

- **HTML/CSS Templates**: Server-side rendered templates using Jinja2
- **JavaScript Modules**: Client-side logic for interactive components
- **UI Components**: Modular components for water heater display and control

#### 2. API Layer

The API layer exposes REST endpoints for client interactions:

- **Manufacturer-Agnostic APIs**: Brand-neutral endpoints for water heaters (`/api/manufacturer/water-heaters`)
- **Device Management APIs**: APIs for device registration, status updates, and configuration

#### 3. Service Layer

Services implement the business logic of the application:

- **ConfigurableWaterHeaterService**: The main service managing water heater operations
- **User Service**: Handles authentication and authorization
- **Analytics Service**: Processes telemetry data for insights and predictions

#### 4. Repository Layer

Repositories provide data access abstraction:

- **PostgreSQL Repository**: Production data access for water heaters
- **SQLite Repository**: Alternative for development/testing
- **Mock Data Repository**: Fallback for testing and demos

#### 5. Database Layer

The persistence layer stores all application data:

- **PostgreSQL with TimescaleDB**: Primary database for production
- **SQLite**: Lightweight alternative for development and testing

### Current Implementation Focus

The current implementation focuses on water heaters with these key features:

1. **Manufacturer-Agnostic API**: Common interface for all water heater brands
2. **PostgreSQL Integration**: Reliable data storage with time-series capabilities
3. **Water Heater Management**: Comprehensive monitoring and control
4. **Cache Management**: Proper cache handling for remote clients

## Connection to Target Architecture

The current implementation serves as the foundation for the planned device-agnostic architecture outlined in [device_agnostic_platform.md](./device_agnostic_platform.md). Specifically:

1. The manufacturer-agnostic API design is a stepping stone toward the full capability-based architecture
2. The repository pattern enables the addition of new device types and data sources
3. The service layer can be extended to support the planned capability framework
4. The frontend components will evolve into the planned modular UI framework

## Deprecated Components

The following components have been deprecated and archived:

1. **AquaTherm-Specific Frontend Files**: CSS and JavaScript for AquaTherm water heaters
2. **Mock Water Heater API**: Legacy endpoint returning simulated devices
3. **AquaTherm-Specific APIs**: Brand-specific endpoints and implementation
4. **Debug and Test Files**: Temporary files used during development

## Next Steps

The immediate next steps in the architecture evolution are:

1. Complete water heater feature set
2. Design core device model interfaces
3. Begin database schema preparation for multi-device support
4. Extract reusable components from water heater UI
