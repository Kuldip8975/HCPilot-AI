"""Geocoding service — converts a free-text address into latitude/longitude.

Uses OpenStreetMap's Nominatim (free, no API key). Nominatim's usage policy
caps requests at 1/second and requires a descriptive User-Agent with a real
contact — both are respected here. If geocoding fails (bad address, network
issue, rate limit), this returns (None, None) rather than raising, so an
HCP/rep can still be saved without blocking on a third-party lookup — the
"Navigate"/map features simply won't show that record until the address is
corrected and re-saved.
"""

import logging
from typing import Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "hcp-crm-app/1.0 (contact: emvs2005@gmail.com)"


class GeocodingService:
    """Wraps the free Nominatim geocoding API."""

    async def geocode(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """Return (latitude, longitude) for a free-text address, or (None, None) on failure."""
        if not address or not address.strip():
            return None, None

        params = {
            "q": address,
            "format": "json",
            "limit": 1,
        }
        headers = {"User-Agent": USER_AGENT}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(NOMINATIM_URL, params=params, headers=headers)
                response.raise_for_status()
                results = response.json()
        except Exception as exc:
            logger.warning(f"Geocoding failed for address '{address}': {exc}")
            return None, None

        if not results:
            logger.info(f"Geocoding found no match for address '{address}'")
            return None, None

        try:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            return lat, lon
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning(f"Geocoding returned unexpected shape for '{address}': {exc}")
            return None, None