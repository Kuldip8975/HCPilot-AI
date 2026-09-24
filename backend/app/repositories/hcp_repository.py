"""HCP repository."""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.models.hcp import HCP
from app.repositories.base_repository import BaseRepository


class HCPRepository(BaseRepository[HCP]):
    """Repository for HCP model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, HCP)

    async def search(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[HCP]:
        """Search HCPs by name, specialty, or address."""
        conditions = [self.model.deleted_at.is_(None)]

        if query:
            search = f"%{query}%"
            conditions.append(
                or_(
                    self.model.name.ilike(search),
                    self.model.specialty.ilike(search),
                    self.model.address.ilike(search),
                )
            )

        if filters:
            if filters.get("specialty"):
                conditions.append(self.model.specialty == filters["specialty"])
            if filters.get("status"):
                conditions.append(self.model.status == filters["status"])
            if filters.get("location"):
                conditions.append(self.model.address.ilike(f"%{filters['location']}%"))

        stmt = select(self.model).where(and_(*conditions)).order_by(
            self.model.name
        ).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_specialty(self, specialty: str) -> List[HCP]:
        """Get HCPs by specialty."""
        stmt = select(self.model).where(
            self.model.specialty == specialty,
            self.model.deleted_at.is_(None)
        ).order_by(self.model.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_email(self, email: str) -> Optional[HCP]:
        """Get an HCP profile by email (case-insensitive).

        Used at doctor signup: if a rep already added this doctor with the
        same email, the new login gets linked to that existing profile
        instead of creating a duplicate.
        """
        if not email:
            return None
        stmt = select(self.model).where(
            self.model.email.ilike(email),
            self.model.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()