"""
MCP (Model Context Protocol) server for the HCP CRM.

This exposes the same 6 actions the in-app AI chat can perform
(log_interaction, edit_interaction, search_hcp, view_history,
schedule_followup, analyze_trends) as MCP *tools*, so ANY MCP-compatible
client (Claude Desktop, another agent, a different LLM app) can call
them directly - without going through our own LangGraph agent or our
own frontend at all.

Why this file is separate from the LangGraph agent
----------------------------------------------------
The LangGraph agent (app/ai/langgraph_agent.py) is OUR chat's "brain":
it reads a free-text user message, calls Groq to decide which of the
6 actions is meant and to pull out the fields, then calls these same
services.

MCP tools don't need that "figure out what the user meant" step -
the calling MCP client (e.g. Claude Desktop) already does its own
reasoning and calls the tool with clean, named arguments. So this file
is a thin, deterministic wrapper directly over the service layer -
no Groq/LangGraph call happens in here at all. It is a second,
independent "front door" into the exact same business logic the REST
API and the AI chat already use.

Auth model
----------
MCP has no cookies/session like a browser. Every tool call here takes
a `token` argument - the same JWT access token a user gets back from
POST /api/v1/auth/login. The MCP client is expected to log in once via
the REST API and then pass that token on every tool call. We decode it
with the exact same SecurityConfig.decode_token() the REST API uses,
so a token is valid/invalid under identical rules in both places.

Each tool opens its own short-lived AsyncSession (AsyncSessionLocal),
because MCP tool calls are not FastAPI requests - there is no
`Depends(get_db)` to lean on here.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.core.exceptions import AppException, AuthenticationError
from app.core.security import SecurityConfig
from app.models.database import AsyncSessionLocal
from app.repositories.followup_repository import FollowUpRepository
from app.repositories.hcp_repository import HCPRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.user_repository import UserRepository
from app.services.analytics_service import AnalyticsService
from app.services.hcp_service import HCPService
from app.services.interaction_service import InteractionService

logger = logging.getLogger(__name__)

# The MCP SDK has DNS-rebinding protection turned on by default, which
# checks the incoming request's Host/Origin headers against an allow-list.
# With an empty allow-list (the default) EVERY request gets rejected -
# including our own local dev calls to http://localhost:8000/mcp - which
# is what caused the "Session terminated" error the first time this was
# tested. For local development we allow the usual localhost/127.0.0.1
# hosts and the frontend's dev-server origins. If you deploy this for
# real, replace these with your actual domain(s).
_transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[
        "localhost",
        "localhost:8000",
        "127.0.0.1",
        "127.0.0.1:8000",
    ],
    allowed_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
)

mcp = FastMCP(
    name="hcp-crm",
    instructions=(
        "Tools for a pharma sales rep's HCP (Healthcare Professional) CRM. "
        "Every tool needs a `token` argument: the JWT access token returned by "
        "POST /api/v1/auth/login on this CRM's REST API. Log in there first, "
        "then pass that token into every tool call below."
    ),
    transport_security=_transport_security,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

async def _authenticate(token: str, db) -> str:
    """Decode the JWT and return the authenticated user's id, or raise."""
    try:
        payload = SecurityConfig.decode_token(token)
    except AuthenticationError as e:
        raise ValueError(f"Authentication failed: {e}")

    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Authentication failed: token has no subject")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise ValueError("Authentication failed: user not found")
    if not user.is_active:
        raise ValueError("Authentication failed: user is inactive")

    return str(user.id)


def _serialize_interaction(interaction) -> Dict[str, Any]:
    return {
        "id": str(interaction.id),
        "hcp_name": interaction.hcp_name,
        "hcp_specialty": interaction.hcp_specialty,
        "interaction_date": interaction.interaction_date.isoformat() if interaction.interaction_date else None,
        "interaction_type": interaction.interaction_type.value if hasattr(interaction.interaction_type, "value") else interaction.interaction_type,
        "status": interaction.status.value if hasattr(interaction.status, "value") else interaction.status,
        "topics": interaction.topics,
        "summary": interaction.summary,
        "notes": interaction.notes,
        "follow_up_required": interaction.follow_up_required,
        "follow_up_date": interaction.follow_up_date.isoformat() if interaction.follow_up_date else None,
    }


def _serialize_hcp(hcp) -> Dict[str, Any]:
    return {
        "id": str(hcp.id),
        "name": hcp.name,
        "title": hcp.title,
        "specialty": hcp.specialty,
        "organization": hcp.organization,
        "location": hcp.address,
        "status": hcp.status.value if hasattr(hcp.status, "value") else hcp.status,
        "engagement_score": hcp.engagement_score,
    }


def _error(message: str) -> Dict[str, Any]:
    return {"success": False, "error": message}


# ---------------------------------------------------------------------------
# Tool 1: log_interaction
# ---------------------------------------------------------------------------

@mcp.tool()
async def log_interaction(
    token: str,
    hcp_name: str,
    interaction_type: str = "meeting",
    summary: str = "",
    topics: Optional[str] = None,
    notes: Optional[str] = None,
    follow_up_required: bool = False,
    follow_up_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Log a new interaction with a Healthcare Professional (HCP).

    Args:
        token: JWT access token from POST /api/v1/auth/login.
        hcp_name: Name of the HCP the interaction was with (e.g. "Dr. Sarah Chen").
            Matched against existing HCPs by a case-insensitive substring search;
            the first match found is used.
        interaction_type: One of "meeting", "call", "email", "other".
        summary: Short summary of what happened in the interaction.
        topics: Comma-separated topics discussed (e.g. "Product X, dosing").
        notes: Any additional freeform notes.
        follow_up_required: Whether a follow-up visit/call is needed.
        follow_up_date: ISO date (YYYY-MM-DD) for the follow-up, if required.

    Returns:
        The created interaction, or an error if the HCP could not be found.
    """
    async with AsyncSessionLocal() as db:
        try:
            user_id = await _authenticate(token, db)

            hcp_repo = HCPRepository(db)
            matches = await hcp_repo.search(query=hcp_name, limit=1)
            if not matches:
                return _error(f"No HCP found matching '{hcp_name}'. Try search_hcp first.")
            hcp = matches[0]

            followup_repo = FollowUpRepository(db)
            interaction_repo = InteractionRepository(db)
            interaction_service = InteractionService(interaction_repo, hcp_repo, followup_repo)

            data = {
                "hcp_id": str(hcp.id),
                "interaction_type": interaction_type,
                "summary": summary,
                "topics": topics,
                "notes": notes,
                "follow_up_required": follow_up_required,
                "follow_up_date": follow_up_date,
            }
            interaction = await interaction_service.create_interaction(user_id, data)
            await db.commit()

            return {"success": True, "interaction": _serialize_interaction(interaction)}
        except ValueError as e:
            await db.rollback()
            return _error(str(e))
        except AppException as e:
            await db.rollback()
            return _error(str(e))
        except Exception as e:
            await db.rollback()
            logger.error(f"MCP log_interaction failed: {e}", exc_info=True)
            return _error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# Tool 2: edit_interaction
# ---------------------------------------------------------------------------

@mcp.tool()
async def edit_interaction(
    token: str,
    hcp_name: str,
    summary: Optional[str] = None,
    topics: Optional[str] = None,
    notes: Optional[str] = None,
    interaction_type: Optional[str] = None,
    follow_up_required: Optional[bool] = None,
    follow_up_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Edit the most recent interaction logged with a given HCP.

    Only the fields you pass a value for are changed; everything else on
    the interaction stays the same.

    Args:
        token: JWT access token from POST /api/v1/auth/login.
        hcp_name: Name of the HCP whose most recent interaction should be edited.
        summary: New summary text, if changing it.
        topics: New comma-separated topics, if changing them.
        notes: New notes, if changing them.
        interaction_type: New type ("meeting", "call", "email", "other"), if changing it.
        follow_up_required: New follow-up flag, if changing it.
        follow_up_date: New ISO follow-up date, if changing it.

    Returns:
        The updated interaction, or an error if no matching HCP/interaction exists.
    """
    async with AsyncSessionLocal() as db:
        try:
            user_id = await _authenticate(token, db)

            hcp_repo = HCPRepository(db)
            matches = await hcp_repo.search(query=hcp_name, limit=1)
            if not matches:
                return _error(f"No HCP found matching '{hcp_name}'.")
            hcp = matches[0]

            interaction_repo = InteractionRepository(db)
            recent = await interaction_repo.get_by_hcp_id(hcp_id=str(hcp.id), limit=1)
            if not recent:
                return _error(f"No interactions found for '{hcp.name}' to edit.")
            interaction = recent[0]

            followup_repo = FollowUpRepository(db)
            interaction_service = InteractionService(interaction_repo, hcp_repo, followup_repo)

            changes: Dict[str, Any] = {}
            if summary is not None:
                changes["summary"] = summary
            if topics is not None:
                changes["topics"] = topics
            if notes is not None:
                changes["notes"] = notes
            if interaction_type is not None:
                changes["interaction_type"] = interaction_type
            if follow_up_required is not None:
                changes["follow_up_required"] = follow_up_required
            if follow_up_date is not None:
                changes["follow_up_date"] = follow_up_date

            if not changes:
                return _error("No fields to update were provided.")

            updated = await interaction_service.update_interaction(
                str(interaction.id), user_id, changes
            )
            await db.commit()

            return {"success": True, "interaction": _serialize_interaction(updated)}
        except ValueError as e:
            await db.rollback()
            return _error(str(e))
        except AppException as e:
            await db.rollback()
            return _error(str(e))
        except Exception as e:
            await db.rollback()
            logger.error(f"MCP edit_interaction failed: {e}", exc_info=True)
            return _error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# Tool 3: search_hcp
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_hcp(token: str, query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search Healthcare Professionals by name, specialty, or location.

    Args:
        token: JWT access token from POST /api/v1/auth/login.
        query: Free-text search term (e.g. "Chen", "Oncology", "Boston").
        limit: Max number of results to return (default 5).

    Returns:
        A list of matching HCPs.
    """
    async with AsyncSessionLocal() as db:
        try:
            await _authenticate(token, db)

            hcp_repo = HCPRepository(db)
            matches = await hcp_repo.search(query=query, limit=limit)

            return {
                "success": True,
                "count": len(matches),
                "hcps": [_serialize_hcp(h) for h in matches],
            }
        except ValueError as e:
            return _error(str(e))
        except Exception as e:
            logger.error(f"MCP search_hcp failed: {e}", exc_info=True)
            return _error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# Tool 4: view_history
# ---------------------------------------------------------------------------

@mcp.tool()
async def view_history(token: str, hcp_name: str, limit: int = 10) -> Dict[str, Any]:
    """
    View the interaction history for a specific HCP.

    Args:
        token: JWT access token from POST /api/v1/auth/login.
        hcp_name: Name of the HCP (matched by case-insensitive substring search).
        limit: Max number of past interactions to return (default 10).

    Returns:
        The HCP's details plus their recent interactions, most recent first.
    """
    async with AsyncSessionLocal() as db:
        try:
            await _authenticate(token, db)

            hcp_repo = HCPRepository(db)
            matches = await hcp_repo.search(query=hcp_name, limit=1)
            if not matches:
                return _error(f"No HCP found matching '{hcp_name}'.")
            hcp = matches[0]

            interaction_repo = InteractionRepository(db)
            history = await interaction_repo.get_by_hcp_id(hcp_id=str(hcp.id), limit=limit)

            return {
                "success": True,
                "hcp": _serialize_hcp(hcp),
                "interaction_count": len(history),
                "interactions": [_serialize_interaction(i) for i in history],
            }
        except ValueError as e:
            return _error(str(e))
        except Exception as e:
            logger.error(f"MCP view_history failed: {e}", exc_info=True)
            return _error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# Tool 5: schedule_followup
# ---------------------------------------------------------------------------

@mcp.tool()
async def schedule_followup(
    token: str,
    hcp_name: str,
    scheduled_date: str,
    priority: str = "medium",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Schedule a follow-up against the most recent interaction with an HCP.

    Args:
        token: JWT access token from POST /api/v1/auth/login.
        hcp_name: Name of the HCP to schedule a follow-up for.
        scheduled_date: ISO date/datetime (e.g. "2026-10-01") for the follow-up.
        priority: One of "low", "medium", "high" (default "medium").
        notes: Optional notes about what the follow-up should cover.

    Returns:
        The created follow-up, or an error if no interaction exists yet for that HCP.
    """
    async with AsyncSessionLocal() as db:
        try:
            user_id = await _authenticate(token, db)

            hcp_repo = HCPRepository(db)
            matches = await hcp_repo.search(query=hcp_name, limit=1)
            if not matches:
                return _error(f"No HCP found matching '{hcp_name}'.")
            hcp = matches[0]

            interaction_repo = InteractionRepository(db)
            recent = await interaction_repo.get_by_hcp_id(hcp_id=str(hcp.id), limit=1)
            if not recent:
                return _error(
                    f"'{hcp.name}' has no logged interactions yet. "
                    "Log an interaction before scheduling a follow-up."
                )
            interaction = recent[0]

            followup_repo = FollowUpRepository(db)
            interaction_service = InteractionService(interaction_repo, hcp_repo, followup_repo)

            followup = await interaction_service.schedule_followup(
                str(interaction.id),
                user_id,
                {
                    "scheduled_date": scheduled_date,
                    "priority": priority,
                    "notes": notes or "",
                },
            )
            await db.commit()

            return {
                "success": True,
                "followup": {
                    "id": str(followup.id),
                    "hcp_name": hcp.name,
                    "scheduled_date": followup.scheduled_date.isoformat() if followup.scheduled_date else None,
                    "priority": followup.priority,
                    "notes": followup.notes,
                    "status": followup.status.value if hasattr(followup.status, "value") else followup.status,
                },
            }
        except ValueError as e:
            await db.rollback()
            return _error(str(e))
        except AppException as e:
            await db.rollback()
            return _error(str(e))
        except Exception as e:
            await db.rollback()
            logger.error(f"MCP schedule_followup failed: {e}", exc_info=True)
            return _error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# Tool 6: analyze_trends
# ---------------------------------------------------------------------------

@mcp.tool()
async def analyze_trends(token: str, days: int = 30) -> Dict[str, Any]:
    """
    Analyze interaction trends and dashboard-style stats for the logged-in rep.

    Args:
        token: JWT access token from POST /api/v1/auth/login.
        days: How many trailing days to analyze (default 30).

    Returns:
        Totals (interactions, distinct HCPs, follow-ups due) plus a
        day-by-day interaction count for the requested window.
    """
    async with AsyncSessionLocal() as db:
        try:
            user_id = await _authenticate(token, db)

            interaction_repo = InteractionRepository(db)
            hcp_repo = HCPRepository(db)
            analytics_service = AnalyticsService(interaction_repo, hcp_repo)

            stats = await analytics_service.get_dashboard_stats(user_id)
            trends = await analytics_service.get_interaction_trends(user_id, days=days)

            return {
                "success": True,
                "total_interactions": stats["total_interactions"],
                "total_hcps_engaged": stats["total_hcps"],
                "followups_due": stats["followups_due"],
                "window_days": days,
                "daily_trend": trends["trends"],
                "total_in_window": trends["total"],
            }
        except ValueError as e:
            return _error(str(e))
        except Exception as e:
            logger.error(f"MCP analyze_trends failed: {e}", exc_info=True)
            return _error(f"Unexpected error: {e}")