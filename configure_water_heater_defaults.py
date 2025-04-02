#!/usr/bin/env python3
"""
Script to set up default water heater configuration in the database.
This configures health status thresholds and alert rules.
"""
import asyncio
import os
import logging
from src.repositories.water_heater_repository import SQLiteWaterHeaterRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("configure_water_heater_defaults")

# Default health status configuration
DEFAULT_HEALTH_CONFIG = {
    "temperature_critical_high": {
        "threshold": 75.0,
        "status": "RED",
        "description": "Water temperature critically high, risk of scalding"
    },
    "temperature_high": {
        "threshold": 70.0,
        "status": "YELLOW",
        "description": "Water temperature is high"
    },
    "temperature_low": {
        "threshold": 40.0,
        "status": "YELLOW",
        "description": "Water temperature is low, may not be effective"
    },
    "pressure_high": {
        "threshold": 6.0,
        "status": "RED",
        "description": "Water pressure critically high, check relief valve"
    },
    "pressure_warning": {
        "threshold": 5.0,
        "status": "YELLOW",
        "description": "Water pressure is elevated"
    },
    "energy_usage_high": {
        "threshold": 3000.0,
        "status": "YELLOW",
        "description": "Energy usage is high, check for efficiency issues"
    },
    "flow_rate_low": {
        "threshold": 1.0,
        "status": "YELLOW",
        "description": "Flow rate is low, check for blockage"
    }
}

# Default alert rules
DEFAULT_ALERT_RULES = [
    {
        "name": "Critical Temperature Alert",
        "condition": "temperature > 75",
        "severity": "HIGH",
        "message": "Water heater temperature exceeds safe level",
        "enabled": True
    },
    {
        "name": "Energy Usage Alert",
        "condition": "energy_usage > 3000",
        "severity": "MEDIUM",
        "message": "Water heater energy consumption is high",
        "enabled": True
    },
    {
        "name": "Pressure Alert",
        "condition": "pressure > 6.0",
        "severity": "HIGH",
        "message": "Water heater pressure exceeds safe level",
        "enabled": True
    },
    {
        "name": "Low Temperature Alert",
        "condition": "temperature < 40",
        "severity": "LOW",
        "message": "Water heater temperature is below effective range",
        "enabled": True
    },
    {
        "name": "Low Flow Rate Alert",
        "condition": "flow_rate < 1.0",
        "severity": "MEDIUM",
        "message": "Water flow rate is low, check for blockage",
        "enabled": True
    }
]

async def configure_defaults():
    """Set up default configuration in the database."""
    # Use the SQLite repository implementation
    db_path = os.environ.get("DB_PATH", "data/iotsphere.db")
    repository = SQLiteWaterHeaterRepository(db_path=db_path)
    
    # Set health configuration
    logger.info("Setting up default health status configuration...")
    try:
        await repository.set_health_configuration(DEFAULT_HEALTH_CONFIG)
        logger.info("Health status configuration complete.")
    except Exception as e:
        logger.error(f"Error setting health configuration: {str(e)}")
    
    # Set up alert rules
    logger.info("Setting up default alert rules...")
    try:
        # First, get existing rules to avoid duplicates
        existing_rules = await repository.get_alert_rules()
        existing_names = [rule["name"] for rule in existing_rules]
        
        for rule in DEFAULT_ALERT_RULES:
            if rule["name"] not in existing_names:
                await repository.add_alert_rule(rule)
                logger.info(f"Added alert rule: {rule['name']}")
            else:
                logger.info(f"Alert rule already exists: {rule['name']}")
        
        logger.info("Alert rules configuration complete.")
    except Exception as e:
        logger.error(f"Error setting alert rules: {str(e)}")
    
    logger.info("Configuration complete!")

if __name__ == "__main__":
    asyncio.run(configure_defaults())
