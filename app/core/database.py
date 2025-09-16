"""
Database configuration and session management for KOL system.
Using async SQLAlchemy 2.0 patterns from the PRP.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging

from app.core.config import settings, get_database_url

logger = logging.getLogger(__name__)

# Create async engine with connection pooling
engine = create_async_engine(
    get_database_url(),
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,   # Recycle connections every hour
    # Use NullPool for testing to avoid connection issues
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
)

# Create async session maker
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI.
    Follows the exact pattern from the PRP reference implementation.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for consistency with imports
get_session = get_db


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Import all models to ensure they are registered
        from app.models import kol, campaign, communication, content, user

        logger.info("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db() -> None:
    """Close database connections."""
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")


# Connection event listeners for better debugging
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set database-specific configurations."""
    if settings.DATABASE_ECHO:
        logger.info("Database connection established")


@event.listens_for(Engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log when connection is checked out from pool."""
    if settings.DEBUG:
        logger.debug("Connection checked out from pool")


@event.listens_for(Engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log when connection is returned to pool."""
    if settings.DEBUG:
        logger.debug("Connection returned to pool")


# Database health check
async def check_db_health() -> bool:
    """Check database connectivity for health endpoints."""
    try:
        async with async_session() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Transaction context manager
class DatabaseTransaction:
    """Context manager for database transactions with proper error handling."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
        else:
            await self.session.commit()


# Utility function for running migrations
async def run_migrations():
    """Run database migrations programmatically."""
    from alembic.config import Config
    from alembic import command

    logger.info("Running database migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations completed")


# Database connection retry logic
import asyncio
from typing import Callable, TypeVar, Any

T = TypeVar('T')

async def with_db_retry(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    **kwargs
) -> T:
    """
    Retry database operations with exponential backoff.
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt == max_retries - 1:
                logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                raise

            wait_time = retry_delay * (2 ** attempt)
            logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)

    raise last_exception