# Message Broker Layer for IoTSphere

## Long-Term Architecture: Message Broker Implementation

### Overview

This design document outlines the complete decoupling of data sources from clients using a dedicated message broker layer in the IoTSphere platform. This represents the long-term architectural goal that builds upon the Change Data Capture (CDC) implementation.

![Message Broker Architecture](../assets/message_broker_architecture.png)

*Figure 1: Message Broker Architecture showing complete decoupling of data sources and clients*

### Design Goals

1. **Complete Decoupling**: Eliminate direct dependencies between data sources and consumers
2. **System Resilience**: Ensure the system operates correctly during partial outages
3. **Horizontal Scalability**: Enable independent scaling of each system component
4. **Load Isolation**: Protect the database from consumer load spikes
5. **Message Persistence**: Guarantee message delivery even during temporary outages
6. **Flow Control**: Handle backpressure when consumers process data slower than it's produced

### Message Broker Selection Criteria

| Criteria | Requirement | Rationale |
|----------|-------------|-----------|
| Reliability | Guaranteed delivery | Critical for IoT systems that control physical devices |
| Throughput | 10,000+ messages/second | Accommodate future growth |
| Latency | <50ms mean | Maintain real-time user experience |
| Scalability | Horizontal scaling | Support growing device population |
| Persistence | Configurable retention | Allow replay of events during recovery |
| Topology | Pub/Sub with routing | Support complex message distribution patterns |
| Protocol Support | MQTT, AMQP, WebSockets | Interface with diverse client types |

### Clean Architecture Implementation

Following our established Clean Architecture principles:

1. **Entities Layer**:
   - `Message` - Core message structure with payload and metadata
   - `Topic` - Hierarchical addressing scheme for message routing
   - `Subscription` - Represents a consumer's interest in specific messages

2. **Use Cases Layer**:
   - `MessagePublishUseCase` - Business logic for publishing messages
   - `MessageSubscriptionUseCase` - Managing subscriptions and message delivery
   - `MessageFlowControlUseCase` - Handling backpressure and delivery guarantees

3. **Interface Adapters Layer**:
   - `MessageBrokerAdapter` - Interface to the selected message broker
   - `DatabaseChangeAdapter` - Captures and transforms database changes
   - `ClientDeliveryAdapter` - Delivers messages to various client types

4. **Frameworks & Drivers Layer**:
   - `RabbitMQDriver` - Implementation using RabbitMQ (primary)
   - `RedisMessagingDriver` - Alternative implementation using Redis Pub/Sub
   - `WebSocketGateway` - Client-facing WebSocket server for message delivery

### Message Flow Patterns

#### 1. Database Change Propagation

```
MongoDB → Change Listener → Message Transformer → Message Broker → WebSocket Gateway → Clients
```

#### 2. Device Command Flow

```
Client → API Gateway → Command Validator → Message Broker → Command Processor → Device Shadow → MongoDB
```

#### 3. Device Telemetry Flow

```
Device → MQTT Gateway → Message Normalizer → Message Broker → Telemetry Processor → MongoDB
                                                            → Real-time Analytics → Clients
```

### Topic Hierarchy

We will implement a hierarchical topic structure to enable fine-grained message filtering:

```
iotsphere/
  ├── devices/
  │    ├── {device_id}/
  │    │    ├── shadow/
  │    │    │    ├── reported
  │    │    │    ├── desired
  │    │    │    └── delta
  │    │    ├── telemetry/
  │    │    │    ├── temperature
  │    │    │    ├── pressure
  │    │    │    └── status
  │    │    └── commands/
  │    │         ├── response
  │    │         └── request
  │    └── batch/
  │         ├── status
  │         └── alerts
  ├── users/
  │    └── {user_id}/
  │         ├── notifications
  │         └── preferences
  └── system/
       ├── status
       ├── metrics
       └── alerts
```

### Message Structure

All messages will follow a consistent structure:

```json
{
  "metadata": {
    "messageId": "uuid-string",
    "timestamp": "ISO-8601 timestamp",
    "topic": "full/topic/path",
    "source": "component-id",
    "correlationId": "uuid-string",
    "messageType": "event|command|response|notification",
    "version": "1.0"
  },
  "payload": {
    // Message-specific content
  }
}
```

### Broker Implementation Options

#### Primary Option: RabbitMQ

**Strengths:**
- Mature, battle-tested implementation
- Supports multiple messaging patterns
- Provides strong delivery guarantees
- Excellent flow control capabilities
- Clustering for high availability

**Implementation Approach:**
- Deploy as dedicated service with clustering
- Configure persistent message storage
- Implement exchange-to-exchange bindings for topic hierarchies
- Use separate queue per client type

#### Alternative Option: Redis Pub/Sub with Streams

**Strengths:**
- Lightweight, high-performance
- Already used in parts of our system
- Simple to deploy and operate
- Streams provide persistence and consumer groups

**Implementation Approach:**
- Configure Redis streams for persistence
- Use Redis Pub/Sub for transient messaging
- Deploy Redis Cluster for high availability
- Implement message de-duplication at client layer

### Client Adaptation Strategy

1. **WebSocket Gateway**:
   - Subscribes to relevant topics on message broker
   - Maintains client connection registry
   - Forwards messages to connected clients
   - Handles client connection lifecycle

2. **Client SDK**:
   - Connection management
   - Subscription handling
   - Message caching
   - Offline operation and synchronization

### Deployment Architecture

![Deployment Architecture](../assets/message_broker_deployment.png)

*Figure 2: Message Broker Deployment Architecture showing component distribution*

The deployment will utilize containerization with:
- Separate containers for each major component
- Horizontal scaling for high-throughput components
- Redundancy for critical components
- Load balancing for client-facing gateways

### Performance Considerations

1. **Message Batching**:
   - Group related messages during high-throughput periods
   - Balance batch size against latency requirements

2. **Message Compression**:
   - Apply compression for large payloads
   - Use binary protocols where possible

3. **Connection Pooling**:
   - Reuse connections to message broker
   - Implement connection backoff strategies

4. **Message Filtering**:
   - Apply server-side filtering via topic subscriptions
   - Implement client-side filtering for fine-grained control

### Security Considerations

1. **Authentication**:
   - Client authentication for broker access
   - Service-to-service authentication

2. **Authorization**:
   - Topic-based access control
   - Client-specific permissions

3. **Encryption**:
   - TLS for all communications
   - Payload encryption for sensitive data

4. **Audit Logging**:
   - Record message publication events
   - Track subscription changes

### Migration Strategy

1. **Phase 1**: Implement message broker alongside CDC
2. **Phase 2**: Migrate shadow change propagation to use broker
3. **Phase 3**: Implement command and telemetry flows
4. **Phase 4**: Refactor existing components to use message bus

### Testing Strategy

Testing will follow our established TDD methodology:

1. **Unit Tests**:
   - Message serialization/deserialization
   - Topic routing logic
   - Client connection handling

2. **Integration Tests**:
   - End-to-end message delivery
   - Broker cluster behavior
   - Reconnection and recovery scenarios

3. **Performance Tests**:
   - Message throughput
   - Latency under load
   - Scaling behavior

4. **Resilience Tests**:
   - Component failure handling
   - Network partition scenarios
   - Recovery after outages
