"""Interaction repository."""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.interaction import Interaction
from app.repositories.base_repository import BaseRepository


class InteractionRepository(BaseRepository[Interaction]):
    """Repository for Interaction model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Interaction)

    async def get_by_hcp_id(
        self,
        hcp_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Interaction]:
        """Get interactions by HCP ID."""
        try:
            stmt = select(self.model).where(
                self.model.hcp_id == hcp_id,
                self.model.deleted_at.is_(None)
            ).order_by(desc(self.model.interaction_date)).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            return []

    async def get_by_hcp_id_with_rep(
        self,
        hcp_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Interaction]:
        """Get interactions for an HCP, eager-loading the rep (user) who
        logged each one. Used by the doctor dashboard's History and
        Analytics views - a plain lazy-load of `interaction.user` would
        raise under an async session, since nothing here awaits it
        implicitly (SQLAlchemy async requires an explicit eager load)."""
        try:
            stmt = (
                select(self.model)
                .options(selectinload(self.model.user))
                .where(
                    self.model.hcp_id == hcp_id,
                    self.model.deleted_at.is_(None)
                )
                .order_by(desc(self.model.interaction_date))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            return []

    async def get_by_user_id(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Interaction]:
        """Get interactions by user ID."""
        try:
            stmt = select(self.model).where(
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None)
            ).order_by(desc(self.model.interaction_date)).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            return []

    async def get_with_filters(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[Interaction]:
        """Get interactions with filters."""
        try:
            # Start with base condition
            conditions = [self.model.deleted_at.is_(None)]
            
            # Add filters only if they have values
            if filters and isinstance(filters, dict):
                # HCP ID filter
                hcp_id = filters.get("hcp_id")
                if hcp_id:
                    conditions.append(self.model.hcp_id == hcp_id)
                
                # User ID filter
                user_id = filters.get("user_id")
                if user_id:
                    conditions.append(self.model.user_id == user_id)
                
                # Interaction type filter
                interaction_type = filters.get("interaction_type")
                if interaction_type:
                    conditions.append(self.model.interaction_type == interaction_type)
                
                # Date range filters
                date_from = filters.get("date_from")
                if date_from:
                    conditions.append(self.model.interaction_date >= date_from)
                
                date_to = filters.get("date_to")
                if date_to:
                    conditions.append(self.model.interaction_date <= date_to)
                
                # Search filter
                search = filters.get("search")
                if search:
                    search_term = f"%{search}%"
                    conditions.append(
                        or_(
                            self.model.hcp_name.ilike(search_term),
                            self.model.topics.ilike(search_term),
                            self.model.summary.ilike(search_term),
                        )
                    )
            
            # Build query
            stmt = select(self.model).where(and_(*conditions)).order_by(
                desc(self.model.interaction_date)
            ).offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            # Return empty list on error
            return []

    async def count_with_filters(self, filters: Dict[str, Any]) -> int:
        """Count interactions with filters."""
        try:
            conditions = [self.model.deleted_at.is_(None)]
            
            if filters and isinstance(filters, dict):
                hcp_id = filters.get("hcp_id")
                if hcp_id:
                    conditions.append(self.model.hcp_id == hcp_id)
                
                user_id = filters.get("user_id")
                if user_id:
                    conditions.append(self.model.user_id == user_id)
                
                interaction_type = filters.get("interaction_type")
                if interaction_type:
                    conditions.append(self.model.interaction_type == interaction_type)
                
                date_from = filters.get("date_from")
                if date_from:
                    conditions.append(self.model.interaction_date >= date_from)
                
                date_to = filters.get("date_to")
                if date_to:
                    conditions.append(self.model.interaction_date <= date_to)
                
                search = filters.get("search")
                if search:
                    search_term = f"%{search}%"
                    conditions.append(
                        or_(
                            self.model.hcp_name.ilike(search_term),
                            self.model.topics.ilike(search_term),
                            self.model.summary.ilike(search_term),
                        )
                    )
            
            stmt = select(self.model).where(and_(*conditions))
            result = await self.session.execute(stmt)
            return len(result.scalars().all())
            
        except Exception as e:
            return 0