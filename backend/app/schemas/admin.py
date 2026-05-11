"""
Admin user API schemas.

Covers backoffice admin user management with 6 RBAC roles,
authentication, and MFA/TOTP setup and verification.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ──────────────────────────────────────────────────────────────────────────────
# Admin Response (read)
# ──────────────────────────────────────────────────────────────────────────────


class AdminResponse(BaseModel):
    """Admin user profile returned in API responses.

    Sensitive fields (hashed_password, mfa_secret, backup_codes)
    are NEVER included.
    """

    id: str = Field(
        ...,
        description="Admin user UUID",
        examples=["e5f6a7b8-c9d0-1234-efab-123456789abc"],
    )
    email: str = Field(
        ...,
        description="Admin email address",
        examples=["admin@orangefi.com"],
    )
    display_name: str = Field(
        ...,
        description="Display name shown in the backoffice UI",
        examples=["Jane Underwriter"],
    )
    role: str = Field(
        ...,
        description="RBAC role assigned to this admin",
        examples=["underwriter", "super_admin", "compliance"],
    )
    mfa_enabled: bool = Field(
        ...,
        description="Whether MFA/TOTP is enabled for this account",
    )
    is_active: bool = Field(
        ...,
        description="Whether the admin account is active",
    )
    is_locked: bool = Field(
        ...,
        description="Whether the admin account is temporarily locked",
    )
    locked_until: Optional[datetime] = Field(
        None,
        description="UTC timestamp until which the account is locked",
    )
    last_login_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp of the last successful login",
    )
    last_login_ip: Optional[str] = Field(
        None,
        description="IP address of the last login",
        max_length=45,
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the admin account was created",
    )
    updated_at: datetime = Field(
        ...,
        description="UTC timestamp of the last update to the account",
    )

    model_config = {"frozen": True, "from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Admin Create
# ──────────────────────────────────────────────────────────────────────────────


class AdminCreateRequest(BaseModel):
    """Request schema for creating a new admin user (super_admin only)."""

    email: EmailStr = Field(
        ...,
        description="Admin email address (used for login)",
        max_length=320,
        examples=["new.admin@orangefi.com"],
    )
    display_name: str = Field(
        ...,
        description="Display name for the backoffice UI",
        min_length=1,
        max_length=256,
        examples=["Sarah Support"],
    )
    password: str = Field(
        ...,
        description="Initial password (must meet complexity requirements)",
        min_length=12,
        max_length=128,
        examples=["SecurePass123!@#"],
    )
    role: str = Field(
        ...,
        description="RBAC role to assign",
        pattern=r"^(super_admin|underwriter|collections|compliance|support|viewer)$",
        examples=["underwriter"],
    )
    permissions: Optional[dict[str, Any]] = Field(
        None,
        description="Granular permission overrides (if needed beyond RBAC role)",
        examples={"can_export_data": True, "max_approval_limit": 50000},
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password complexity requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?`~" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "sarah.support@orangefi.com",
                "display_name": "Sarah Support",
                "password": "SecurePass123!@#",
                "role": "support",
            }
        }
    }


# ──────────────────────────────────────────────────────────────────────────────
# Admin Update
# ──────────────────────────────────────────────────────────────────────────────


class AdminUpdateRequest(BaseModel):
    """Request schema for updating an existing admin user."""

    display_name: Optional[str] = Field(
        None,
        description="Updated display name",
        min_length=1,
        max_length=256,
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Updated email address",
        max_length=320,
    )
    password: Optional[str] = Field(
        None,
        description="New password (must meet complexity requirements)",
        min_length=12,
        max_length=128,
    )
    role: Optional[str] = Field(
        None,
        description="Updated RBAC role",
        pattern=r"^(super_admin|underwriter|collections|compliance|support|viewer)$",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Activate or deactivate the admin account",
    )
    permissions: Optional[dict[str, Any]] = Field(
        None,
        description="Updated granular permissions",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not any(c.isupper() for c in v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(c.islower() for c in v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not any(c.isdigit() for c in v):
                raise ValueError("Password must contain at least one digit")
            if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?`~" for c in v):
                raise ValueError("Password must contain at least one special character")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "display_name": "Sarah Senior Support",
                "role": "support",
                "is_active": True,
            }
        }
    }


# ──────────────────────────────────────────────────────────────────────────────
# Admin Login
# ──────────────────────────────────────────────────────────────────────────────


class AdminLoginRequest(BaseModel):
    """Admin login credentials with optional MFA code."""

    email: EmailStr = Field(
        ...,
        description="Admin email address",
        max_length=320,
        examples=["admin@orangefi.com"],
    )
    password: str = Field(
        ...,
        description="Admin password",
        min_length=1,
        max_length=128,
        examples=["SecurePass123!@#"],
    )
    mfa_code: Optional[str] = Field(
        None,
        description="TOTP MFA code (required if MFA is enabled on the account)",
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        examples=["123456"],
    )


class AdminLoginResponse(BaseModel):
    """Response returned on successful admin login."""

    access_token: str = Field(
        ...,
        description="JWT access token for API authentication",
        examples=["eyJhbGciOiJIUzI1NiIs..."],
    )
    refresh_token: Optional[str] = Field(
        None,
        description="JWT refresh token",
        examples=["eyJhbGciOiJIUzI1NiIs..."],
    )
    token_type: str = Field(
        "bearer",
        description="Token type for Authorization header",
    )
    expires_in: int = Field(
        ...,
        description="Token lifetime in seconds",
        examples=[3600],
    )
    admin_id: str = Field(
        ...,
        description="UUID of the authenticated admin",
        examples=["e5f6a7b8-c9d0-1234-efab-123456789abc"],
    )
    display_name: str = Field(
        ...,
        description="Admin display name",
    )
    email: str = Field(
        ...,
        description="Admin email address",
    )
    role: str = Field(
        ...,
        description="Admin RBAC role",
    )
    mfa_enabled: bool = Field(
        ...,
        description="Whether MFA is enabled on this account",
    )
    requires_mfa: bool = Field(
        ...,
        description="Set to True if MFA code is required to complete login",
        examples=[False],
    )

    model_config = {"frozen": True}


# ──────────────────────────────────────────────────────────────────────────────
# MFA Setup & Verification
# ──────────────────────────────────────────────────────────────────────────────


class AdminMfaSetupResponse(BaseModel):
    """Response returned when initiating MFA/TOTP setup."""

    secret: str = Field(
        ...,
        description="TOTP shared secret (base32-encoded). Store this in the authenticator app.",
        examples=["JBSWY3DPEHPK3PXP"],
    )
    qr_code_url: str = Field(
        ...,
        description="URL for the QR code that can be scanned by authenticator apps (otpauth://)",
        examples=["otpauth://totp/OrangeFi:admin@orangefi.com?secret=JBSWY3DPEHPK3PXP&issuer=OrangeFi"],
    )
    backup_codes: list[str] = Field(
        ...,
        description="List of one-time backup codes for account recovery. Store securely.",
        min_length=8,
        max_length=8,
        examples=[
            "A1B2C3D4",
            "E5F6G7H8",
            "I9J0K1L2",
            "M3N4O5P6",
            "Q7R8S9T0",
            "U1V2W3X4",
            "Y5Z6A7B8",
            "C9D0E1F2",
        ],
    )
    message: str = Field(
        ...,
        description="Instructions for the admin user",
        examples=["Scan the QR code with your authenticator app and verify with a code to enable MFA."],
    )

    model_config = {"frozen": True}


class AdminMfaVerifyRequest(BaseModel):
    """Request schema for verifying a TOTP code during MFA setup."""

    totp_code: str = Field(
        ...,
        description="6-digit TOTP code from the authenticator app",
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        examples=["123456"],
    )
    secret: str = Field(
        ...,
        description="TOTP secret provided during MFA setup initiation",
        min_length=16,
        max_length=64,
        examples=["JBSWY3DPEHPK3PXP"],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Admin User List Filter
# ──────────────────────────────────────────────────────────────────────────────


class AdminUserListFilter(BaseModel):
    """Query parameters for filtering the admin user list."""

    role: Optional[str] = Field(
        None,
        description="Filter by role",
        pattern=r"^(super_admin|underwriter|collections|compliance|support|viewer)$",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Filter by active/inactive status",
    )
    is_locked: Optional[bool] = Field(
        None,
        description="Filter by locked/unlocked status",
    )
    search: Optional[str] = Field(
        None,
        description="Free-text search across email and display name",
        max_length=200,
    )
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by",
        pattern=r"^(email|display_name|role|created_at|last_login_at)$",
        examples=["created_at"],
    )
    sort_order: Optional[str] = Field(
        "desc",
        description="Sort direction",
        pattern=r"^(asc|desc)$",
        examples=["desc"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "role": "underwriter",
                "is_active": True,
                "sort_by": "created_at",
                "sort_order": "desc",
            }
        }
    }
