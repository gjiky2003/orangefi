"""
Common API response schemas for the OrangeFi platform.

Includes pagination wrappers, error responses, and health check schemas
shared across all endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

# ──────────────────────────────────────────────────────────────────────────────
# Type variable for generic paginated responses
# ──────────────────────────────────────────────────────────────────────────────

T = TypeVar("T")


# ──────────────────────────────────────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Schema for the /health endpoint response."""

    status: str = Field(
        ...,
        description="Service health status",
        examples=["ok", "degraded", "down"],
    )
    version: str = Field(
        ...,
        description="Application version from config",
        examples=["0.1.0"],
    )
    environment: str = Field(
        ...,
        description="Deployment environment",
        examples=["development", "staging", "production"],
    )
    database: str = Field(
        ...,
        description="Database connectivity status",
        examples=["connected", "disconnected"],
    )
    redis: Optional[str] = Field(
        None,
        description="Redis connectivity status",
        examples=["connected", "disconnected"],
    )
    uptime_seconds: Optional[float] = Field(
        None,
        description="Server uptime in seconds",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check",
    )

    model_config = {"json_schema_extra": {"example": {"status": "ok", "version": "0.1.0", "environment": "development", "database": "connected", "redis": "connected", "uptime_seconds": 3600.0, "timestamp": "2026-05-11T13:57:00Z"}}}


# ──────────────────────────────────────────────────────────────────────────────
# Pagination
# ──────────────────────────────────────────────────────────────────────────────


class PaginationMeta(BaseModel):
    """Pagination metadata embedded in paginated list responses."""

    page: int = Field(
        ...,
        ge=1,
        description="Current page number (1-indexed)",
        examples=[1],
    )
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of items per page",
        examples=[25],
    )
    total_items: int = Field(
        ...,
        ge=0,
        description="Total number of items matching the query",
        examples=[142],
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages based on total_items and page_size",
        examples=[6],
    )
    has_next: bool = Field(
        ...,
        description="Whether a subsequent page exists",
    )
    has_previous: bool = Field(
        ...,
        description="Whether a prior page exists",
    )

    model_config = {"frozen": True}


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Usage:
        class MyListResponse(PaginatedResponse[MyItemSchema]):
            pass
    """

    data: list[T] = Field(
        ...,
        description="List of items for the current page",
    )
    pagination: PaginationMeta = Field(
        ...,
        description="Pagination metadata",
    )

    model_config = {"frozen": True}


# ──────────────────────────────────────────────────────────────────────────────
# Success / Error Responses
# ──────────────────────────────────────────────────────────────────────────────


class SuccessResponse(BaseModel):
    """Generic success response with optional data payload."""

    success: bool = Field(
        True,
        description="Indicates the request succeeded",
    )
    message: str = Field(
        ...,
        description="Human-readable success message",
        examples=["Resource created successfully"],
    )
    data: Optional[dict[str, Any]] = Field(
        None,
        description="Optional response payload",
    )

    model_config = {"json_schema_extra": {"example": {"success": True, "message": "Borrower registered successfully", "data": {"borrower_id": "uuid-string"}}}}


class ValidationErrorDetail(BaseModel):
    """Single field validation error."""

    field: str = Field(
        ...,
        description="Name of the field that failed validation",
        examples=["email"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Invalid email format"],
    )
    code: Optional[str] = Field(
        None,
        description="Machine-readable error code",
        examples=["value_error.email"],
    )

    model_config = {"frozen": True}


class ErrorResponse(BaseModel):
    """Standard error response for API error conditions."""

    success: bool = Field(
        False,
        description="Always False for error responses",
    )
    error: str = Field(
        ...,
        description="Human-readable error summary",
        examples=["Borrower not found"],
    )
    detail: Optional[str] = Field(
        None,
        description="Detailed error description or debug info",
        examples=["No borrower found with the provided ID"],
    )
    code: Optional[str] = Field(
        None,
        description="Machine-readable error code for programmatic handling",
        examples=["BORROWER_NOT_FOUND", "VALIDATION_ERROR", "UNAUTHORIZED"],
    )
    status_code: Optional[int] = Field(
        None,
        description="HTTP status code",
        examples=[404, 400, 401, 403, 422, 500],
    )
    validation_errors: Optional[list[ValidationErrorDetail]] = Field(
        None,
        description="List of field-level validation errors (for 422 responses)",
    )
    request_id: Optional[str] = Field(
        None,
        description="Correlation ID for tracing the request in logs",
        examples=["req_abc123def"],
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the error occurred",
    )

    model_config = {"json_schema_extra": {"example": {"success": False, "error": "Borrower not found", "detail": "No borrower with ID 'abc-123' exists", "code": "BORROWER_NOT_FOUND", "status_code": 404, "validation_errors": None, "request_id": "req_abc123def", "timestamp": "2026-05-11T13:57:00Z"}}}
