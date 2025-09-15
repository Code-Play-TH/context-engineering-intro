"""
Database configuration and session management.

Provides async SQLAlchemy engine with connection pooling for PostgreSQL.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import get_settings

settings = get_settings()

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=30,
    pool_recycle=3600,  # Recycle connections every hour
)

# Create session maker
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection.
    
    Yields:
        AsyncSession: Database session instance
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    Creates all tables defined in SQLModel metadata.
    """
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from app.models import user, product, sales, production, purchasing, audit  # noqa
        
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    
    Disposes of the engine and closes all connections.
    """
    await engine.dispose()


# Database dependency for FastAPI
def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI.
    
    Returns:
        AsyncGenerator: Database session generator
    """
    return get_session()