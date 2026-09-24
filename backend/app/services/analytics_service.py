"""Analytics service."""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone

from app.repositories.interaction_repository import InteractionRepository
from app.repositories.hcp_repository import HCPRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics and reporting."""

    def __init__(
        self,
        interaction_repo: InteractionRepository,
        hcp_repo: HCPRepository,
    ):
        self.interaction_repo = interaction_repo
        self.hcp_repo = hcp_repo

    async def get_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard statistics."""
        interactions = await self.interaction_repo.get_by_user_id(user_id, limit=1000)
        
        return {
            "total_interactions": len(interactions),
            "total_hcps": len(set(i.hcp_id for i in interactions)),
            "followups_due": len([i for i in interactions if i.follow_up_required]),
            "recent_interactions": interactions[:10],
        }

    async def get_interaction_trends(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get interaction trends."""
        interactions = await self.interaction_repo.get_by_user_id(user_id, limit=1000)

        # Group by date
        trends = {}
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        for interaction in interactions:
            interaction_date = interaction.interaction_date
            if interaction_date is None:
                continue
            # interaction_date comes back timezone-aware from Postgres
            # (DateTime(timezone=True) column), but older rows or a
            # different DB driver could hand back a naive datetime.
            # Normalize both sides to aware UTC before comparing, so this
            # never raises "can't compare offset-naive and offset-aware
            # datetimes".
            if interaction_date.tzinfo is None:
                interaction_date = interaction_date.replace(tzinfo=timezone.utc)
            if interaction_date >= cutoff:
                date_key = interaction_date.strftime("%Y-%m-%d")
                trends[date_key] = trends.get(date_key, 0) + 1

        return {
            "trends": trends,
            "total": sum(trends.values()),
        }

    async def get_hcp_analytics(self, user_id: str, top_n: int = 10) -> Dict[str, Any]:
        """Get the HCPs this user has engaged with the most, ranked by
        number of logged interactions.

        Real logic (this used to be a hardcoded stub that always returned
        an empty list): we pull this user's interactions, count how many
        times each hcp_id shows up, rank by count, then look each of the
        top N HCPs up in the HCP repo to attach their current name/
        specialty (rather than trusting the possibly-stale hcp_name
        snapshot stored on the interaction row itself).
        """
        interactions = await self.interaction_repo.get_by_user_id(user_id, limit=1000)

        counts: Dict[str, int] = {}
        last_interaction_at: Dict[str, datetime] = {}

        for interaction in interactions:
            if interaction.hcp_id is None:
                continue
            hcp_id = str(interaction.hcp_id)
            counts[hcp_id] = counts.get(hcp_id, 0) + 1

            interaction_date = interaction.interaction_date
            if interaction_date is not None:
                existing = last_interaction_at.get(hcp_id)
                if existing is None or interaction_date > existing:
                    last_interaction_at[hcp_id] = interaction_date

        # Rank by interaction count, most-engaged first. Ties broken by
        # most recent interaction so a newer relationship doesn't get
        # buried behind an old, stale one with the same count.
        ranked_hcp_ids = sorted(
            counts.keys(),
            key=lambda hid: (counts[hid], last_interaction_at.get(hid) or datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True,
        )[:top_n]

        top_hcps: List[Dict[str, Any]] = []
        for hcp_id in ranked_hcp_ids:
            hcp = await self.hcp_repo.get_by_id(hcp_id)
            if hcp is None:
                # HCP was hard-deleted or soft-deleted since these
                # interactions were logged - skip rather than error.
                continue

            last_seen = last_interaction_at.get(hcp_id)
            top_hcps.append({
                "hcp_id": hcp_id,
                "hcp_name": hcp.name,
                "specialty": hcp.specialty,
                "interaction_count": counts[hcp_id],
                "last_interaction_date": last_seen.isoformat() if last_seen else None,
            })

        return {
            "top_hcps": top_hcps,
            "total_hcps": len(counts),
        }