"""AI Agent tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_chat_message(async_client: AsyncClient, test_token: str):
    """Test AI chat message endpoint."""
    response = await async_client.post(
        "/api/v1/ai/chat",
        json={
            "message": "I want to log a meeting with Dr. Smith",
            "context": {"user_id": "test_user"},
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "response" in response.json()
    assert "session_id" in response.json()


@pytest.mark.asyncio
async def test_ai_log_interaction(async_client: AsyncClient, test_token: str):
    """Test AI-powered interaction logging."""
    response = await async_client.post(
        "/api/v1/ai/chat/log-interaction",
        json={
            "description": "Met with Dr. Chen today to discuss the oncology trial. She was very interested in the results.",
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "success" in response.json()
    assert "response" in response.json()


@pytest.mark.asyncio
async def test_ai_followup_recommendations(async_client: AsyncClient, test_token: str):
    """Test AI follow-up recommendations."""
    response = await async_client.get(
        "/api/v1/ai/chat/followup-recommendations",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "success" in response.json()