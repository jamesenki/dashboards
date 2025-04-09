# 5. MongoDB for Device Shadow Storage

Date: 2025-04-08

## Status

Proposed

## Context

IoTSphere currently implements device shadows using an in-memory storage solution. This approach has significant limitations:

* Shadow data is lost when the application restarts
* No persistence across deployments
* Missing shadows cause errors in the UI and API
* History data cannot be reliably retrieved

Device shadows are a critical component of the IoT platform, providing:
* Current device state representation (even when devices are offline)
* Historical state information for analytics and charts
* Desired vs. reported state reconciliation

Following our Test-Driven Development (TDD) principles, we need a solution that:
1. Allows tests to verify shadow persistence across application lifecycles
2. Supports all shadow operations with proper data integrity
3. Enables efficient querying and retrieval patterns

We evaluated several storage options:
* Relational databases (SQL)
* Document databases (NoSQL)
* Blob storage
* Key-value stores

## Decision

**We will use MongoDB Community Edition as the persistent storage layer for device shadow documents, with Redis as an optional caching layer for high-performance operations.**

MongoDB was selected for the following reasons:

1. **Document-oriented nature**: Shadow documents are inherently JSON structures that map naturally to MongoDB's document model
2. **Schema flexibility**: Device shadows evolve over time as devices gain new capabilities
3. **Query capabilities**: MongoDB allows efficient filtering and indexing on shadow attributes
4. **Versioning support**: Can easily store and retrieve shadow history
5. **Open-source availability**: MongoDB Community Edition can be deployed on-premises at no cost
6. **Python integration**: Excellent Python driver (PyMongo) aligns well with our codebase
7. **TDD compatibility**: MongoDB can be easily containerized for testing with frameworks like testcontainers
8. **Maturity**: Well-established, widely adopted database with strong community support
9. **Performance**: Good performance characteristics for our access patterns

## Consequences

### Positive

* Shadow data will persist across application restarts
* History data will be reliably available for charts and analytics
* Shadow documents can evolve to accommodate new device capabilities
* Efficient querying of shadow data by various attributes
* Simplified testing through containerization
* Follows industry best practices for IoT device shadow storage

### Negative

* Increased complexity compared to simple in-memory storage
* Additional infrastructure requirements
* Need for backup and maintenance procedures
* Learning curve for team members not familiar with MongoDB

### Neutral

* Shadow service architecture will need to be refactored to support pluggable storage providers
* Migration path needed for existing development data

## Implementation Plan

1. Create a MongoDB-backed shadow storage provider implementing the shadow storage interface
2. Implement proper update and query patterns
3. Create a migration utility to populate shadow data for existing devices
4. Add containerized MongoDB for development and testing environments
5. Update documentation for operations and development

## Verification

Following TDD principles, we will verify this solution by:

1. Writing tests that confirm shadow persistence across application restarts
2. Testing shadow data consistency during concurrent updates
3. Benchmarking shadow history retrieval performance
4. Validating shadow query performance against expected patterns
5. Ensuring all existing tests pass with the new storage layer
