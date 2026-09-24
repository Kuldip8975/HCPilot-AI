"""Test configuration and fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.config import settings

# Tests hit the app through httpx's ASGITransport with base_url="http://test",
# so every test request's Host header is "test". FastAPI's TrustedHostMiddleware
# (added in app/main.py) rejects any request whose Host header isn't in
# ALLOWED_HOSTS, with an instant 400 — before the request ever reaches a route,
# a dependency, or the database. That's exactly what was happening here: every
# single test (login, register, /me) failed with 400 in ~1ms regardless of
# what it actually tested. This opens it up for the test run only, without
# touching the real .env used outside tests.
settings.ALLOWED_HOSTS = ["*"]

from app.main import app
from app.models.database import Base, get_db
from app.models.user import User
from app.core.security import SecurityConfig


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_db"


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session.

    The engine is created fresh INSIDE this fixture (not at module level)
    and disposed at the end. pytest-asyncio gives every test its own
    event loop, and an asyncpg connection is tied to the loop it was
    created on — a module-level engine shared across tests would try to
    reuse a connection from a closed loop, causing
    'cannot perform operation: another operation is in progress'.
    """
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client whose requests use the TEST database,
    not the real DATABASE_URL from .env."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=SecurityConfig.get_password_hash("test123"),
        full_name="Test User",
        role="sales_rep",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def test_token(test_user: User) -> str:
    """Create a test JWT token."""
    return SecurityConfig.create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email, "role": test_user.role}
    )