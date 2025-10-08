"""
Database connection and session management
"""
from sqlmodel import Session, create_engine
from sqlalchemy.pool import QueuePool
from typing import Generator
from app.core.config import settings


# Create SQLModel engine with connection pooling
# pool_size=20: Maximum number of connections to keep in the pool
# max_overflow=10: Maximum number of connections that can be created beyond pool_size
# pool_pre_ping=True: Verify connections before using them (handles stale connections)
# pool_recycle=3600: Recycle connections after 1 hour to prevent stale connections
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Yields:
        Session: SQLModel database session
        
    Example:
        @app.get("/users")
        def get_users(session: Session = Depends(get_session)):
            users = session.exec(select(User)).all()
            return users
    """
    with Session(engine) as session:
        yield session


def init_db() -> None:
    """
    Initialize database tables.
    
    This function should be called on application startup to create
    all tables defined in SQLModel models.
    
    Note: In production, use Alembic migrations instead of this function.
    """
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)


def close_db() -> None:
    """
    Close database connections and dispose of the engine.
    
    This function should be called on application shutdown to properly
    clean up database connections.
    """
    engine.dispose()
