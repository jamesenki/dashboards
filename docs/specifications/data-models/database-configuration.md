# IoTSphere Database Configuration Guide

This document provides detailed information about the IoTSphere PostgreSQL database configuration, including setup instructions and best practices.

## Database Architecture

IoTSphere uses PostgreSQL as its primary database system with the following features:

- **Core Database**: PostgreSQL for reliable relational data storage
- **Time-Series Data**: Optional TimescaleDB extension for optimized time-series data handling
- **Data Models**: SQLAlchemy ORM for database interaction

## PostgreSQL Configuration

### Connection Settings

The application connects to PostgreSQL using these default settings (configurable in the environment):

```
DB_TYPE: postgres
DB_HOST: localhost
DB_PORT: 5432
DB_USER: iotsphere
DB_PASSWORD: iotsphere
DB_NAME: iotsphere
```

### Database Setup Instructions

1. **Install PostgreSQL**:
   ```bash
   brew install postgresql@14
   ```

2. **Start PostgreSQL Service**:
   ```bash
   brew services start postgresql@14
   ```

3. **Create Database and User**:
   ```bash
   createdb iotsphere
   psql -c "CREATE USER iotsphere WITH ENCRYPTED PASSWORD 'iotsphere';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE iotsphere TO iotsphere;"
   ```

4. **Configure Application**:
   Update your environment variables or `/src/db/config.py` file to match the PostgreSQL connection settings.

## TimescaleDB Integration (Optional)

IoTSphere supports TimescaleDB for enhanced time-series data performance but will function correctly without it.

### TimescaleDB Installation

1. **Install TimescaleDB**:
   ```bash
   brew install timescaledb
   ```

2. **Configure PostgreSQL for TimescaleDB**:
   ```bash
   # Run the timescaledb configuration utility
   /opt/homebrew/bin/timescaledb-tune --quiet --yes

   # Restart PostgreSQL to apply changes
   brew services restart postgresql@14
   ```

3. **Create TimescaleDB Extension**:
   ```bash
   # Connect to your database and create the extension
   psql iotsphere -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"
   ```

### Version Compatibility

- IoTSphere has been tested with PostgreSQL 14
- TimescaleDB 2.x is recommended but optional
- The application is designed to work with or without TimescaleDB

## Data Migration Process

The application automatically handles database migration, including:

1. **Table Creation**: Creates necessary tables if they don't exist
2. **TimescaleDB Configuration**: Configures hypertables if TimescaleDB is available
3. **Graceful Degradation**: Falls back to standard PostgreSQL tables if TimescaleDB is unavailable

## Troubleshooting

### Common Issues and Solutions

#### TimescaleDB Extension Not Found

If you see this warning:
```
WARNING:src.db.migration:Cannot check for TimescaleDB extension: Not an executable object: "SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'"
```

Possible solutions:
1. Verify PostgreSQL is running: `brew services list`
2. Check TimescaleDB installation: `brew info timescaledb`
3. Ensure your PostgreSQL and TimescaleDB versions are compatible
4. Try reinstalling TimescaleDB: `brew reinstall timescaledb`
5. The application will continue to work without TimescaleDB

#### PostgreSQL Connection Issues

If the application cannot connect to PostgreSQL:

1. Verify PostgreSQL is running: `brew services list`
2. Check connection details in `src/db/config.py`
3. Ensure the database and user exist: `psql -l`
4. Test connection manually: `psql -U iotsphere iotsphere`

## Performance Considerations

- **Indexes**: The database schema includes optimized indexes for common queries
- **Hypertables**: TimescaleDB hypertables improve query performance for time-series data
- **Connection Pooling**: The application uses connection pooling to efficiently manage database connections

## Security Recommendations

For production deployments, consider these security enhancements:

1. **Stronger Passwords**: Change default database passwords
2. **Network Security**: Restrict database access to only necessary IP addresses
3. **Encryption**: Enable SSL for database connections
4. **Regular Backups**: Implement automated database backups
