"""
Payment API schemas.

Covers payment schedule viewing, making payments, and listing
payment history with filtering.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────────────────────────────────────
# Payment Response (single item)
# ──────────────────────────────────────────────────────────────────────────────


class PaymentResponse(BaseModel):
    """Full payment record returned in API responses."""

    id: str = Field(
        ...,
        description="Payment UUID",
        examples=["d4e5f6a7-b8c9-0123-defa-123456789abc"],
    )
    loan_id: str = Field(
        ...,
        description="UUID of the associated loan",
    )
    borrower_id: str = Field(
        ...,
        description="UUID of the borrower",
    )
    payment_number: int = Field(
        ...,
        description="Sequential payment number in the amortization schedule",
        ge=1,
        examples=[1],
    )
    status: str = Field(
        ...,
        description="Payment status",
        examples=["scheduled", "completed", "failed"],
    )
    scheduled_date: date = Field(
        ...,
        description="Date the payment is/was scheduled",
    )
    paid_date: Optional[date] = Field(
        None,
        description="Date the payment was actually completed",
    )
    period_start: Optional[date] = Field(
        None,
        description="Start of the billing period this payment covers",
    )
    period_end: Optional[date] = Field(
        None,
        description="End of the billing period this payment covers",
    )
    total_amount: Decimal = Field(
        ...,
        description="Total payment amount due",
        max_digits=12,
        decimal_places=2,
    )
    principal_amount: Decimal = Field(
        ...,
        description="Principal portion of the payment",
        max_digits=12,
        decimal_places=2,
    )
    interest_amount: Decimal = Field(
        ...,
        description="Interest portion of the payment",
        max_digits=12,
        decimal_places=2,
    )
    fees_amount: Decimal = Field(
        Decimal("0.00"),
        description="Fee portion of the payment",
        max_digits=12,
        decimal_places=2,
    )
    late_fee: Decimal = Field(
        Decimal("0.00"),
        description="Late fee assessed (if applicable)",
        max_digits=12,
        decimal_places=2,
    )
    amount_paid: Optional[Decimal] = Field(
        None,
        description="Actual amount paid (may differ from total_amount)",
        max_digits=12,
        decimal_places=2,
    )
    payment_method: Optional[str] = Field(
        None,
        description="Method used for payment",
        examples=["ach", "debit_card", "wire", "check"],
    )
    payment_source: Optional[str] = Field(
        None,
        description="Source account identifier (masked or Plaid ID)",
        examples=["plaid_conn_abc123", "****1234"],
    )
    external_reference: Optional[str] = Field(
        None,
        description="External gateway reference (e.g. Stripe payment intent ID)",
    )
    external_status: Optional[str] = Field(
        None,
        description="External gateway processing status",
    )
    failure_reason: Optional[str] = Field(
        None,
        description="Reason for payment failure (if applicable)",
    )
    retry_count: int = Field(
        0,
        description="Number of retry attempts for this payment",
        ge=0,
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the payment record was created",
    )
    updated_at: datetime = Field(
        ...,
        description="UTC timestamp of last update",
    )

    model_config = {"frozen": True, "from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Payment Schedule Item (lightweight, for amortization displays)
# ──────────────────────────────────────────────────────────────────────────────


class PaymentScheduleItem(BaseModel):
    """Lightweight payment schedule entry for amortization views."""

    payment_number: int = Field(
        ...,
        ge=1,
        description="Sequential payment number",
    )
    scheduled_date: date = Field(
        ...,
        description="Scheduled payment date",
    )
    total_amount: Decimal = Field(
        ...,
        description="Total amount due",
        max_digits=12,
        decimal_places=2,
    )
    principal_amount: Decimal = Field(
        ...,
        description="Principal portion",
        max_digits=12,
        decimal_places=2,
    )
    interest_amount: Decimal = Field(
        ...,
        description="Interest portion",
        max_digits=12,
        decimal_places=2,
    )
    fees_amount: Decimal = Field(
        Decimal("0.00"),
        description="Fee portion",
        max_digits=12,
        decimal_places=2,
    )
    remaining_balance: Optional[Decimal] = Field(
        None,
        description="Estimated remaining principal after this payment",
        max_digits=12,
        decimal_places=2,
    )
    status: str = Field(
        ...,
        description="Payment status",
    )
    is_past_due: bool = Field(
        ...,
        description="Whether this payment is past its scheduled date and unpaid",
    )

    model_config = {"frozen": True}


# ──────────────────────────────────────────────────────────────────────────────
# Make Payment
# ──────────────────────────────────────────────────────────────────────────────


class MakePaymentRequest(BaseModel):
    """Request schema for initiating a payment on a loan."""

    loan_id: str = Field(
        ...,
        description="UUID of the loan to pay",
        examples=["c3d4e5f6-a7b8-9012-cdef-123456789012"],
    )
    amount: Decimal = Field(
        ...,
        description="Payment amount in dollars",
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        examples=[350.00],
    )
    payment_method: str = Field(
        ...,
        description="Payment method to use",
        pattern=r"^(ach|debit_card|wire|check|internal)$",
        examples=["ach"],
    )
    payment_source_id: Optional[str] = Field(
        None,
        description="UUID or identifier of the payment source (e.g., Plaid connection ID or saved card ID)",
        examples=["plaid_conn_abc123"],
    )
    payment_number: Optional[int] = Field(
        None,
        description="Specific scheduled payment number to apply this payment to (if not provided, applies to next due)",
        ge=1,
    )
    memo: Optional[str] = Field(
        None,
        description="Optional memo or note for the payment",
        max_length=500,
    )
    idempotency_key: Optional[str] = Field(
        None,
        description="Unique idempotency key to prevent duplicate payments",
        max_length=128,
        examples=["pay_d4e5f6a7b8c90123"],
    )

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Ensure payment amount is reasonable."""
        if v > Decimal("999999.99"):
            raise ValueError("Payment amount exceeds maximum allowed")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "loan_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "amount": 350.00,
                "payment_method": "ach",
                "payment_source_id": "plaid_conn_abc123",
                "payment_number": 5,
                "memo": "May 2026 payment",
                "idempotency_key": "pay_d4e5f6a7b8c90123",
            }
        }
    }


class MakePaymentResponse(BaseModel):
    """Response returned after a payment is initiated."""

    payment_id: str = Field(
        ...,
        description="UUID of the created payment record",
    )
    loan_id: str = Field(
        ...,
        description="UUID of the loan",
    )
    payment_number: int = Field(
        ...,
        description="Payment number this was applied to",
        ge=1,
    )
    amount: Decimal = Field(
        ...,
        description="Amount submitted for payment",
        max_digits=12,
        decimal_places=2,
    )
    status: str = Field(
        ...,
        description="Initial payment status (typically 'processing')",
        examples=["processing"],
    )
    message: str = Field(
        ...,
        description="Human-readable result message",
        examples=["Payment of $350.00 is being processed"],
    )
    estimated_completion: Optional[datetime] = Field(
        None,
        description="Estimated UTC timestamp for payment completion",
    )
    idempotency_key: Optional[str] = Field(
        None,
        description="Idempotency key used for deduplication",
    )

    model_config = {"frozen": True}


# ──────────────────────────────────────────────────────────────────────────────
# Payment List
# ──────────────────────────────────────────────────────────────────────────────


class PaymentListFilter(BaseModel):
    """Query parameters for filtering the payment list."""

    loan_id: Optional[str] = Field(
        None,
        description="Filter by loan UUID",
    )
    borrower_id: Optional[str] = Field(
        None,
        description="Filter by borrower UUID",
    )
    status: Optional[str] = Field(
        None,
        description="Filter by payment status",
        examples=["completed", "failed", "scheduled"],
    )
    payment_method: Optional[str] = Field(
        None,
        description="Filter by payment method",
        examples=["ach", "debit_card"],
    )
    scheduled_after: Optional[date] = Field(
        None,
        description="Filter by scheduled date on or after this date",
    )
    scheduled_before: Optional[date] = Field(
        None,
        description="Filter by scheduled date on or before this date",
    )
    paid_after: Optional[date] = Field(
        None,
        description="Filter by paid date on or after this date",
    )
    paid_before: Optional[date] = Field(
        None,
        description="Filter by paid date on or before this date",
    )
    payment_number_min: Optional[int] = Field(
        None,
        description="Minimum payment number",
        ge=1,
    )
    payment_number_max: Optional[int] = Field(
        None,
        description="Maximum payment number",
        ge=1,
    )
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by",
        pattern=r"^(scheduled_date|paid_date|payment_number|created_at|total_amount)$",
        examples=["scheduled_date"],
    )
    sort_order: Optional[str] = Field(
        "asc",
        description="Sort direction",
        pattern=r"^(asc|desc)$",
        examples=["asc"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "loan_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "status": "completed",
                "sort_by": "payment_number",
                "sort_order": "asc",
            }
        }
    }


class PaymentListResponse(PaymentResponse):
    """Payment fields returned in paginated list responses.

    Inherits all fields from PaymentResponse.
    """

    pass
