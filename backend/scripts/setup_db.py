"""Database setup script."""

import asyncio
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.database import Base
from app.models.user import User
from app.models.hcp import HCP
from app.models.interaction import Interaction
from app.models.followup import FollowUp
from app.core.security import SecurityConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_database():
    """Setup database with initial data."""
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True
    )
    
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created")
    
    # Create session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create admin user
        admin = User(
            email="admin@example.com",
            hashed_password=SecurityConfig.get_password_hash("admin123"),
            full_name="Admin User",
            role="admin",
            is_active=True
        )
        session.add(admin)
        
        # Create test HCPs
        hcps = [
            HCP(
                name="Dr. Sarah Chen",
                title="Oncologist",
                specialty="Oncology",
                email="sarah.chen@hospital.com",
                phone="+1-555-0101"
            ),
            HCP(
                name="Dr. James Wilson",
                title="Cardiologist",
                specialty="Cardiology",
                email="james.wilson@cardiology.com",
                phone="+1-555-0102"
            )
        ]
        for hcp in hcps:
            session.add(hcp)
        
        await session.commit()
        logger.info("Seed data created")
    
    await engine.dispose()
    logger.info("Database setup complete")


if __name__ == "__main__":
    asyncio.run(setup_database())