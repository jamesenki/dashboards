#!/usr/bin/env python3
"""
TimescaleDB Migration Script for IoTSphere Telemetry
Creates tables optimized for time-series data with appropriate hypertable configurations.
"""
import logging
import os
import sys

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "user": os.environ.get("DB_USER", "iotsphere"),
    "password": os.environ.get("DB_PASSWORD", "iotsphere"),
    "dbname": os.environ.get("DB_NAME", "iotsphere"),
}

# SQL statements for table creation
CREATE_DEVICE_TELEMETRY_TABLE = """
CREATE TABLE IF NOT EXISTS device_telemetry (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    telemetry_type VARCHAR(50) NOT NULL,
    value_numeric DOUBLE PRECISION,
    value_text TEXT,
    value_json JSONB,
    value_boolean BOOLEAN,
    units VARCHAR(20),
    source VARCHAR(20) NOT NULL DEFAULT 'device',
    simulated BOOLEAN NOT NULL DEFAULT FALSE
);
"""

CREATE_WATER_HEATER_TELEMETRY_TABLE = """
CREATE TABLE IF NOT EXISTS water_heater_telemetry (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    temperature_current DOUBLE PRECISION,
    temperature_setpoint DOUBLE PRECISION,
    heating_status BOOLEAN,
    power_consumption_watts DOUBLE PRECISION,
    water_flow_gpm DOUBLE PRECISION,
    error_code VARCHAR(20),
    mode VARCHAR(20),
    simulated BOOLEAN NOT NULL DEFAULT FALSE
);
"""

CREATE_DEVICE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS device_events (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT,
    details JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(50),
    acknowledged_at TIMESTAMPTZ,
    simulated BOOLEAN NOT NULL DEFAULT FALSE
);
"""

# Create hypertables for time-series data
CREATE_HYPERTABLES = [
    "SELECT create_hypertable('device_telemetry', 'timestamp', if_not_exists => TRUE);",
    "SELECT create_hypertable('water_heater_telemetry', 'timestamp', if_not_exists => TRUE);",
    "SELECT create_hypertable('device_events', 'timestamp', if_not_exists => TRUE);",
]

# Create indexes for frequent queries
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_device_telemetry_device_id_timestamp ON device_telemetry (device_id, timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_water_heater_telemetry_device_id_timestamp ON water_heater_telemetry (device_id, timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_device_events_device_id_timestamp ON device_events (device_id, timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_device_telemetry_type ON device_telemetry (telemetry_type);",
    "CREATE INDEX IF NOT EXISTS idx_device_events_type ON device_events (event_type);",
]


def create_tables():
    """Create all required tables in the TimescaleDB database"""
    conn = None
    try:
        # Connect to the database
        logger.info("Connecting to TimescaleDB...")
        conn = psycopg2.connect(**DB_PARAMS)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if TimescaleDB extension is installed
        cursor.execute(
            "SELECT extname FROM pg_extension WHERE extname = 'timescaledb';"
        )
        if cursor.fetchone() is None:
            logger.info("Creating TimescaleDB extension...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")

        # Create tables
        logger.info("Creating telemetry tables...")
        cursor.execute(CREATE_DEVICE_TELEMETRY_TABLE)
        cursor.execute(CREATE_WATER_HEATER_TELEMETRY_TABLE)
        cursor.execute(CREATE_DEVICE_EVENTS_TABLE)

        # Create hypertables
        logger.info("Converting tables to hypertables...")
        for query in CREATE_HYPERTABLES:
            cursor.execute(query)

        # Create indexes
        logger.info("Creating indexes...")
        for query in CREATE_INDEXES:
            cursor.execute(query)

        logger.info("TimescaleDB setup completed successfully!")

    except Exception as e:
        logger.error(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()
    return True


if __name__ == "__main__":
    if create_tables():
        sys.exit(0)
    else:
        sys.exit(1)
