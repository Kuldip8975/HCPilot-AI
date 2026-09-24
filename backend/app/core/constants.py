"""Application constants and enums."""

from enum import Enum


class InteractionType(str, Enum):
    """Interaction type enum."""
    MEETING = "meeting"
    CALL = "call"
    EMAIL = "email"
    OTHER = "other"


class InteractionStatus(str, Enum):
    """Interaction status enum."""
    DRAFT = "draft"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class FollowUpStatus(str, Enum):
    """Follow-up status enum."""
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    """User role enum."""
    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    VIEWER = "viewer"


class HCPStatus(str, Enum):
    """HCP status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class AuditAction(str, Enum):
    """Audit action enum."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    LOGIN = "login"
    LOGOUT = "logout"


class IntentType(str, Enum):
    """AI intent types for LangGraph agent."""
    LOG_INTERACTION = "log_interaction"
    EDIT_INTERACTION = "edit_interaction"
    VIEW_HISTORY = "view_history"
    SEARCH_HCPS = "search_hcps"
    SCHEDULE_FOLLOWUP = "schedule_followup"
    ANALYZE_TRENDS = "analyze_trends"
    GENERIC_QUERY = "generic_query"
    CONFIRMATION = "confirmation"
    CANCEL = "cancel"


# Rate limiting constants
RATE_LIMIT_DEFAULTS = {
    "auth": "5/minute",
    "chat": "20/minute",
    "api": "100/minute",
    "analytics": "50/minute"
}

# Pagination defaults
PAGINATION_DEFAULTS = {
    "default_limit": 20,
    "max_limit": 100
}

# Maximum lengths for fields
MAX_LENGTHS = {
    "name": 200,
    "email": 255,
    "phone": 20,
    "specialty": 100,
    "title": 100,
    "summary": 500,
    "notes": 2000,
    "topics": 500,
    "address": 500,
    "organization": 255,
}

# Regex patterns
PATTERNS = {
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "phone": r"^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$",
}