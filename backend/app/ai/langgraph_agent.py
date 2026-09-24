"""Complete LangGraph Agent with Groq LLM and 7 Tools."""

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler

from app.config import settings
from app.services.interaction_service import InteractionService
from app.services.hcp_service import HCPService
from app.services.analytics_service import AnalyticsService
from app.repositories.hcp_repository import HCPRepository
from app.models.hcp import HCP
from app.models.database import get_db
from app.core.exceptions import ConflictError

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for LangGraph agent."""
    messages: Annotated[List[Dict[str, str]], add_messages]
    user_id: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    tool_result: Dict[str, Any]
    response: str
    should_end: bool
    error: Optional[str]
    db: Optional[Any]  # Request-scoped SQLAlchemy AsyncSession, injected by the caller


class LangGraphAgent:
    """
    Complete LangGraph Agent with 7 Tools using Groq LLM.
    """

    def __init__(
        self,
        interaction_service: InteractionService,
        hcp_service: HCPService,
        analytics_service: AnalyticsService,
    ):
        self.interaction_service = interaction_service
        self.hcp_service = hcp_service
        self.analytics_service = analytics_service
        
        # Initialize Groq LLM
        # Two clients: one forced into JSON mode for structured extraction
        # (intent classification, entity extraction, etc.), and a plain one
        # for free-text conversational replies. Forcing JSON mode globally
        # would break generic_response_node, which needs normal prose.
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
        )
        self.llm_json = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0.1,  # low temperature: consistent, deterministic extraction
            max_tokens=settings.GROQ_MAX_TOKENS,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        # Langfuse observability: traces every LLM call below (prompt, response,
        # latency, tokens) so failures and behavior can be inspected on a
        # dashboard instead of grepping through log files. If keys aren't
        # configured, this still works - the handler just has nothing to send to.
        try:
            Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST,
            )
            self.langfuse_handler = LangfuseCallbackHandler()
            logger.info("Langfuse observability enabled")
        except Exception as e:
            logger.warning(f"Langfuse initialization failed, continuing without tracing: {e}")
            # Harmless no-op so `callbacks=[self.langfuse_handler]` below always
            # gets a valid handler, even if Langfuse itself isn't configured.
            from langchain_core.callbacks import BaseCallbackHandler
            self.langfuse_handler = BaseCallbackHandler()
        
        # Build the graph
        self.graph = self._build_graph()
        logger.info(f"LangGraph Agent initialized with Groq {settings.GROQ_MODEL}")

    @staticmethod
    def _parse_json_response(content: str) -> Dict[str, Any]:
        """Robustly parse a JSON object out of an LLM response.

        Groq/Gemma (and most chat LLMs) frequently do NOT return pure JSON
        even when asked to -- they wrap it in markdown code fences
        (```json ... ```) or add a sentence of preamble/explanation before
        or after the object. A bare `json.loads(response.content)` fails on
        all of these and silently falls back to a generic/default response,
        which is why intent classification, interaction extraction, and
        search-query extraction were all behaving like they ignored the LLM
        entirely. This strips fences and extracts the first {...} block
        before parsing.
        """
        if not content:
            raise ValueError("Empty LLM response")

        text = content.strip()

        # Strip ```json ... ``` or ``` ... ``` code fences if present
        fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if fence_match:
            text = fence_match.group(1).strip()

        # If there's still leading/trailing prose, grab the first {...} block
        if not text.startswith("{"):
            brace_match = re.search(r"\{.*\}", text, re.DOTALL)
            if brace_match:
                text = brace_match.group(0)

        return json.loads(text)

    @staticmethod
    def _get_last_message_text(messages: List[Any]) -> str:
        """Extract the text content of the last message, regardless of
        whether it's a plain dict (the shape we pass in initially) or a
        LangChain BaseMessage object (what LangGraph's `add_messages`
        reducer actually converts it to internally). The previous code
        (`messages[-1]["content"] if isinstance(messages[-1], dict) else
        messages[-1]`) returned the *entire message object* in the object
        case instead of its `.content`, which either got silently
        stringified when interpolated into an f-string, or raised a
        pydantic validation error when passed directly as `content=` to a
        new HumanMessage/SystemMessage."""
        if not messages:
            return ""
        last = messages[-1]
        if isinstance(last, dict):
            return last.get("content", "")
        if hasattr(last, "content"):
            return last.content
        return str(last)

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("classify_intent", self.classify_intent_node)
        workflow.add_node("log_interaction", self.log_interaction_node)
        workflow.add_node("edit_interaction", self.edit_interaction_node)
        workflow.add_node("view_history", self.view_history_node)
        workflow.add_node("search_hcp", self.search_hcp_node)
        workflow.add_node("schedule_followup", self.schedule_followup_node)
        workflow.add_node("analyze_trends", self.analyze_trends_node)
        workflow.add_node("generic_response", self.generic_response_node)
        workflow.add_node("format_response", self.format_response_node)
        
        # Set entry point
        workflow.set_entry_point("classify_intent")
        
        # Conditional routing
        workflow.add_conditional_edges(
            "classify_intent",
            self.route_to_tool,
            {
                "log_interaction": "log_interaction",
                "edit_interaction": "edit_interaction",
                "view_history": "view_history",
                "search_hcp": "search_hcp",
                "schedule_followup": "schedule_followup",
                "analyze_trends": "analyze_trends",
                "generic_response": "generic_response",
            }
        )
        
        # All tools go to format_response
        workflow.add_edge("log_interaction", "format_response")
        workflow.add_edge("edit_interaction", "format_response")
        workflow.add_edge("view_history", "format_response")
        workflow.add_edge("search_hcp", "format_response")
        workflow.add_edge("schedule_followup", "format_response")
        workflow.add_edge("analyze_trends", "format_response")
        workflow.add_edge("generic_response", "format_response")
        
        workflow.add_edge("format_response", END)
        
        return workflow.compile()

    # ============================================
    # NODE 1: CLASSIFY INTENT (Uses Groq LLM)
    # ============================================
    async def classify_intent_node(self, state: AgentState) -> Dict[str, Any]:
        """Classify user intent using Groq LLM."""
        try:
            messages = state.get("messages", [])
            if not messages:
                return self._default_intent_response()
            
            last_message = self._get_last_message_text(messages)
            
            system_prompt = """You are an AI assistant for a Healthcare Professional CRM system.
            Classify the user's intent from their message.

            Available intents:
            1. log_interaction - User wants to log a new HCP interaction
            2. edit_interaction - User wants to edit an existing interaction
            3. view_history - User wants to view interaction history
            4. search_hcp - User wants to search for HCPs
            5. schedule_followup - User wants to schedule a follow-up
            6. analyze_trends - User wants to see analytics/trends
            7. generic_response - General question or greeting

            Return ONLY a JSON object with:
            {
                "intent": "one of the above",
                "confidence": 0.0-1.0,
                "entities": {
                    "hcp_name": "extracted name or null",
                    "hcp_specialty": "extracted specialty or null",
                    "interaction_id": "extracted ID or null",
                    "date": "extracted date or null",
                    "follow_up_date": "extracted follow-up date or null",
                    "summary": "extracted summary or null"
                }
            }"""
            
            response = await self.llm_json.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"User message: {last_message}")
            ], config={"callbacks": [self.langfuse_handler]})
            
            try:
                result = self._parse_json_response(response.content)
                return {
                    "intent": result.get("intent", "generic_response"),
                    "confidence": result.get("confidence", 0.0),
                    "entities": result.get("entities", {}),
                    "error": None
                }
            except (json.JSONDecodeError, ValueError) as parse_err:
                logger.warning(f"Could not parse intent JSON from LLM: {parse_err}. Raw response: {response.content[:200]!r}")
                return self._default_intent_response()
                
        except Exception as e:
            logger.error(f"Intent classification error: {str(e)}")
            return self._default_intent_response()

    def _default_intent_response(self) -> Dict[str, Any]:
        """Default intent response."""
        return {
            "intent": "generic_response",
            "confidence": 0.5,
            "entities": {},
            "error": None
        }

    def route_to_tool(self, state: AgentState) -> str:
        """Route to appropriate tool based on intent."""
        intent = state.get("intent", "generic_response")
        if state.get("confidence", 0.0) < 0.4:
            return "generic_response"
        return intent

    # ============================================
    # TOOL 1: LOG INTERACTION
    # ============================================
    async def log_interaction_node(self, state: AgentState) -> Dict[str, Any]:
        """Tool 1: Log a new interaction using Groq LLM."""
        try:
            entities = state.get("entities", {})
            messages = state.get("messages", [])
            last_message = self._get_last_message_text(messages)
            
            # Use Groq to extract structured data
            extract_prompt = f"""Extract structured interaction data from this text:
            "{last_message}"
            
            Return JSON with:
            hcp_name: name of the HCP (if mentioned)
            hcp_specialty: specialty (if mentioned)
            interaction_date: date (if mentioned, else today)
            interaction_type: meeting/call/email/other
            topics: list of topics discussed
            summary: brief summary (max 100 words)
            follow_up_required: true/false
            follow_up_date: follow-up date (if mentioned)
            follow_up_notes: follow-up notes (if mentioned)"""
            
            response = await self.llm_json.ainvoke([
                SystemMessage(content="Extract structured data from the user's interaction description."),
                HumanMessage(content=extract_prompt)
            ], config={"callbacks": [self.langfuse_handler]})
            
            try:
                extracted = self._parse_json_response(response.content)
            except (json.JSONDecodeError, ValueError) as parse_err:
                logger.warning(f"Could not parse extraction JSON from LLM: {parse_err}. Raw response: {response.content[:200]!r}")
                extracted = {}
            
            # Extract HCP name from entities or extracted
            hcp_name = entities.get("hcp_name") or extracted.get("hcp_name")
            hcp_specialty = entities.get("hcp_specialty") or extracted.get("hcp_specialty")
            
            # Find or create HCP
            hcp_id = None
            db = state.get("db")
            if hcp_name and db is not None:
                hcp_repo = HCPRepository(db)

                # Search for an existing HCP with this name first, so we
                # don't create a duplicate every time someone logs an
                # interaction (this was the previous bug: it always
                # created a brand-new HCP record instead of matching
                # against the existing one).
                existing = await hcp_repo.search(query=hcp_name, limit=1)
                if existing:
                    hcp_id = str(existing[0].id)
                    logger.info(f"Found existing HCP '{hcp_name}' (ID: {hcp_id})")
                else:
                    new_hcp = HCP(
                        name=hcp_name,
                        specialty=hcp_specialty or "Unknown",
                    )
                    db.add(new_hcp)
                    await db.commit()
                    await db.refresh(new_hcp)
                    hcp_id = str(new_hcp.id)
                    logger.info(f"Created new HCP '{hcp_name}' (ID: {hcp_id})")
            
            # Create interaction
            if hcp_id:
                interaction_data = {
                    "hcp_id": hcp_id,
                    "interaction_date": datetime.now(),
                    "interaction_type": extracted.get("interaction_type", "meeting"),
                    "topics": ", ".join(extracted.get("topics", [])) if isinstance(extracted.get("topics"), list) else extracted.get("topics", "AI Logged"),
                    "summary": extracted.get("summary", last_message[:200]),
                    "notes": last_message,
                    "follow_up_required": extracted.get("follow_up_required", False),
                    "follow_up_date": None,
                    "follow_up_priority": "medium",
                }
                
                interaction = await self.interaction_service.create_interaction(
                    user_id=state.get("user_id"),
                    data=interaction_data,
                )
                
                return {
                    "tool_result": {
                        "success": True,
                        "interaction_id": str(interaction.id),
                        "hcp_name": hcp_name or "Unknown HCP",
                        "summary": interaction_data["summary"][:100],
                    },
                    "response": f"✅ Interaction logged successfully with {hcp_name or 'the HCP'}!",
                }
            
            return {
                "tool_result": {"success": False, "error": "No HCP found"},
                "response": "I couldn't identify the HCP. Please provide the HCP name.",
            }
            
        except Exception as e:
            logger.error(f"Log interaction error: {str(e)}")
            return {
                "tool_result": {"success": False, "error": str(e)},
                "response": f"Error logging interaction: {str(e)}",
            }

    # ============================================
    # TOOL 2: EDIT INTERACTION
    # ============================================
    async def edit_interaction_node(self, state: AgentState) -> Dict[str, Any]:
        """Tool 2: Edit an existing interaction using Groq LLM."""
        try:
            messages = state.get("messages", [])
            last_message = self._get_last_message_text(messages)
            entities = state.get("entities", {})
            db = state.get("db")

            # Use Groq to understand what to edit. We ask for hcp_name too
            # since the user usually refers to "my last interaction with
            # Dr. X" rather than an actual interaction ID.
            edit_prompt = f"""The user wants to edit a logged HCP interaction. Parse this request:
            "{last_message}"
            
            Return JSON with:
            interaction_id: the ID of the interaction to edit, if an actual ID is mentioned, else null
            hcp_name: name of the HCP whose most recent interaction should be edited, if no ID is given
            changes: an object of field:new_value pairs to update. Valid fields: summary, notes, interaction_type, follow_up_required, follow_up_date
            Example: {{"interaction_id": null, "hcp_name": "Dr. Sarah Chen", "changes": {{"notes": "sentiment: neutral"}}}}"""
            
            response = await self.llm_json.ainvoke([
                SystemMessage(content="Parse the user's edit request and return only JSON."),
                HumanMessage(content=edit_prompt)
            ], config={"callbacks": [self.langfuse_handler]})

            try:
                parsed = self._parse_json_response(response.content)
            except (json.JSONDecodeError, ValueError) as parse_err:
                logger.warning(f"Could not parse edit-request JSON from LLM: {parse_err}. Raw response: {response.content[:200]!r}")
                parsed = {}

            interaction_id = parsed.get("interaction_id")
            hcp_name = entities.get("hcp_name") or parsed.get("hcp_name")
            changes = parsed.get("changes") or {}

            if not changes:
                return {
                    "tool_result": {"success": False, "error": "No changes identified"},
                    "response": "I couldn't tell what you'd like to change. Could you be more specific, e.g. 'change the summary to ...'?",
                }

            # The Interaction model has no dedicated 'sentiment' column, but
            # people naturally ask to change it (it's in the UI mockup).
            # Fold it into notes instead of silently dropping it.
            if "sentiment" in changes:
                sentiment_value = changes.pop("sentiment")
                changes["notes"] = f"Sentiment: {sentiment_value}"

            # Resolve which interaction to edit
            if not interaction_id:
                if not hcp_name or db is None:
                    return {
                        "tool_result": {"success": False, "error": "No interaction identified"},
                        "response": "I couldn't tell which interaction to edit. Please name the HCP or the interaction.",
                    }
                hcp_repo = HCPRepository(db)
                matches = await hcp_repo.search(query=hcp_name, limit=1)
                if not matches:
                    return {
                        "tool_result": {"success": False, "error": "HCP not found"},
                        "response": f"I couldn't find an HCP named '{hcp_name}'.",
                    }
                recent = await self.interaction_service.interaction_repo.get_by_hcp_id(
                    hcp_id=str(matches[0].id), limit=1
                )
                if not recent:
                    return {
                        "tool_result": {"success": False, "error": "No interaction found"},
                        "response": f"I couldn't find a logged interaction with {matches[0].name} to edit.",
                    }
                interaction_id = str(recent[0].id)
                hcp_name = matches[0].name

            updated = await self.interaction_service.update_interaction(
                interaction_id=interaction_id,
                user_id=state.get("user_id"),
                data=changes,
            )

            return {
                "tool_result": {
                    "success": True,
                    "interaction_id": str(updated.id),
                    "changes": changes,
                },
                "response": f"✅ Updated the interaction with {hcp_name or 'that HCP'}: {', '.join(changes.keys())} changed.",
            }
            
        except Exception as e:
            logger.error(f"Edit interaction error: {str(e)}")
            return {
                "tool_result": {"success": False, "error": str(e)},
                "response": f"Error editing interaction: {str(e)}",
            }

    # ============================================
    # TOOL 3: VIEW HISTORY
    # ============================================
    async def view_history_node(self, state: AgentState) -> Dict[str, Any]:
        """Tool 3: View interaction history."""
        try:
            user_id = state.get("user_id")
            if not user_id:
                return {
                    "tool_result": {"success": False, "error": "User not authenticated"},
                    "response": "Please login to view your history.",
                }
            
            interactions = await self.interaction_service.get_interactions(
                user_id=user_id,
                limit=5
            )
            
            if not interactions:
                return {
                    "tool_result": {"success": True, "interactions": []},
                    "response": "You don't have any interactions logged yet.",
                }
            
            # Format response
            response = "📋 **Your Recent Interactions:**\n\n"
            for i, interaction in enumerate(interactions[:5], 1):
                hcp_name = getattr(interaction, 'hcp_name', 'Unknown HCP')
                date = getattr(interaction, 'interaction_date', 'Unknown date')
                summary = getattr(interaction, 'summary', 'No summary')[:100]
                response += f"{i}. **{hcp_name}** - {date.strftime('%Y-%m-%d')}\n   _{summary}..._\n\n"
            
            return {
                "tool_result": {"success": True, "interactions": interactions},
                "response": response,
            }
            
        except Exception as e:
            logger.error(f"View history error: {str(e)}")
            return {
                "tool_result": {"success": False, "error": str(e)},
                "response": f"Error viewing history: {str(e)}",
            }

    # ============================================
    # TOOL 4: SEARCH HCP
    # ============================================
    async def search_hcp_node(self, state: AgentState) -> Dict[str, Any]:
        """Tool 4: Search for HCPs."""
        try:
            entities = state.get("entities", {})
            messages = state.get("messages", [])
            last_message = self._get_last_message_text(messages)
            
            # Use Groq to extract search query
            search_prompt = f"""Extract the search query from this message:
            "{last_message}"
            
            Return JSON with:
            query: the search term
            specialty: specialty filter (if mentioned)
            location: location filter (if mentioned)"""
            
            response = await self.llm_json.ainvoke([
                SystemMessage(content="Extract search query."),
                HumanMessage(content=search_prompt)
            ], config={"callbacks": [self.langfuse_handler]})
            
            try:
                extracted = self._parse_json_response(response.content)
                query = extracted.get("query", last_message)
            except (json.JSONDecodeError, ValueError) as parse_err:
                logger.warning(f"Could not parse search query JSON from LLM: {parse_err}. Raw response: {response.content[:200]!r}")
                query = last_message
            
            logger.info(f"Search HCP query extracted from LLM: {query!r}")
            hcps = await self.hcp_service.get_hcps(filters={"search": query}, limit=5)

            # The LLM's extracted query sometimes subtly differs from the
            # literal text (dropped punctuation, reordered words, etc.),
            # which breaks an exact ILIKE substring match even when the
            # HCP clearly exists. Fall back to trying each significant
            # word from the raw message on its own before giving up.
            if not hcps:
                words = [w.strip(".,!?") for w in last_message.split() if len(w.strip(".,!?")) > 2]
                stopwords = {"the", "for", "find", "search", "look", "hcp", "hcps", "and", "with"}
                for word in words:
                    if word.lower() in stopwords:
                        continue
                    hcps = await self.hcp_service.get_hcps(filters={"search": word}, limit=5)
                    if hcps:
                        logger.info(f"Search HCP fallback matched on word: {word!r}")
                        break
            
            if not hcps:
                return {
                    "tool_result": {"success": True, "hcps": []},
                    "response": f"No HCPs found matching '{query}'.",
                }
            
            response_text = "🔍 **Search Results:**\n\n"
            for hcp in hcps:
                name = getattr(hcp, 'name', 'Unknown')
                specialty = getattr(hcp, 'specialty', 'No specialty')
                location = getattr(hcp, 'location', 'No location')
                response_text += f"• **{name}**\n  {specialty} | {location}\n\n"
            
            return {
                "tool_result": {"success": True, "hcps": hcps},
                "response": response_text,
            }
            
        except Exception as e:
            logger.error(f"Search HCP error: {str(e)}")
            return {
                "tool_result": {"success": False, "error": str(e)},
                "response": f"Error searching HCPs: {str(e)}",
            }

    # ============================================
    # TOOL 5: SCHEDULE FOLLOW-UP
    # ============================================
    async def schedule_followup_node(self, state: AgentState) -> Dict[str, Any]:
        """Tool 5: Schedule a follow-up."""
        try:
            messages = state.get("messages", [])
            last_message = self._get_last_message_text(messages)
            entities = state.get("entities", {})
            db = state.get("db")

            # Use Groq to extract follow-up details
            followup_prompt = f"""Extract follow-up details from this message:
            "{last_message}"
            
            Return JSON with:
            hcp_name: name of the HCP
            follow_up_date: when (YYYY-MM-DD format, if mentioned, else null)
            follow_up_notes: any notes about the follow-up
            priority: high/medium/low"""
            
            response = await self.llm_json.ainvoke([
                SystemMessage(content="Extract follow-up details."),
                HumanMessage(content=followup_prompt)
            ], config={"callbacks": [self.langfuse_handler]})

            try:
                extracted = self._parse_json_response(response.content)
            except (json.JSONDecodeError, ValueError) as parse_err:
                logger.warning(f"Could not parse follow-up JSON from LLM: {parse_err}. Raw response: {response.content[:200]!r}")
                extracted = {}

            hcp_name = entities.get("hcp_name") or extracted.get("hcp_name")

            if not hcp_name or db is None:
                return {
                    "tool_result": {"success": False, "error": "No HCP identified"},
                    "response": "I couldn't tell which HCP this follow-up is for. Could you name them specifically?",
                }

            # Find the HCP, then their most recent interaction to attach the follow-up to
            hcp_repo = HCPRepository(db)
            matches = await hcp_repo.search(query=hcp_name, limit=1)
            if not matches:
                return {
                    "tool_result": {"success": False, "error": "HCP not found"},
                    "response": f"I couldn't find an HCP named '{hcp_name}'. Please check the name and try again.",
                }

            hcp = matches[0]
            recent_interactions = await self.interaction_service.interaction_repo.get_by_hcp_id(
                hcp_id=str(hcp.id), limit=1
            )
            if not recent_interactions:
                return {
                    "tool_result": {"success": False, "error": "No interaction to attach follow-up to"},
                    "response": f"I couldn't schedule a follow-up because there's no logged interaction with {hcp.name} yet. Log an interaction first.",
                }

            interaction = recent_interactions[0]
            followup_date_str = extracted.get("follow_up_date")

            try:
                followup = await self.interaction_service.schedule_followup(
                    interaction_id=str(interaction.id),
                    user_id=state.get("user_id"),
                    data={
                        "scheduled_date": followup_date_str,
                        "priority": extracted.get("priority", "medium"),
                        "notes": extracted.get("follow_up_notes", last_message[:200]),
                    },
                )
            except ConflictError as conflict_err:
                # Double-booking: this HCP already has another pending
                # follow-up near the requested time. Instead of a raw
                # error, let the agent explain the clash and ask the rep
                # to pick a different time - this is the "agent reacts
                # intelligently instead of blindly saving" behavior.
                return {
                    "tool_result": {"success": False, "error": "conflict", "detail": conflict_err.message},
                    "response": f"⚠️ {conflict_err.message}",
                }

            date_display = followup.scheduled_date.strftime("%B %d, %Y at %I:%M %p") if followup.scheduled_date else "soon"

            return {
                "tool_result": {
                    "success": True,
                    "followup_id": str(followup.id),
                    "hcp_name": hcp.name,
                },
                "response": f"✅ Follow-up with {hcp.name} scheduled for {date_display}! 📅",
            }

        except Exception as e:
            logger.error(f"Schedule followup error: {str(e)}")
            return {
                "tool_result": {"success": False, "error": str(e)},
                "response": f"Error scheduling follow-up: {str(e)}",
            }

    # ============================================
    # TOOL 6: ANALYZE TRENDS
    # ============================================
    async def analyze_trends_node(self, state: AgentState) -> Dict[str, Any]:
        """Tool 6: Analyze interaction trends."""
        try:
            user_id = state.get("user_id")
            if not user_id:
                return {
                    "tool_result": {"success": False, "error": "User not authenticated"},
                    "response": "Please login to view analytics.",
                }
            
            stats = await self.analytics_service.get_dashboard_stats(user_id)
            
            response = "📊 **Analytics Summary:**\n\n"
            response += f"📌 Total Interactions: {stats.get('total_interactions', 0)}\n"
            response += f"👨‍⚕️ Active HCPs: {stats.get('total_hcps', 0)}\n"
            response += f"⏰ Follow-ups Due: {stats.get('followups_due', 0)}\n\n"
            response += "Visit the Analytics page for detailed charts."
            
            return {
                "tool_result": {"success": True, "stats": stats},
                "response": response,
            }
            
        except Exception as e:
            logger.error(f"Analyze trends error: {str(e)}")
            return {
                "tool_result": {"success": False, "error": str(e)},
                "response": f"Error analyzing trends: {str(e)}",
            }

    # ============================================
    # TOOL 7: GENERIC RESPONSE
    # ============================================
    async def generic_response_node(self, state: AgentState) -> Dict[str, Any]:
        """Tool 7: Handle generic queries using Groq LLM."""
        try:
            messages = state.get("messages", [])
            last_message = self._get_last_message_text(messages)
            
            system_prompt = """You are a helpful AI assistant for a Healthcare Professional CRM system.
            Respond in a friendly, professional manner. Keep responses concise.
            Offer to help with logging interactions, scheduling follow-ups, searching HCPs, or viewing analytics."""
            
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=last_message)
            ], config={"callbacks": [self.langfuse_handler]})
            
            return {
                "tool_result": {"success": True},
                "response": response.content,
            }
            
        except Exception as e:
            logger.error(f"Generic response error: {str(e)}")
            return {
                "tool_result": {"success": False, "error": str(e)},
                "response": "I'm here to help! How can I assist you with HCP interactions today?",
            }

    # ============================================
    # FORMAT RESPONSE
    # ============================================
    async def format_response_node(self, state: AgentState) -> Dict[str, Any]:
        """Format the final response."""
        response = state.get("response", "I've processed your request.")
        tool_result = state.get("tool_result", {})
        
        if tool_result.get("success") == False:
            response = f"⚠️ {response}"
        
        return {
            "response": response,
            "should_end": False
        }

    # ============================================
    # RUN AGENT
    # ============================================
    async def run(self, state: AgentState) -> Dict[str, Any]:
        """Run the LangGraph agent."""
        try:
            result = await self.graph.ainvoke(state)
            return {
                "response": result.get("response", "I've processed your request."),
                "intent": result.get("intent", "generic_response"),
                "tool_result": result.get("tool_result", {}),
                "should_end": result.get("should_end", False),
                "error": result.get("error"),
            }
        except Exception as e:
            logger.error(f"Agent run error: {str(e)}", exc_info=True)
            return {
                "response": "I encountered an error. Please try again.",
                "intent": "generic_response",
                "tool_result": {"success": False, "error": str(e)},
                "should_end": True,
                "error": str(e),
            }