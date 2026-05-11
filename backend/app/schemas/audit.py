"""
Audit log API schemas.

Provides schemas for querying the immutable audit trail and
viewing audit log entries. Supports filtering by actor, action,
resource, date range, and severity.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Audit Log Response (single entry)
# ──────────────────────────────────────────────────────────────────────────────


class AuditLogResponse(BaseModel):
    """Single audit log entry returned in API responses."""

    id: str = Field(
        ...,
        description="Audit log entry UUID",
        examples=["f6a7b8c9-d0e1-2345-fabc-123456789abc"],
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the action occurred (immutable)",
    )
    actor_id: Optional[str] = Field(
        None,
        description="UUID of the actor who performed the action",
    )
    actor_type: Optional[str] = Field(
        None,
        description="Type of actor (borrower, admin, system)",
        examples=["borrower", "admin", "system"],
    )
    admin_user_id: Optional[str] = Field(
        None,
        description="UUID of the admin user (if actor was an admin)",
    )
    action: str = Field(
        ...,
        description="The action that was performed",
        examples=[
            "application_created",
            "decision_made",
            "payment_received",
            "admin_login",
        ],
    )
    resource_type: str = Field(
        ...,
        description="Type of resource that was acted upon",
        examples=["application", "loan", "borrower", "payment"],
    )
    resource_id: Optional[str] = Field(
        None,
        description="UUID or identifier of the resource",
    )
    details: Optional[dict[str, Any]] = Field(
        None,
        description="Arbitrary structured context about the action",
        examples={"application_id": "abc123", "requested_amount": 10000},
    )
    changes: Optional[dict[str, Any]] = Field(
        None,
        description="Before/after diff for resource updates",
        examples={
            "before": {"status": "submitted"},
            "after": {"status": "approved"},
        },
    )
    description: Optional[str] = Field(
        None,
        description="Human-readable summary of what happened",
        examples=["Application abc123 was approved by underwriter jane.doe"],
    )
    ip_address: Optional[str] = Field(
        None,
        description="IP address of the actor at the time of the action",
        max_length=45,
    )
    user_agent: Optional[str] = Field(
        None,
        description="User-Agent header from the client",
        max_length=512,
    )
    request_id: Optional[str] = Field(
        None,
        description="Correlation ID for tracing across services",
        examples=["req_abc123def"],
    )
    severity: str = Field(
        "info",
        description="Severity level of the event",
        examples=["info", "warning", "error", "critical"],
    )
    admin_display_name: Optional[str] = Field(
        None,
        description="Display name of the admin (if actor was an admin)",
    )

    model_config = {"frozen": True, "from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Audit Log Detail Response
# ──────────────────────────────────────────────────────────────────────────────


class AuditLogDetailResponse(AuditLogResponse):
    """Full audit log entry detail (same fields as AuditLogResponse)."""

    pass


# ──────────────────────────────────────────────────────────────────────────────
# Audit Log List Filter
# ──────────────────────────────────────────────────────────────────────────────


class AuditLogListFilter(BaseModel):
    """Query parameters for filtering audit log entries.

    Supports filtering by actor, action type, resource, date range,
    severity, and free-text search.
    """

    actor_id: Optional[str] = Field(
        None,
        description="Filter by actor UUID",
    )
    actor_type: Optional[str] = Field(
        None,
        description="Filter by actor type",
        examples=["borrower", "admin", "system"],
    )
    action: Optional[str] = Field(
        None,
        description="Filter by specific action (exact match)",
        examples=["application_created", "decision_made"],
    )
    actions: Optional[list[str]] = Field(
        None,
        description="Filter by multiple actions (OR logic)",
        min_length=1,
        max_length=20,
        examples=[["payment_received", "payment_failed"]],
    )
    resource_type: Optional[str] = Field(
        None,
        description="Filter by resource type",
        examples=["application", "loan", "borrower"],
    )
    resource_id: Optional[str] = Field(
        None,
        description="Filter by specific resource identifier",
    )
    severity: Optional[str] = Field(
        None,
        description="Filter by severity level",
        pattern=r"^(info|warning|error|critical)$",
        examples=["error", "critical"],
    )
    created_after: Optional[datetime] = Field(
        None,
        description="Filter by entries created on or after this UTC timestamp",
    )
    created_before: Optional[datetime] = Field(
        None,
        description="Filter by entries created on or before this UTC timestamp",
    )
    search: Optional[str] = Field(
        None,
        description="Free-text search across description and details",
        max_length=200,
    )
    admin_user_id: Optional[str] = Field(
        None,
        description="Filter by specific admin user UUID",
    )
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by",
        pattern=r"^(created_at|action|severity|resource_type)$",
        examples=["created_at"],
    )
    sort_order: Optional[str] = Field(
        "desc",
        description="Sort direction (most recent first by default)",
        pattern=r"^(asc|desc)$",
        examples=["desc"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "actor_type": "admin",
                "action": "decision_made",
                "created_after": "2026-01-01T00:00:00Z",
                "created_before": "2026-06-01T00:00:00Z",
                "sort_by": "created_at",
                "sort_order": "desc",
                "page": 1,
                "page_size": 25,
            }
        }
    }


class AuditLogListResponse(AuditLogResponse):
    """Audit log fields returned in paginated list responses.

    Inherits all fields from AuditLogResponse.
    """

    pass
