"""Audit log schemas."""

from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from pydantic import BaseModel, field_validator


class AuditLogResponse(BaseModel):
    """One audit trail entry, as returned to the frontend."""
    id: str
    user_id: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def validate_uuid(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True