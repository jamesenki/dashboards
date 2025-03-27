#!/usr/bin/env python3
"""
Script to demonstrate the Component Failure Prediction feature with real water heater data.
This retrieves actual water heaters from the database and runs predictions on them.
"""
import asyncio
import sys
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path to ensure imports work correctly
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.db.connection import get_db_session
from src.db.models import DeviceModel, DiagnosticCodeModel, ReadingModel
from src.models.device import DeviceType
from src.models.water_heater import WaterHeater, WaterHeaterType
from src.predictions.maintenance.component_failure import ComponentFailurePrediction


async def get_water_heater_ids() -> List[str]:
    """Get IDs of all water heaters in the database."""
    water_heater_ids = []
    
    async for session in get_db_session():
        if session is None:
            logger.error("Could not establish database session")
            return []
            
        # Query all devices that are water heaters
        from sqlalchemy import select
        stmt = (select(DeviceModel.id)
                .where(DeviceModel.type == DeviceType.WATER_HEATER.value))
        
        result = await session.execute(stmt)
        water_heater_ids = result.scalars().all()
        
        logger.info(f"Found {len(water_heater_ids)} water heaters in the database")
    
    return water_heater_ids


async def get_water_heater_telemetry(device_id: str, hours: int = 24) -> Dict[str, Any]:
    """
    Get telemetry data for a water heater for the specified time period.
    
    Args:
        device_id: The ID of the water heater
        hours: Number of hours of history to retrieve
        
    Returns:
        Dictionary with telemetry data
    """
    telemetry = {
        "device_id": device_id,
        "timestamp": [],
        "temperature": [],
        "pressure": [],
        "energy_usage": [],
        "flow_rate": [],
        "heating_cycles": []
    }
    
    async for session in get_db_session():
        if session is None:
            logger.error("Could not establish database session")
            return telemetry
            
        # Get timestamp range
        from sqlalchemy import select, func, desc
        since_time = datetime.now() - timedelta(hours=hours)
        
        # Query readings for this device
        stmt = (select(ReadingModel)
                .where(ReadingModel.device_id == device_id)
                .where(ReadingModel.timestamp >= since_time)
                .order_by(ReadingModel.timestamp))
        
        result = await session.execute(stmt)
        readings = result.scalars().all()
        
        if not readings:
            logger.warning(f"No readings found for device {device_id}")
            # Generate synthetic data for demonstration purposes
            timestamps = pd.date_range(end=datetime.now(), periods=30, freq='h')
            telemetry["timestamp"] = timestamps.tolist()
            telemetry["temperature"] = np.linspace(60, 70, 30).tolist()
            telemetry["pressure"] = (np.ones(30) * 2.5 + np.random.normal(0, 0.2, 30)).tolist()
            telemetry["energy_usage"] = (np.ones(30) * 1200 + np.random.normal(0, 50, 30)).tolist()
            telemetry["flow_rate"] = np.linspace(10, 9.5, 30).tolist()
            telemetry["heating_cycles"] = (np.ones(30) * 15 + np.random.normal(0, 1, 30)).tolist()
            return telemetry
            
        # Process readings
        for reading in readings:
            telemetry["timestamp"].append(reading.timestamp)
            
            # Check if we have valid value data
            if reading.value and isinstance(reading.value, dict):
                # Extract values based on metric name
                if reading.metric_name == "temperature":
                    telemetry["temperature"].append(float(reading.value.get("value", 65)))
                elif reading.metric_name == "pressure":
                    telemetry["pressure"].append(float(reading.value.get("value", 2.5)))
                elif reading.metric_name == "energy_usage":
                    telemetry["energy_usage"].append(float(reading.value.get("value", 1200)))
                elif reading.metric_name == "flow_rate":
                    telemetry["flow_rate"].append(float(reading.value.get("value", 10)))
                elif reading.metric_name == "heating_cycle_duration":
                    telemetry["heating_cycles"].append(float(reading.value.get("value", 15)))
    
    logger.info(f"Retrieved {len(telemetry['timestamp'])} readings for device {device_id}")
    
    # If we don't have enough data, add synthetic data
    if len(telemetry["timestamp"]) < 5:
        logger.warning(f"Not enough real data for device {device_id}, adding synthetic data")
        # Generate synthetic data to supplement
        count = 30 - len(telemetry["timestamp"])
        if count > 0:
            timestamps = pd.date_range(end=datetime.now(), periods=count, freq='h')
            telemetry["timestamp"].extend(timestamps.tolist())
            telemetry["temperature"].extend(np.linspace(60, 70, count).tolist())
            telemetry["pressure"].extend((np.ones(count) * 2.5 + np.random.normal(0, 0.2, count)).tolist())
            telemetry["energy_usage"].extend((np.ones(count) * 1200 + np.random.normal(0, 50, count)).tolist())
            telemetry["flow_rate"].extend(np.linspace(10, 9.5, count).tolist())
            telemetry["heating_cycles"].extend((np.ones(count) * 15 + np.random.normal(0, 1, count)).tolist())
    
    return telemetry


async def get_water_heater_info(device_id: str) -> Dict[str, Any]:
    """Get basic information about a water heater."""
    info = {
        "device_id": device_id,
        "name": "Unknown Water Heater",
        "total_operation_hours": 8760,  # Default to 1 year
        "maintenance_history": []
    }
    
    async for session in get_db_session():
        if session is None:
            logger.error("Could not establish database session")
            return info
            
        # Query device information
        from sqlalchemy import select
        stmt = (select(DeviceModel)
                .where(DeviceModel.id == device_id))
        
        result = await session.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            logger.warning(f"Device {device_id} not found in database")
            return info
            
        # Update basic information
        info["name"] = device.name
        
        # Extract operation hours from properties or use default
        if device.properties and "installation_date" in device.properties:
            try:
                # Handle both string and datetime installation dates
                installation_date_value = device.properties["installation_date"]
                if isinstance(installation_date_value, str):
                    installation_date = datetime.fromisoformat(installation_date_value)
                elif isinstance(installation_date_value, dict) and "value" in installation_date_value:
                    # Handle nested JSON structure
                    installation_date = datetime.fromisoformat(installation_date_value["value"])
                else:
                    # Default to a year ago
                    installation_date = datetime.now() - timedelta(days=365)
                    
                hours_since_installation = (datetime.now() - installation_date).total_seconds() / 3600
                info["total_operation_hours"] = hours_since_installation
            except Exception as e:
                logger.error(f"Error parsing installation date: {e}")
        
        # Generate a simple maintenance history if not in properties
        # In a real system, this would be stored in the database
        if device.properties and "maintenance_history" in device.properties:
            info["maintenance_history"] = device.properties["maintenance_history"]
        else:
            # Generate a synthetic maintenance history
            last_maintenance = datetime.now() - timedelta(days=90)
            info["maintenance_history"] = [
                {"type": "regular", "date": last_maintenance},
                {"type": "anode_inspection", "date": last_maintenance - timedelta(days=180)},
                {"type": "descaling", "date": last_maintenance - timedelta(days=365)}
            ]
    
    return info


async def main():
    """Run component failure predictions on all water heaters."""
    # Get all water heater IDs
    water_heater_ids = await get_water_heater_ids()
    
    if not water_heater_ids:
        logger.error("No water heaters found in the database")
        return
    
    # Initialize the prediction model
    model = ComponentFailurePrediction()
    
    # Run predictions for each water heater
    prediction_results = []
    
    for idx, device_id in enumerate(water_heater_ids, 1):
        logger.info(f"[{idx}/{len(water_heater_ids)}] Processing water heater: {device_id}")
        
        # Get telemetry data
        telemetry = await get_water_heater_info(device_id)
        telemetry.update(await get_water_heater_telemetry(device_id))
        
        # Run prediction
        prediction = await model.predict(device_id, telemetry)
        prediction_results.append(prediction)
        
        # Display results
        logger.info(f"Prediction for {telemetry['name']} (ID: {device_id}):")
        logger.info(f"  - Overall failure probability: {prediction.predicted_value:.1%}")
        logger.info(f"  - Confidence: {prediction.confidence:.1%}")
        
        # Component-specific probabilities
        if prediction.raw_details and "components" in prediction.raw_details:
            logger.info("  - Component failure probabilities:")
            for component, probability in prediction.raw_details["components"].items():
                logger.info(f"    - {component}: {probability:.1%}")
        
        # Recommendations
        if prediction.recommended_actions:
            logger.info("  - Recommended actions:")
            for action in prediction.recommended_actions:
                logger.info(f"    - {action.description} (Severity: {action.severity.value})")
                logger.info(f"      Due: {action.due_date.strftime('%Y-%m-%d')}")
        
        logger.info("=" * 80)
    
    logger.info(f"Processed {len(water_heater_ids)} water heaters")
    
    return prediction_results


if __name__ == "__main__":
    asyncio.run(main())
