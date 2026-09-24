"""Base repository with common CRUD operations."""

from typing import Type, TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.sql import func

from app.models.base import BaseModel

# Use uuid.uuid4 instead of uuid7
import uuid

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def create(self, entity: T) -> T:
        """Create a new entity."""
        if not hasattr(entity, "id") or entity.id is None:
            entity.id = str(uuid.uuid4())
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get all entities with pagination."""
        stmt = select(self.model).where(self.model.deleted_at.is_(None))
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update an entity."""
        stmt = (
            update(self.model)
            .where(self.model.id == id, self.model.deleted_at.is_(None))
            .values(**data)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        await self.session.commit()
        # commit() expires the entity's attributes; refresh reloads them
        # inside this same async context so later attribute access (e.g.
        # Pydantic building a response from it) doesn't try to lazily
        # fetch them outside an async-safe context, which raises
        # MissingGreenlet.
        if entity is not None:
            await self.session.refresh(entity)
        return entity

    async def delete(self, id: str, soft: bool = True) -> bool:
        """Delete an entity."""
        if soft:
            stmt = (
                update(self.model)
                .where(self.model.id == id)
                .values(deleted_at=func.now())
            )
        else:
            stmt = delete(self.model).where(self.model.id == id)
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities."""
        stmt = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None)
        )
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0