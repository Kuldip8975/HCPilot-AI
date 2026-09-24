"""Authentication schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import uuid


class UserCreate(BaseModel):
    """Schema for user registration.

    role determines which extra fields matter:
      - "sales_rep": specialty/organization are unused; address is optional
        (used as a GPS-denied fallback for the day-planner map).
      - "doctor": specialty/organization/address/phone are used to either
        create the doctor's HCP profile, or fill in gaps on an existing one
        a rep already added (matched by email).
    """
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")
    full_name: str = Field(..., min_length=1, description="Full name")
    role: Optional[str] = Field("sales_rep", description="User role: sales_rep or doctor")

    # Doctor-only signup fields (ignored for sales_rep signups)
    specialty: Optional[str] = Field(None, description="Doctor's specialty (doctor signup only)")
    organization: Optional[str] = Field(None, description="Doctor's hospital/clinic (doctor signup only)")
    phone: Optional[str] = Field(None, description="Doctor's phone number (doctor signup only)")

    # Used by BOTH roles: for a doctor it becomes their HCP profile address;
    # for a sales_rep it's their own base location, used as a fallback when
    # the browser's live GPS is unavailable/denied. Either way it's
    # auto-geocoded server-side - never typed as raw coordinates.
    address: Optional[str] = Field(None, description="Street address (auto-geocoded to lat/long)")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Only two roles exist in this system."""
        if v not in ("sales_rep", "doctor"):
            raise ValueError("role must be 'sales_rep' or 'doctor'")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    hcp_id: Optional[str] = Field(None, description="Linked HCP profile ID (doctors only)")
    address: Optional[str] = Field(None, description="User's base address")
    latitude: Optional[float] = Field(None, description="Auto-computed from address")
    longitude: Optional[float] = Field(None, description="Auto-computed from address")

    @field_validator("id", "hcp_id", mode="before")
    @classmethod
    def validate_id(cls, v):
        """Convert UUID to string if needed."""
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password-reset OTP."""
    email: EmailStr = Field(..., description="Account email to reset")


class ForgotPasswordResponse(BaseModel):
    """Response for the OTP request.

    Scope note: this project has no email-sending service configured
    (no SMTP/SendGrid etc.), so the OTP is returned directly here and
    shown on-screen by the frontend instead of being emailed - a
    deliberate demo-scope choice, not an oversight. In a real deployment
    this response would NOT include the otp field; only a confirmation
    message, with the OTP delivered via email/SMS instead.
    """
    otp: str = Field(..., description="6-digit OTP - demo-only, normally sent via email")
    expires_in_seconds: int = Field(..., description="How long this OTP stays valid")


class ResetPasswordRequest(BaseModel):
    """Schema for completing a password reset with an OTP."""
    email: EmailStr = Field(..., description="Account email")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP shown on screen")
    new_password: str = Field(..., min_length=6, description="New password")
    confirm_password: str = Field(..., min_length=6, description="Must match new_password")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v