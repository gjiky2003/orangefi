"""
AES-256 symmetric encryption / decryption for PII fields.

Uses the ``cryptography`` library's Fernet implementation (AES-128-CBC with
a SHA-256 HMAC, keyed by a 32-byte URL-safe base64-encoded key).

The encryption key is read from ``settings.ENCRYPTION_KEY``. If it is not
set, a warning is emitted and operations will raise ``EncryptionError``.
"""

from __future__ import annotations

import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from app.config import settings

logger = logging.getLogger("orangefi.encryption")


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


# ──────────────────────────────────────────────────────────────────────────────
# Lazy-loaded Fernet instance
# ──────────────────────────────────────────────────────────────────────────────

_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    """Return a singleton Fernet instance, initialising on first call."""
    global _fernet
    if _fernet is not None:
        return _fernet

    key: Optional[str] = settings.ENCRYPTION_KEY
    if not key:
        logger.error(
            "ENCRYPTION_KEY is not set — PII encryption/decryption is unavailable. "
            "Set a 32-byte URL-safe base64 key in your environment or .env file."
        )
        raise EncryptionError(
            "ENCRYPTION_KEY not configured. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    try:
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as exc:
        raise EncryptionError(f"Invalid ENCRYPTION_KEY: {exc}") from exc

    return _fernet


def reset_fernet() -> None:
    """Reset the cached Fernet instance (useful in tests when settings change)."""
    global _fernet
    _fernet = None


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────


def encrypt(plain_text: str) -> bytes:
    """Encrypt a plaintext string using Fernet (AES-256).

    Args:
        plain_text: String to encrypt (e.g., SSN, income value).

    Returns:
        Encrypted bytes (URL-safe base64).

    Raises:
        EncryptionError: If the encryption key is not configured.
    """
    f = _get_fernet()
    return f.encrypt(plain_text.encode("utf-8"))


def decrypt(cipher_text: bytes) -> str:
    """Decrypt a Fernet-encrypted blob back to the original plaintext.

    Args:
        cipher_text: Encrypted bytes (as stored in the database).

    Returns:
        Decrypted UTF-8 string.

    Raises:
        EncryptionError: If the key is not configured or the token is invalid.
    """
    f = _get_fernet()
    try:
        return f.decrypt(cipher_text).decode("utf-8")
    except InvalidToken as exc:
        raise EncryptionError(
            "Failed to decrypt cipher text — token is invalid or key has changed"
        ) from exc


def encrypt_field(value: Optional[str]) -> Optional[bytes]:
    """Convenience helper: encrypt a nullable field, returning None for None.

    Args:
        value: Plaintext string or None.

    Returns:
        Encrypted bytes, or None if the input was None.
    """
    if value is None:
        return None
    return encrypt(value)


def decrypt_field(value: Optional[bytes]) -> Optional[str]:
    """Convenience helper: decrypt a nullable field, returning None for None.

    Args:
        value: Encrypted bytes or None.

    Returns:
        Decrypted string, or None if the input was None.
    """
    if value is None:
        return None
    return decrypt(value)
