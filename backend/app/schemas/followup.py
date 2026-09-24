"""Follow-up schemas."""

from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, field_validator


class FollowUpBase(BaseModel):
    """Base follow-up schema."""
    interaction_id: str = Field(..., description="Interaction ID")
    scheduled_date: datetime = Field(..., description="Scheduled date")
    priority: Optional[str] = Field("medium", description="Priority (low, medium, high)")
    notes: Optional[str] = Field(None, description="Follow-up notes")


class FollowUpCreate(FollowUpBase):
    """Schema for creating a follow-up."""
    force: Optional[bool] = Field(
        False,
        description=(
            "If true, skip the double-booking check and create the "
            "follow-up even if this HCP already has another pending "
            "follow-up around the same time."
        ),
    )


class FollowUpUpdate(BaseModel):
    """Schema for updating a follow-up."""
    scheduled_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class FollowUpResponse(FollowUpBase):
    """Schema for follow-up response."""
    id: str
    user_id: str
    status: str
    completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "user_id", "interaction_id", mode="before")
    @classmethod
    def validate_uuid(cls, v):
        """Convert UUID to string if needed (SQLAlchemy returns UUID
        objects, but the response schema declares these as plain str)."""
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True