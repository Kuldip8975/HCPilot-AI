"""HCP service."""

import logging
from typing import Optional, Dict, Any, List
import uuid

from app.repositories.hcp_repository import HCPRepository
from app.models.hcp import HCP, HCPStatus
from app.services.geocoding_service import GeocodingService
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class HCPService:
    """Service for managing HCPs."""

    def __init__(self, hcp_repo: HCPRepository, geocoding_service: Optional[GeocodingService] = None):
        self.hcp_repo = hcp_repo
        # Optional so existing tests/call-sites that don't pass it don't break;
        # falls back to a real GeocodingService if none is injected.
        self.geocoding_service = geocoding_service or GeocodingService()

    async def create_hcp(self, data: Dict[str, Any]) -> HCP:
        """Create a new HCP."""
        if not data.get("name"):
            raise ValidationError("HCP name is required")

        # Never trust client-sent lat/long — always derive from address server-side.
        data.pop("latitude", None)
        data.pop("longitude", None)

        address = data.get("address")
        if address:
            lat, lon = await self.geocoding_service.geocode(address)
            data["latitude"] = lat
            data["longitude"] = lon

        hcp = HCP(**data)
        return await self.hcp_repo.create(hcp)

    async def get_hcp(self, hcp_id: str) -> HCP:
        """Get HCP by ID."""
        hcp = await self.hcp_repo.get_by_id(hcp_id)
        if not hcp:
            raise NotFoundError("HCP", hcp_id)
        return hcp

    async def get_hcps(
        self,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[HCP]:
        """Get HCPs with filters."""
        filters = filters or {}
        return await self.hcp_repo.search(
            query=filters.get("search", ""),
            filters=filters,
            skip=skip,
            limit=limit
        )

    async def update_hcp(self, hcp_id: str, data: Dict[str, Any]) -> HCP:
        """Update an HCP."""
        hcp = await self.get_hcp(hcp_id)

        # Never trust client-sent lat/long — always derive from address server-side.
        data.pop("latitude", None)
        data.pop("longitude", None)

        # Only re-geocode if the address actually changed — avoids hammering
        # the free Nominatim API on unrelated field edits (e.g. just a phone
        # number update shouldn't trigger a geocoding call).
        new_address = data.get("address")
        if new_address and new_address != hcp.address:
            lat, lon = await self.geocoding_service.geocode(new_address)
            data["latitude"] = lat
            data["longitude"] = lon

        for key, value in data.items():
            if hasattr(hcp, key):
                setattr(hcp, key, value)
        return await self.hcp_repo.update(hcp_id, data)

    async def delete_hcp(self, hcp_id: str) -> bool:
        """Delete an HCP."""
        await self.get_hcp(hcp_id)
        return await self.hcp_repo.delete(hcp_id)