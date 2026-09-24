"""Audit log model."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AuditLog(BaseModel):
    """Audit log model for tracking changes."""

    __tablename__ = "audit_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    resource = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(50), nullable=True)
    changes = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.resource} by {self.user_id}>"