# 12. Multi-Database Architecture for IoT Data Management

Date: 2025-04-06

## Status

Accepted

## Context

The IoTSphere platform needs to handle diverse types of IoT data with different access patterns, consistency requirements, and performance characteristics. Our previous architecture used a single PostgreSQL database for all data types, which created challenges:

1. Performance bottlenecks for time-series telemetry data
2. Latency issues for real-time device state queries
3. Schema complexity when mixing different data models
4. Limited scalability for high-volume telemetry ingestion
5. Difficulty optimizing for both transactional and analytical workloads

The BDD tests require support for advanced analytics, real-time operations, and predictive maintenance across multiple device types, which demands a more specialized data architecture.

## Decision

We will implement a multi-database architecture with specialized databases for different data domains:

1. **Device Registry Database** (PostgreSQL):
   - Focus: Device identity, authentication, and basic status
   - Characteristics: Strong consistency, transactional, relational
   - Schema: Optimized for identity and security operations

2. **Asset Database** (PostgreSQL):
   - Focus: Rich device metadata, relationships, capabilities
   - Characteristics: Relational with JSONB for flexibility
   - Schema: Supports complex queries and joins for business intelligence

3. **Telemetry Database** (TimescaleDB):
   - Focus: High-volume time-series data from devices
   - Characteristics: Optimized for time-range queries with automatic partitioning
   - Schema: Hypertables with time-based chunking and compression

4. **Device Shadow/Twin** (Redis):
   - Focus: Current device state and desired state
   - Characteristics: In-memory with persistence, very low latency
   - Schema: Key-value structure optimized for real-time access

## Consequences

### Positive

1. **Optimized Performance**: Each database can be tuned for its specific data access patterns
2. **Improved Scalability**: Databases can scale independently based on their specific requirements
3. **Better Development Workflow**: Teams can work on different data domains without conflicts
4. **Enhanced Query Capability**: Specialized databases provide better query tools for their data types
5. **Future-Proof**: Architecture can adapt to new device types and data volumes

### Negative

1. **Increased Complexity**: Operating multiple database systems requires more expertise
2. **Data Consistency Challenges**: Maintaining consistency across databases requires careful design
3. **Higher Infrastructure Costs**: Running multiple database systems increases resource requirements
4. **Additional Development Effort**: Initial implementation requires more work than a single database

### Mitigations

1. We will implement a service layer that abstracts database complexity from application code
2. For development environments, we'll provide Docker Compose configurations that include all required databases
3. We'll develop clear data ownership boundaries to manage consistency concerns
4. We'll implement comprehensive monitoring to track performance across all databases

## Compliance with TDD Principles

This decision supports our TDD approach by:

1. Enabling more comprehensive test coverage across different data domains
2. Allowing us to mock specific databases for isolated component testing
3. Supporting realistic test data generation with appropriate data stores
4. Providing clear boundaries for test organization

Our tests will define the expected behavior for each data domain, and our implementation will make those tests pass while leveraging the strengths of each specialized database.

## Alternative Options Considered

1. **Single PostgreSQL Database with Partitioning**:
   - Pros: Simpler operations, transactional consistency across all data
   - Cons: Performance compromises, scale limitations, complexity in query optimization
   - Rejected because: Cannot optimize for all access patterns simultaneously

2. **Document Database for Everything**:
   - Pros: Schema flexibility, potentially simpler development model
   - Cons: Weaker query capabilities for complex analytics, less optimal for time-series
   - Rejected because: Doesn't address the specialized nature of IoT data

3. **Microservice with Database-per-Service**:
   - Pros: Strong isolation, independent scaling
   - Cons: Extreme proliferation of databases, higher operational overhead
   - Rejected because: Too granular, creates unnecessary complexity
