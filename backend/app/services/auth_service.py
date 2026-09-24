"""Authentication service."""

import logging
import random
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from app.repositories.user_repository import UserRepository
from app.repositories.hcp_repository import HCPRepository
from app.models.user import User
from app.models.hcp import HCP
from app.services.geocoding_service import GeocodingService
from app.core.exceptions import AuthenticationError, NotFoundError, ConflictError, ValidationError
from app.core.security import SecurityConfig

logger = logging.getLogger(__name__)

# How long a password-reset OTP stays valid.
OTP_VALIDITY_SECONDS = 50

# In-memory OTP store: {email: {"otp": str, "expires_at": datetime}}.
# Scope note: this is a module-level dict, not a DB table - same
# single-instance limitation as the rate limiter (see rate_limit.py). It
# resets if the server restarts, and won't work across multiple backend
# instances behind a load balancer without moving to Redis. Fine for this
# project's scale; a real production deployment would use a shared store
# (Redis, or a DB table with a TTL/cleanup job) instead.
_otp_store: Dict[str, Dict[str, Any]] = {}


class AuthService:
    """Authentication service for user management."""

    def __init__(
        self,
        user_repo: UserRepository,
        hcp_repo: Optional[HCPRepository] = None,
        geocoding_service: Optional[GeocodingService] = None,
    ):
        self.user_repo = user_repo
        # Optional so existing callers that only need login (not doctor
        # signup) don't have to change. register_user() only needs it when
        # role == "doctor".
        self.hcp_repo = hcp_repo
        self.geocoding_service = geocoding_service or GeocodingService()

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user with email and password."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise AuthenticationError("Invalid credentials")

        if not SecurityConfig.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        # Update last login
        user.last_login = datetime.utcnow()
        await self.user_repo.update(str(user.id), {"last_login": datetime.utcnow()})

        return user

    async def _link_or_create_doctor_hcp(self, user_data: Dict[str, Any]) -> Optional[str]:
        """For a doctor signup, find or create the HCP profile row this
        login should be linked to, and return its id.

        Two cases:
          1. A rep already added this doctor as an HCP (by name) at some
             point, and that HCP record has this same email on file - link
             to it, so the doctor "claims" the profile reps have been
             logging visits against.
          2. No matching HCP exists yet - create one from what the doctor
             gave us at signup, so they immediately have a profile reps can
             find and log interactions with.

        Either way, if an address was given, it's geocoded here so the new
        (or freshly-filled-in) HCP row has latitude/longitude ready for the
        map/route-planning features, same as HCPService.create_hcp does for
        rep-created HCPs.
        """
        if self.hcp_repo is None:
            logger.warning("AuthService has no hcp_repo - skipping HCP link for doctor signup")
            return None

        email = user_data["email"]
        address = user_data.get("address")

        existing = await self.hcp_repo.get_by_email(email)
        if existing:
            logger.info(f"Doctor signup matched existing HCP profile (ID: {existing.id}) by email")
            # If the existing profile has no address yet but the doctor
            # just gave one at signup, fill it in (and geocode it) rather
            # than leaving it blank.
            if address and not existing.address:
                lat, lon = await self.geocoding_service.geocode(address)
                await self.hcp_repo.update(
                    str(existing.id),
                    {"address": address, "latitude": lat, "longitude": lon},
                )
            return str(existing.id)

        latitude, longitude = (None, None)
        if address:
            latitude, longitude = await self.geocoding_service.geocode(address)

        new_hcp = HCP(
            name=user_data["full_name"],
            specialty=user_data.get("specialty") or "General",
            email=email,
            phone=user_data.get("phone"),
            address=address,
            latitude=latitude,
            longitude=longitude,
            organization=user_data.get("organization"),
        )
        created = await self.hcp_repo.create(new_hcp)
        logger.info(f"Doctor signup created new HCP profile (ID: {created.id})")
        return str(created.id)

    async def register_user(self, user_data: Dict[str, Any]) -> User:
        """Register a new user (sales rep or doctor)."""
        # Check if user exists
        existing = await self.user_repo.get_by_email(user_data["email"])
        if existing:
            raise ConflictError("User with this email already exists")

        role = user_data.get("role", "sales_rep")
        hcp_id = None
        address = user_data.get("address")
        latitude, longitude = (None, None)

        if role == "doctor":
            # Doctor's address lives on the HCP row, not this User row.
            hcp_id = await self._link_or_create_doctor_hcp(user_data)
            address = None
        elif address:
            # Sales rep: geocode their own base address so it's ready as a
            # GPS-denied fallback for the day-planner map.
            latitude, longitude = await self.geocoding_service.geocode(address)

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=user_data["email"],
            hashed_password=SecurityConfig.get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=role,
            is_active=True,
            hcp_id=hcp_id,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )

        return await self.user_repo.create(user)

    async def request_password_reset_otp(self, email: str) -> str:
        """Generate a 6-digit OTP for a password reset and return it.

        Scope note: there's no email service wired up in this project, so
        the OTP is returned directly to the caller (the API endpoint hands
        it straight to the frontend, which displays it on-screen) instead
        of being emailed. A real deployment would email/SMS this instead
        of returning it in the response.

        Doesn't reveal whether the email exists or not in its own return
        value - if there's no account with this email, a real-looking OTP
        is still generated and returned so the frontend behaves the same
        either way (this avoids leaking which emails are registered) - but
        it's simply never going to match any account when reset_password()
        is actually called for a non-existent user.
        """
        user = await self.user_repo.get_by_email(email)

        otp = f"{random.randint(0, 999999):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=OTP_VALIDITY_SECONDS)
        _otp_store[email] = {"otp": otp, "expires_at": expires_at}

        if user:
            logger.info(f"Password reset OTP generated for: {email}")
        else:
            logger.info(f"Password reset OTP requested for unknown email: {email} (OTP generated anyway, won't match on verify)")

        return otp

    async def reset_password_with_otp(self, email: str, otp: str, new_password: str) -> None:
        """Verify the OTP and, if valid, actually update the user's password."""
        entry = _otp_store.get(email)
        if not entry:
            raise ValidationError("No verification code was requested for this email. Please request a new one.")

        if datetime.now(timezone.utc) > entry["expires_at"]:
            del _otp_store[email]
            raise ValidationError("This verification code has expired. Please request a new one.")

        if entry["otp"] != otp:
            raise ValidationError("Incorrect verification code.")

        user = await self.user_repo.get_by_email(email)
        if not user:
            # OTP matched (it was generated for this email), but the
            # account itself doesn't exist - shouldn't normally happen,
            # but don't silently pretend it worked.
            raise NotFoundError("User", email)

        await self.user_repo.update(
            str(user.id), {"hashed_password": SecurityConfig.get_password_hash(new_password)}
        )

        # OTP is single-use - remove it so it can't be replayed.
        del _otp_store[email]
        logger.info(f"Password reset completed for: {email}")