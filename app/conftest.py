"""
Pytest configuration file with shared fixtures for testing.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from core.database import Base, get_db
from core.config import Settings


@pytest.fixture(scope="session")
def engine():
    """
    Create a test database engine for the entire test session.
    Uses PostgreSQL test database (habi_testdb).
    """
    test_db_url = Settings.get_test_db_url()
    test_engine = create_engine(test_db_url, pool_pre_ping=True)

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    # Drop all tables after tests
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """
    Create a new database session for each test function.
    Rolls back after each test to ensure test isolation.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a TestClient with a test database session.
    Overrides the get_db dependency to use the test database.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def clean_tables(db_session):
    """
    Clean all tables after each test.
    This fixture runs automatically for all tests.
    """
    yield

    # Clean all tables after test
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()


@pytest.fixture
def sample_category_data():
    """
    Provides sample category data for tests.
    """
    return {
        "name": "Electrónica",
        "description": "Categoría de productos electrónicos",
    }


@pytest.fixture
def sample_spare_part_data():
    """
    Provides sample spare part data for tests.
    """
    return {
        "name": "Resistencia de 100 Ohms",
        "description": "Resistencia eléctrica",
        "price": 0.50,
        "stock": 100,
        "category_id": 1,
    }


@pytest.fixture
def sample_service_order_data():
    """
    Provides sample service order data for tests.
    """
    return {
        "client_name": "Juan Pérez",
        "client_phone": "+57 300 123 4567",
        "client_email": "juan.perez@example.com",
        "description": "Reparación de equipo",
        "status": "pending",
    }
