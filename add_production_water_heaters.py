"""
Script to add production-ready water heaters to the database.

This script creates 5 realistic water heaters with complete data
in the database for use in the IoTSphere dashboard.
"""
import asyncio
import logging
import os
import random
import sqlite3
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "data/iotsphere.db"

# Ensure we use the database (not mock data)
os.environ["USE_MOCK_DATA"] = "False"


async def create_production_water_heaters():
    """Create 5 production-ready water heaters with complete data."""
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check for existing water heaters
        cursor.execute("SELECT COUNT(*) FROM water_heaters")
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} existing water heaters in database")

        # Sample water heaters with comprehensive data
        water_heaters = [
            {
                "id": f"wh-{uuid.uuid4().hex[:8]}",
                "name": "Building A - Main Office Utility",
                "brand": "EcoTemp",
                "model": "ProSeries 200",
                "manufacturer": "EcoTemp Industries",
                "type": "WATER_HEATER",
                "size": "200L",
                "location": "Building A - 1st Floor Utility Room",
                "current_temperature": 52.5,
                "target_temperature": 55.0,
                "mode": "ECO",
                "status": "HEATING",
                "installation_date": (datetime.now() - timedelta(days=365)).isoformat(),
                "warranty_expiry": (
                    datetime.now() + timedelta(days=365 * 4)
                ).isoformat(),
                "last_maintenance": (datetime.now() - timedelta(days=90)).isoformat(),
                "efficiency_rating": 94.5,
                "health_status": "GREEN",
                "last_seen": datetime.now().isoformat(),
                "metadata": '{"capacity": 200, "power_rating": 3000, "voltage": 240, "energy_star": true}',
            },
            {
                "id": f"wh-{uuid.uuid4().hex[:8]}",
                "name": "Building B - Conference Center",
                "brand": "HydroHeat",
                "model": "Commercial Plus 300",
                "manufacturer": "HydroHeat Systems",
                "type": "WATER_HEATER",
                "size": "300L",
                "location": "Building B - Basement Level",
                "current_temperature": 65.8,
                "target_temperature": 65.0,
                "mode": "BOOST",
                "status": "STANDBY",
                "installation_date": (datetime.now() - timedelta(days=182)).isoformat(),
                "warranty_expiry": (
                    datetime.now() + timedelta(days=365 * 5)
                ).isoformat(),
                "last_maintenance": (datetime.now() - timedelta(days=30)).isoformat(),
                "efficiency_rating": 92.0,
                "health_status": "GREEN",
                "last_seen": datetime.now().isoformat(),
                "metadata": '{"capacity": 300, "power_rating": 4500, "voltage": 240, "energy_star": true}',
            },
            {
                "id": f"wh-{uuid.uuid4().hex[:8]}",
                "name": "Building C - Research Lab",
                "brand": "ThermalX",
                "model": "Laboratory Series 150",
                "manufacturer": "ThermalX Technologies",
                "type": "WATER_HEATER",
                "size": "150L",
                "location": "Building C - 2nd Floor Lab Section",
                "current_temperature": 42.3,
                "target_temperature": 45.0,
                "mode": "ECO",
                "status": "HEATING",
                "installation_date": (datetime.now() - timedelta(days=790)).isoformat(),
                "warranty_expiry": (
                    datetime.now() + timedelta(days=365 * 2)
                ).isoformat(),
                "last_maintenance": (datetime.now() - timedelta(days=120)).isoformat(),
                "efficiency_rating": 96.5,
                "health_status": "GREEN",
                "last_seen": datetime.now().isoformat(),
                "metadata": '{"capacity": 150, "power_rating": 2500, "voltage": 240, "energy_star": true}',
            },
            {
                "id": f"wh-{uuid.uuid4().hex[:8]}",
                "name": "Building D - Cafeteria",
                "brand": "ProHeat",
                "model": "Food Service 400",
                "manufacturer": "ProHeat Commercial",
                "type": "WATER_HEATER",
                "size": "400L",
                "location": "Building D - Kitchen Area",
                "current_temperature": 75.7,
                "target_temperature": 75.0,
                "mode": "BOOST",
                "status": "STANDBY",
                "installation_date": (datetime.now() - timedelta(days=450)).isoformat(),
                "warranty_expiry": (
                    datetime.now() + timedelta(days=365 * 3)
                ).isoformat(),
                "last_maintenance": (datetime.now() - timedelta(days=60)).isoformat(),
                "efficiency_rating": 89.5,
                "health_status": "YELLOW",
                "last_seen": datetime.now().isoformat(),
                "metadata": '{"capacity": 400, "power_rating": 6000, "voltage": 240, "energy_star": false}',
            },
            {
                "id": f"wh-{uuid.uuid4().hex[:8]}",
                "name": "Building E - Maintenance Required",
                "brand": "AquaPro",
                "model": "Standard 100",
                "manufacturer": "AquaPro Systems",
                "type": "WATER_HEATER",
                "size": "100L",
                "location": "Building E - Basement Utility",
                "current_temperature": 30.2,
                "target_temperature": 50.0,
                "mode": "OFF",
                "status": "STANDBY",
                "installation_date": (
                    datetime.now() - timedelta(days=1200)
                ).isoformat(),
                "warranty_expiry": (datetime.now() - timedelta(days=100)).isoformat(),
                "last_maintenance": (datetime.now() - timedelta(days=250)).isoformat(),
                "efficiency_rating": 78.0,
                "health_status": "RED",
                "last_seen": datetime.now().isoformat(),
                "metadata": '{"capacity": 100, "power_rating": 2000, "voltage": 240, "energy_star": false}',
            },
        ]

        # Add to database
        for heater in water_heaters:
            logger.info(f"Creating water heater: {heater['name']}")
            cursor.execute(
                """
                INSERT INTO water_heaters (
                    id, name, brand, model, manufacturer, type, size, location,
                    current_temperature, target_temperature, mode, status,
                    installation_date, warranty_expiry, last_maintenance,
                    efficiency_rating, health_status, last_seen, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    heater["id"],
                    heater["name"],
                    heater["brand"],
                    heater["model"],
                    heater["manufacturer"],
                    heater["type"],
                    heater["size"],
                    heater["location"],
                    heater["current_temperature"],
                    heater["target_temperature"],
                    heater["mode"],
                    heater["status"],
                    heater["installation_date"],
                    heater["warranty_expiry"],
                    heater["last_maintenance"],
                    heater["efficiency_rating"],
                    heater["health_status"],
                    heater["last_seen"],
                    heater["metadata"],
                ),
            )

        # Add health configuration data if not exist
        cursor.execute("SELECT COUNT(*) FROM water_heater_health_config")
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} existing health configs in database")

        health_configs = [
            {
                "id": str(uuid.uuid4()),
                "metric": "temperature_high",
                "threshold": 75.0,
                "status": "RED",
                "description": "High temperature warning threshold",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "metric": "temperature_warning",
                "threshold": 65.0,
                "status": "YELLOW",
                "description": "Temperature warning threshold",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "metric": "efficiency_low",
                "threshold": 80.0,
                "status": "YELLOW",
                "description": "Low efficiency warning threshold",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "metric": "efficiency_critical",
                "threshold": 70.0,
                "status": "RED",
                "description": "Critical efficiency threshold",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        ]

        # Check if the table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='water_heater_health_config'"
        )
        if not cursor.fetchone():
            logger.info("Creating water_heater_health_config table")
            cursor.execute(
                """
                CREATE TABLE water_heater_health_config (
                    id TEXT PRIMARY KEY,
                    key TEXT NOT NULL,
                    threshold REAL,
                    status TEXT,
                    created_at TEXT
                )
            """
            )

        # Only add health configs if count is 0
        if count == 0:
            for config in health_configs:
                logger.info(f"Adding health config: {config['metric']}")
                cursor.execute(
                    """
                    INSERT INTO water_heater_health_config
                    (id, metric, threshold, status, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        config["id"],
                        config["metric"],
                        config["threshold"],
                        config["status"],
                        config["description"],
                        config["created_at"],
                        config["updated_at"],
                    ),
                )
        else:
            logger.info("Skipping health config insertion as configs already exist")

        # Add alert rules
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

        cursor.execute("SELECT COUNT(*) FROM water_heater_alert_rules")
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} existing alert rules in database")

        alert_rules = [
            {
                "id": str(uuid.uuid4()),
                "name": "High Temperature Alert",
                "condition": "current_temperature > 70",
                "severity": "HIGH",
                "message": "Water temperature exceeds safe level",
                "enabled": 1,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Low Temperature Warning",
                "condition": "current_temperature < 40",
                "severity": "MEDIUM",
                "message": "Water temperature below recommended minimum",
                "enabled": 1,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Efficiency Alert",
                "condition": "efficiency_rating < 85",
                "severity": "MEDIUM",
                "message": "Water heater efficiency below threshold",
                "enabled": 1,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        ]

        # Only add alert rules if none exist
        if count == 0:
            for rule in alert_rules:
                logger.info(f"Adding alert rule: {rule['name']}")
                cursor.execute(
                    """
                    INSERT INTO water_heater_alert_rules
                    (id, name, condition, severity, message, enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        rule["id"],
                        rule["name"],
                        rule["condition"],
                        rule["severity"],
                        rule["message"],
                        rule["enabled"],
                        rule["created_at"],
                        rule["updated_at"],
                    ),
                )
        else:
            logger.info("Skipping alert rules insertion as rules already exist")

        # Also add some history readings for each water heater
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='water_heater_readings'"
        )
        if not cursor.fetchone():
            logger.info("Creating water_heater_readings table")
            cursor.execute(
                """
                CREATE TABLE water_heater_readings (
                    id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    temperature REAL,
                    pressure REAL,
                    energy_usage REAL,
                    flow_rate REAL,
                    timestamp TEXT,
                    FOREIGN KEY (device_id) REFERENCES water_heaters (id)
                )
            """
            )

        cursor.execute("SELECT COUNT(*) FROM water_heater_readings")
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} existing water heater readings in database")

        # Generate 24 hours of readings for each new water heater
        for heater in water_heaters:
            # First check if this is a new water heater that we just added
            cursor.execute(
                "SELECT COUNT(*) FROM water_heater_readings WHERE water_heater_id = ?",
                (heater["id"],),
            )
            reading_count = cursor.fetchone()[0]

            if reading_count > 0:
                logger.info(
                    f"Skipping readings for {heater['name']} as readings already exist"
                )
                continue

            logger.info(f"Adding historical readings for: {heater['name']}")
            # Generate readings for the past 24 hours
            base_temp = heater["current_temperature"]

            for hour in range(24, 0, -1):
                # Create some variation in readings
                timestamp = (datetime.now() - timedelta(hours=hour)).isoformat()
                temp_variation = random.uniform(-3.0, 3.0)
                temperature = max(30, min(80, base_temp + temp_variation))

                pressure = random.uniform(1.0, 2.5)
                energy_usage = random.uniform(800, 2500)
                flow_rate = random.uniform(0, 15) if random.random() > 0.3 else 0

                cursor.execute(
                    """
                    INSERT INTO water_heater_readings
                    (id, water_heater_id, temperature, pressure, energy_usage, flow_rate, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(uuid.uuid4()),
                        heater["id"],
                        temperature,
                        pressure,
                        energy_usage,
                        flow_rate,
                        timestamp,
                    ),
                )

        # Commit changes
        conn.commit()
        logger.info(
            f"Added {len(water_heaters)} water heaters to the database with complete data"
        )

    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        logger.error(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(create_production_water_heaters())
