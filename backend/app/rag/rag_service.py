"""
RAG (Retrieval-Augmented Generation) service for the website support widget.

This powers a totally different feature from the LangGraph agent
(app/ai/langgraph_agent.py):

  - LangGraph agent = a TOOL-CALLING agent for logged-in reps. It reads a
    message, decides which CRM action is meant (log an interaction,
    search an HCP, ...), and calls real backend services - it takes
    ACTIONS.
  - This RAG service = a QUESTION-ANSWERING assistant for anonymous
    website visitors on the homepage. It never touches the database or
    takes any action - it only answers "what is this product / how does
    X work" style questions, grounded in our own knowledge base. It
    ANSWERS, it doesn't ACT.

The RAG pipeline here is the textbook two-step process:
    1. Retrieve: find the knowledge-base chunks most relevant to the
       question (see retriever.py).
    2. Generate: hand those chunks to the LLM as context and have it
       write a natural-language answer grounded in them - NOT from
       whatever the model happens to "remember", since it was never
       trained on anything about this specific product.

Grounding matters here specifically because Clinera is a brand-new
product; a general-purpose LLM has literally never seen anything about it
during training, so without retrieval it would either say "I don't know"
or (worse) hallucinate plausible-sounding but wrong details. Retrieval is
what makes an accurate answer possible at all.
"""

import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.rag.knowledge_base import get_knowledge_base
from app.rag.retriever import TfidfRetriever

logger = logging.getLogger(__name__)

# Below this similarity score, a retrieved chunk is considered "not
# actually relevant" and is dropped - this stops the LLM from being fed
# irrelevant context for off-topic questions (e.g. "what's the weather
# today?"), so it can correctly say it doesn't know instead of forcing an
# answer out of unrelated chunks.
MIN_RELEVANCE_SCORE = 0.05

SYSTEM_PROMPT_TEMPLATE = """You are a friendly customer support assistant on HcPilot AI's website. \
HcPilot AI is an app that helps pharma/healthcare sales reps keep track of \
the doctors they visit.

You are talking to a first-time visitor who may have NO idea what this \
software does or how to use it - assume no prior knowledge. Explain things \
the way a helpful human support agent would, in plain everyday language.

Answer using ONLY the CONTEXT below. Keep answers short (2-4 sentences), \
warm, and practical - focus on WHAT TO CLICK and WHAT HAPPENS, not on how \
anything works internally.

Hard rules:
- NEVER mention internal technology names or implementation details - no \
  "AI agent", "LLM", "LangGraph", "MCP", "API", "database", "tech stack", \
  or anything like that. If a visitor asks about those specifically, just \
  say the app is built with modern AI technology and steer back to what it \
  helps them DO.
- If the CONTEXT does not contain the answer, say you're not sure and \
  suggest they sign up and explore, or reach out to support - do NOT make \
  up information that isn't in the CONTEXT.

CONTEXT:
{context}
"""


class RAGService:
    """Retrieval-Augmented Generation service answering product FAQs."""

    def __init__(self):
        self.retriever = TfidfRetriever(get_knowledge_base())
        # Low temperature: this is a factual-answer task, not a creative
        # one - we want the model to stick close to the retrieved context
        # rather than getting inventive.
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0.2,
            max_tokens=300,
        )
        logger.info("RAG service initialized (TF-IDF retriever + Groq generation)")

    async def answer(self, question: str) -> Dict[str, Any]:
        """
        Answer a visitor's question, grounded in the knowledge base.

        Returns: {"answer": str, "sources": List[str]}
        """
        hits = self.retriever.retrieve(question, top_k=3)
        relevant_hits = [h for h in hits if h["score"] >= MIN_RELEVANCE_SCORE]

        if not relevant_hits:
            context = "(no relevant information found in the knowledge base)"
        else:
            context = "\n\n".join(
                f"[{h['title']}]\n{h['text']}" for h in relevant_hits
            )

        system_message = SystemMessage(
            content=SYSTEM_PROMPT_TEMPLATE.format(context=context)
        )
        human_message = HumanMessage(content=question)

        response = await self.llm.ainvoke([system_message, human_message])
        answer_text = response.content.strip()

        return {
            "answer": answer_text,
            "sources": [h["title"] for h in relevant_hits],
        }


# Module-level singleton - the TF-IDF index only needs to be built once
# per process, not on every request.
_rag_service_instance: RAGService | None = None


def get_rag_service() -> RAGService:
    """FastAPI dependency: return the shared RAGService instance."""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance