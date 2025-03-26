import asyncio
import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.schema import CreateTable

from src.db.connection import get_engine
from src.db.models import Base, DeviceModel, ReadingModel

logger = logging.getLogger(__name__)


async def create_tables() -> None:
    """Create all tables if they don't exist."""
    engine = get_engine()
    
    async with engine.begin() as conn:
        # Create tables one by one to handle dependencies
        for table in [DeviceModel.__table__, ReadingModel.__table__]:
            try:
                await conn.execute(CreateTable(table, if_not_exists=True))
                logger.info(f"Created table {table.name}")
            except Exception as e:
                logger.error(f"Error creating table {table.name}: {e}")
    
    logger.info("Database tables created")


async def configure_timescale() -> None:
    """Configure TimescaleDB for time-series data if using PostgreSQL."""
    from src.db.config import db_settings
    
    if db_settings.DB_TYPE != "postgres":
        logger.info("Skipping TimescaleDB configuration (not using PostgreSQL)")
        return
    
    engine = get_engine()
    
    async with engine.begin() as conn:
        try:
            # Check if TimescaleDB extension is available
            result = await conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'")
            timescale_exists = result.scalar() is not None
            
            if not timescale_exists:
                # Create TimescaleDB extension
                await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
                logger.info("Created TimescaleDB extension")
            
            # Convert readings table to hypertable
            await conn.execute(
                "SELECT create_hypertable('readings', 'timestamp', if_not_exists => TRUE)"
            )
            logger.info("Configured readings table as TimescaleDB hypertable")
            
        except Exception as e:
            logger.error(f"Error configuring TimescaleDB: {e}")
            logger.warning("Continuing without TimescaleDB optimization")


async def initialize_db() -> None:
    """Initialize database with tables and extensions."""
    await create_tables()
    await configure_timescale()


if __name__ == "__main__":
    asyncio.run(initialize_db())
