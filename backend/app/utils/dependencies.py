"""
FastAPI dependencies: current-user extraction, role enforcement, and DB session.

Provides reusable dependencies for route handlers:

* ``get_db`` — yields an async SQLAlchemy session (re-exported from app.database).
* ``get_current_borrower`` — validates the access token and returns the borrower UUID.
* ``get_current_admin`` — validates the access token and returns the admin user row.
* ``require_admin_role`` — factory that creates a role-check dependency.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db  # noqa: F401 — re-export for convenience
from app.models import AdminUser, AdminRole, Borrower
from app.utils.security import decode_token

# ──────────────────────────────────────────────────────────────────────────────
# Auth Schemes
# ──────────────────────────────────────────────────────────────────────────────

_bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="JWT access token (Bearer <token>)",
    auto_error=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _extract_subject(payload: dict[str, Any]) -> str:
    """Extract the 'sub' claim from a decoded JWT payload."""
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return sub


def _raise_401(detail: str = "Not authenticated") -> HTTPException:
    """Raise a 401 Unauthorized with the Bearer challenge header."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Borrower Dependency
# ──────────────────────────────────────────────────────────────────────────────


async def get_current_borrower(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Borrower:
    """Dependency: extract the authenticated borrower from the JWT.

    Validates the access token, loads the borrower from the database,
    and returns the ORM row. Raises 401 if the token is invalid or
    the borrower does not exist / is not active.
    """
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise _raise_401("Invalid token type — expected access token")
        subject = _extract_subject(payload)
    except JWTError:
        raise _raise_401("Invalid or expired token")

    # Load borrower
    result = await db.execute(
        select(Borrower).where(
            Borrower.id == uuid.UUID(subject),
            Borrower.is_active.is_(True),
            Borrower.is_deleted.is_(False),
        )
    )
    borrower = result.scalar_one_or_none()
    if borrower is None:
        raise _raise_401("Borrower not found or inactive")

    return borrower


async def get_current_borrower_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> uuid.UUID:
    """Dependency: extract the borrower UUID from the JWT without a DB lookup.

    Useful when the route only needs the ID (e.g., for filtering).
    """
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise _raise_401("Invalid token type — expected access token")
        subject = _extract_subject(payload)
        return uuid.UUID(subject)
    except (JWTError, ValueError):
        raise _raise_401("Invalid or expired token")


# ──────────────────────────────────────────────────────────────────────────────
# Admin Dependencies
# ──────────────────────────────────────────────────────────────────────────────


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """Dependency: extract the authenticated admin from the JWT.

    Validates the access token, loads the admin user from the database,
    and returns the ORM row. Raises 401/403 on failure.
    """
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise _raise_401("Invalid token type — expected access token")
        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint requires admin privileges",
            )
        subject = _extract_subject(payload)
    except JWTError:
        raise _raise_401("Invalid or expired token")

    result = await db.execute(
        select(AdminUser).where(
            AdminUser.id == uuid.UUID(subject),
            AdminUser.is_active.is_(True),
            AdminUser.is_locked.is_(False),
        )
    )
    admin = result.scalar_one_or_none()
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account not found or deactivated",
        )

    return admin


def require_admin_role(
    *roles: AdminRole,
) -> Callable[..., Any]:
    """Dependency factory: require the admin to have one of the given roles.

    Usage::

        @router.get("/admin/reports")
        async def view_reports(
            admin: AdminUser = Depends(require_admin_role(
                AdminRole.super_admin,
                AdminRole.compliance,
            )),
        ):
            ...

    Args:
        *roles: One or more ``AdminRole`` values that are permitted.

    Returns:
        A FastAPI dependency callable that returns the ``AdminUser`` if authorised.
    """

    async def _role_checker(
        admin: AdminUser = Depends(get_current_admin),
    ) -> AdminUser:
        if admin.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Insufficient permissions. Required one of: "
                    f"{', '.join(r.value for r in roles)}. "
                    f"Your role: {admin.role.value}"
                ),
            )
        return admin

    return _role_checker
