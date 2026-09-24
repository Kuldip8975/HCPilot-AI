"""DayPlanVisit repository - tracks Smart Day Planner history for
"planned vs actual" analytics.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func

from app.models.day_plan_visit import DayPlanVisit
from app.repositories.base_repository import BaseRepository


class DayPlanVisitRepository(BaseRepository[DayPlanVisit]):
    """Repository for DayPlanVisit model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DayPlanVisit)

    async def create_many(self, entities: List[DayPlanVisit]) -> List[DayPlanVisit]:
        """Bulk-insert planned stops from one generated day plan."""
        for entity in entities:
            self.session.add(entity)
        await self.session.commit()
        for entity in entities:
            await self.session.refresh(entity)
        return entities

    async def mark_visited(self, user_id: str, hcp_id: str) -> Optional[DayPlanVisit]:
        """Mark the most recently planned, not-yet-visited entry for this
        HCP (for this rep) as visited now. If the same HCP was planned more
        than once (e.g. the plan was regenerated), only the latest pending
        one is updated - older ones stay as an honest record that they were
        planned but not marked complete that time."""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.hcp_id == hcp_id,
                self.model.visited_at.is_(None),
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.planned_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry is None:
            return None

        entry.visited_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def get_recent_summary(self, user_id: str, days: int = 7) -> dict:
        """Counts for the "planned vs actual" analytics: how many stops
        were planned in the last N days, and how many were actually marked
        visited."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        planned_stmt = select(func.count()).where(
            self.model.user_id == user_id,
            self.model.planned_at >= since,
            self.model.deleted_at.is_(None),
        )
        visited_stmt = select(func.count()).where(
            self.model.user_id == user_id,
            self.model.planned_at >= since,
            self.model.visited_at.is_not(None),
            self.model.deleted_at.is_(None),
        )

        planned_result = await self.session.execute(planned_stmt)
        visited_result = await self.session.execute(visited_stmt)

        planned_count = planned_result.scalar() or 0
        visited_count = visited_result.scalar() or 0

        return {
            "days": days,
            "planned_count": planned_count,
            "visited_count": visited_count,
            "completion_rate": round((visited_count / planned_count) * 100, 1) if planned_count > 0 else 0.0,
        }