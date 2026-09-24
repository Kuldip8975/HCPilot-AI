"""Follow-up endpoints."""

import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.repositories.followup_repository import FollowUpRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.audit_repository import AuditRepository
from app.services.followup_service import FollowUpService
from app.services.audit_service import AuditService
from app.schemas.followup import FollowUpCreate, FollowUpUpdate, FollowUpResponse
from app.core.exceptions import NotFoundError, ValidationError, ConflictError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Follow-ups"])


def get_followup_service(
    db: AsyncSession = Depends(get_db),
) -> FollowUpService:
    """Dependency injection for follow-up service."""
    followup_repo = FollowUpRepository(db)
    interaction_repo = InteractionRepository(db)
    return FollowUpService(
        followup_repo=followup_repo,
        interaction_repo=interaction_repo,
    )


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(AuditRepository(db))


@router.get("", response_model=List[FollowUpResponse])
async def list_followups(
    current_user: User = Depends(get_current_user),
    service: FollowUpService = Depends(get_followup_service),
) -> List[FollowUpResponse]:
    """List the current (rep) user's own follow-ups - used by the
    interaction history page to show each visit's REAL scheduled follow-up
    date (instead of the deprecated, always-empty field on the interaction
    row itself)."""
    try:
        return await service.get_followups(str(current_user.id))
    except Exception as e:
        logger.error(f"List followups error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list followups: {str(e)}",
        )


@router.get("/check-availability")
async def check_followup_availability(
    hcp_id: str = Query(..., description="HCP ID to check"),
    scheduled_date: datetime = Query(..., description="Requested follow-up date/time"),
    current_user: User = Depends(get_current_user),
    service: FollowUpService = Depends(get_followup_service),
) -> Dict[str, Any]:
    """Check whether an HCP is free around a given time, WITHOUT booking
    anything. The frontend calls this before logging an interaction, so a
    double-booked time is caught up front instead of after the visit is
    already saved.
    """
    try:
        return await service.check_conflict(hcp_id=hcp_id, scheduled_date=scheduled_date)
    except Exception as e:
        logger.error(f"Check availability error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check availability: {str(e)}",
        )


@router.post("", response_model=FollowUpResponse)
async def create_followup(
    followup_data: FollowUpCreate,
    current_user: User = Depends(get_current_user),
    service: FollowUpService = Depends(get_followup_service),
    audit: AuditService = Depends(get_audit_service),
) -> FollowUpResponse:
    """Create a follow-up for an interaction."""
    try:
        data = followup_data.model_dump()
        force = data.pop("force", False)
        followup = await service.create_followup(
            interaction_id=followup_data.interaction_id,
            user_id=str(current_user.id),
            data=data,
            force=force,
        )
        await audit.log(
            user_id=str(current_user.id),
            action="create",
            resource="followup",
            resource_id=str(followup.id),
            changes={
                "interaction_id": followup_data.interaction_id,
                "scheduled_date": str(followup_data.scheduled_date),
                "priority": followup_data.priority,
                "forced": force,
            },
        )
        return followup
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message,
        )
    except ConflictError as e:
        # Double-booking: this HCP already has another pending follow-up
        # near the requested time. 409 so the frontend can show the
        # conflict and offer "pick another time" / "book anyway".
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Create followup error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create followup: {str(e)}",
        )


@router.put("/{followup_id}/complete")
async def complete_followup(
    followup_id: str,
    current_user: User = Depends(get_current_user),
    service: FollowUpService = Depends(get_followup_service),
    audit: AuditService = Depends(get_audit_service),
) -> Dict[str, Any]:
    """Mark a follow-up as completed."""
    try:
        await service.complete_followup(followup_id, user_id=str(current_user.id))
        await audit.log(
            user_id=str(current_user.id),
            action="complete",
            resource="followup",
            resource_id=followup_id,
        )
        return {"success": True, "message": "Follow-up completed successfully"}
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Complete followup error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete followup: {str(e)}",
        )