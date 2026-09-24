"""Interaction service."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.repositories.interaction_repository import InteractionRepository
from app.repositories.hcp_repository import HCPRepository
from app.repositories.followup_repository import FollowUpRepository
from app.models.interaction import Interaction, InteractionType, InteractionStatus
from app.models.followup import FollowUp, FollowUpStatus
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class InteractionService:
    """Service for managing interactions."""

    def __init__(
        self,
        interaction_repo: InteractionRepository,
        hcp_repo: HCPRepository,
        followup_repo: FollowUpRepository,
    ):
        self.interaction_repo = interaction_repo
        self.hcp_repo = hcp_repo
        self.followup_repo = followup_repo

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Convert string to datetime object."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                # Try ISO format with Z
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try ISO format without timezone
                    return datetime.fromisoformat(value)
                except ValueError:
                    try:
                        # Try date only format
                        return datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        logger.warning(f"Could not parse date string: {value}")
                        return datetime.now()
        return datetime.now()

    async def create_interaction(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> Interaction:
        """Create a new interaction."""
        # Parse date fields
        if "interaction_date" in data:
            data["interaction_date"] = self._parse_datetime(data["interaction_date"])
        else:
            data["interaction_date"] = datetime.now()
            
        if "follow_up_date" in data:
            data["follow_up_date"] = self._parse_datetime(data["follow_up_date"])
        
        # Validate HCP exists
        if data.get("hcp_id"):
            hcp = await self.hcp_repo.get_by_id(data["hcp_id"])
            if not hcp:
                raise NotFoundError("HCP", data["hcp_id"])
            data["hcp_name"] = hcp.name
            data["hcp_specialty"] = hcp.specialty

        # Set defaults
        data["user_id"] = user_id
        if not data.get("interaction_type"):
            data["interaction_type"] = InteractionType.MEETING
        if not data.get("status"):
            data["status"] = InteractionStatus.COMPLETED

        # Create interaction
        interaction = Interaction(**data)
        return await self.interaction_repo.create(interaction)

    async def get_interaction(
        self,
        interaction_id: str,
        user_id: Optional[str] = None,
    ) -> Interaction:
        """Get interaction by ID.

        If user_id is provided, enforces that the interaction belongs to
        that user and raises NotFoundError (not a permission error) if it
        doesn't, so callers can't use this to probe which IDs exist.
        """
        interaction = await self.interaction_repo.get_by_id(interaction_id)
        if not interaction:
            raise NotFoundError("Interaction", interaction_id)
        if user_id is not None and str(interaction.user_id) != user_id:
            raise NotFoundError("Interaction", interaction_id)
        return interaction

    async def get_interactions(
        self,
        user_id: str,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Interaction]:
        """Get interactions for a user."""
        filters = filters or {}
        filters["user_id"] = user_id
        return await self.interaction_repo.get_with_filters(filters, skip, limit)

    async def update_interaction(
        self,
        interaction_id: str,
        user_id: str,
        data: Dict[str, Any]
    ) -> Interaction:
        """Update an interaction."""
        interaction = await self.get_interaction(interaction_id)
        
        # Check ownership
        if str(interaction.user_id) != user_id:
            raise ValidationError("You don't have permission to edit this interaction")

        # Parse date fields if present
        if "interaction_date" in data:
            data["interaction_date"] = self._parse_datetime(data["interaction_date"])
        if "follow_up_date" in data:
            data["follow_up_date"] = self._parse_datetime(data["follow_up_date"])

        # Update fields
        for key, value in data.items():
            if hasattr(interaction, key):
                setattr(interaction, key, value)

        return await self.interaction_repo.update(interaction_id, data)

    async def delete_interaction(self, interaction_id: str, user_id: str) -> bool:
        """Delete an interaction."""
        interaction = await self.get_interaction(interaction_id)
        
        if str(interaction.user_id) != user_id:
            raise ValidationError("You don't have permission to delete this interaction")

        return await self.interaction_repo.delete(interaction_id)

    async def schedule_followup(
        self,
        interaction_id: str,
        user_id: str,
        data: Dict[str, Any]
    ) -> FollowUp:
        """Schedule a follow-up for an interaction."""
        interaction = await self.get_interaction(interaction_id)
        
        # Parse scheduled date
        scheduled_date = self._parse_datetime(data.get("scheduled_date"))
        if not scheduled_date:
            scheduled_date = datetime.now()
        
        followup = FollowUp(
            interaction_id=interaction_id,
            user_id=user_id,
            scheduled_date=scheduled_date,
            priority=data.get("priority", "medium"),
            notes=data.get("notes", ""),
            status=FollowUpStatus.PENDING,
        )
        
        return await self.followup_repo.create(followup)