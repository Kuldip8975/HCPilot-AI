"""Analytics endpoints."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.hcp_repository import HCPRepository
from app.services.analytics_service import AnalyticsService
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analytics"])


def get_analytics_service(
    db: AsyncSession = Depends(get_db),
) -> AnalyticsService:
    """Dependency injection for analytics service."""
    interaction_repo = InteractionRepository(db)
    hcp_repo = HCPRepository(db)
    return AnalyticsService(
        interaction_repo=interaction_repo,
        hcp_repo=hcp_repo,
    )


@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Get dashboard analytics data."""
    try:
        stats = await service.get_dashboard_stats(str(current_user.id))
        return stats
    except Exception as e:
        logger.error(f"Dashboard analytics error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}",
        )


@router.get("/interactions")
async def get_interaction_analytics(
    aggregation: str = Query("daily", description="Aggregation period"),
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Get interaction analytics."""
    try:
        trends = await service.get_interaction_trends(str(current_user.id), days)
        return trends
    except Exception as e:
        logger.error(f"Interaction analytics error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch interaction analytics: {str(e)}",
        )


@router.get("/hcps")
async def get_hcp_analytics(
    top_n: int = Query(10, ge=1, le=50, description="Number of top HCPs"),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Get HCP analytics."""
    try:
        return await service.get_hcp_analytics(str(current_user.id), top_n)
    except Exception as e:
        logger.error(f"HCP analytics error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch HCP analytics: {str(e)}",
        )