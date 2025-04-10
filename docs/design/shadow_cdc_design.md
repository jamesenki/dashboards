# IoTSphere Shadow Service Redesign

## Change Data Capture (CDC) with MongoDB Change Streams

### Overview

This design document outlines the implementation of Change Data Capture (CDC) using MongoDB Change Streams to improve the performance and scalability of the IoTSphere shadow service. The system will transition from a pull-based to a push-based architecture, reducing database load and improving real-time data delivery.

![Change Data Capture Architecture](../assets/cdc_architecture.png)

*Figure 1: Change Data Capture Architecture showing the flow of data from MongoDB to clients via change streams*

### Current Architecture Limitations

The current architecture suffers from several performance limitations:

1. **Polling Overhead**: Clients repeatedly request shadow updates, creating unnecessary database load
2. **Connection Saturation**: High numbers of concurrent connections to MongoDB under peak load
3. **Scalability Constraints**: Direct database connections limit horizontal scaling capabilities
4. **Delayed Updates**: Clients may experience lag between data changes and UI updates
5. **Resource Consumption**: Frequent polling consumes server resources and network bandwidth

### Proposed Architecture

#### 1. Core Components

1. **MongoDB Change Stream Listener**:
   - Subscribes to change events from the shadow collection
   - Filters relevant events (inserts, updates, deletes)
   - Transforms events into standardized message format

2. **Shadow Change Event Model**:
   - Device ID
   - Operation type (insert, update, delete)
   - Changed fields
   - Full shadow document
   - Timestamp
   - Version

3. **WebSocket Server Enhancement**:
   - Device-specific channels/rooms
   - Client subscription management
   - Event forwarding to relevant subscribers

4. **Client-Side Shadow Cache**:
   - Local storage of shadow state
   - Incremental updates based on change events
   - Reconnection and recovery logic

#### 2. Data Flow

1. Device or application updates shadow document in MongoDB
2. MongoDB generates change event
3. Change Stream Listener captures and processes event
4. Event is forwarded to WebSocket server
5. WebSocket server pushes to subscribed clients
6. Client updates local cache and UI

### Clean Architecture Implementation

Following our established Clean Architecture principles:

1. **Entities Layer**:
   - `ShadowChangeEvent` - Represents a change to a shadow document
   - `ShadowSubscription` - Represents a client subscription to shadow changes

2. **Use Cases Layer**:
   - `ShadowChangeStreamUseCase` - Core business logic for handling shadow changes
   - `ClientSubscriptionUseCase` - Manages client subscriptions and notifications

3. **Interface Adapters Layer**:
   - `MongoDBChangeStreamAdapter` - Connects to MongoDB change streams
   - `WebSocketNotificationAdapter` - Delivers notifications to clients

4. **Frameworks & Drivers Layer**:
   - `MongoDBDriver` - Direct interaction with MongoDB
   - `WebSocketServer` - WebSocket implementation (FastAPI/Starlette)

### Implementation Guidelines

1. **Optimistic Updates**:
   - UI updates immediately on user action
   - Confirmation or rollback on server response

2. **Conflict Resolution**:
   - Version-based conflict detection
   - Last-writer-wins strategy for most updates
   - Merge strategy for non-conflicting field updates

3. **Error Handling & Recovery**:
   - Automatic reconnection to change streams
   - Resumption tokens for continuing from disconnection point
   - Fallback to traditional polling if change streams unavailable

4. **Connection Management**:
   - Connection pooling for MongoDB access
   - WebSocket heartbeats and keepalive mechanisms
   - Progressive backoff for reconnection attempts

### Performance Expectations

1. **Latency Reduction**:
   - From 1000-2000ms (polling) to 50-100ms (push)

2. **Server Load Reduction**:
   - Database queries reduction: 90%+ for real-time monitoring
   - Connection count reduction: 80%+ during peak usage

3. **Scalability Improvement**:
   - Support for 10x current user base with minimal infrastructure changes

### Testing Strategy

Testing will follow our established TDD methodology:

1. **Unit Tests**:
   - Change event capture and transformation
   - Subscription management logic
   - Event filtering and routing

2. **Integration Tests**:
   - End-to-end event propagation
   - Database to client notification flow
   - Reconnection and recovery scenarios

3. **Performance Tests**:
   - Latency measurements
   - Connection handling under load
   - Event throughput benchmarks

### Migration Path

1. **Phase 1**: Implement change stream listener alongside existing polling
2. **Phase 2**: Integrate WebSocket notification system
3. **Phase 3**: Gradually transition clients to subscription model
4. **Phase 4**: Retain polling as fallback but deemphasize in favor of push
