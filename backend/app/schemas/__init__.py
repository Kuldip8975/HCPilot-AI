"""Schemas exports."""

from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
)
from app.schemas.hcp import (
    HCPCreate,
    HCPUpdate,
    HCPResponse,
    HCPListResponse,
)
from app.schemas.interaction import (
    InteractionCreate,
    InteractionUpdate,
    InteractionResponse,
    InteractionListResponse,
)
from app.schemas.followup import (
    FollowUpCreate,
    FollowUpUpdate,
    FollowUpResponse,
)

__all__ = [
    # Auth
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    # HCP
    "HCPCreate",
    "HCPUpdate",
    "HCPResponse",
    "HCPListResponse",
    # Interaction
    "InteractionCreate",
    "InteractionUpdate",
    "InteractionResponse",
    "InteractionListResponse",
    # FollowUp
    "FollowUpCreate",
    "FollowUpUpdate",
    "FollowUpResponse",
]