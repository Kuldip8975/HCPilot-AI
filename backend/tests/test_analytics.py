"""Analytics tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analytics_dashboard(async_client: AsyncClient, test_token: str):
    """Test analytics dashboard endpoint."""
    response = await async_client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "total_interactions" in response.json()
    assert "total_hcps" in response.json()


@pytest.mark.asyncio
async def test_analytics_interactions(async_client: AsyncClient, test_token: str):
    """Test interaction analytics endpoint."""
    response = await async_client.get(
        "/api/v1/analytics/interactions",
        params={"aggregation": "daily"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "trends" in response.json()


@pytest.mark.asyncio
async def test_analytics_hcps(async_client: AsyncClient, test_token: str):
    """Test HCP analytics endpoint."""
    response = await async_client.get(
        "/api/v1/analytics/hcps",
        params={"top_n": 5},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "top_hcps" in response.json()