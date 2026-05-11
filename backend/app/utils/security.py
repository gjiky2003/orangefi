"""
Security utilities: password hashing, JWT tokens, and MFA/TOTP.

Uses passlib with bcrypt for password hashing, python-jose for JWT, and pyotp for TOTP.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import pyotp
import qrcode
import qrcode.image.svg
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ──────────────────────────────────────────────────────────────────────────────
# Password Hashing
# ──────────────────────────────────────────────────────────────────────────────

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ──────────────────────────────────────────────────────────────────────────────
# JWT Token Management
# ──────────────────────────────────────────────────────────────────────────────


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    """Create a JWT token with the given subject, type, expiry, and optional claims."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        # Merge extra claims but do not allow overwriting reserved fields
        for k, v in extra_claims.items():
            if k not in payload:
                payload[k] = v
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    subject: str,
    extra_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a short-lived JWT access token.

    Args:
        subject: Unique identifier of the user (e.g., borrower UUID string).
        extra_claims: Optional dict of additional claims (e.g., ``{"role": "borrower"}``).
        expires_delta: Override the default access token expiry.

    Returns:
        Encoded JWT string.
    """
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, "access", delta, extra_claims)


def create_refresh_token(
    subject: str,
    extra_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        subject: Unique identifier of the user.
        extra_claims: Optional additional claims.
        expires_delta: Override the default refresh token expiry.

    Returns:
        Encoded JWT string.
    """
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, "refresh", delta, extra_claims)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: The encoded JWT string.

    Returns:
        Decoded payload dictionary.

    Raises:
        JWTError: If the token is expired, malformed, or signature is invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise


def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Verify a JWT token and check its type.

    Args:
        token: The encoded JWT string.
        expected_type: Expected ``type`` claim value (``"access"`` or ``"refresh"``).

    Returns:
        Decoded payload if valid.

    Raises:
        JWTError: If the token type does not match or token is invalid.
    """
    payload = decode_token(token)
    token_type = payload.get("type")
    if token_type != expected_type:
        raise JWTError(
            f"Invalid token type: expected '{expected_type}', got '{token_type}'"
        )
    return payload


def get_subject_from_token(token: str, expected_type: str = "access") -> str:
    """Extract the ``sub`` claim from a verified token.

    Returns:
        Subject string (user UUID).

    Raises:
        JWTError: If the token is invalid or the ``sub`` claim is missing.
    """
    payload = verify_token(token, expected_type)
    sub = payload.get("sub")
    if not sub:
        raise JWTError("Token missing 'sub' claim")
    return sub


# ──────────────────────────────────────────────────────────────────────────────
# MFA / TOTP
# ──────────────────────────────────────────────────────────────────────────────


def generate_totp_secret() -> str:
    """Generate a new TOTP secret (base32-encoded)."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Build an otpauth:// URI for QR code generation.

    Args:
        secret: TOTP shared secret (base32).
        email: User email displayed in the authenticator app.

    Returns:
        ``otpauth://`` URI string compatible with Google Authenticator / Authy.
    """
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.MFA_ISSUER_NAME,
    )


def generate_totp_qr_svg(secret: str, email: str) -> str:
    """Generate an inline SVG string of the TOTP QR code.

    Args:
        secret: TOTP shared secret.
        email: User email for the provisioning URI.

    Returns:
        SVG markup as a string.
    """
    uri = get_totp_uri(secret, email)
    qr = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage)
    return qr.to_string().decode("utf-8")


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code against the shared secret.

    Args:
        secret: TOTP shared secret (base32).
        code: The 6-digit code provided by the user.

    Returns:
        True if the code is valid, False otherwise.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def generate_backup_codes(count: int = 8) -> list[str]:
    """Generate a list of one-time backup codes for MFA recovery.

    Each code is a 10-character alphanumeric string grouped as ``XXXX-XXXX``.

    Args:
        count: Number of backup codes to generate (default 8).

    Returns:
        List of backup code strings.
    """
    import secrets
    import string

    codes: list[str] = []
    for _ in range(count):
        raw = secrets.token_hex(5).upper()  # 10 hex chars
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes
