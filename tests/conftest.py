"""
Test configuration and fixtures for Factory ERP System.

Provides pytest fixtures for database setup, authentication, and test data.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.database import get_db
from app.models.base import SQLModel
from app.models.user import User, Department, Role
from app.models.product import Product, ProductionStep
from app.models.sales import Customer, CustomerRequirement
from app.models.production import ProductionOrder, ProductionTracking
from app.config import get_settings

# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

settings = get_settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh test database for each test function.
    
    Yields:
        AsyncSession: Test database session
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with database dependency override.
    
    Args:
        test_db: Test database session
        
    Yields:
        AsyncClient: HTTP test client
    """
    def get_test_db():
        return test_db
    
    app.dependency_overrides[get_db] = get_test_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_departments(test_db: AsyncSession) -> list[Department]:
    """
    Create test departments.
    
    Args:
        test_db: Test database session
        
    Returns:
        list[Department]: Created departments
    """
    departments = [
        Department(name="Admin", description="System Administration"),
        Department(name="Sales", description="Sales Department"),
        Department(name="Production", description="Production Department"),
        Department(name="Purchasing", description="Purchasing Department"),
    ]
    
    for dept in departments:
        test_db.add(dept)
    
    await test_db.commit()
    
    for dept in departments:
        await test_db.refresh(dept)
    
    return departments


@pytest_asyncio.fixture
async def test_roles(test_db: AsyncSession) -> list[Role]:
    """
    Create test roles.
    
    Args:
        test_db: Test database session
        
    Returns:
        list[Role]: Created roles
    """
    roles = [
        Role(
            name="Admin",
            description="System Administrator",
            permissions={
                "users": ["create", "read", "update", "delete"],
                "products": ["create", "read", "update", "delete"],
                "sales": ["create", "read", "update", "delete"],
                "production": ["create", "read", "update", "delete"],
                "excel": ["upload", "download"],
                "erpnext": ["sync", "configure"]
            }
        ),
        Role(
            name="Sales",
            description="Sales User",
            permissions={
                "sales": ["create", "read", "update"],
                "customers": ["create", "read", "update"],
                "products": ["read"],
                "excel": ["upload", "download"]
            }
        ),
        Role(
            name="Production",
            description="Production User",
            permissions={
                "production": ["create", "read", "update"],
                "products": ["read"],
                "sales": ["read"],
                "excel": ["download"]
            }
        ),
        Role(
            name="User",
            description="Basic User",
            permissions={
                "products": ["read"],
                "sales": ["read"],
                "production": ["read"]
            }
        ),
    ]
    
    for role in roles:
        test_db.add(role)
    
    await test_db.commit()
    
    for role in roles:
        await test_db.refresh(role)
    
    return roles


@pytest_asyncio.fixture
async def test_users(
    test_db: AsyncSession,
    test_departments: list[Department],
    test_roles: list[Role]
) -> list[User]:
    """
    Create test users.
    
    Args:
        test_db: Test database session
        test_departments: Test departments
        test_roles: Test roles
        
    Returns:
        list[User]: Created users
    """
    from app.core.security import get_password_hash
    
    # Find departments and roles
    admin_dept = next(d for d in test_departments if d.name == "Admin")
    sales_dept = next(d for d in test_departments if d.name == "Sales")
    production_dept = next(d for d in test_departments if d.name == "Production")
    
    admin_role = next(r for r in test_roles if r.name == "Admin")
    sales_role = next(r for r in test_roles if r.name == "Sales")
    production_role = next(r for r in test_roles if r.name == "Production")
    
    users = [
        User(
            username="admin",
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            hashed_password=get_password_hash("admin123"),
            department_id=admin_dept.id,
            role_id=admin_role.id,
            is_active=True
        ),
        User(
            username="sales_user",
            email="sales@test.com",
            first_name="Sales",
            last_name="User",
            hashed_password=get_password_hash("sales123"),
            department_id=sales_dept.id,
            role_id=sales_role.id,
            is_active=True
        ),
        User(
            username="production_user",
            email="production@test.com",
            first_name="Production",
            last_name="User",
            hashed_password=get_password_hash("production123"),
            department_id=production_dept.id,
            role_id=production_role.id,
            is_active=True
        ),
    ]
    
    for user in users:
        test_db.add(user)
    
    await test_db.commit()
    
    for user in users:
        await test_db.refresh(user)
    
    return users


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, test_users: list[User]) -> str:
    """
    Get authentication token for admin user.
    
    Args:
        client: HTTP test client
        test_users: Test users
        
    Returns:
        str: JWT token for admin user
    """
    response = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def sales_token(client: AsyncClient, test_users: list[User]) -> str:
    """
    Get authentication token for sales user.
    
    Args:
        client: HTTP test client
        test_users: Test users
        
    Returns:
        str: JWT token for sales user
    """
    response = await client.post(
        "/api/auth/login",
        json={"username": "sales_user", "password": "sales123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def production_token(client: AsyncClient, test_users: list[User]) -> str:
    """
    Get authentication token for production user.
    
    Args:
        client: HTTP test client
        test_users: Test users
        
    Returns:
        str: JWT token for production user
    """
    response = await client.post(
        "/api/auth/login",
        json={"username": "production_user", "password": "production123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def test_products(test_db: AsyncSession) -> list[Product]:
    """
    Create test products.
    
    Args:
        test_db: Test database session
        
    Returns:
        list[Product]: Created products
    """
    products = [
        Product(
            part_no="PART001",
            part_name="Test Product 1",
            drawing_no="DRW001",
            material_code="MAT001",
            material_description="Steel Rod 10mm",
            unit_of_measure="PCS",
            standard_cost=25.50,
            specifications={"length": "100mm", "diameter": "10mm"}
        ),
        Product(
            part_no="PART002",
            part_name="Test Product 2",
            drawing_no="DRW002",
            material_code="MAT002",
            material_description="Aluminum Sheet",
            unit_of_measure="SQM",
            standard_cost=45.75,
            specifications={"thickness": "2mm", "grade": "6061"}
        ),
        Product(
            part_no="PART003",
            part_name="Test Product 3",
            drawing_no="DRW003",
            material_code="MAT003",
            material_description="Copper Wire",
            unit_of_measure="MTR",
            standard_cost=12.30,
            specifications={"gauge": "14AWG", "insulation": "PVC"}
        ),
    ]
    
    for product in products:
        test_db.add(product)
    
    await test_db.commit()
    
    for product in products:
        await test_db.refresh(product)
    
    return products


@pytest_asyncio.fixture
async def test_customers(test_db: AsyncSession) -> list[Customer]:
    """
    Create test customers.
    
    Args:
        test_db: Test database session
        
    Returns:
        list[Customer]: Created customers
    """
    customers = [
        Customer(
            customer_code="CUST001",
            customer_name="Test Customer 1",
            contact_person="John Doe",
            email="john@customer1.com",
            phone="+1234567890",
            address="123 Test Street, Test City, TC 12345",
            payment_terms="Net 30"
        ),
        Customer(
            customer_code="CUST002",
            customer_name="Test Customer 2",
            contact_person="Jane Smith",
            email="jane@customer2.com",
            phone="+1234567891",
            address="456 Another Street, Another City, AC 67890",
            payment_terms="Net 15"
        ),
    ]
    
    for customer in customers:
        test_db.add(customer)
    
    await test_db.commit()
    
    for customer in customers:
        await test_db.refresh(customer)
    
    return customers


@pytest_asyncio.fixture
async def test_customer_requirements(
    test_db: AsyncSession,
    test_products: list[Product],
    test_customers: list[Customer],
    test_users: list[User]
) -> list[CustomerRequirement]:
    """
    Create test customer requirements.
    
    Args:
        test_db: Test database session
        test_products: Test products
        test_customers: Test customers
        test_users: Test users
        
    Returns:
        list[CustomerRequirement]: Created customer requirements
    """
    sales_user = next(u for u in test_users if u.username == "sales_user")
    
    requirements = [
        CustomerRequirement(
            sale_no="SALE001",
            po_no="PO001",
            customer_name=test_customers[0].customer_name,
            customer_id=test_customers[0].id,
            product_id=test_products[0].id,
            due_date=datetime.utcnow() + timedelta(days=30),
            po_quantity=100,
            delivered_quantity=75,
            unit_price=25.50,
            status="partial",
            sales_person_id=sales_user.id,
            notes="Test customer requirement 1"
        ),
        CustomerRequirement(
            sale_no="SALE002",
            po_no="PO002",
            customer_name=test_customers[1].customer_name,
            customer_id=test_customers[1].id,
            product_id=test_products[1].id,
            due_date=datetime.utcnow() + timedelta(days=15),
            po_quantity=50,
            delivered_quantity=50,
            unit_price=45.75,
            status="completed",
            sales_person_id=sales_user.id,
            notes="Test customer requirement 2"
        ),
    ]
    
    for req in requirements:
        test_db.add(req)
    
    await test_db.commit()
    
    for req in requirements:
        await test_db.refresh(req)
    
    return requirements


@pytest.fixture
def auth_headers():
    """
    Helper function to create authorization headers.
    
    Returns:
        function: Function that creates auth headers from token
    """
    def _auth_headers(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}
    
    return _auth_headers


@pytest.fixture
def sample_excel_data():
    """
    Sample Excel data for testing uploads.
    
    Returns:
        dict: Sample data structure for Excel testing
    """
    return {
        "customer_requirements": [
            {
                "sale_no": "SALE003",
                "po_no": "PO003",
                "customer_name": "Excel Test Customer",
                "product_part_no": "PART001",
                "due_date": "2024-12-31",
                "po_quantity": 200,
                "delivered_quantity": 0,
                "unit_price": 25.50
            }
        ],
        "products": [
            {
                "part_no": "PART004",
                "part_name": "Excel Test Product",
                "material_code": "MAT004",
                "material_description": "Test Material",
                "unit_of_measure": "PCS",
                "standard_cost": 10.00
            }
        ]
    }


# Test utility functions
def assert_response_success(response, expected_status: int = 200):
    """Assert that response is successful with expected status code."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"


def assert_response_error(response, expected_status: int = 400):
    """Assert that response is an error with expected status code."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"


def assert_has_keys(data: dict, keys: list):
    """Assert that dictionary has all required keys."""
    for key in keys:
        assert key in data, f"Missing key: {key}"


def assert_valid_datetime(date_str: str):
    """Assert that string is a valid datetime."""
    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"Invalid datetime format: {date_str}")


def assert_valid_uuid(uuid_str: str):
    """Assert that string is a valid UUID."""
    import uuid
    try:
        uuid.UUID(uuid_str)
    except ValueError:
        pytest.fail(f"Invalid UUID format: {uuid_str}")