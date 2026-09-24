"""
Public support/FAQ chat endpoint - powers the RAG-based chat widget on
the marketing homepage.

Unlike every other endpoint in this API, this one takes NO auth
(`get_current_user` is not a dependency here). That's intentional: this
widget is meant for anonymous visitors on the public homepage who haven't
signed up yet - the whole point is to answer their questions about the
product *before* they create an account.
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.rag.rag_service import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter()


class SupportChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


@router.post("/chat")
async def support_chat(payload: SupportChatRequest):
    """
    Answer a visitor's question about the product, using the RAG
    pipeline (TF-IDF retrieval over app/rag/knowledge_base.py + Groq
    generation grounded in the retrieved chunks).
    """
    try:
        rag_service = get_rag_service()
        result = await rag_service.answer(payload.message)
        return {
            "success": True,
            "answer": result["answer"],
            "sources": result["sources"],
        }
    except Exception as e:
        logger.error(f"Support chat failed: {e}", exc_info=True)
        return {
            "success": False,
            "answer": "Sorry, I'm having trouble answering right now. Please try again in a moment.",
            "sources": [],
        }