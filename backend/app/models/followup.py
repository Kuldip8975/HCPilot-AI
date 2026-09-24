"""Follow-up model."""

from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class FollowUpStatus(str, enum.Enum):
    """Follow-up status enum."""
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class FollowUp(BaseModel):
    """Follow-up model for scheduled follow-ups."""

    __tablename__ = "followups"

    interaction_id = Column(UUID(as_uuid=True), ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    scheduled_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(SQLEnum(FollowUpStatus), nullable=False, default=FollowUpStatus.PENDING)
    priority = Column(String(20), nullable=False, default="medium")
    notes = Column(Text, nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    interaction = relationship("Interaction", back_populates="followups")
    user = relationship("User", back_populates="followups")

    def __repr__(self):
        return f"<FollowUp for interaction {self.interaction_id} - {self.status}>"