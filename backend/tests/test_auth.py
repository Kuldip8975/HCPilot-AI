"""Authentication tests."""

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user: User):
    """Test successful login."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "test123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert "user" in response.json()


@pytest.mark.asyncio
async def test_login_failure(async_client: AsyncClient):
    """Test login with invalid credentials."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    """Test successful registration."""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "newpass123",
            "full_name": "New User",
            "role": "sales_rep",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    """Test registration with duplicate email."""
    # First registration
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "pass123",
            "full_name": "Duplicate User",
        },
    )
    
    # Second registration with same email
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "pass123",
            "full_name": "Duplicate User",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient, test_token: str):
    """Test getting current user profile."""
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "email" in response.json()