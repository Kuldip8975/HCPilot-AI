"""DayPlanVisit model - tracks Smart Day Planner history: which HCPs were
planned to be visited (from a generated day plan) and whether the rep
actually marked them visited, so we can show simple "planned vs actual"
analytics. This is intentionally denormalized (hcp_name stored directly,
not just hcp_id) so analytics queries don't need a join, and history stays
readable even if an HCP is later deleted.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class DayPlanVisit(BaseModel):
    """One planned (and possibly completed) stop from a generated day plan."""

    __tablename__ = "day_plan_visits"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hcp_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hcps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hcp_name = Column(String(200), nullable=False)

    # When this stop was included in a generated plan.
    planned_at = Column(DateTime(timezone=True), nullable=False)

    # Set when the rep clicks "Visited" on this stop. Null = still pending
    # (either not yet visited, or the plan was regenerated/abandoned).
    visited_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<DayPlanVisit hcp={self.hcp_name} visited={self.visited_at is not None}>"