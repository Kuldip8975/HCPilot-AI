"""AI request/response schemas."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """Request schema for chat message."""
    message: str = Field(..., description="User message", min_length=1)
    session_id: Optional[str] = Field(None, description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatMessageResponse(BaseModel):
    """Response schema for chat message."""
    success: bool = Field(..., description="Whether request was successful")
    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session identifier")
    interaction: Optional[Dict[str, Any]] = Field(None, description="Created/updated interaction")
    tool_executed: Optional[str] = Field(None, description="Tool that was executed")
    should_end: bool = Field(False, description="Whether conversation should end")


class LogInteractionAIRequest(BaseModel):
    """Request schema for AI-powered interaction logging."""
    description: str = Field(..., description="Natural language description", min_length=1)
    hcp_id: Optional[str] = Field(None, description="HCP identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class LogInteractionAIResponse(BaseModel):
    """Response schema for AI-powered interaction logging."""
    success: bool = Field(..., description="Whether logging was successful")
    interaction: Optional[Dict[str, Any]] = Field(None, description="Created interaction")
    response: str = Field(..., description="AI response")


class EditInteractionAIRequest(BaseModel):
    """Request schema for AI-powered interaction editing."""
    interaction_id: str = Field(..., description="Interaction identifier")
    description: str = Field(..., description="Natural language description of changes", min_length=1)


class EditInteractionAIResponse(BaseModel):
    """Response schema for AI-powered interaction editing."""
    success: bool = Field(..., description="Whether editing was successful")
    interaction: Optional[Dict[str, Any]] = Field(None, description="Updated interaction")
    response: str = Field(..., description="AI response")


class FollowupRecommendationResponse(BaseModel):
    """Response schema for follow-up recommendations."""
    success: bool = Field(..., description="Whether request was successful")
    total_pending: Optional[int] = Field(None, description="Total pending follow-ups")
    followups: List[Dict[str, Any]] = Field(default_factory=list, description="Follow-up list")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="AI recommendations")
    response: Optional[str] = Field(None, description="AI response")