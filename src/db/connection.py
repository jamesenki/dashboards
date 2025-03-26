import logging
from typing import AsyncGenerator, Optional

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.db.config import db_settings, get_db_url

logger = logging.getLogger(__name__)

# Global engine variable
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """Get or create SQLAlchemy engine."""
    global engine
    if engine is None:
        url = get_db_url()
        if db_settings.DB_TYPE == "memory":
            # Use NullPool for in-memory SQLite to avoid thread issues
            engine = create_async_engine(url, poolclass=NullPool, echo=False)
        else:
            engine = create_async_engine(
                url,
                pool_size=db_settings.DB_POOL_SIZE,
                max_overflow=db_settings.DB_MAX_OVERFLOW,
                echo=False,
            )
        logger.info(f"Created database engine for {db_settings.DB_TYPE}")
    return engine


def get_session_factory() -> async_sessionmaker:
    """Get or create AsyncSession factory."""
    global async_session_factory
    if async_session_factory is None:
        engine = get_engine()
        async_session_factory = async_sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
    return async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting DB session."""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise
    finally:
        await session.close()
