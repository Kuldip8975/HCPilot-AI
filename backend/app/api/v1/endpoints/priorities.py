"""Priority (Next Best Action) endpoints.

Mounted at prefix "/priorities" in router.py, so route decorators here are
relative ("" not "/priorities") - see followups.py's history for why a
matching prefix in both places causes a double "/priorities/priorities"
404.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.models.day_plan_visit import DayPlanVisit
from app.repositories.hcp_repository import HCPRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.followup_repository import FollowUpRepository
from app.repositories.day_plan_visit_repository import DayPlanVisitRepository
from app.services.priority_service import PriorityService
from app.services.route_planner_service import RoutePlannerService
from app.schemas.priority import (
    PriorityResponse,
    DayPlanRequest,
    DayPlanResponse,
    DayPlanStop,
    DayPlanSkipped,
    MarkVisitedRequest,
    MarkVisitedResponse,
    DayPlanAnalytics,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_priority_service(
    db: AsyncSession = Depends(get_db),
) -> PriorityService:
    """Dependency injection for the priority (Next Best Action) service."""
    hcp_repo = HCPRepository(db)
    interaction_repo = InteractionRepository(db)
    followup_repo = FollowUpRepository(db)
    return PriorityService(
        hcp_repo=hcp_repo,
        interaction_repo=interaction_repo,
        followup_repo=followup_repo,
    )


def get_route_planner_service() -> RoutePlannerService:
    """Dependency injection for the route planner - stateless, no DB session needed."""
    return RoutePlannerService()


def get_day_plan_visit_repo(db: AsyncSession = Depends(get_db)) -> DayPlanVisitRepository:
    """Dependency injection for day-plan visit history (analytics)."""
    return DayPlanVisitRepository(db)


@router.get("/weekly", response_model=PriorityResponse)
async def get_weekly_priorities(
    current_user: User = Depends(get_current_user),
    service: PriorityService = Depends(get_priority_service),
) -> PriorityResponse:
    """Ranked list of the logged-in rep's HCPs to prioritize this week,
    with a short explanation for each (rule-based score + LLM rationale,
    see priority_service.py)."""
    try:
        result = await service.get_weekly_priorities(str(current_user.id))
        return result
    except Exception as e:
        logger.error(f"Get weekly priorities error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute weekly priorities: {str(e)}",
        )


@router.post("/day-plan", response_model=DayPlanResponse)
async def get_day_plan(
    body: DayPlanRequest,
    current_user: User = Depends(get_current_user),
    priority_service: PriorityService = Depends(get_priority_service),
    route_planner: RoutePlannerService = Depends(get_route_planner_service),
    visit_repo: DayPlanVisitRepository = Depends(get_day_plan_visit_repo),
) -> DayPlanResponse:
    """Suggests which HCPs to visit today, in what order, within the rep's
    time budget.

    Reuses the same priority scores as GET /priorities/weekly as each
    HCP's "value", and real road travel time (via OSRM) as the "cost" -
    see route_planner_service.py for the selection/sequencing algorithm.

    The rep's starting point is their live location if the client sends
    latitude/longitude (browser GPS), otherwise their registered profile
    address is used as a fallback.

    exclude_hcp_ids lets the frontend re-route around HCPs already marked
    visited (see POST /day-plan/mark-visited) without them reappearing.

    Every stop in the returned plan is logged as a DayPlanVisit row
    (planned_at=now, visited_at=null) - this is what powers
    GET /day-plan/analytics. Regenerating a plan (e.g. after marking one
    stop visited) logs a fresh row per remaining stop; that's intentional -
    it's an honest record of what was actually suggested at that moment,
    not just the first plan of the day.
    """
    rep_lat = body.latitude if body.latitude is not None else current_user.latitude
    rep_lon = body.longitude if body.longitude is not None else current_user.longitude

    if rep_lat is None or rep_lon is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No location available - share your live location, or set an address on your profile.",
        )

    priorities_result = await priority_service.get_weekly_priorities(str(current_user.id))
    priorities = [
        item for item in priorities_result["priorities"]
        if item["hcp_id"] not in set(body.exclude_hcp_ids)
    ]

    if not priorities:
        return DayPlanResponse(
            plan=[],
            skipped=[],
            total_value=0,
            total_time_minutes=0,
            rep_start_latitude=rep_lat,
            rep_start_longitude=rep_lon,
        )

    candidates = [
        {
            "hcp_id": item["hcp_id"],
            "name": item["hcp_name"],
            "specialty": item.get("specialty"),
            "reason": item.get("reason"),
            "priority_score": item["score"],
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
        }
        for item in priorities
    ]

    try:
        result = await route_planner.plan_day(
            rep_location=(rep_lat, rep_lon),
            candidates=candidates,
            time_budget_minutes=body.time_budget_minutes,
        )
    except Exception as e:
        logger.error(f"Day-plan computation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute day plan: {str(e)}",
        )

    # Log every stop in this plan for "planned vs actual" analytics. Best
    # effort - a logging failure shouldn't break the actual plan response.
    try:
        if result["plan"]:
            now = datetime.now(timezone.utc)
            visit_rows = [
                DayPlanVisit(
                    user_id=str(current_user.id),
                    hcp_id=stop["hcp_id"],
                    hcp_name=stop["name"],
                    planned_at=now,
                )
                for stop in result["plan"]
            ]
            await visit_repo.create_many(visit_rows)
    except Exception as e:
        logger.warning(f"Failed to log day-plan visits for analytics: {e}")

    return DayPlanResponse(
        plan=[DayPlanStop(**stop) for stop in result["plan"]],
        skipped=[DayPlanSkipped(**s) for s in result["skipped"]],
        total_value=result["total_value"],
        total_time_minutes=result["total_time_minutes"],
        rep_start_latitude=rep_lat,
        rep_start_longitude=rep_lon,
    )


@router.post("/day-plan/mark-visited", response_model=MarkVisitedResponse)
async def mark_day_plan_visited(
    body: MarkVisitedRequest,
    current_user: User = Depends(get_current_user),
    visit_repo: DayPlanVisitRepository = Depends(get_day_plan_visit_repo),
) -> MarkVisitedResponse:
    """Marks the most recently planned (and not yet visited) stop for this
    HCP as visited now. The frontend then re-requests a day plan with this
    HCP added to exclude_hcp_ids to get a re-routed remaining list."""
    entry = await visit_repo.mark_visited(str(current_user.id), body.hcp_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending planned visit found for this HCP - it may already be marked visited, "
                   "or was never part of a generated plan.",
        )
    return MarkVisitedResponse(hcp_id=str(entry.hcp_id), visited_at=entry.visited_at.isoformat())


@router.get("/day-plan/analytics", response_model=DayPlanAnalytics)
async def get_day_plan_analytics(
    current_user: User = Depends(get_current_user),
    visit_repo: DayPlanVisitRepository = Depends(get_day_plan_visit_repo),
) -> DayPlanAnalytics:
    """Simple 'planned vs actual' numbers for the rep's Smart Day Planner
    usage over the last 7 days: how many stops were suggested, how many
    were actually marked visited, and the resulting completion rate."""
    summary = await visit_repo.get_recent_summary(str(current_user.id), days=7)
    return DayPlanAnalytics(**summary)