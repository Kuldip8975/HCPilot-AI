"""Schemas for the RAG-based interaction search feature."""

from typing import List, Optional
from pydantic import BaseModel, Field


class InteractionSearchRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural-language question about past visits")
    hcp_id: Optional[str] = Field(None, description="Optionally scope the search to one HCP")


class InteractionSearchSource(BaseModel):
    interaction_id: str
    hcp_name: str
    date: Optional[str] = None
    snippet: str


class InteractionSearchResponse(BaseModel):
    answer: str
    sources: List[InteractionSearchSource]