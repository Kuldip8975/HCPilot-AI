"""User model."""

from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization.

    Two roles use this same table:
      - "sales_rep": a medical representative. Logs interactions, searches
        HCPs, schedules follow-ups. `hcp_id` is always null for these.
        `address`/`latitude`/`longitude` are their own base location, used
        as a fallback for the day-planner map when live browser GPS is
        unavailable or denied.
      - "doctor": a healthcare professional (HCP) who can log in to see the
        follow-ups reps have scheduled with them. `hcp_id` links this login
        to their existing profile row in the `hcps` table (the same table
        reps use to search/add doctors) - so a doctor's "profile" data
        (name, specialty, organization, address, lat/long) lives in one
        place whether a rep added them first or the doctor signed up first.
        This user's own `address`/`latitude`/`longitude` columns are left
        null for doctors - the HCP row is the source of truth for them.
    """

    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False, default="sales_rep")
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Sales-rep-only fields (see class docstring). Nullable because doctors
    # don't use these, and a rep may not have set an address yet either.
    address = Column(String(300), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Only set when role == "doctor" - points at this doctor's HCP profile
    # row (created fresh at signup, or matched against one a rep already
    # added, by email).
    hcp_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hcps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    interactions = relationship("Interaction", back_populates="user", lazy="select")
    followups = relationship("FollowUp", back_populates="user", lazy="select")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="select")
    hcp_profile = relationship("HCP", foreign_keys=[hcp_id], lazy="select")

    def to_dict(self):
        """Convert to dictionary with string ID."""
        data = super().to_dict()
        data["id"] = str(self.id)
        if self.hcp_id:
            data["hcp_id"] = str(self.hcp_id)
        return data