"""RAG-based search over a rep's own past interactions.

Answers questions like "what did Dr. Sharma say about Product X last
time?" by RETRIEVING the rep's own logged visits most relevant to the
question (TF-IDF, same technique already used for the website FAQ bot in
app/rag/), then asking the LLM to GENERATE an answer grounded ONLY in
those retrieved visits - so the answer is never hallucinated, and always
traceable back to a real, cited interaction.

This is intentionally a separate, small service from app/rag/rag_service.py
(that one answers generic product FAQs for anonymous visitors from a fixed
knowledge base). Here the "knowledge base" is different for every request
- it's built fresh from whichever rep is asking, scoped to their own data,
so nothing leaks across reps.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.rag.retriever import TfidfRetriever
from app.repositories.interaction_repository import InteractionRepository

logger = logging.getLogger(__name__)

# Below this similarity score a retrieved interaction is considered "not
# actually relevant" and dropped - same idea as the FAQ RAG service.
MIN_RELEVANCE_SCORE = 0.05

SYSTEM_PROMPT_TEMPLATE = """You are a helpful assistant for a pharmaceutical sales rep, answering \
questions about their OWN past visits to doctors (HCPs).

Answer using ONLY the VISIT RECORDS below - these are real logged visits, \
each with a doctor's name, the date, and what was discussed. Be specific \
and cite which doctor/date each fact comes from when relevant.

Hard rules:
- If the visit records don't contain the answer, say so plainly - do NOT \
  invent or guess details that aren't in the records.
- Keep the answer concise (2-5 sentences) and practical - a busy rep is \
  reading this on their phone.

VISIT RECORDS:
{context}
"""


class InteractionSearchService:
    """RAG search over one rep's logged interactions."""

    def __init__(self, interaction_repo: InteractionRepository):
        self.interaction_repo = interaction_repo
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0.2,
            max_tokens=400,
        )

    async def ask(
        self,
        user_id: str,
        question: str,
        hcp_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answer `question`, grounded in this rep's own logged visits.

        Returns: {"answer": str, "sources": [{"interaction_id", "hcp_name",
        "date", "snippet"}]}
        """
        interactions = await self.interaction_repo.get_by_user_id(user_id, limit=500)
        if hcp_id:
            interactions = [i for i in interactions if str(i.hcp_id) == hcp_id]

        if not interactions:
            return {
                "answer": "You don't have any logged visits yet, so I don't have anything to search.",
                "sources": [],
            }

        # Build the retrieval corpus fresh from this rep's own visits -
        # each interaction becomes one searchable "document".
        documents = [
            {
                "id": str(i.id),
                "title": f"{i.hcp_name or 'Unknown HCP'} - {i.interaction_date.strftime('%Y-%m-%d') if i.interaction_date else 'unknown date'}",
                "text": " ".join(filter(None, [i.topics, i.summary, i.notes])) or "(no details logged)",
            }
            for i in interactions
        ]

        retriever = TfidfRetriever(documents)
        hits = retriever.retrieve(question, top_k=5)
        relevant_hits = [h for h in hits if h["score"] >= MIN_RELEVANCE_SCORE]

        if not relevant_hits:
            return {
                "answer": "I couldn't find any past visit that matches that question. Try rephrasing, or mention the doctor's name.",
                "sources": [],
            }

        by_id = {str(i.id): i for i in interactions}
        context = "\n\n".join(f"[{h['title']}]\n{h['text']}" for h in relevant_hits)

        response = await self.llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT_TEMPLATE.format(context=context)),
            HumanMessage(content=question),
        ])
        answer_text = response.content.strip()

        sources = []
        for h in relevant_hits:
            interaction = by_id.get(h["id"])
            if not interaction:
                continue
            sources.append({
                "interaction_id": h["id"],
                "hcp_name": interaction.hcp_name or "Unknown HCP",
                "date": interaction.interaction_date.isoformat() if interaction.interaction_date else None,
                "snippet": h["text"][:200],
            })

        return {"answer": answer_text, "sources": sources}