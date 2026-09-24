"""Audit log endpoints - lets a logged-in user see their own activity
trail (what they created/changed, and when)."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditLogResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Audit"])


def get_audit_repo(db: AsyncSession = Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)


@router.get("", response_model=List[AuditLogResponse])
async def get_my_audit_log(
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_user),
    audit_repo: AuditRepository = Depends(get_audit_repo),
) -> List[AuditLogResponse]:
    """List the current user's own audit trail, most recent first -
    every interaction/follow-up/HCP change they made, with what changed."""
    try:
        logs = await audit_repo.get_by_user_id(str(current_user.id), limit=limit)
        return logs
    except Exception as e:
        logger.error(f"Get audit log error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch audit log: {str(e)}",
        )