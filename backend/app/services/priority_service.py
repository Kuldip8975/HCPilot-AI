"""
Priority (Next Best Action) service.

Real-world context: this mirrors what pharma sales-force tools like Veeva
CRM / Aktana call "Next Best Action" (NBA) - for each rep, rank which HCPs
need attention this week and explain why, instead of the rep working
through a flat, unordered list.

Honest scope note: this is NOT a trained ML model - there isn't enough
historical labeled data in a project like this to train one without
overfitting or faking it. It's a transparent, rule-based scoring formula
(recency since last contact + engagement score + follow-up status)
combined with an LLM that writes a short, human-readable rationale for
the top picks - the same "explainable AI, decision-support only" pattern
real NBA tools use, just without a trained prediction model underneath.
The score alone is always valid; the LLM only adds an explanation on top
of it, and if that call fails, a rule-based sentence is used instead so
the endpoint never breaks because of the LLM.

Engagement score note: the HCP.engagement_score DB column is never
written anywhere in this codebase (it just sits at its default of 0
forever), so it cannot be used as a real signal. Instead, engagement is
computed here, on the fly, from the rep's own logged interaction history
with that HCP - specifically, how many of those interactions actually
happened (status=COMPLETED).

Follow-up completion note: has_pending_followup now also carries the
actual follow_up_id (when one exists) so the frontend can offer a "Mark
Complete" action that calls the existing (previously unused)
PUT /followups/{id}/complete endpoint directly from this list - this is
the one place in the app that surfaces "this HCP has something pending"
per-HCP, so it's the natural place to let the rep resolve it.

Location note: latitude/longitude are carried through from the HCP row
(set by geocoding at HCP save time) so the Smart Day Planner
(route_planner_service.py) can route to these HCPs without a second
lookup. They're None for any HCP that hasn't been geocoded yet.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.models.interaction import InteractionStatus
from app.repositories.hcp_repository import HCPRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.followup_repository import FollowUpRepository

logger = logging.getLogger(__name__)

# How many HCPs to return in the ranked list.
TOP_N = 8

# Recency scoring: days since last contact, capped here - being this many
# days cold is already "as urgent as it gets" for this formula, so we
# don't keep rewarding forever-uncontacted HCPs disproportionately.
MAX_RECENCY_DAYS = 45

# Engagement scoring: how many COMPLETED interactions with an HCP count as
# "fully engaged" (100).
COMPLETED_INTERACTIONS_FOR_MAX_ENGAGEMENT = 8

# Scoring weights (tunable) - recency and engagement matter roughly
# equally, with a small bonus for anyone overdue with nothing already
# scheduled.
WEIGHT_RECENCY = 0.55
WEIGHT_ENGAGEMENT = 0.35
WEIGHT_OVERDUE_BONUS = 0.10

SYSTEM_PROMPT = """You are a sales-enablement assistant for pharma sales reps who visit doctors (HCPs). \
You are given a JSON list of HCPs the rep should prioritize this week, each with computed signals: \
days since last contact, engagement score out of 100, number of past interactions, whether a \
follow-up is already pending, and the topics/summary from their most recent interaction.

For EACH HCP in the list, write ONE short, concrete, specific reason (max 25 words) explaining why \
the rep should prioritize them this week. Reference the actual signals given (e.g. days since \
contact, engagement level, what was last discussed) - do not write generic filler like "should be \
contacted soon".

Respond with ONLY a JSON array, no other text, in this exact shape:
[{"hcp_id": "<id>", "reason": "<short reason>"}, ...]
"""


class PriorityService:
    """Computes and explains the rep's weekly HCP priority list."""

    def __init__(
        self,
        hcp_repo: HCPRepository,
        interaction_repo: InteractionRepository,
        followup_repo: FollowUpRepository,
    ):
        self.hcp_repo = hcp_repo
        self.interaction_repo = interaction_repo
        self.followup_repo = followup_repo
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0.4,
            max_tokens=800,
        )

    async def get_weekly_priorities(self, user_id: str) -> Dict[str, Any]:
        """
        Returns: {"priorities": [ {...ranked HCP with score + reason...} ], "generated_at": iso str}
        """
        interactions = await self.interaction_repo.get_by_user_id(user_id, limit=500)

        if not interactions:
            return {"priorities": [], "generated_at": self._now_iso()}

        # Group this rep's interactions by hcp_id -> aggregate signals.
        by_hcp: Dict[str, Dict[str, Any]] = {}
        for interaction in interactions:
            hcp_id = str(interaction.hcp_id)
            entry = by_hcp.setdefault(
                hcp_id,
                {
                    "count": 0,
                    "completed_count": 0,
                    "last_date": None,
                    "last_topics": None,
                    "last_summary": None,
                },
            )
            entry["count"] += 1
            if interaction.status == InteractionStatus.COMPLETED:
                entry["completed_count"] += 1
            i_date = interaction.interaction_date
            if entry["last_date"] is None or (i_date and i_date > entry["last_date"]):
                entry["last_date"] = i_date
                entry["last_topics"] = interaction.topics
                entry["last_summary"] = interaction.summary

        # Pending follow-ups for this rep, so we know which HCPs are
        # already being handled and don't need to be pushed to the top
        # again - and so we can hand the frontend the actual follow-up id
        # to let the rep mark it complete.
        pending_followups = await self.followup_repo.get_by_user_id(
            user_id, status="pending", limit=200
        )
        hcp_id_to_followup_id: Dict[str, str] = {}
        for followup in pending_followups:
            interaction = getattr(followup, "interaction", None)
            if interaction is not None and interaction.hcp_id:
                hcp_key = str(interaction.hcp_id)
                # If an HCP somehow has more than one pending follow-up,
                # keep the earliest-created one (list is already ordered
                # by the repository) - that's the one that's been waiting
                # longest and should be the one the rep resolves first.
                hcp_id_to_followup_id.setdefault(hcp_key, str(followup.id))

        now = datetime.now(timezone.utc)
        scored: List[Dict[str, Any]] = []

        for hcp_id, signals in by_hcp.items():
            hcp = await self.hcp_repo.get_by_id(hcp_id)
            if hcp is None:
                continue

            days_since_contact = self._days_since(signals["last_date"], now)
            followup_id = hcp_id_to_followup_id.get(hcp_id)
            has_pending_followup = followup_id is not None
            engagement_score = self._compute_engagement_score(signals["completed_count"])

            score, breakdown = self._compute_score(
                days_since_contact=days_since_contact,
                engagement_score=engagement_score,
                interaction_count=signals["count"],
                has_pending_followup=has_pending_followup,
            )

            scored.append({
                "hcp_id": hcp_id,
                "hcp_name": hcp.name,
                "specialty": hcp.specialty,
                "score": round(score, 1),
                "days_since_contact": days_since_contact,
                "engagement_score": engagement_score,
                "interaction_count": signals["count"],
                "has_pending_followup": has_pending_followup,
                "followup_id": followup_id,
                "last_topics": signals["last_topics"],
                "last_summary": signals["last_summary"],
                "reason": None,
                "score_breakdown": breakdown,
                "latitude": hcp.latitude,
                "longitude": hcp.longitude,
            })

        # Highest priority first.
        scored.sort(key=lambda item: item["score"], reverse=True)
        top = scored[:TOP_N]

        if top:
            top = await self._attach_rationales(top)

        return {"priorities": top, "generated_at": self._now_iso()}

    @staticmethod
    def _compute_engagement_score(completed_count: int) -> int:
        """Transparent, rule-based engagement score (0-100), derived from
        how many of the rep's logged interactions with this HCP actually
        happened (status=COMPLETED). More real, completed contact = a
        more engaged relationship. Capped once a solid working
        relationship is already established."""
        if completed_count <= 0:
            return 0
        score = (completed_count / COMPLETED_INTERACTIONS_FOR_MAX_ENGAGEMENT) * 100
        return int(min(round(score), 100))

    def _compute_score(
        self,
        days_since_contact: int,
        engagement_score: int,
        interaction_count: int,
        has_pending_followup: bool,
    ) -> Tuple[float, Dict[str, float]]:
        """Transparent, rule-based scoring (0-100). Higher = contact sooner."""
        recency_component = min(days_since_contact / MAX_RECENCY_DAYS, 1.0) * 100
        engagement_component = min(max(engagement_score, 0), 100)
        overdue_bonus = (
            100
            if interaction_count > 0 and not has_pending_followup and days_since_contact >= 14
            else 0
        )

        raw_score = (
            recency_component * WEIGHT_RECENCY
            + engagement_component * WEIGHT_ENGAGEMENT
            + overdue_bonus * WEIGHT_OVERDUE_BONUS
        )

        # An HCP with something already pending doesn't need to be pushed
        # back to the top of the list - the rep already has it handled.
        if has_pending_followup:
            raw_score *= 0.4

        breakdown = {
            "recency_component": round(recency_component, 1),
            "engagement_component": round(engagement_component, 1),
            "bonus_component": round(overdue_bonus, 1),
        }
        return raw_score, breakdown

    async def _attach_rationales(self, top: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ask the LLM for a short, specific reason per HCP in one batched
        call. Falls back to a rule-based sentence per item if the LLM call
        fails or returns something unparseable - this must never break the
        endpoint, it's an explanation layer on top of a score that is
        already valid on its own."""
        payload = [
            {
                "hcp_id": item["hcp_id"],
                "hcp_name": item["hcp_name"],
                "days_since_contact": item["days_since_contact"],
                "engagement_score": item["engagement_score"],
                "interaction_count": item["interaction_count"],
                "has_pending_followup": item["has_pending_followup"],
                "last_topics": item["last_topics"] or "(not recorded)",
                "last_summary": (item["last_summary"] or "")[:200],
            }
            for item in top
        ]

        try:
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=json.dumps(payload)),
            ]
            response = await self.llm.ainvoke(messages)
            raw = response.content.strip()

            # Models sometimes wrap JSON in ```json fences despite instructions.
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.lower().startswith("json"):
                    raw = raw[4:].strip()

            reasons = json.loads(raw)
            reason_by_id = {
                r["hcp_id"]: r["reason"] for r in reasons if "hcp_id" in r and "reason" in r
            }

            for item in top:
                item["reason"] = reason_by_id.get(item["hcp_id"]) or self._fallback_reason(item)
            return top

        except Exception as e:
            logger.warning(f"Priority rationale generation failed, using fallback reasons: {e}")
            for item in top:
                item["reason"] = self._fallback_reason(item)
            return top

    @staticmethod
    def _fallback_reason(item: Dict[str, Any]) -> str:
        """Rule-based sentence used if the LLM call fails or is skipped."""
        if item["has_pending_followup"]:
            return (
                f"Follow-up already pending, but {item['days_since_contact']} "
                f"days since last contact."
            )
        if item["days_since_contact"] >= 14:
            return (
                f"No contact in {item['days_since_contact']} days despite an "
                f"engagement score of {item['engagement_score']}."
            )
        return (
            f"Last contacted {item['days_since_contact']} days ago; "
            f"engagement score {item['engagement_score']}/100."
        )

    @staticmethod
    def _days_since(past: Optional[datetime], now: datetime) -> int:
        if past is None:
            return 999  # never contacted - treat as maximally overdue
        if past.tzinfo is None:
            past = past.replace(tzinfo=timezone.utc)
        delta = now - past
        return max(delta.days, 0)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()