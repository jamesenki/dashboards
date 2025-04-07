#!/usr/bin/env python3
"""
PostgreSQL Migration Script for IoTSphere Asset Database
Creates tables for device registry, device metadata, and asset management.
"""
import os
import sys
import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'user': os.environ.get('DB_USER', 'iotsphere'),
    'password': os.environ.get('DB_PASSWORD', 'iotsphere'),
    'dbname': os.environ.get('DB_NAME', 'iotsphere')
}

# SQL statements for device registry tables
CREATE_DEVICE_REGISTRY_TABLE = """
CREATE TABLE IF NOT EXISTS device_registry (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) UNIQUE NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    serial_number VARCHAR(50),
    firmware_version VARCHAR(20),
    registration_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_connection TIMESTAMPTZ,
    connection_status VARCHAR(20) DEFAULT 'disconnected',
    simulated BOOLEAN NOT NULL DEFAULT FALSE
);
"""

CREATE_DEVICE_CAPABILITIES_TABLE = """
CREATE TABLE IF NOT EXISTS device_capabilities (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL REFERENCES device_registry(device_id) ON DELETE CASCADE,
    capability_name VARCHAR(50) NOT NULL,
    capability_type VARCHAR(50) NOT NULL,
    description TEXT,
    parameters JSONB,
    UNIQUE(device_id, capability_name)
);
"""

CREATE_DEVICE_AUTH_TABLE = """
CREATE TABLE IF NOT EXISTS device_auth (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL REFERENCES device_registry(device_id) ON DELETE CASCADE,
    auth_type VARCHAR(20) NOT NULL,
    auth_key VARCHAR(255) NOT NULL,
    auth_secret VARCHAR(255),
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMPTZ,
    enabled BOOLEAN NOT NULL DEFAULT TRUE
);
"""

# SQL statements for asset database tables
CREATE_LOCATION_TABLE = """
CREATE TABLE IF NOT EXISTS location (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    postal_code VARCHAR(20),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    notes TEXT
);
"""

CREATE_DEVICE_LOCATION_TABLE = """
CREATE TABLE IF NOT EXISTS device_location (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL REFERENCES device_registry(device_id) ON DELETE CASCADE,
    location_id INT NOT NULL REFERENCES location(id) ON DELETE CASCADE,
    installation_date TIMESTAMPTZ,
    notes TEXT,
    UNIQUE(device_id, location_id)
);
"""

CREATE_MAINTENANCE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS maintenance_history (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL REFERENCES device_registry(device_id) ON DELETE CASCADE,
    maintenance_date TIMESTAMPTZ NOT NULL,
    maintenance_type VARCHAR(50) NOT NULL,
    technician VARCHAR(100),
    description TEXT,
    parts_replaced JSONB,
    cost DECIMAL(10,2),
    next_maintenance_date TIMESTAMPTZ,
    simulated BOOLEAN NOT NULL DEFAULT FALSE
);
"""

# SQL statements for water heater specific tables
CREATE_WATER_HEATER_METADATA_TABLE = """
CREATE TABLE IF NOT EXISTS water_heater_metadata (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL REFERENCES device_registry(device_id) ON DELETE CASCADE,
    capacity_gallons DOUBLE PRECISION,
    energy_source VARCHAR(20),
    btu_rating INT,
    efficiency_rating DOUBLE PRECISION,
    temperature_min DOUBLE PRECISION,
    temperature_max DOUBLE PRECISION,
    installation_date DATE,
    warranty_expiration DATE,
    tank_type VARCHAR(20),
    UNIQUE(device_id)
);
"""

# Create indexes for frequent queries
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_device_registry_type ON device_registry (device_type);",
    "CREATE INDEX IF NOT EXISTS idx_device_registry_manufacturer ON device_registry (manufacturer);",
    "CREATE INDEX IF NOT EXISTS idx_device_registry_model ON device_registry (model);",
    "CREATE INDEX IF NOT EXISTS idx_device_registry_connection ON device_registry (connection_status);",
    "CREATE INDEX IF NOT EXISTS idx_device_capabilities_name ON device_capabilities (capability_name);",
    "CREATE INDEX IF NOT EXISTS idx_maintenance_history_date ON maintenance_history (maintenance_date);",
    "CREATE INDEX IF NOT EXISTS idx_maintenance_history_type ON maintenance_history (maintenance_type);"
]

def create_tables():
    """Create all required tables in the PostgreSQL database"""
    conn = None
    try:
        # Connect to the database
        logger.info("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_PARAMS)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create tables
        logger.info("Creating device registry tables...")
        cursor.execute(CREATE_DEVICE_REGISTRY_TABLE)
        cursor.execute(CREATE_DEVICE_CAPABILITIES_TABLE)
        cursor.execute(CREATE_DEVICE_AUTH_TABLE)
        
        logger.info("Creating asset database tables...")
        cursor.execute(CREATE_LOCATION_TABLE)
        cursor.execute(CREATE_DEVICE_LOCATION_TABLE)
        cursor.execute(CREATE_MAINTENANCE_HISTORY_TABLE)
        
        logger.info("Creating water heater specific tables...")
        cursor.execute(CREATE_WATER_HEATER_METADATA_TABLE)
        
        # Create indexes
        logger.info("Creating indexes...")
        for query in CREATE_INDEXES:
            cursor.execute(query)
            
        logger.info("Asset database setup completed successfully!")
        
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
