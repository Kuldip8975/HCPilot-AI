"""User repository."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: str) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == id, User.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()