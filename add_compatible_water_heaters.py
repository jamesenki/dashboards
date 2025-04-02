"""
Script to add sample water heaters to the database using the existing schema.
"""
import asyncio
import logging
import os
import sqlite3
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "data/iotsphere.db"


async def create_sample_water_heaters():
    """Create sample water heaters with varied data that works with the existing schema."""
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Sample water heaters with varied but realistic data
        water_heaters = [
            {
                "id": f"wh-{uuid.uuid4().hex[:8]}",
                "name": "Residential Water Heater",
                "brand": "EcoTemp",
                "model": "RT-500",
                "type": "WATER_HEATER",
                "location": "Building A - Apartment 101",
                "current_temperature": 48.7,
                "target_temperature": 50.0,
                "mode": "ECO",
                "status": "HEATING",
                "efficiency_rating": 92.5,
                "health_status": "GREEN",
                "last_seen": datetime.now().isoformat(),
            },
            {
                "id": f"wh-{uuid.uuid4().hex[:8]}",
                "name": "Commercial Kitchen Heater",
                "brand": "ProHeat",
                "model": "C-2000",
                "type": "WATER_HEATER",
                "location": "Building B - Kitchen",
                "current_temperature": 65.2,
                "target_temperature": 65.0,
                "mode": "BOOST",
                "status": "STANDBY",
                "efficiency_rating": 88.0,
                "health_status": "YELLOW",
                "last_seen": datetime.now().isoformat(),
            },
            {
                "id": f"wh-{uuid.uuid4().hex[:8]}",
                "name": "Energy Saving Heater",
                "brand": "GreenWater",
                "model": "ES-100",
                "type": "WATER_HEATER",
                "location": "Building C - Basement",
                "current_temperature": 42.5,
                "target_temperature": 45.0,
                "mode": "ECO",
                "status": "HEATING",
                "efficiency_rating": 95.5,
                "health_status": "GREEN",
                "last_seen": datetime.now().isoformat(),
            },
            {
                "id": f"wh-{uuid.uuid4().hex[:8]}",
                "name": "Maintenance Mode Heater",
                "brand": "ThermalX",
                "model": "TX-350",
                "type": "WATER_HEATER",
                "location": "Building D - Utility Room",
                "current_temperature": 20.0,
                "target_temperature": 40.0,
                "mode": "OFF",
                "status": "STANDBY",
                "efficiency_rating": 85.0,
                "health_status": "RED",
                "last_seen": datetime.now().isoformat(),
            },
        ]

        # Add to database
        for heater in water_heaters:
            logger.info(f"Creating water heater: {heater['name']}")
            cursor.execute(
                """
                INSERT INTO water_heaters (
                    id, name, brand, model, type, location,
                    current_temperature, target_temperature, mode, status,
                    efficiency_rating, health_status, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    heater["id"],
                    heater["name"],
                    heater["brand"],
                    heater["model"],
                    heater["type"],
                    heater["location"],
                    heater["current_temperature"],
                    heater["target_temperature"],
                    heater["mode"],
                    heater["status"],
                    heater["efficiency_rating"],
                    heater["health_status"],
                    heater["last_seen"],
                ),
            )

        # Commit changes
        conn.commit()
        logger.info(f"Added {len(water_heaters)} water heaters to the database")

        # Add a health configuration
        # First check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='water_heater_health_config'"
        )
        if not cursor.fetchone():
            logger.info("Creating water_heater_health_config table")
            cursor.execute(
                """
                CREATE TABLE water_heater_health_config (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    threshold REAL,
                    status TEXT,
                    created_at TEXT
                )
            """
            )

        # Add health config entries
        health_configs = [
            {
                "id": str(uuid.uuid4()),
                "name": "temperature_high",
                "threshold": 75.0,
                "status": "RED",
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "name": "temperature_warning",
                "threshold": 65.0,
                "status": "YELLOW",
                "created_at": datetime.now().isoformat(),
            },
        ]

        for config in health_configs:
            logger.info(f"Adding health config: {config['name']}")
            cursor.execute(
                """
                INSERT OR REPLACE INTO water_heater_health_config
                (id, name, threshold, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    config["id"],
                    config["name"],
                    config["threshold"],
                    config["status"],
                    config["created_at"],
                ),
            )

        # Add alert rules table if it doesn't exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='water_heater_alert_rules'"
        )
        if not cursor.fetchone():
            logger.info("Creating water_heater_alert_rules table")
            cursor.execute(
                """
                CREATE TABLE water_heater_alert_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT,
                    enabled INTEGER,
                    created_at TEXT
                )
            """
            )

        # Add a sample alert rule
        alert_rule = {
            "id": str(uuid.uuid4()),
            "name": "High Temperature Alert",
            "condition": "temperature > 70",
            "severity": "HIGH",
            "message": "Water temperature exceeds safe level",
            "enabled": 1,
            "created_at": datetime.now().isoformat(),
        }

        logger.info(f"Adding alert rule: {alert_rule['name']}")
        cursor.execute(
            """
            INSERT INTO water_heater_alert_rules
            (id, name, condition, severity, message, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                alert_rule["id"],
                alert_rule["name"],
                alert_rule["condition"],
                alert_rule["severity"],
                alert_rule["message"],
                alert_rule["enabled"],
                alert_rule["created_at"],
            ),
        )

        # Commit changes
        conn.commit()
        logger.info("All changes committed to database")

    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if conn:
            conn.close()

    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(create_sample_water_heaters())
