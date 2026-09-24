"""HCP CRUD tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_hcp(async_client: AsyncClient, test_token: str):
    """Test creating an HCP."""
    response = await async_client.post(
        "/api/v1/hcps",
        json={
            "name": "Dr. Test HCP",
            "title": "Cardiologist",
            "specialty": "Cardiology",
            "email": "test@hospital.com",
            "phone": "+1-555-0101",
            "location": "Test City",
            "organization": "Test Hospital",
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Dr. Test HCP"
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_list_hcps(async_client: AsyncClient, test_token: str):
    """Test listing HCPs."""
    # Create an HCP first
    await async_client.post(
        "/api/v1/hcps",
        json={
            "name": "Dr. List HCP",
            "specialty": "Oncology",
            "email": "list@hospital.com",
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    
    response = await async_client.get(
        "/api/v1/hcps",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "items" in response.json()
    assert len(response.json()["items"]) > 0


@pytest.mark.asyncio
async def test_get_hcp_by_id(async_client: AsyncClient, test_token: str):
    """Test getting an HCP by ID."""
    # Create HCP
    create_response = await async_client.post(
        "/api/v1/hcps",
        json={
            "name": "Dr. Detail HCP",
            "specialty": "Neurology",
            "email": "detail@hospital.com",
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    hcp_id = create_response.json()["id"]
    
    # Get HCP
    response = await async_client.get(
        f"/api/v1/hcps/{hcp_id}",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == hcp_id


@pytest.mark.asyncio
async def test_update_hcp(async_client: AsyncClient, test_token: str):
    """Test updating an HCP."""
    # Create HCP
    create_response = await async_client.post(
        "/api/v1/hcps",
        json={
            "name": "Dr. Update HCP",
            "specialty": "Cardiology",
            "email": "update@hospital.com",
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    hcp_id = create_response.json()["id"]
    
    # Update HCP
    response = await async_client.put(
        f"/api/v1/hcps/{hcp_id}",
        json={"name": "Dr. Updated HCP"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Dr. Updated HCP"


@pytest.mark.asyncio
async def test_delete_hcp(async_client: AsyncClient, test_token: str):
    """Test deleting an HCP."""
    # Create HCP
    create_response = await async_client.post(
        "/api/v1/hcps",
        json={
            "name": "Dr. Delete HCP",
            "specialty": "Dermatology",
            "email": "delete@hospital.com",
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    hcp_id = create_response.json()["id"]
    
    # Delete HCP
    response = await async_client.delete(
        f"/api/v1/hcps/{hcp_id}",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200