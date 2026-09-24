"""Follow-up service."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.repositories.followup_repository import FollowUpRepository
from app.repositories.interaction_repository import InteractionRepository
from app.models.followup import FollowUp, FollowUpStatus
from app.core.exceptions import NotFoundError, ValidationError, ConflictError

logger = logging.getLogger(__name__)

# Same buffer as InteractionService.schedule_followup - two follow-ups with
# the same HCP within this many minutes of each other count as a clash.
# Kept in sync manually since these are two separate creation paths
# (this direct /followups endpoint, and the AI agent's schedule_followup
# tool via InteractionService) that both need to enforce the same rule.
CONFLICT_BUFFER_MINUTES = 30


class FollowUpService:
    """Service for managing follow-ups."""

    def __init__(
        self,
        followup_repo: FollowUpRepository,
        interaction_repo: InteractionRepository,
    ):
        self.followup_repo = followup_repo
        self.interaction_repo = interaction_repo

    async def create_followup(
        self,
        interaction_id: str,
        user_id: str,
        data: Dict[str, Any],
        force: bool = False,
    ) -> FollowUp:
        """Create a new follow-up.

        Before saving, checks this interaction's HCP for any other PENDING
        follow-up within CONFLICT_BUFFER_MINUTES of the requested time
        (the "double-booking" check) and raises ConflictError if one
        exists - unless `force=True`, which a rep can pass to deliberately
        book anyway.
        """
        interaction = await self.interaction_repo.get_by_id(interaction_id)
        if not interaction:
            raise NotFoundError("Interaction", interaction_id)

        scheduled_date = data.get("scheduled_date")
        if scheduled_date and not isinstance(scheduled_date, datetime):
            try:
                scheduled_date = datetime.fromisoformat(str(scheduled_date).replace("Z", "+00:00"))
            except ValueError:
                scheduled_date = None

        if not force and scheduled_date and interaction.hcp_id:
            conflicts = await self.followup_repo.get_conflicts_for_hcp(
                hcp_id=str(interaction.hcp_id),
                requested_datetime=scheduled_date,
                buffer_minutes=CONFLICT_BUFFER_MINUTES,
            )
            if conflicts:
                existing = conflicts[0]
                rep_name = existing.user.full_name if existing.user else "another rep"
                raise ConflictError(
                    f"This HCP already has a follow-up booked around "
                    f"{existing.scheduled_date.isoformat() if existing.scheduled_date else 'that time'} "
                    f"(booked by {rep_name}). Please pick a different time."
                )

        followup = FollowUp(
            interaction_id=interaction_id,
            user_id=user_id,
            scheduled_date=scheduled_date or data.get("scheduled_date"),
            priority=data.get("priority", "medium"),
            notes=data.get("notes", ""),
            status=FollowUpStatus.PENDING,
        )
        return await self.followup_repo.create(followup)

    async def check_conflict(
        self,
        hcp_id: str,
        scheduled_date: datetime,
        buffer_minutes: int = CONFLICT_BUFFER_MINUTES,
    ) -> Dict[str, Any]:
        """Check whether this HCP already has a pending follow-up near the
        requested time, WITHOUT creating anything.

        Used by the frontend to check availability BEFORE logging the
        interaction at all, so a double-booked time blocks the whole
        submission up front instead of saving the visit and then failing
        to book the follow-up afterwards.
        """
        conflicts = await self.followup_repo.get_conflicts_for_hcp(
            hcp_id=hcp_id,
            requested_datetime=scheduled_date,
            buffer_minutes=buffer_minutes,
        )
        if conflicts:
            existing = conflicts[0]
            rep_name = existing.user.full_name if existing.user else "another rep"
            return {
                "available": False,
                "message": (
                    f"This HCP already has a follow-up booked around "
                    f"{existing.scheduled_date.isoformat() if existing.scheduled_date else 'that time'} "
                    f"(booked by {rep_name}). Please pick a different time."
                ),
            }
        return {"available": True, "message": None}

    async def get_followups(self, user_id: str) -> List[FollowUp]:
        """Get follow-ups for a user."""
        return await self.followup_repo.get_by_user_id(user_id)

    async def complete_followup(
        self,
        followup_id: str,
        user_id: Optional[str] = None,
    ) -> FollowUp:
        """Mark a follow-up as completed.

        If user_id is provided, enforces that the follow-up belongs to
        that user and raises NotFoundError (not a permission error) if it
        doesn't, so callers can't use this to probe which IDs exist or
        complete another rep's follow-ups.
        """
        followup = await self.followup_repo.get_by_id(followup_id)
        if not followup:
            raise NotFoundError("FollowUp", followup_id)

        if user_id is not None and str(followup.user_id) != user_id:
            raise NotFoundError("FollowUp", followup_id)

        followup.status = FollowUpStatus.COMPLETED
        followup.completed_date = datetime.utcnow()
        return await self.followup_repo.update(followup_id, {
            "status": FollowUpStatus.COMPLETED,
            "completed_date": datetime.utcnow()
        })