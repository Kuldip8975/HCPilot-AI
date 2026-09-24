"""Authentication endpoints."""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.hcp_repository import HCPRepository
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
)
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError, NotFoundError
from app.core.security import SecurityConfig
from app.config import settings
from app.api.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency injection for auth service."""
    user_repo = UserRepository(db)
    hcp_repo = HCPRepository(db)
    return AuthService(user_repo, hcp_repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    try:
        payload = SecurityConfig.decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token")

        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("User is inactive")

        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise AuthenticationError("Invalid authentication credentials")


async def require_doctor(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that only lets role='doctor' users through.

    Use this on any endpoint that's specifically the doctor-facing
    dashboard (e.g. viewing follow-ups scheduled with them), so a sales
    rep's token can't be used to peek at it.
    """
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available to doctor accounts.",
        )
    return current_user


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        hcp_id=str(user.hcp_id) if user.hcp_id else None,
        address=user.address,
        latitude=user.latitude,
        longitude=user.longitude,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request,
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login user and return JWT tokens."""
    try:
        user = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
        )

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "hcp_id": str(user.hcp_id) if user.hcp_id else None,
        }
        access_token = SecurityConfig.create_access_token(token_data)
        refresh_token = SecurityConfig.create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": _to_user_response(user),
        }
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/register", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(
    request: Request,
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user and return JWT tokens."""
    try:
        user = await auth_service.register_user(user_data.model_dump())

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "hcp_id": str(user.hcp_id) if user.hcp_id else None,
        }
        access_token = SecurityConfig.create_access_token(token_data)
        refresh_token = SecurityConfig.create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": _to_user_response(user),
        }
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Request a password-reset OTP.

    Scope note: no email service is configured in this project, so the
    OTP is returned directly in this response - the frontend displays it
    on-screen instead of it being emailed. See AuthService.
    request_password_reset_otp for the full explanation.
    """
    otp = await auth_service.request_password_reset_otp(data.email)
    return ForgotPasswordResponse(otp=otp, expires_in_seconds=50)


@router.post("/reset-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Complete a password reset using the OTP from /forgot-password."""
    try:
        await auth_service.reset_password_with_otp(
            email=data.email,
            otp=data.otp,
            new_password=data.new_password,
        )
        return {"success": True, "message": "Password has been reset successfully."}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """Logout user (client-side token removal)."""
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
):
    """Refresh access token using refresh token."""
    try:
        payload = SecurityConfig.decode_token(refresh_data.refresh_token, is_refresh=True)
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        hcp_id = payload.get("hcp_id")

        if not user_id:
            raise AuthenticationError("Invalid refresh token")

        token_data = {"sub": user_id, "email": email, "role": role, "hcp_id": hcp_id}
        access_token = SecurityConfig.create_access_token(token_data)
        refresh_token = SecurityConfig.create_refresh_token(token_data)

        user_response = UserResponse(
            id=user_id,
            email=email or "",
            full_name="User",
            role=role or "sales_rep",
            is_active=True,
            hcp_id=hcp_id,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_response,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Get current user profile."""
    return _to_user_response(current_user)