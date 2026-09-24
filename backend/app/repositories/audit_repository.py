"""Audit log repository."""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.audit_log import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLog)

    async def get_by_user_id(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs by user ID."""
        stmt = select(self.model).where(
            self.model.user_id == user_id
        ).order_by(desc(self.model.created_at)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_action(
        self,
        action: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs by action."""
        stmt = select(self.model).where(
            self.model.action == action
        ).order_by(desc(self.model.created_at)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()