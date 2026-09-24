"""Priority (Next Best Action) schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """How the priority score was built - shown so the ranking is
    transparent rather than a black box (this is a rule-based score, not
    a trained ML model - see priority_service.py for why)."""

    recency_component: float
    engagement_component: float
    bonus_component: float


class PriorityItem(BaseModel):
    """A single ranked HCP in the rep's weekly priority list."""

    hcp_id: str
    hcp_name: str
    specialty: Optional[str] = None
    score: float = Field(..., description="0-100 priority score, higher = contact sooner")
    days_since_contact: int
    engagement_score: int
    interaction_count: int
    has_pending_followup: bool
    followup_id: Optional[str] = Field(
        default=None,
        description="The pending FollowUp's id, if has_pending_followup is true - lets the "
                     "frontend call PUT /followups/{id}/complete directly from this list.",
    )
    last_topics: Optional[str] = None
    last_summary: Optional[str] = None
    reason: str = Field(..., description="Short, LLM-written (or rule-based fallback) explanation")
    score_breakdown: ScoreBreakdown
    latitude: Optional[float] = Field(None, description="From the HCP's geocoded address, if available")
    longitude: Optional[float] = Field(None, description="From the HCP's geocoded address, if available")


class PriorityResponse(BaseModel):
    """Response for GET /priorities/weekly."""

    priorities: List[PriorityItem]
    generated_at: str

    class Config:
        from_attributes = True


class DayPlanRequest(BaseModel):
    """Request for POST /priorities/day-plan."""

    time_budget_minutes: int = Field(
        ..., gt=0, le=720, description="How much time the rep has today (or has left), in minutes"
    )
    latitude: Optional[float] = Field(
        None,
        description="Rep's current live location (from browser GPS), if available. "
                     "Falls back to the rep's registered address if omitted.",
    )
    longitude: Optional[float] = Field(None, description="Paired with latitude.")
    exclude_hcp_ids: List[str] = Field(
        default_factory=list,
        description="HCPs to leave out of this plan - used when re-routing after some stops "
                     "have already been marked visited, so they aren't suggested again.",
    )


class DayPlanStop(BaseModel):
    """A single visit in the suggested day plan, in visiting order.

    Deliberately uses plain field names ("name", "priority_score") with no
    aliases - FastAPI serializes response models BY ALIAS by default, so an
    earlier version of this schema that aliased hcp_name->"name" and
    score->"priority_score" actually sent the ALIAS as the JSON key, not
    the field name, which silently broke the frontend (it was reading
    stop.hcp_name / stop.score, but those keys were never in the response).
    Matching field names to both the route planner's output dict AND what
    the frontend reads avoids that trap entirely.
    """

    hcp_id: str
    name: str
    specialty: Optional[str] = None
    priority_score: Optional[float] = None
    reason: Optional[str] = None
    latitude: float
    longitude: float
    travel_minutes_from_previous: float
    estimated_arrival_offset_minutes: float


class DayPlanSkipped(BaseModel):
    """An HCP the planner considered but did not include in the route."""

    hcp_id: str
    name: str
    skip_reason: str = Field(..., description="'no_coordinates' (address not geocoded yet) or 'time_budget' (didn't fit)")


class DayPlanResponse(BaseModel):
    """Response for POST /priorities/day-plan."""

    plan: List[DayPlanStop]
    skipped: List[DayPlanSkipped]
    total_value: float
    total_time_minutes: float
    rep_start_latitude: float
    rep_start_longitude: float


class MarkVisitedRequest(BaseModel):
    """Request for POST /priorities/day-plan/mark-visited."""

    hcp_id: str


class MarkVisitedResponse(BaseModel):
    """Response for POST /priorities/day-plan/mark-visited."""

    hcp_id: str
    visited_at: str


class DayPlanAnalytics(BaseModel):
    """Response for GET /priorities/day-plan/analytics - simple 'planned
    vs actual' numbers for the rep's recent Smart Day Planner usage."""

    days: int
    planned_count: int
    visited_count: int
    completion_rate: float = Field(..., description="visited_count / planned_count as a percentage")