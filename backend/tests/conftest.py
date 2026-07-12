#!/usr/bin/env python3
"""Test configuration and fixtures for FraudWatch backend."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for testing
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create a fresh database session for each test."""
    async with engine.begin() as conn:
        # Create all tables
        from backend.app.models import Base
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session

    # Teardown
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    return AsyncMock()


@pytest.fixture
def mock_celery():
    """Mock Celery app for testing."""
    return MagicMock()


@pytest.fixture
def test_user():
    """Create a test user."""
    return {
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
    }


@pytest.fixture
def test_transaction():
    """Create a test transaction."""
    return {
        "amount": 100.50,
        "currency": "USD",
        "transaction_type": "purchase",
        "payment_method": "card",
    }


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    return {"Authorization": "Bearer test-token"}
