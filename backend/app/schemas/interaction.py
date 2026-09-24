"""Interaction schemas."""

from typing import Optional, List
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, field_validator


class InteractionBase(BaseModel):
    """Base interaction schema."""
    hcp_id: str = Field(..., description="HCP ID")
    interaction_date: datetime = Field(..., description="Date of interaction")
    interaction_type: str = Field(..., description="Type of interaction (meeting, call, email, other)")
    topics: Optional[str] = Field(None, description="Topics discussed")
    summary: Optional[str] = Field(None, description="Summary of interaction")
    notes: Optional[str] = Field(None, description="Additional notes")
    follow_up_required: bool = Field(False, description="Whether follow-up is required")
    follow_up_date: Optional[datetime] = Field(None, description="Follow-up date")
    follow_up_priority: Optional[str] = Field("medium", description="Follow-up priority")


class InteractionCreate(InteractionBase):
    """Schema for creating an interaction."""
    pass


class InteractionUpdate(BaseModel):
    """Schema for updating an interaction."""
    hcp_id: Optional[str] = None
    interaction_date: Optional[datetime] = None
    interaction_type: Optional[str] = None
    topics: Optional[str] = None
    summary: Optional[str] = None
    notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    follow_up_priority: Optional[str] = None


class InteractionResponse(InteractionBase):
    """Schema for interaction response."""
    id: str
    user_id: str
    hcp_name: Optional[str] = None
    hcp_specialty: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "user_id", "hcp_id", mode="before")
    @classmethod
    def validate_uuid(cls, v):
        """Convert UUID to string if needed."""
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class InteractionListResponse(BaseModel):
    """Schema for interaction list response."""
    items: List[InteractionResponse]
    total: int
    page: int
    limit: int