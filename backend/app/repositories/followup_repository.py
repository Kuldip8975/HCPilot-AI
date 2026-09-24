"""Follow-up repository."""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.models.followup import FollowUp, FollowUpStatus
from app.models.interaction import Interaction
from app.repositories.base_repository import BaseRepository


class FollowUpRepository(BaseRepository[FollowUp]):
    """Repository for FollowUp model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, FollowUp)

    async def get_by_user_id(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FollowUp]:
        """Get follow-ups by user ID."""
        conditions = [
            self.model.user_id == user_id,
            self.model.deleted_at.is_(None)
        ]
        if status:
            conditions.append(self.model.status == status)

        stmt = select(self.model).where(and_(*conditions)).order_by(
            self.model.scheduled_date
        ).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_interaction_id(self, interaction_id: str) -> List[FollowUp]:
        """Get follow-ups by interaction ID."""
        stmt = select(self.model).where(
            self.model.interaction_id == interaction_id,
            self.model.deleted_at.is_(None)
        ).order_by(self.model.scheduled_date)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_due_followups(self, user_id: str) -> List[FollowUp]:
        """Get due follow-ups for a user."""
        now = datetime.utcnow()
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.status == "pending",
            self.model.scheduled_date <= now,
            self.model.deleted_at.is_(None)
        ).order_by(self.model.scheduled_date)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_conflicts_for_hcp(
        self,
        hcp_id: str,
        requested_datetime: datetime,
        buffer_minutes: int = 30,
        exclude_followup_id: Optional[str] = None,
    ) -> List[FollowUp]:
        """Find any existing PENDING follow-up with this same HCP whose
        scheduled_date falls within `buffer_minutes` of the requested time.

        This is the "double-booking" check: a FollowUp doesn't store hcp_id
        directly (it's scoped to an interaction, which is scoped to an
        HCP), so we join through Interaction to filter by hcp_id. Only
        PENDING follow-ups count as a conflict - a cancelled or completed
        one doesn't block a new booking at the same time.
        """
        window_start = requested_datetime - timedelta(minutes=buffer_minutes)
        window_end = requested_datetime + timedelta(minutes=buffer_minutes)

        conditions = [
            Interaction.hcp_id == hcp_id,
            self.model.status == FollowUpStatus.PENDING,
            self.model.scheduled_date >= window_start,
            self.model.scheduled_date <= window_end,
            self.model.deleted_at.is_(None),
        ]
        if exclude_followup_id:
            conditions.append(self.model.id != exclude_followup_id)

        stmt = (
            select(self.model)
            .join(Interaction, self.model.interaction_id == Interaction.id)
            .options(selectinload(self.model.user))
            .where(and_(*conditions))
            .order_by(self.model.scheduled_date)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_hcp_id(
        self,
        hcp_id: str,
        status: Optional[str] = None,
        upcoming_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> List[FollowUp]:
        """Get follow-ups scheduled with a given HCP (doctor dashboard).

        Eager-loads the related interaction and the rep (user) who
        scheduled it, so the doctor dashboard endpoint can show "who" and
        "about what" without extra queries per row.
        """
        conditions = [
            Interaction.hcp_id == hcp_id,
            self.model.deleted_at.is_(None),
        ]
        if status:
            conditions.append(self.model.status == status)
        if upcoming_only:
            conditions.append(self.model.scheduled_date >= datetime.utcnow())

        stmt = (
            select(self.model)
            .join(Interaction, self.model.interaction_id == Interaction.id)
            .options(
                selectinload(self.model.interaction),
                selectinload(self.model.user),
            )
            .where(and_(*conditions))
            .order_by(self.model.scheduled_date)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()