"""
Pytest configuration and fixtures for testing
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.database import get_session
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL or "postgresql://postgres:postgres_test@localhost:5433/kol_management_test"


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def engine():
    """Create test database engine (session scope - created once per test session)"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    yield engine
    
    # Drop all tables after all tests
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def session(engine) -> Generator[Session, None, None]:
    """Create a new database session for each test (function scope)"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    # Rollback transaction after each test (clean slate)
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(session: Session) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with overridden database session"""
    
    def override_get_session():
        yield session
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(session: Session) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for testing async endpoints"""
    
    def override_get_session():
        yield session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def test_user(session: Session):
    """Create a test user"""
    from app.models.user import User
    from app.core.security import hash_password
    
    user = User(
        email="test@example.com",
        hashed_password=hash_password("password123"),
        full_name="Test User",
        role="account_executive",
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


@pytest.fixture
def admin_user(session: Session):
    """Create an admin user"""
    from app.models.user import User
    from app.core.security import hash_password
    
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        full_name="Admin User",
        role="admin",
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


@pytest.fixture
def auth_headers(client: TestClient, test_user) -> dict:
    """Get authentication headers with valid JWT token"""
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client: TestClient, admin_user) -> dict:
    """Get admin authentication headers"""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"
    })
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def test_campaign(session: Session, test_user):
    """Create a test campaign"""
    from app.models.campaign import Campaign
    from datetime import date, timedelta
    
    campaign = Campaign(
        name="Test Campaign",
        status="draft",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        total_budget=10000.00,
        currency="USD",
        objectives="Test campaign objectives",
        target_audience={"age": "25-35", "gender": "all"},
        created_by=test_user.id
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    
    return campaign


@pytest.fixture
def test_kol(session: Session):
    """Create a test KOL"""
    from app.models.kol import KOL
    
    kol = KOL(
        name="Test KOL",
        email="kol@example.com",
        niche=["fashion", "beauty"],
        tier="micro",
        status="active"
    )
    session.add(kol)
    session.commit()
    session.refresh(kol)
    
    return kol


# ============================================================================
# Event Loop Fixture (for async tests)
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
