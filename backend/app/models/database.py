"""Database connection and session management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base

from app.config import settings

# Create Base class
Base = declarative_base()

# Convert sync URL to async URL
async_database_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Async engine - removed pool_size and max_overflow for NullPool
async_engine = create_async_engine(
    async_database_url,
    echo=settings.DATABASE_ECHO,
    poolclass=NullPool,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await async_engine.dispose()