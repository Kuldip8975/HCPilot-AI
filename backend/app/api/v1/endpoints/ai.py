"""AI endpoints using LangGraph agent with Groq LLM."""

import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from groq import AsyncGroq

from app.api.v1.endpoints.auth import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.repositories.hcp_repository import HCPRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.followup_repository import FollowUpRepository
from app.services.interaction_service import InteractionService
from app.services.hcp_service import HCPService
from app.services.analytics_service import AnalyticsService
from app.services.ai_service import AIService
from app.core.exceptions import NotFoundError
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def get_ai_service(
    db: AsyncSession = Depends(get_db),
) -> AIService:
    """Dependency injection for AI service."""
    interaction_repo = InteractionRepository(db)
    hcp_repo = HCPRepository(db)
    followup_repo = FollowUpRepository(db)

    interaction_service = InteractionService(
        interaction_repo=interaction_repo,
        hcp_repo=hcp_repo,
        followup_repo=followup_repo,
    )
    hcp_service = HCPService(hcp_repo)
    analytics_service = AnalyticsService(
        interaction_repo=interaction_repo,
        hcp_repo=hcp_repo,
    )
    
    return AIService(
        interaction_service=interaction_service,
        hcp_service=hcp_service,
        analytics_service=analytics_service,
    )

@router.post("/chat")
async def chat_message(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
) -> Dict[str, Any]:
    """Send a chat message through the LangGraph agent."""
    try:
        message = request.get("message", "")
        session_id = request.get("session_id", str(uuid.uuid4()))
        context = request.get("context", {})
        
        logger.info(f"Chat - User: {current_user.id}, Message: {message[:100]}...")
        
        # Pass db as a parameter
        result = await ai_service.process_chat_message(
            user_id=str(current_user.id),
            message=message,
            session_id=session_id,
            context=context,
            db=db,  # Pass db here
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "response": "❌ I encountered an error. Please try again.",
            "error": str(e),
            "session_id": request.get("session_id", str(uuid.uuid4())),
        }

@router.post("/chat/log-interaction")
async def log_interaction_with_ai(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
) -> Dict[str, Any]:
    """
    Extract structured interaction fields from a natural-language
    description using AI, for the split-screen Log Interaction page.
    Does not save anything - the frontend uses the returned fields to
    populate the form for the user to review and submit themselves.
    """
    try:
        description = request.get("description", "")
        hcp_id = request.get("hcp_id")
        context = request.get("context", {})
        
        result = await ai_service.log_interaction_with_ai(
            user_id=str(current_user.id),
            description=description,
            hcp_id=hcp_id,
            context=context,
            db=db,
        )
        
        return {
            "success": result.get("success", False),
            "response": result.get("response", "Interaction logged successfully!"),
            "extracted": result.get("extracted"),
            "error": result.get("error"),
        }
        
    except Exception as e:
        logger.error(f"Log interaction error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "response": f"❌ Error: {str(e)}",
            "error": str(e),
        }


@router.get("/chat/followup-recommendations")
async def get_followup_recommendations(
    interaction_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
) -> Dict[str, Any]:
    """
    Get AI-powered follow-up recommendations.
    """
    try:
        # Process through LangGraph
        message = "Give me follow-up recommendations"
        if interaction_id:
            message += f" for interaction {interaction_id}"
        
        result = await ai_service.process_chat_message(
            user_id=str(current_user.id),
            message=message,
            session_id=str(uuid.uuid4()),
        )
        
        return {
            "success": True,
            "recommendations": result.get("tool_result", {}).get("recommendations", []),
            "response": result.get("response"),
        }
        
    except Exception as e:
        logger.error(f"Followup recommendations error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/chat/transcribe")
async def transcribe_voice(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Transcribe a voice recording to text using Groq's hosted Whisper model.
    The returned text flows through the exact same extraction pipeline as
    typed messages (log_interaction_with_ai / process_chat_message) - this
    endpoint's only job is turning audio into text, nothing more.
    """
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No audio data received")

        groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        transcription = await groq_client.audio.transcriptions.create(
            file=(audio.filename or "recording.webm", audio_bytes),
            model="whisper-large-v3-turbo",
        )

        return {
            "success": True,
            "text": transcription.text,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice transcription error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "text": "",
        }