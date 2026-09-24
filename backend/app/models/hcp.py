"""HCP (Healthcare Professional) model."""

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class HCPStatus(str, enum.Enum):
    """HCP status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class HCP(BaseModel):
    """Healthcare Professional model."""

    __tablename__ = "hcps"

    name = Column(String(200), nullable=False, index=True)
    title = Column(String(100), nullable=True)
    specialty = Column(String(100), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(300), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    organization = Column(String(255), nullable=True)
    status = Column(SQLEnum(HCPStatus), nullable=False, default=HCPStatus.ACTIVE)
    engagement_score = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    preferences = Column(Text, nullable=True)
    last_interaction = Column(DateTime(timezone=True), nullable=True)

    interactions = relationship("Interaction", back_populates="hcp", lazy="select")

    def __repr__(self):
        return f"<HCP {self.name} ({self.specialty})>"