"""Interaction endpoints."""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.hcp_repository import HCPRepository
from app.repositories.followup_repository import FollowUpRepository
from app.repositories.audit_repository import AuditRepository
from app.services.interaction_service import InteractionService
from app.services.audit_service import AuditService
from app.schemas.interaction import (
    InteractionCreate,
    InteractionUpdate,
    InteractionResponse,
    InteractionListResponse,
)
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


def get_interaction_service(
    db: AsyncSession = Depends(get_db),
) -> InteractionService:
    interaction_repo = InteractionRepository(db)
    hcp_repo = HCPRepository(db)
    followup_repo = FollowUpRepository(db)
    return InteractionService(
        interaction_repo=interaction_repo,
        hcp_repo=hcp_repo,
        followup_repo=followup_repo,
    )


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(AuditRepository(db))

@router.get("", response_model=InteractionListResponse)
async def get_interactions(
    hcp_id: Optional[str] = Query(None, description="Filter by HCP ID"),
    interaction_type: Optional[str] = Query(None, description="Filter by type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    service: InteractionService = Depends(get_interaction_service),
) -> Dict[str, Any]:
    """Get all interactions with filters."""
    try:
        filters = {}
        if hcp_id:
            filters["hcp_id"] = hcp_id
        if interaction_type:
            filters["interaction_type"] = interaction_type
        
        skip = (page - 1) * limit
        
        interactions = await service.get_interactions(
            user_id=str(current_user.id),
            filters=filters,
            skip=skip,
            limit=limit,
        )
        
        # Convert to response models safely
        items = []
        for interaction in interactions:
            try:
                items.append(InteractionResponse.model_validate(interaction))
            except Exception as e:
                logger.warning(f"Failed to validate interaction {interaction.id}: {e}")
                continue
        
        return {
            "items": items,
            "total": len(items),
            "page": page,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Get interactions error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch interactions: {str(e)}",
        )

@router.post("", response_model=InteractionResponse)
async def create_interaction(
    interaction_data: InteractionCreate,
    current_user: User = Depends(get_current_user),
    service: InteractionService = Depends(get_interaction_service),
    audit: AuditService = Depends(get_audit_service),
) -> InteractionResponse:
    """Create a new interaction."""
    try:
        interaction = await service.create_interaction(
            user_id=str(current_user.id),
            data=interaction_data.model_dump(),
        )
        await audit.log(
            user_id=str(current_user.id),
            action="create",
            resource="interaction",
            resource_id=str(interaction.id),
            changes={
                "hcp_id": interaction_data.hcp_id,
                "interaction_type": interaction_data.interaction_type,
                "topics": interaction_data.topics,
            },
        )
        return InteractionResponse.model_validate(interaction)
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
    except Exception as e:
        logger.error(f"Create interaction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create interaction: {str(e)}",
        )


@router.get("/{interaction_id}", response_model=InteractionResponse)
async def get_interaction(
    interaction_id: str,
    current_user: User = Depends(get_current_user),
    service: InteractionService = Depends(get_interaction_service),
) -> InteractionResponse:
    """Get interaction by ID."""
    try:
        interaction = await service.get_interaction(
            interaction_id,
            user_id=str(current_user.id),
        )
        return InteractionResponse.model_validate(interaction)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Get interaction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch interaction: {str(e)}",
        )


@router.put("/{interaction_id}", response_model=InteractionResponse)
async def update_interaction(
    interaction_id: str,
    interaction_data: InteractionUpdate,
    current_user: User = Depends(get_current_user),
    service: InteractionService = Depends(get_interaction_service),
    audit: AuditService = Depends(get_audit_service),
) -> InteractionResponse:
    """Update an interaction."""
    try:
        changed_fields = interaction_data.model_dump(exclude_unset=True)
        interaction = await service.update_interaction(
            interaction_id=interaction_id,
            user_id=str(current_user.id),
            data=changed_fields,
        )
        await audit.log(
            user_id=str(current_user.id),
            action="update",
            resource="interaction",
            resource_id=interaction_id,
            changes=changed_fields,
        )
        return InteractionResponse.model_validate(interaction)
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
    except Exception as e:
        logger.error(f"Update interaction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update interaction: {str(e)}",
        )


@router.delete("/{interaction_id}")
async def delete_interaction(
    interaction_id: str,
    current_user: User = Depends(get_current_user),
    service: InteractionService = Depends(get_interaction_service),
    audit: AuditService = Depends(get_audit_service),
) -> Dict[str, Any]:
    """Delete an interaction."""
    try:
        await service.delete_interaction(interaction_id, str(current_user.id))
        await audit.log(
            user_id=str(current_user.id),
            action="delete",
            resource="interaction",
            resource_id=interaction_id,
        )
        return {"success": True, "message": "Interaction deleted successfully"}
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Delete interaction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete interaction: {str(e)}",
        )