"""
Pytest Configuration and Fixtures

Test configuration, database setup, and common fixtures for the KOL Management System tests.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

from app.main import app
from app.core.database import Base, get_session
from app.core.config import get_settings
from app.models.auth import User, Role, Permission
from app.core.auth import security_service
from app.utils.auth_seeder import AuthSeeder


# Test database URL (SQLite in-memory for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False
)

# Test session maker
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Yields:
        AsyncSession: Test database session
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def seeded_db_session(db_session: AsyncSession) -> AsyncSession:
    """
    Create a seeded test database session with auth data.

    Args:
        db_session: Base database session

    Returns:
        AsyncSession: Seeded database session
    """
    seeder = AuthSeeder()
    await seeder.seed_all(db_session)
    return db_session


@pytest.fixture(scope="function")
def test_app(db_session: AsyncSession) -> FastAPI:
    """
    Create a test FastAPI application.

    Args:
        db_session: Test database session

    Returns:
        FastAPI: Test application
    """
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    yield app

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_app: FastAPI) -> TestClient:
    """
    Create a test client.

    Args:
        test_app: Test FastAPI application

    Returns:
        TestClient: Test client
    """
    return TestClient(test_app)


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client.

    Args:
        test_app: Test FastAPI application

    Yields:
        AsyncClient: Async test client
    """
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def test_user(seeded_db_session: AsyncSession) -> User:
    """
    Create a test user.

    Args:
        seeded_db_session: Seeded database session

    Returns:
        User: Test user
    """
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=security_service.hash_password("TestPassword123!"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        status="active"
    )
    seeded_db_session.add(user)
    await seeded_db_session.commit()
    await seeded_db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_admin_user(seeded_db_session: AsyncSession) -> User:
    """
    Create a test admin user.

    Args:
        seeded_db_session: Seeded database session

    Returns:
        User: Test admin user
    """
    from sqlalchemy import select
    from app.models.auth import user_roles

    # Create admin user
    admin_user = User(
        email="admin@example.com",
        username="testadmin",
        hashed_password=security_service.hash_password("AdminPassword123!"),
        full_name="Test Admin",
        is_active=True,
        is_verified=True,
        is_superuser=True,
        status="active"
    )
    seeded_db_session.add(admin_user)
    await seeded_db_session.flush()

    # Assign admin role
    admin_role = await seeded_db_session.execute(
        select(Role).where(Role.name == "admin")
    )
    role = admin_role.scalar_one_or_none()

    if role:
        await seeded_db_session.execute(
            user_roles.insert().values(
                user_id=admin_user.id,
                role_id=role.id
            )
        )

    await seeded_db_session.commit()
    await seeded_db_session.refresh(admin_user)
    return admin_user


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    """
    Create authentication headers for test user.

    Args:
        test_user: Test user

    Returns:
        dict: Authentication headers
    """
    access_token = security_service.create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(test_admin_user: User) -> dict:
    """
    Create authentication headers for admin user.

    Args:
        test_admin_user: Test admin user

    Returns:
        dict: Authentication headers
    """
    access_token = security_service.create_access_token({"sub": str(test_admin_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def mock_email_service():
    """
    Mock email service for testing.

    Returns:
        MagicMock: Mocked email service
    """
    mock = MagicMock()
    mock.send_email.return_value = {"success": True, "message": "Email sent"}
    return mock


@pytest.fixture(scope="function")
def mock_social_media_service():
    """
    Mock social media service for testing.

    Returns:
        MagicMock: Mocked social media service
    """
    mock = MagicMock()
    mock.get_profile_data = AsyncMock(return_value={
        "platform": "instagram",
        "username": "test_user",
        "followers": 1000,
        "following": 500,
        "posts": 100
    })
    mock.get_posts_data = AsyncMock(return_value=[
        {
            "id": "123",
            "text": "Test post",
            "likes": 50,
            "comments": 10,
            "shares": 5,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ])
    return mock


@pytest.fixture(scope="function")
def mock_ai_analyzer():
    """
    Mock AI analyzer service for testing.

    Returns:
        MagicMock: Mocked AI analyzer
    """
    mock = MagicMock()
    mock.analyze_content = AsyncMock(return_value={
        "sentiment": {"label": "positive", "score": 0.85},
        "emotions": {"joy": 0.7, "trust": 0.6},
        "topics": ["technology", "innovation"],
        "entities": [{"text": "AI", "type": "TECHNOLOGY"}],
        "quality_score": 0.9,
        "engagement_prediction": 0.8
    })
    return mock


@pytest.fixture(scope="function")
def mock_celery_task():
    """
    Mock Celery task for testing.

    Returns:
        MagicMock: Mocked Celery task
    """
    mock = MagicMock()
    mock.delay.return_value = MagicMock(id="test-task-id")
    mock.apply_async.return_value = MagicMock(id="test-task-id")
    return mock


# Test data fixtures
@pytest.fixture
def sample_kol_data():
    """Sample KOL data for testing."""
    return {
        "name": "Test KOL",
        "email": "kol@example.com",
        "platforms": {
            "instagram": {
                "username": "test_kol",
                "followers": 10000,
                "engagement_rate": 0.05
            }
        },
        "categories": ["fashion", "lifestyle"],
        "demographics": {
            "age_range": "25-34",
            "gender": "female",
            "location": "New York, NY"
        }
    }


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing."""
    return {
        "name": "Test Campaign",
        "description": "A test campaign",
        "budget": 10000.0,
        "start_date": "2024-01-01",
        "end_date": "2024-02-01",
        "objectives": ["brand_awareness", "engagement"],
        "target_audience": {
            "age_range": "18-35",
            "interests": ["fashion", "technology"]
        }
    }


@pytest.fixture
def sample_content_data():
    """Sample content data for testing."""
    return {
        "platform": "instagram",
        "content_type": "post",
        "text": "Check out this amazing product! #sponsored",
        "media_urls": ["https://example.com/image.jpg"],
        "hashtags": ["sponsored", "product", "amazing"],
        "mentions": ["@brand"]
    }


# Settings override for testing
@pytest.fixture(autouse=True)
def override_settings():
    """Override settings for testing."""
    settings = get_settings()
    settings.TESTING = True
    settings.DATABASE_URL = TEST_DATABASE_URL
    settings.JWT_SECRET_KEY = "test-secret-key"
    settings.CELERY_BROKER_URL = "memory://"
    settings.CELERY_RESULT_BACKEND = "cache+memory://"
    return settings


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_database():
    """Cleanup database after each test."""
    yield
    # Any additional cleanup can go here