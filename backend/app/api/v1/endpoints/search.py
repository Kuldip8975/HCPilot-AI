"""Interaction search endpoint - RAG-based Q&A over a rep's own past
visits ("what did Dr. X say about Product Y last time?")."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.repositories.interaction_repository import InteractionRepository
from app.services.interaction_search_service import InteractionSearchService
from app.schemas.search import InteractionSearchRequest, InteractionSearchResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Search"])


def get_search_service(db: AsyncSession = Depends(get_db)) -> InteractionSearchService:
    return InteractionSearchService(InteractionRepository(db))


@router.post("/ask", response_model=InteractionSearchResponse)
async def ask_about_interactions(
    request: InteractionSearchRequest,
    current_user: User = Depends(get_current_user),
    service: InteractionSearchService = Depends(get_search_service),
) -> InteractionSearchResponse:
    """Ask a natural-language question about the current user's own
    logged visits, answered with retrieval-augmented generation - grounded
    in real interaction records, with cited sources."""
    try:
        result = await service.ask(
            user_id=str(current_user.id),
            question=request.question,
            hcp_id=request.hcp_id,
        )
        return InteractionSearchResponse(**result)
    except Exception as e:
        logger.error(f"Interaction search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )