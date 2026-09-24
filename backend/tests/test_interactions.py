"""Interaction tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_interaction(async_client: AsyncClient, test_token: str):
    """Test creating an interaction."""
    # First create an HCP
    hcp_response = await async_client.post(
        "/api/v1/hcps",
        json={
            "name": "Dr. Interaction HCP",
            "specialty": "Cardiology",
            "email": "interaction@hospital.com",
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    hcp_id = hcp_response.json()["id"]
    
    # Create interaction
    response = await async_client.post(
        "/api/v1/interactions",
        json={
            "hcp_id": hcp_id,
            "interaction_date": "2026-07-15",
            "interaction_type": "meeting",
            "topics": "Clinical trial results",
            "summary": "Discussed trial outcomes",
            "follow_up_required": True,
            "follow_up_date": "2026-07-29",
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert response.json()["summary"] == "Discussed trial outcomes"
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_list_interactions(async_client: AsyncClient, test_token: str):
    """Test listing interactions."""
    response = await async_client.get(
        "/api/v1/interactions",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_update_interaction(async_client: AsyncClient, test_token: str):
    """Test updating an interaction."""
    # Create HCP
    hcp_response = await async_client.post(
        "/api/v1/hcps",
        json={
            "name": "Dr. Update Interaction HCP",
            "specialty": "Oncology",
            "email": "updateinter@hospital.com",
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    hcp_id = hcp_response.json()["id"]
    
    # Create interaction
    create_response = await async_client.post(
        "/api/v1/interactions",
        json={
            "hcp_id": hcp_id,
            "interaction_date": "2026-07-15",
            "interaction_type": "call",
            "topics": "Initial discussion",
            "summary": "First contact",
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    interaction_id = create_response.json()["id"]
    
    # Update interaction
    response = await async_client.put(
        f"/api/v1/interactions/{interaction_id}",
        json={"summary": "Updated summary", "topics": "Follow-up discussion"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert response.json()["summary"] == "Updated summary"