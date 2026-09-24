"""Interaction model."""

from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class InteractionType(str, enum.Enum):
    """Interaction type enum."""
    MEETING = "meeting"
    CALL = "call"
    EMAIL = "email"
    OTHER = "other"


class InteractionStatus(str, enum.Enum):
    """Interaction status enum."""
    DRAFT = "draft"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class Interaction(BaseModel):
    """Interaction model for HCP interactions."""

    __tablename__ = "interactions"

    hcp_id = Column(UUID(as_uuid=True), ForeignKey("hcps.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    hcp_name = Column(String(200), nullable=True)
    hcp_specialty = Column(String(100), nullable=True)
    
    interaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    interaction_type = Column(SQLEnum(InteractionType), nullable=False, default=InteractionType.MEETING)
    status = Column(SQLEnum(InteractionStatus), nullable=False, default=InteractionStatus.COMPLETED)
    
    topics = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    follow_up_required = Column(Boolean, nullable=False, default=False)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_priority = Column(String(20), nullable=True, default="medium")
    follow_up_notes = Column(Text, nullable=True)
    
    # Relationships
    hcp = relationship("HCP", back_populates="interactions")
    user = relationship("User", back_populates="interactions")
    followups = relationship("FollowUp", back_populates="interaction", lazy="select")

    def __repr__(self):
        return f"<Interaction {self.hcp_name} - {self.interaction_type} on {self.interaction_date}>"