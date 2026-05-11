"""
Audit log helper — creates structured audit log entries.

Provides a single ``create_audit_log`` function that accepts all the fields
defined in the ``AuditLog`` model and writes them to the database.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def create_audit_log(
    db: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    actor_id: Optional[uuid.UUID] = None,
    actor_type: Optional[str] = None,
    admin_user_id: Optional[uuid.UUID] = None,
    details: Optional[dict[str, Any]] = None,
    changes: Optional[dict[str, Any]] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    severity: str = "info",
) -> AuditLog:
    """Create and persist an audit log entry.

    Args:
        db: Active database session.
        action: The ``AuditAction`` enum value (as a string).
        resource_type: Entity type (e.g. ``"application"``, ``"loan"``).
        resource_id: String representation of the entity's primary key.
        actor_id: UUID of the user (borrower or admin) who performed the action.
        actor_type: ``"borrower"``, ``"admin"``, or ``"system"``.
        admin_user_id: If the actor is an admin, their ``AdminUser.id``.
        details: Arbitrary structured context payload.
        changes: Before/after diff for update operations.
        description: Human-readable summary of the event.
        ip_address: Originating IP address.
        user_agent: Originating user-agent string.
        request_id: Correlation / tracing ID.
        severity: ``"info"``, ``"warning"``, ``"error"``, or ``"critical"``.

    Returns:
        The created ``AuditLog`` ORM instance (already flushed to the session).
    """
    entry = AuditLog(
        created_at=datetime.now(timezone.utc),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        actor_type=actor_type,
        admin_user_id=admin_user_id,
        details=details,
        changes=changes,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        severity=severity,
    )
    db.add(entry)
    await db.flush()
    return entry
