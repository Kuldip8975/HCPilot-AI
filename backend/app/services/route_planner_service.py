"""Route planning service.

Implements a simplified Orienteering Problem solver: given a rep's start
location, a set of candidate HCPs (each with a priority "value" score and
a lat/long), and a time budget, picks WHICH HCPs to visit and in WHAT
ORDER, to maximize total priority value visited within the budget.

Unlike plain TSP (visit everyone, minimize total distance), a rep usually
can't visit every HCP on their list in one day - this also decides who to
SKIP, preferring high-priority HCPs that are reasonably close over
low-priority ones that are far away.

Algorithm (greedy insertion + 2-opt), not an exact solver:
  1. Get real travel times between every pair of locations (rep + all
     candidate HCPs) from OSRM's routing engine.
  2. Greedily insert HCPs one at a time - at each step, pick whichever
     remaining HCP gives the best "value added per minute of extra travel
     time" (marginal value/cost ratio) when inserted at its best position
     in the current route, as long as it still fits the time budget.
  3. Run 2-opt on the final selected route to untangle any crossing paths
     the greedy insertion left behind (pure sequencing improvement, doesn't
     change WHO is visited, just the order).

This is a heuristic, not a guaranteed-optimal solver (the real Orienteering
Problem is NP-hard) - for a rep's daily list (usually well under 30 HCPs),
it runs in milliseconds and gets close to optimal in practice.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

OSRM_TABLE_URL = "http://router.project-osrm.org/table/v1/driving"

# Minutes assumed spent actually meeting each HCP (on top of travel time).
DEFAULT_VISIT_DURATION_MINUTES = 20

# Fallback average speed (km/h) used for the Haversine-based time estimate
# when OSRM is unreachable. Deliberately conservative (city traffic, not
# highway) since reps travel between clinics/hospitals in urban areas.
FALLBACK_AVG_SPEED_KMH = 25


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/long points, in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class RoutePlannerService:
    """Builds a time-budgeted, priority-optimized visit route for a rep."""

    async def _get_travel_time_matrix(
        self, points: List[Tuple[float, float]]
    ) -> List[List[float]]:
        """Return an NxN matrix of travel times in minutes between every
        pair of points, via OSRM. Falls back to Haversine-distance-based
        estimates for the whole matrix if OSRM is unreachable, so route
        planning never hard-fails just because a free third-party service
        is briefly down.

        points: list of (latitude, longitude) tuples.
        """
        n = len(points)
        if n <= 1:
            return [[0.0] * n for _ in range(n)]

        # OSRM expects "lon,lat;lon,lat;..." (longitude first).
        coords = ";".join(f"{lon},{lat}" for lat, lon in points)
        url = f"{OSRM_TABLE_URL}/{coords}"
        params = {"annotations": "duration"}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            if data.get("code") != "Ok":
                raise ValueError(f"OSRM returned non-Ok code: {data.get('code')}")

            durations_seconds = data["durations"]
            return [
                [(d / 60.0) if d is not None else float("inf") for d in row]
                for row in durations_seconds
            ]
        except Exception as exc:
            logger.warning(f"OSRM travel-time lookup failed, falling back to Haversine estimate: {exc}")
            matrix = [[0.0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    if i == j:
                        continue
                    dist_km = _haversine_km(*points[i], *points[j])
                    matrix[i][j] = (dist_km / FALLBACK_AVG_SPEED_KMH) * 60.0
            return matrix

    async def plan_day(
        self,
        rep_location: Tuple[float, float],
        candidates: List[Dict],
        time_budget_minutes: int,
        visit_duration_minutes: int = DEFAULT_VISIT_DURATION_MINUTES,
    ) -> Dict:
        """Select and sequence HCP visits within a time budget.

        candidates: list of dicts, each with at least:
            "hcp_id", "name", "latitude", "longitude", "priority_score"
          (HCPs missing latitude/longitude are skipped - can't route to an
          address that hasn't been geocoded yet.)

        Returns a dict with the ordered "plan" (selected HCPs with arrival
        estimates), the "skipped" HCPs (either no coordinates, or the
        budget ran out), and summary totals.
        """
        geocoded = [c for c in candidates if c.get("latitude") is not None and c.get("longitude") is not None]
        skipped_no_location = [c for c in candidates if c not in geocoded]

        if not geocoded:
            return {
                "plan": [],
                "skipped": [
                    {**c, "skip_reason": "no_coordinates"} for c in skipped_no_location
                ],
                "total_value": 0,
                "total_time_minutes": 0,
            }

        # Index 0 = rep's own location; indices 1..n = candidate HCPs.
        points = [rep_location] + [(c["latitude"], c["longitude"]) for c in geocoded]
        matrix = await self._get_travel_time_matrix(points)

        # route: list of indices into `geocoded` (NOT into `points`),
        # in visiting order. Starts empty; rep's current position tracked
        # separately via `route_point_indices` (indices into `points`,
        # always starting with 0 = rep).
        route: List[int] = []
        route_point_indices: List[int] = [0]
        remaining = set(range(len(geocoded)))
        time_used = 0.0

        def travel_time(point_idx_a: int, point_idx_b: int) -> float:
            return matrix[point_idx_a][point_idx_b]

        # Greedy insertion: repeatedly add whichever remaining HCP gives
        # the best value/marginal-time ratio, inserted at its cheapest
        # position in the current route, as long as it still fits the
        # budget.
        while remaining:
            best_choice = None  # (candidate_idx, insert_pos, marginal_time, ratio)

            for cand_idx in remaining:
                cand_point_idx = cand_idx + 1  # +1 because index 0 is the rep
                value = geocoded[cand_idx].get("priority_score", 0) or 0

                # Try every insertion position in the current route
                # (including at the very end) and keep the cheapest.
                for pos in range(len(route_point_indices)):
                    prev_point = route_point_indices[pos]
                    next_point = route_point_indices[pos + 1] if pos + 1 < len(route_point_indices) else None

                    if next_point is None:
                        # Inserting at the end: just travel there + visit.
                        marginal_time = travel_time(prev_point, cand_point_idx) + visit_duration_minutes
                    else:
                        # Inserting between two existing stops: extra
                        # detour cost = new legs minus the leg it replaces.
                        old_leg = travel_time(prev_point, next_point)
                        new_legs = travel_time(prev_point, cand_point_idx) + travel_time(cand_point_idx, next_point)
                        marginal_time = (new_legs - old_leg) + visit_duration_minutes

                    if time_used + marginal_time > time_budget_minutes:
                        continue

                    # Avoid division by zero for a same-location HCP.
                    ratio = value / max(marginal_time, 0.1)

                    if best_choice is None or ratio > best_choice[3]:
                        best_choice = (cand_idx, pos, marginal_time, ratio)

            if best_choice is None:
                # Nothing remaining fits in the leftover budget.
                break

            cand_idx, pos, marginal_time, _ratio = best_choice
            route.insert(pos, cand_idx)
            route_point_indices.insert(pos + 1, cand_idx + 1)
            time_used += marginal_time
            remaining.discard(cand_idx)

        # 2-opt refinement: try reversing segments of the SELECTED route to
        # reduce total travel time, without changing who's on it.
        route = self._two_opt(route, route_point_indices, matrix)

        # Build the final ordered plan with running arrival-time estimates.
        plan = []
        running_minutes = 0.0
        prev_point_idx = 0  # rep's start
        for cand_idx in route:
            point_idx = cand_idx + 1
            leg_time = travel_time(prev_point_idx, point_idx)
            running_minutes += leg_time
            arrival_offset = running_minutes
            running_minutes += visit_duration_minutes

            hcp = geocoded[cand_idx]
            plan.append({
                **hcp,
                "travel_minutes_from_previous": round(leg_time, 1),
                "estimated_arrival_offset_minutes": round(arrival_offset, 1),
            })
            prev_point_idx = point_idx

        visited_ids = {geocoded[i]["hcp_id"] for i in route}
        skipped_budget = [
            {**c, "skip_reason": "time_budget"} for i, c in enumerate(geocoded) if i not in {r for r in route}
        ]

        return {
            "plan": plan,
            "skipped": [{**c, "skip_reason": "no_coordinates"} for c in skipped_no_location] + skipped_budget,
            "total_value": sum(p.get("priority_score", 0) or 0 for p in plan),
            "total_time_minutes": round(time_used, 1),
        }

    def _two_opt(
        self,
        route: List[int],
        route_point_indices: List[int],
        matrix: List[List[float]],
    ) -> List[int]:
        """Standard 2-opt local search: repeatedly try reversing a segment
        of the route and keep the reversal if it shortens total travel
        time. Runs until no improving swap is found (or a safety cap on
        iterations, since a rep's daily list is small - this is fast).
        """
        if len(route) < 3:
            return route

        def route_length(points: List[int]) -> float:
            total = 0.0
            for a, b in zip(points, points[1:]):
                total += matrix[a][b]
            return total

        points = list(route_point_indices)  # includes rep at index 0
        improved = True
        iterations = 0
        while improved and iterations < 200:
            improved = False
            iterations += 1
            for i in range(1, len(points) - 1):
                for j in range(i + 1, len(points)):
                    new_points = points[:i] + points[i:j + 1][::-1] + points[j + 1:]
                    if route_length(new_points) < route_length(points) - 1e-6:
                        points = new_points
                        improved = True

        # Convert back from point-indices (with rep at [0]) to
        # candidate-indices (matching the original `route` list's meaning).
        return [p - 1 for p in points[1:]]