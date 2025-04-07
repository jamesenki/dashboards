#!/usr/bin/env python3
"""
MODIFIED VERSION:
This script ensures there are at least 2 Rheem water heaters of each type
(Tank, Tankless, Hybrid) in the PostgreSQL database.

Usage:
    IOTSPHERE_ENV=development python src/scripts/ensure_rheem_water_heaters.py
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import asyncpg

# Setup path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials

# Connection parameters for PostgreSQL
# Get database connection parameters from environment variables
db_credentials = get_db_credentials()
POSTGRES_HOST = db_credentials["host"]
POSTGRES_PORT = db_credentials["port"]
POSTGRES_DATABASE = db_credentials["database"]
POSTGRES_USER = db_credentials["user"]
POSTGRES_PASSWORD = db_credentials["password"]
from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
    WaterHeaterType,
)
from src.repositories.postgres_water_heater_repository import (
    PostgresWaterHeaterRepository,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rheem water heater product series by type
RHEEM_SERIES = {
    WaterHeaterType.TANK: ["Classic", "Classic Plus", "Prestige", "Professional"],
    WaterHeaterType.TANKLESS: ["Performance", "Performance Platinum", "Condensing"],
    WaterHeaterType.HYBRID: ["ProTerra"],
}

# Rheem water heater features by type
RHEEM_FEATURES = {
    WaterHeaterType.TANK: [
        ["Standard Efficiency", "Basic Controls"],
        ["Mid-tier Efficiency", "Advanced Controls", "Extended Warranty"],
        ["High Efficiency", "Smart Controls", "EcoNet", "Extended Warranty"],
        ["Pro Grade", "EcoNet", "LeakGuard", "Extended Warranty"],
    ],
    WaterHeaterType.TANKLESS: [
        ["On-Demand", "Compact Design", "Basic Controls"],
        ["High Efficiency", "EcoNet", "Recirculation Pump"],
        ["Ultra Efficiency", "EcoNet", "LeakGuard", "Self-Cleaning"],
    ],
    WaterHeaterType.HYBRID: [
        [
            "Ultra Efficiency",
            "EcoNet",
            "LeakGuard",
            "Heat Pump",
            "Multiple Operation Modes",
        ],
    ],
}

# Rheem water heater operation modes by type
RHEEM_OPERATION_MODES = {
    WaterHeaterType.TANK: [
        ["Standard", "Energy Saver", "Vacation"],
        ["Standard", "Energy Saver", "High Demand", "Vacation"],
        ["Standard", "Energy Saver", "High Demand", "Vacation", "Schedule"],
    ],
    WaterHeaterType.TANKLESS: [
        ["On-Demand", "Recirculation"],
        ["On-Demand", "Recirculation", "Schedule"],
    ],
    WaterHeaterType.HYBRID: [
        ["Heat Pump", "Hybrid", "Electric", "High Demand", "Vacation", "Schedule"],
    ],
}


async def ensure_rheem_water_heaters() -> None:
    """
    Ensure there are at least 2 Rheem water heaters of each type in the database.
    Using a direct SQL approach to avoid model conversion issues.
    """
    try:
        # Get environment
        environment = os.environ.get("IOTSPHERE_ENV", "development")
        print(f"Configuring database for environment: {environment}")

        # Create direct PostgreSQL connection
        conn = await asyncpg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DATABASE,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )

        # Get current water heater types
        water_heaters = await conn.fetch(
            "SELECT id, name, manufacturer, type FROM water_heaters WHERE manufacturer = 'Rheem'"
        )

        # Count water heaters by type
        tanks = [wh for wh in water_heaters if wh["type"] == "Tank"]
        tankless = [wh for wh in water_heaters if wh["type"] == "Tankless"]
        hybrid = [wh for wh in water_heaters if wh["type"] == "Hybrid"]

        # Log current distribution
        logger.info(
            f"Found {len(water_heaters)} Rheem water heaters in PostgreSQL database"
        )
        logger.info(
            f"Tank: {len(tanks)}, Tankless: {len(tankless)}, Hybrid: {len(hybrid)}"
        )

        # Define how many of each type to add
        to_add = {
            "Tank": max(0, 2 - len(tanks)),
            "Tankless": max(0, 2 - len(tankless)),
            "Hybrid": max(0, 2 - len(hybrid)),
        }

        total_to_add = sum(to_add.values())
        logger.info(f"Need to add {total_to_add} water heaters: {to_add}")

        # Add water heaters as needed
        for wh_type, count in to_add.items():
            for i in range(count):
                # Generate a UUID for this water heater
                wh_id = f"wh-{uuid.uuid4().hex[:8]}"
                now = datetime.now().isoformat()
                future = (datetime.now() + timedelta(days=365 * 5)).isoformat()

                # Pick a series based on type
                if wh_type == "Tank":
                    series = ["Classic", "Prestige"][i % 2]
                    features = json.dumps(["Standard Efficiency", "Smart Controls"])
                    operation_modes = json.dumps(
                        ["Standard", "Energy Saver", "Vacation"]
                    )
                    size = "Large"
                    capacity = 80.0
                elif wh_type == "Tankless":
                    series = ["Performance", "Performance Platinum"][i % 2]
                    features = json.dumps(["On-Demand", "Compact Design"])
                    operation_modes = json.dumps(["On-Demand", "Recirculation"])
                    size = "Medium"
                    capacity = None
                else:  # Hybrid
                    series = "ProTerra"
                    features = json.dumps(["Ultra Efficiency", "EcoNet", "Heat Pump"])
                    operation_modes = json.dumps(
                        ["Heat Pump", "Hybrid", "Electric", "Vacation"]
                    )
                    size = "Medium"
                    capacity = 65.0

                # Build metadata
                metadata = json.dumps(
                    {
                        "source": "PostgreSQL migration",
                        "created_by": "ensure_rheem_water_heaters.py",
                        "type_specific": {
                            "efficiency_uef": 0.95 if wh_type == "Hybrid" else 0.82,
                            "energy_star": True
                            if wh_type in ["Hybrid", "Tankless"]
                            else False,
                        },
                    }
                )

                # Insert the water heater - using direct SQL to avoid type conversion issues
                logger.info(f"Adding Rheem {wh_type} water heater: {wh_id}")
                await conn.execute(
                    """
                    INSERT INTO water_heaters (
                        id, name, manufacturer, brand, model, type, size, location, status,
                        installation_date, warranty_expiry, last_maintenance, last_seen,
                        current_temperature, target_temperature, efficiency_rating, mode,
                        health_status, series, features, operation_modes, metadata
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
                    )
                """,
                    wh_id,
                    f"Rheem {series} {wh_type}",
                    "Rheem",
                    "Rheem",
                    f"RH-{wh_type[:3].upper()}{uuid.uuid4().hex[:4].upper()}",
                    wh_type,
                    size,
                    "Main Building",
                    "ONLINE",
                    now,
                    future,
                    now,
                    now,
                    45.0,
                    60.0,
                    0.90 if wh_type == "Hybrid" else 0.85,
                    "ECO",
                    "Good",
                    series,
                    features,
                    operation_modes,
                    metadata,
                )

                # Add some readings
                for j in range(3):  # Just add 3 readings to keep it simple
                    reading_id = str(uuid.uuid4())
                    reading_time = (datetime.now() - timedelta(hours=j)).isoformat()
                    temperature = 45.0 + (j % 5)

                    await conn.execute(
                        """
                        INSERT INTO water_heater_readings (
                            id, water_heater_id, timestamp, temperature, pressure, flow_rate, energy_usage
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                        reading_id,
                        wh_id,
                        reading_time,
                        temperature,
                        50.0,
                        5.0 if wh_type != "Tank" else 0.0,
                        2.5 if wh_type == "Hybrid" else 3.5,
                    )

        # Get final counts
        water_heaters = await conn.fetch(
            "SELECT id, name, manufacturer, type FROM water_heaters WHERE manufacturer = 'Rheem'"
        )
        tanks = [wh for wh in water_heaters if wh["type"] == "Tank"]
        tankless = [wh for wh in water_heaters if wh["type"] == "Tankless"]
        hybrid = [wh for wh in water_heaters if wh["type"] == "Hybrid"]

        logger.info(f"\nFinal Rheem water heater distribution:")
        logger.info(
            f"Tank: {len(tanks)}, Tankless: {len(tankless)}, Hybrid: {len(hybrid)}"
        )
        logger.info("Ids: " + ", ".join([wh["id"] for wh in water_heaters]))

        # Close connection
        await conn.close()

    except Exception as e:
        logger.error(f"Error ensuring Rheem water heaters: {e}")
        import traceback

        logger.error(traceback.format_exc())
    finally:
        # Close the PostgreSQL connection pool
        if "postgres_repo" in locals() and postgres_repo.pool:
            await postgres_repo.pool.close()
            logger.info("Closed PostgreSQL connection pool")


async def main():
    """Main entry point"""
    await ensure_rheem_water_heaters()


if __name__ == "__main__":
    asyncio.run(main())
