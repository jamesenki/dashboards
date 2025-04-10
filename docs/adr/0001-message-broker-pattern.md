# ADR 0001: Implementation of Message Broker Pattern for Real-Time MQTT Architecture

## Date: 2025-04-10

## Status
Accepted

## Context
The IoTSphere application requires real-time updates of device shadow data from MongoDB to the frontend UI. The previous architecture used a direct polling mechanism from the frontend to the backend API, which had several limitations:

1. **Scalability Issues**: Polling created unnecessary load on the backend
2. **Limited Real-Time Capabilities**: Updates were delayed by the polling interval
3. **Network Overhead**: Redundant requests were made even when no data changed
4. **Poor Resource Utilization**: Backend resources were consumed regardless of data changes

The application needs a more efficient way to transmit real-time device shadow and telemetry data from MongoDB to the frontend while maintaining proper separation of concerns according to Clean Architecture principles.

## Decision
We will implement a Message Broker Pattern using MQTT as the messaging protocol with the following components:

1. **ShadowPublisher**: Publishes shadow updates from MongoDB to MQTT
2. **MongoDBShadowListener**: Listens for changes in MongoDB via change streams
3. **MQTT-WebSocket Bridge**: Connects MQTT messages to WebSocket clients
4. **MessageBrokerIntegrator**: Coordinates all components during startup/shutdown

The data flow will be:
```
Device → IoT Agent → External MQTT → MessageService → MongoDB → Internal MQTT → WebSockets → Frontend
```

## Components to Deprecate
This decision supersedes the following components which should be marked as deprecated:

1. **Polling-based Shadow Updates**: All code related to frontend polling of shadow data
2. **Direct API Endpoints for Shadow Updates**: The REST endpoints used solely for shadow polling
3. **Manual Shadow State Management**: Any code manually managing shadow state in the frontend without using the real-time WebSocket connection
4. **Previous WebSocket Implementation**: The older WebSocket manager that didn't integrate with MQTT

## Consequences

### Benefits
1. **Enhanced Real-Time Experience**: Users will see device updates immediately without waiting for polling intervals
2. **Reduced Backend Load**: Elimination of redundant polling requests will reduce server load
3. **Improved Scalability**: The message broker pattern allows for better scaling with increased device count
4. **Bandwidth Efficiency**: Only actual data changes are transmitted, reducing network overhead
5. **Decoupled Architecture**: Components can evolve independently, following Clean Architecture principles
6. **Better Testability**: Each component can be tested in isolation
7. **Unified Protocol**: MQTT provides a standard protocol for both IoT devices and internal communications

### Drawbacks
1. **Increased Complexity**: The system now involves more components and dependencies
2. **Additional Dependencies**: Requires MQTT broker deployment and management
3. **Learning Curve**: Developers need to understand MQTT and the Message Broker Pattern
4. **Potential Message Loss**: Without proper persistence, messages might be lost during network issues
5. **Debugging Challenges**: Asynchronous messaging can be more difficult to debug

### Mitigations
1. **Comprehensive Testing**: Implement thorough unit, integration, and E2E tests following our 70:20:10 testing pyramid
2. **Monitoring**: Add proper monitoring for MQTT broker health and message flow
3. **Documentation**: Provide clear documentation of the new architecture
4. **Fallback Mechanism**: Implement a fallback to polling if real-time updates fail

## Implementation Notes
- The implementation follows Test-Driven Development (TDD) principles with a Red-Green-Refactor cycle
- The testing pyramid ratio of 70:20:10 (unit:integration:e2e) is maintained
- Clean Architecture principles are applied to ensure separation of concerns

## References
- Message Broker Pattern: https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageBroker.html
- MQTT Protocol: https://mqtt.org/
- MongoDB Change Streams: https://www.mongodb.com/docs/manual/changeStreams/
- WebSocket Protocol: https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
