# ADR 003: PostgreSQL with Optional TimescaleDB for Database Storage

## Status
Accepted

## Context
The IoTSphere application requires persistent data storage for device information, readings, and predictive analytics results. A significant portion of this data is time-series in nature (sensor readings, operational metrics). We needed to select a database solution that could efficiently handle both relational data and time-series data.

Options considered:
1. SQLite for development simplicity
2. MySQL as a general-purpose relational database
3. PostgreSQL as an advanced open-source relational database
4. MongoDB for document storage flexibility
5. InfluxDB for time-series specialization
6. PostgreSQL with TimescaleDB extension

## Decision
We will use PostgreSQL as our primary database with optional TimescaleDB extension support.

The application will:
1. Use PostgreSQL by default for all data storage
2. Attempt to leverage TimescaleDB extension when available
3. Gracefully degrade to standard PostgreSQL functionality when TimescaleDB is not available

## Rationale

### PostgreSQL Benefits
- Open-source with strong community support
- Advanced features like JSON support for flexible schema evolution
- Excellent compliance with SQL standards
- Superior data integrity and reliability
- Strong performance for both read and write operations
- Mature ecosystem with robust tooling

### TimescaleDB Benefits
- Purpose-built for time-series data
- Maintains full SQL compatibility
- Automatic partitioning of time-series data (hypertables)
- Performance optimizations for time-based queries
- Data retention policies for managing historical data
- Ability to handle both relational and time-series workloads in a single database

### Making TimescaleDB Optional
- Reduces installation complexity for development environments
- Improves deployment flexibility
- Ensures application resilience against missing extensions
- Follows our Test-Driven Development principles by making the system more robust

## Implementation Details
- SQLAlchemy ORM for database abstraction
- Database migration system that configures TimescaleDB when available
- Enhanced error handling to detect and log TimescaleDB availability
- Clear documentation for setting up both PostgreSQL and TimescaleDB

## Consequences

### Positive Consequences
- Unified database solution for all data needs
- Improved query performance for time-series data with TimescaleDB
- Simplified backup and maintenance compared to multiple database systems
- Flexibility for developers who may not need TimescaleDB for all tasks
- Graceful fallback to standard PostgreSQL capabilities

### Negative Consequences
- Additional configuration complexity for production environments
- Potential version compatibility issues between PostgreSQL and TimescaleDB
- Learning curve for developers unfamiliar with TimescaleDB
- May not be as specialized for time-series data as purpose-built alternatives

## References
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Time-Series Database Requirements Analysis](https://db-engines.com/en/article/Time+Series+DBMSs)
- IoTSphere Project [database_configuration.md](/docs/database_configuration.md)
