# IoTSphere Marketecture

## Executive Overview

The IoTSphere platform is a device-agnostic IoT solution built according to Clean Architecture principles to support real-time monitoring, control, and analytics for smart devices with a focus on water heaters. This document provides a high-level overview of the key architectural components and data flows designed for executive stakeholders.

![IoTSphere Marketecture Diagram](../diagrams/iotsphere_marketecture.png)
*Figure 1: Clean Architecture-based IoT Platform*

> **Note:** The above diagram is generated from the PlantUML source file at `docs/diagrams/iotsphere_marketecture.puml`. See [Architecture Diagram Notes](architecture-note.md) for details on viewing these diagrams.

## Architectural Layers

Following Clean Architecture principles, the IoTSphere platform is structured into concentric layers with dependencies pointing inward, ensuring separation of concerns and testability throughout the development lifecycle:

### 1. Core Business Entities (Innermost)

The heart of the system contains pure business models independent of any technology:

- **Device Models**: Capability-based entities with manufacturer-agnostic specifications
- **Shadow Documents**: Consistent representation of device state (reported and desired)
- **Telemetry Models**: Time series data structures for sensor readings
- **Alert Entities**: Standardized condition monitoring and notification structures

### 2. Business Logic / Use Cases

This layer contains application-specific business rules and orchestrates the flow of data:

- **Device Shadow Service**: Provides real-time state synchronization using MongoDB's Change Data Capture
- **Telemetry Service**: Processes and analyzes sensor data streams
- **Device Management**: Handles device configuration and operational controls
- **Analytics Engine**: Delivers predictive insights and trend analysis
- **Notification Service**: Manages alerting and messaging workflows

### 3. Interface Adapters

This layer converts data between business logic and external frameworks:

- **REST Controllers**: Device API endpoints implementing our device-agnostic interfaces
- **WebSocket Manager**: Push notification system for real-time UI updates
- **Repository Adapters**: Data access objects abstracting underlying storage technologies

### 4. External Frameworks & Devices (Outermost)

The outermost layer contains frameworks, tools, and external systems:

- **Web Dashboard**: Angular-based UI for monitoring and control
- **Mobile Application**: Field service tools for technicians
- **API Gateway**: Centralized access point with authentication and routing
- **WebSocket Service**: Real-time communication channel
- **Storage**: MongoDB (device shadows), PostgreSQL (device registry), TimescaleDB (telemetry)
- **Message Broker**: Event bus implemented with Kafka/RabbitMQ
- **IoT Device Fleet**: Connected water heaters, vending machines, and future device types

## Key Benefits

This architecture delivers significant advantages to stakeholders:

1. **Real-time Responsiveness**: Push-based updates via WebSockets provide immediate visibility into device state changes
2. **Device Agnosticism**: Capability-based device models allow flexible onboarding of diverse device types
3. **Developer Efficiency**: Clean Architecture supports Test-Driven Development with clear boundaries
4. **Scalability**: Event-driven design with message brokers enables horizontal scaling
5. **Future-Proofing**: Clean separation between business logic and external systems simplifies technology migration

## Implementation Strategy

The development follows a Test-Driven Development approach with:

1. **RED Phase**: Writing failing tests to define requirements
2. **GREEN Phase**: Implementing minimal code to make tests pass
3. **REFACTOR Phase**: Improving code quality while maintaining test coverage

This ensures high-quality, maintainable code throughout the project lifecycle.
