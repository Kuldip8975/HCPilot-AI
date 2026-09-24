"""AI service with LangGraph agent - COMPLETE FIXED VERSION."""

import logging
import uuid
from typing import Dict, Any, Optional

from app.services.interaction_service import InteractionService
from app.ai.langgraph_agent import LangGraphAgent
from app.repositories.hcp_repository import HCPRepository
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class AIService:
    """AI service that delegates chat processing to the real LangGraph + Groq agent."""

    def __init__(self, interaction_service, hcp_service, analytics_service):
        self.interaction_service = interaction_service
        self.hcp_service = hcp_service
        self.analytics_service = analytics_service
        self.agent = LangGraphAgent(
            interaction_service=interaction_service,
            hcp_service=hcp_service,
            analytics_service=analytics_service,
        )
        logger.info("AIService initialized with LangGraph agent")

    async def log_interaction_with_ai(
        self,
        user_id: str,
        description: str,
        hcp_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        db=None,
    ) -> Dict[str, Any]:
        """Extract structured interaction fields from a natural-language
        description, WITHOUT saving anything to the database. This powers
        the split-screen Log Interaction page: the user describes the visit
        in the chat panel, the AI fills in the form fields on the left for
        review, and the user clicks the form's own "Log Interaction" button
        to actually submit it. Nothing is persisted here on purpose - the
        person should always see and approve the final data before it's
        written to the database.
        """
        try:
            extract_prompt = f"""Extract structured HCP interaction data from this text:
            "{description}"
            
            Return ONLY JSON with these fields:
            hcp_name: name of the HCP mentioned (or null if none)
            interaction_type: one of meeting/call/email/other (default "meeting")
            topics: short comma-separated list of topics discussed
            summary: a natural, well-written 1-2 sentence summary of the interaction
            notes: any additional relevant notes (sentiment, materials shared, samples distributed, outcomes - combine into one short paragraph, or null)
            follow_up_required: true/false based on whether a follow-up seems needed
            follow_up_date: an ISO date (YYYY-MM-DD) if a follow-up timeframe is mentioned, else null"""

            response = await self.agent.llm_json.ainvoke([
                SystemMessage(content="Extract structured data from the user's interaction description. Return only valid JSON, no markdown fences, no extra text."),
                HumanMessage(content=extract_prompt),
            ], config={"callbacks": [self.agent.langfuse_handler]})

            try:
                extracted = self.agent._parse_json_response(response.content)
            except (ValueError, Exception) as parse_err:
                logger.warning(f"Could not parse log-interaction-with-ai JSON: {parse_err}. Raw: {response.content[:200]!r}")
                extracted = {"summary": description[:200]}

            # Try to resolve an existing HCP by name (read-only lookup, never creates one here)
            resolved_hcp_id = hcp_id
            resolved_hcp_name = None
            hcp_name = extracted.get("hcp_name")
            if not resolved_hcp_id and hcp_name and db is not None:
                hcp_repo = HCPRepository(db)
                matches = await hcp_repo.search(query=hcp_name, limit=1)
                if matches:
                    resolved_hcp_id = str(matches[0].id)
                    resolved_hcp_name = matches[0].name
            elif hcp_name:
                resolved_hcp_name = hcp_name

            fields = {
                "hcp_id": resolved_hcp_id,
                "hcp_name": resolved_hcp_name,
                "interaction_type": extracted.get("interaction_type") or "meeting",
                "topics": extracted.get("topics") or "",
                "summary": extracted.get("summary") or description[:200],
                "notes": extracted.get("notes"),
                "follow_up_required": bool(extracted.get("follow_up_required")),
                "follow_up_date": extracted.get("follow_up_date"),
            }

            if resolved_hcp_name:
                message = f"✅ I've filled in the form based on your description of the visit with {resolved_hcp_name}. Review the details on the left, then click Log Interaction to save."
            else:
                message = "I've filled in what I could from your description. I couldn't identify a specific HCP by name - please select one in the form."

            return {
                "success": True,
                "response": message,
                "extracted": fields,
            }

        except Exception as e:
            logger.error(f"log_interaction_with_ai error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "response": f"I had trouble processing that: {str(e)}",
                "extracted": None,
                "error": str(e),
            }

    async def process_chat_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        db=None,  # Request-scoped AsyncSession, forwarded to the agent's nodes
    ) -> Dict[str, Any]:
        """Process a chat message through the real LangGraph + Groq agent.

        Previously this method classified intent with plain keyword/regex
        matching (e.g. `if "meeting" in message`) and never touched the LLM
        or LangGraph at all, even though both exist elsewhere in the
        codebase. That violated the assignment's requirement that LangGraph
        and an LLM be used, and meant "AI" responses were really just
        string matching. This now runs the actual agent graph, which uses
        Groq for intent classification and entity extraction.
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
            "intent": "",
            "confidence": 0.0,
            "entities": {},
            "tool_result": {},
            "response": "",
            "should_end": False,
            "error": None,
            "db": db,
        }

        try:
            result = await self.agent.run(initial_state)

            tool_result = result.get("tool_result", {}) or {}
            intent = result.get("intent", "generic_response")

            interaction_data = None
            if intent == "log_interaction" and tool_result.get("success"):
                interaction_data = {
                    "id": tool_result.get("interaction_id"),
                    "hcp_name": tool_result.get("hcp_name", "Unknown HCP"),
                    "summary": tool_result.get("summary", ""),
                }

            return {
                "success": result.get("error") is None,
                "response": result.get("response", "I've processed your request."),
                "session_id": session_id,
                "intent": intent,
                "tool_executed": intent if intent != "generic_response" else None,
                "interaction": interaction_data,
                "should_end": result.get("should_end", False),
            }

        except Exception as e:
            logger.error(f"Chat error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "response": f"❌ Error: {str(e)}",
                "session_id": session_id,
                "error": str(e),
            }