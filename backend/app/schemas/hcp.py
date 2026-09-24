"""HCP schemas."""

from typing import Optional, List
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, EmailStr, field_validator


class HCPBase(BaseModel):
    """Base HCP schema."""
    name: str = Field(..., description="HCP name")
    title: Optional[str] = Field(None, description="Professional title")
    specialty: Optional[str] = Field(None, description="Medical specialty")
    email: Optional[EmailStr] = Field(None, description="Email address")  # Changed to Optional
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Street address (used to compute latitude/longitude)")
    latitude: Optional[float] = Field(None, description="Latitude, auto-computed from address")
    longitude: Optional[float] = Field(None, description="Longitude, auto-computed from address")
    organization: Optional[str] = Field(None, description="Organization/affiliation")
    status: Optional[str] = Field("active", description="Status (active, inactive, pending)")
    notes: Optional[str] = Field(None, description="Additional notes")
    preferences: Optional[str] = Field(None, description="Communication preferences")

    @field_validator("email", mode="before")
    @classmethod
    def blank_email_to_none(cls, v):
        """Treat an empty/whitespace-only string as 'no email' instead of
        an invalid email. Some existing HCP rows have '' stored for email,
        which EmailStr rejects outright and previously caused those HCPs
        to be silently dropped from list responses."""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class HCPCreate(HCPBase):
    """Schema for creating an HCP.

    latitude/longitude are intentionally NOT expected from the client here —
    they get computed server-side from `address` at save time by the
    geocoding step. If a client sends them anyway (inherited from HCPBase),
    the service layer overwrites them rather than trusting client input.
    """
    pass


class HCPUpdate(BaseModel):
    """Schema for updating an HCP."""
    name: Optional[str] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    organization: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    preferences: Optional[str] = None


class HCPResponse(HCPBase):
    """Schema for HCP response."""
    id: str
    engagement_score: int = Field(default=0)
    last_interaction: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v):
        """Convert UUID to string if needed."""
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class HCPListResponse(BaseModel):
    """Schema for HCP list response."""
    items: List[HCPResponse]
    total: int
    page: int
    limit: int