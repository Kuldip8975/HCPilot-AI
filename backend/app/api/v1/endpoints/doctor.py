"""Doctor-facing endpoints.

Everything here is only reachable by a logged-in user with role="doctor"
(enforced by the require_doctor dependency). This is the doctor's own
dashboard: their profile, the follow-ups reps have scheduled with them,
their visit history, and a simple overview/analytics view - the answer to
"how does the doctor know who has a follow-up with them, and what's been
going on". A sales rep's token cannot be used here.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator

from app.api.v1.endpoints.auth import require_doctor
from app.models.database import get_db
from app.models.user import User
from app.repositories.hcp_repository import HCPRepository
from app.repositories.followup_repository import FollowUpRepository
from app.repositories.interaction_repository import InteractionRepository
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Doctor"])


class DoctorProfileResponse(BaseModel):
    """The doctor's own HCP profile, as reps see it."""
    id: str
    name: str
    specialty: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v):
        """HCP.id comes back as a UUID object from SQLAlchemy - pydantic
        won't silently coerce it to str on its own, so do it explicitly
        (same pattern as UserResponse in schemas/auth.py)."""
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class DoctorFollowUpItem(BaseModel):
    """One follow-up scheduled with this doctor, from the doctor's point
    of view - who wants to see them, when, and why."""
    followup_id: str
    interaction_id: Optional[str] = None
    scheduled_date: Optional[str] = None
    status: str
    priority: str
    notes: Optional[str] = None
    rep_name: str
    interaction_summary: Optional[str] = None
    interaction_topics: Optional[str] = None


class DoctorStatsResponse(BaseModel):
    """Overview numbers for the doctor's dashboard home."""
    total_visits: int
    distinct_reps: int
    upcoming_followups: int
    last_visit_date: Optional[str] = None


class DoctorHistoryItem(BaseModel):
    """One past interaction a rep logged with this doctor."""
    interaction_id: str
    interaction_date: Optional[str] = None
    interaction_type: str
    summary: Optional[str] = None
    topics: Optional[str] = None
    rep_name: str


class DoctorAnalyticsResponse(BaseModel):
    """A simple visits-over-time trend for the doctor's dashboard."""
    window_days: int
    total_in_window: int
    daily_trend: Dict[str, int]


def get_hcp_repo(db: AsyncSession = Depends(get_db)) -> HCPRepository:
    return HCPRepository(db)


def get_followup_repo(db: AsyncSession = Depends(get_db)) -> FollowUpRepository:
    return FollowUpRepository(db)


def get_interaction_repo(db: AsyncSession = Depends(get_db)) -> InteractionRepository:
    return InteractionRepository(db)


@router.get("/doctor/me/profile", response_model=DoctorProfileResponse)
async def get_my_profile(
    current_user: User = Depends(require_doctor),
    hcp_repo: HCPRepository = Depends(get_hcp_repo),
) -> DoctorProfileResponse:
    """Get the current doctor's own HCP profile."""
    if not current_user.hcp_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No HCP profile is linked to this account yet.",
        )
    hcp = await hcp_repo.get_by_id(str(current_user.hcp_id))
    if not hcp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked HCP profile could not be found.",
        )
    return DoctorProfileResponse.model_validate(hcp)


@router.get("/doctor/follow-ups", response_model=List[DoctorFollowUpItem])
async def get_my_followups(
    upcoming_only: bool = True,
    current_user: User = Depends(require_doctor),
    followup_repo: FollowUpRepository = Depends(get_followup_repo),
) -> List[DoctorFollowUpItem]:
    """List follow-ups reps have scheduled with the current doctor.

    This is what answers "how will the doctor know who has a follow-up
    with them" - they log in, open this, and see exactly which rep
    scheduled what, and when. Defaults to upcoming (not-yet-passed)
    pending follow-ups; pass upcoming_only=false to see the full history
    too.
    """
    if not current_user.hcp_id:
        # A doctor account with no linked HCP profile simply has nothing
        # to show yet - not an error, just an empty dashboard.
        return []

    followups = await followup_repo.get_by_hcp_id(
        hcp_id=str(current_user.hcp_id),
        upcoming_only=upcoming_only,
        limit=100,
    )

    items: List[DoctorFollowUpItem] = []
    for f in followups:
        rep_name = f.user.full_name if f.user else "A sales rep"
        interaction_summary = f.interaction.summary if f.interaction else None
        interaction_topics = f.interaction.topics if f.interaction else None
        status_value = f.status.value if hasattr(f.status, "value") else f.status
        items.append(
            DoctorFollowUpItem(
                followup_id=str(f.id),
                interaction_id=str(f.interaction_id) if f.interaction_id else None,
                scheduled_date=f.scheduled_date.isoformat() if f.scheduled_date else None,
                status=status_value,
                priority=f.priority,
                notes=f.notes,
                rep_name=rep_name,
                interaction_summary=interaction_summary,
                interaction_topics=interaction_topics,
            )
        )
    return items


@router.get("/doctor/stats", response_model=DoctorStatsResponse)
async def get_my_stats(
    current_user: User = Depends(require_doctor),
    interaction_repo: InteractionRepository = Depends(get_interaction_repo),
    followup_repo: FollowUpRepository = Depends(get_followup_repo),
) -> DoctorStatsResponse:
    """Overview numbers for the doctor's dashboard: how many reps have
    visited them in total, how many visits, and how many follow-ups are
    still upcoming. This is the "Overview" tab's data."""
    if not current_user.hcp_id:
        return DoctorStatsResponse(total_visits=0, distinct_reps=0, upcoming_followups=0)

    interactions = await interaction_repo.get_by_hcp_id_with_rep(
        hcp_id=str(current_user.hcp_id), limit=1000
    )
    upcoming = await followup_repo.get_by_hcp_id(
        hcp_id=str(current_user.hcp_id), upcoming_only=True, limit=1000
    )

    distinct_reps = len({str(i.user_id) for i in interactions if i.user_id})
    last_visit = interactions[0].interaction_date if interactions else None

    return DoctorStatsResponse(
        total_visits=len(interactions),
        distinct_reps=distinct_reps,
        upcoming_followups=len(upcoming),
        last_visit_date=last_visit.isoformat() if last_visit else None,
    )


@router.get("/doctor/history", response_model=List[DoctorHistoryItem])
async def get_my_history(
    limit: int = 50,
    current_user: User = Depends(require_doctor),
    interaction_repo: InteractionRepository = Depends(get_interaction_repo),
) -> List[DoctorHistoryItem]:
    """Full visit history: every interaction a rep has logged with this
    doctor, most recent first - who visited, when, and a short summary of
    what was discussed."""
    if not current_user.hcp_id:
        return []

    interactions = await interaction_repo.get_by_hcp_id_with_rep(
        hcp_id=str(current_user.hcp_id), limit=limit
    )

    items: List[DoctorHistoryItem] = []
    for i in interactions:
        rep_name = i.user.full_name if i.user else "A sales rep"
        type_value = i.interaction_type.value if hasattr(i.interaction_type, "value") else i.interaction_type
        items.append(
            DoctorHistoryItem(
                interaction_id=str(i.id),
                interaction_date=i.interaction_date.isoformat() if i.interaction_date else None,
                interaction_type=type_value,
                summary=i.summary,
                topics=i.topics,
                rep_name=rep_name,
            )
        )
    return items


@router.get("/doctor/analytics", response_model=DoctorAnalyticsResponse)
async def get_my_analytics(
    days: int = 30,
    current_user: User = Depends(require_doctor),
    interaction_repo: InteractionRepository = Depends(get_interaction_repo),
) -> DoctorAnalyticsResponse:
    """A simple day-by-day count of visits over the trailing `days` days -
    enough for a small bar/line trend on the doctor's dashboard without
    needing a charting library on the backend."""
    if not current_user.hcp_id:
        return DoctorAnalyticsResponse(window_days=days, total_in_window=0, daily_trend={})

    interactions = await interaction_repo.get_by_hcp_id_with_rep(
        hcp_id=str(current_user.hcp_id), limit=1000
    )

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    trend: Dict[str, int] = {}
    for i in interactions:
        interaction_date = i.interaction_date
        if interaction_date is None:
            continue
        if interaction_date.tzinfo is None:
            interaction_date = interaction_date.replace(tzinfo=timezone.utc)
        if interaction_date >= cutoff:
            key = interaction_date.strftime("%Y-%m-%d")
            trend[key] = trend.get(key, 0) + 1

    return DoctorAnalyticsResponse(
        window_days=days,
        total_in_window=sum(trend.values()),
        daily_trend=trend,
    )