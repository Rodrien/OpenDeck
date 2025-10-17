"""
Pytest Configuration and Fixtures

Provides common test fixtures and configuration for all tests.
"""

import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.db.base import Base
from app.main import app
from app.db.base import get_db
from app.config import settings

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.

    Creates all tables before test and drops them after.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with test database.

    Overrides the database dependency to use the test database.
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


@pytest.fixture
def test_user_data() -> dict:
    """Test user data for registration/authentication."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123"
    }


@pytest.fixture
def test_deck_data() -> dict:
    """Test deck data for creation."""
    return {
        "title": "Biology 101",
        "description": "Introduction to Biology concepts",
        "category": "Science",
        "difficulty": "beginner"
    }


@pytest.fixture
def test_card_data() -> dict:
    """Test card data for creation."""
    return {
        "question": "What is photosynthesis?",
        "answer": "The process by which plants convert light energy into chemical energy",
        "source": "Biology101.pdf - Page 42, Section 3.2",
        "source_url": None
    }
