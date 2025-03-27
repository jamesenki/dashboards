#!/usr/bin/env python3
"""
Script to verify water heaters in the database.
Checks for the presence of both commercial and residential water heaters,
their diagnostic codes, and specification links.
"""
import asyncio
import logging
from sqlalchemy import select, func

from src.db.connection import get_db_session
from src.db.models import DeviceModel, DiagnosticCodeModel
from src.models.device import DeviceType
from src.models.water_heater import WaterHeaterType

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def verify_water_heaters():
    """Verify water heaters in the database."""
    session_generator = get_db_session()
    if not session_generator:
        logger.warning("Database session unavailable.")
        return
        
    async for session in session_generator:
        if not session:
            logger.warning("Database session is None.")
            return
            
        try:
            # Count water heaters
            query = select(func.count()).select_from(DeviceModel).where(
                DeviceModel.type == DeviceType.WATER_HEATER
            )
            result = await session.execute(query)
            heater_count = result.scalar()
            
            logger.info(f"Found {heater_count} water heaters in the database")
            
            # Retrieve all water heaters with their properties
            query = select(DeviceModel).where(DeviceModel.type == DeviceType.WATER_HEATER)
            result = await session.execute(query)
            heaters = result.scalars().all()
            
            commercial_count = 0
            residential_count = 0
            with_specs_count = 0
            
            for heater in heaters:
                properties = heater.properties or {}
                heater_type = properties.get("heater_type")
                
                # Handle both enum values and string values
                if heater_type == "Commercial" or heater_type == WaterHeaterType.COMMERCIAL:
                    commercial_count += 1
                    heater_type = "Commercial"
                elif heater_type == "Residential" or heater_type == WaterHeaterType.RESIDENTIAL:
                    residential_count += 1
                    heater_type = "Residential"
                
                if properties.get("specification_link"):
                    with_specs_count += 1
                
                # Count diagnostic codes for this heater
                diag_query = select(func.count()).select_from(DiagnosticCodeModel).where(
                    DiagnosticCodeModel.device_id == heater.id
                )
                diag_result = await session.execute(diag_query)
                diag_count = diag_result.scalar()
                
                # Get a sample of diagnostic codes
                sample_query = select(DiagnosticCodeModel).where(
                    DiagnosticCodeModel.device_id == heater.id
                ).limit(2)
                sample_result = await session.execute(sample_query)
                sample_codes = sample_result.scalars().all()
                
                sample_codes_info = ", ".join([f"{code.code}: {code.description} ({code.severity})" for code in sample_codes])
                
                logger.info(f"Water Heater: {heater.name}")
                logger.info(f"  - Type: {heater_type}")
                logger.info(f"  - Specification: {properties.get('specification_link')}")
                logger.info(f"  - Diagnostic Codes: {diag_count} ({sample_codes_info if sample_codes else 'None'})")
            
            logger.info(f"Summary:")
            logger.info(f"  - Total Water Heaters: {heater_count}")
            logger.info(f"  - Commercial: {commercial_count}")
            logger.info(f"  - Residential: {residential_count}")
            logger.info(f"  - With Specification Links: {with_specs_count}")
            
        except Exception as e:
            logger.error(f"Error verifying water heaters: {e}")


async def main():
    """Main entry point for the script."""
    logger.info("Starting water heater verification script")
    await verify_water_heaters()
    logger.info("Water heater verification script completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
