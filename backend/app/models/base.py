"""Base model with common fields and utilities."""

from datetime import datetime
from typing import Any, Dict
import uuid
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr

from app.models.database import Base


# Try to import uuid7 from uuid_extensions, fallback to uuid4 if not available
try:
    from uuid_extensions import uuid7 as uuid_generator
except ImportError:
    import uuid
    def uuid_generator():
        return uuid.uuid4()


class BaseModel(Base):
    """
    Base model with common fields and utilities.
    All models should inherit from this class.
    """
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid_generator,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    def to_dict(self, exclude: list = None) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        if exclude is None:
            exclude = []
        
        result = {}
        for column in self.__table__.columns:
            if column.name in exclude:
                continue
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif hasattr(value, 'value'):
                value = value.value
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        
        return result
    
    def soft_delete(self) -> None:
        """Soft delete the record."""
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
    
    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft-deleted."""
        return self.deleted_at is not None