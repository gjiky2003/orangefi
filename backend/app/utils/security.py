"""
Security utilities: password hashing, JWT tokens, and MFA/TOTP.

Uses werkzeug.security for password hashing (pbkdf2:sha256, no bcrypt dependency),
python-jose for JWT, and pyotp for TOTP.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import pyotp
import qrcode
import qrcode.image.svg
from jose import JWTError, jwt
from werkzeug.security import generate_password_hash, check_password_hash

from app.config import settings

# ── Password Hashing ──────────────────────────────────────────────────────────
# Uses werkzeug's pbkdf2:sha256 with salt (no bcrypt dependency issues)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using pbkdf2:sha256."""
    return generate_password_hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return check_password_hash(hashed_password, plain_password)


# ── JWT Token Management ──────────────────────────────────────────────────────


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
        for k, v in extra_claims.items():
            if k not in payload:
                payload[k] = v
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    subject: str,
    extra_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a short-lived JWT access token."""
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, "access", delta, extra_claims)


def create_refresh_token(
    subject: str,
    extra_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a long-lived JWT refresh token."""
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, "refresh", delta, extra_claims)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise


def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Verify a JWT token and check its type."""
    payload = decode_token(token)
    token_type = payload.get("type")
    if token_type != expected_type:
        raise JWTError(
            f"Invalid token type: expected '{expected_type}', got '{token_type}'"
        )
    return payload


def get_subject_from_token(token: str, expected_type: str = "access") -> str:
    """Extract the ``sub`` claim from a verified token."""
    payload = verify_token(token, expected_type)
    sub = payload.get("sub")
    if not sub:
        raise JWTError("Token missing 'sub' claim")
    return sub


# ── MFA / TOTP ────────────────────────────────────────────────────────────────


def generate_totp_secret() -> str:
    """Generate a new TOTP secret (base32-encoded)."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Build an otpauth:// URI for QR code generation."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.MFA_ISSUER_NAME,
    )


def generate_totp_qr_svg(secret: str, email: str) -> str:
    """Generate an inline SVG string of the TOTP QR code."""
    uri = get_totp_uri(secret, email)
    qr = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage)
    return qr.to_string().decode("utf-8")


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code against the shared secret."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def generate_backup_codes(count: int = 8) -> list[str]:
    """Generate a list of one-time backup codes for MFA recovery."""
    import secrets as sec
    codes: list[str] = []
    for _ in range(count):
        raw = sec.token_hex(5).upper()
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes
