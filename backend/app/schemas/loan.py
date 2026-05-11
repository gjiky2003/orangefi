"""
Loan (originated loan) API schemas.

Provides read and list schemas for active, paid-off, and delinquent loans.
Includes amortization schedule items.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Loan Response (single item in lists)
# ──────────────────────────────────────────────────────────────────────────────


class LoanResponse(BaseModel):
    """Core loan fields returned in list responses."""

    id: str = Field(
        ...,
        description="Loan UUID",
        examples=["c3d4e5f6-a7b8-9012-cdef-123456789012"],
    )
    application_id: str = Field(
        ...,
        description="UUID of the originating application",
    )
    borrower_id: str = Field(
        ...,
        description="UUID of the borrower",
    )
    status: str = Field(
        ...,
        description="Current loan status",
        examples=["active", "delinquent", "paid_off"],
    )
    loan_amount: Decimal = Field(
        ...,
        description="Original principal loan amount",
        max_digits=12,
        decimal_places=2,
    )
    apr: Decimal = Field(
        ...,
        description="Annual Percentage Rate (as a percentage, e.g. 9.990 for 9.99%)",
        max_digits=5,
        decimal_places=3,
    )
    term_months: int = Field(
        ...,
        description="Loan term in months",
        examples=[36],
    )
    monthly_payment: Decimal = Field(
        ...,
        description="Scheduled monthly payment amount",
        max_digits=12,
        decimal_places=2,
    )
    disbursement_amount: Optional[Decimal] = Field(
        None,
        description="Net amount disbursed (loan_amount minus fees)",
        max_digits=12,
        decimal_places=2,
    )
    origination_fee: Optional[Decimal] = Field(
        None,
        description="Origination fee charged",
        max_digits=12,
        decimal_places=2,
    )
    interest_rate_type: str = Field(
        "fixed",
        description="Type of interest rate (fixed or variable)",
    )
    interest_accrued: Decimal = Field(
        Decimal("0.00"),
        description="Total interest accrued to date",
        max_digits=12,
        decimal_places=2,
    )
    days_past_due: int = Field(
        0,
        description="Current days past due (0 if current)",
        ge=0,
    )
    total_amount_due: Decimal = Field(
        Decimal("0.00"),
        description="Total amount currently due (including past-due)",
        max_digits=12,
        decimal_places=2,
    )
    collections_status: Optional[str] = Field(
        None,
        description="Collections stage if applicable",
    )
    origination_date: Optional[date] = Field(
        None,
        description="Date the loan was originated",
    )
    first_payment_date: Optional[date] = Field(
        None,
        description="Date of the first scheduled payment",
    )
    maturity_date: Optional[date] = Field(
        None,
        description="Date the loan matures (final payment due)",
    )
    paid_off_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp when loan was paid in full",
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp of loan creation",
    )
    updated_at: datetime = Field(
        ...,
        description="UTC timestamp of last update",
    )

    model_config = {"frozen": True, "from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Loan Summary (dashboard-friendly)
# ──────────────────────────────────────────────────────────────────────────────


class LoanSummary(BaseModel):
    """Lightweight loan summary for borrower dashboard display."""

    id: str = Field(
        ...,
        description="Loan UUID",
    )
    status: str = Field(...)
    loan_amount: Decimal = Field(...)
    apr: Decimal = Field(...)
    term_months: int = Field(...)
    monthly_payment: Decimal = Field(...)
    remaining_balance: Decimal = Field(
        ...,
        description="Estimated remaining principal balance",
        max_digits=12,
        decimal_places=2,
    )
    next_payment_date: Optional[date] = Field(
        None,
        description="Date of the next scheduled payment",
    )
    next_payment_amount: Optional[Decimal] = Field(
        None,
        description="Amount of the next scheduled payment",
        max_digits=12,
        decimal_places=2,
    )
    days_past_due: int = Field(0)
    paid_off_at: Optional[datetime] = Field(None)
    origination_date: Optional[date] = Field(None)
    maturity_date: Optional[date] = Field(None)
    payments_made: int = Field(
        0,
        description="Number of completed payments to date",
    )
    payments_remaining: int = Field(
        0,
        description="Number of payments remaining",
    )
    total_paid: Decimal = Field(
        Decimal("0.00"),
        description="Total amount paid to date (principal + interest + fees)",
        max_digits=12,
        decimal_places=2,
    )
    on_time_payment_rate: Optional[float] = Field(
        None,
        description="Percentage of payments made on time (0.0 - 1.0)",
        ge=0.0,
        le=1.0,
    )

    model_config = {"frozen": True}


# ──────────────────────────────────────────────────────────────────────────────
# Payment Schedule Item (within loan detail)
# ──────────────────────────────────────────────────────────────────────────────


class LoanPaymentScheduleItem(BaseModel):
    """Single entry in a loan's amortization schedule."""

    payment_number: int = Field(
        ...,
        description="Sequential payment number (1-indexed)",
        ge=1,
    )
    scheduled_date: date = Field(
        ...,
        description="Date the payment is scheduled",
    )
    total_amount: Decimal = Field(
        ...,
        description="Total payment amount (principal + interest + fees)",
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
    remaining_balance: Optional[Decimal] = Field(
        None,
        description="Estimated remaining principal after this payment",
        max_digits=12,
        decimal_places=2,
    )
    status: str = Field(
        ...,
        description="Payment status",
        examples=["scheduled", "completed", "failed"],
    )

    model_config = {"frozen": True}


# ──────────────────────────────────────────────────────────────────────────────
# Loan Detail Response
# ──────────────────────────────────────────────────────────────────────────────


class LoanDetailResponse(LoanResponse):
    """Full loan detail including amortization schedule and payment history."""

    payment_schedule: list[LoanPaymentScheduleItem] = Field(
        ...,
        description="Full amortization schedule for the loan",
    )
    recent_payments: list[dict] = Field(
        ...,
        description="Most recent payment transactions (last 12)",
    )
    borrower_name: Optional[str] = Field(
        None,
        description="Borrower display name",
    )
    funding_account_id: Optional[str] = Field(None)
    funding_reference: Optional[str] = Field(None)
    charge_off_reason: Optional[str] = Field(None)
    delinquency_started_at: Optional[date] = Field(None)
    last_interest_calc_at: Optional[datetime] = Field(None)

    model_config = {"frozen": True, "from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Loan List
# ──────────────────────────────────────────────────────────────────────────────


class LoanListFilter(BaseModel):
    """Query parameters for filtering the loan list."""

    status: Optional[str] = Field(
        None,
        description="Filter by loan status (exact match)",
        examples=["active", "delinquent"],
    )
    borrower_id: Optional[str] = Field(
        None,
        description="Filter by borrower UUID",
    )
    days_past_due_min: Optional[int] = Field(
        None,
        description="Minimum days past due (for collections views)",
        ge=0,
    )
    days_past_due_max: Optional[int] = Field(
        None,
        description="Maximum days past due",
        ge=0,
    )
    originated_after: Optional[date] = Field(
        None,
        description="Filter by origination date on or after this date",
    )
    originated_before: Optional[date] = Field(
        None,
        description="Filter by origination date on or before this date",
    )
    maturity_after: Optional[date] = Field(
        None,
        description="Filter by maturity date on or after this date",
    )
    maturity_before: Optional[date] = Field(
        None,
        description="Filter by maturity date on or before this date",
    )
    search: Optional[str] = Field(
        None,
        description="Free-text search across borrower name",
        max_length=200,
    )
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by",
        pattern=r"^(created_at|loan_amount|apr|status|days_past_due|maturity_date)$",
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
                "status": "active",
                "days_past_due_min": 30,
                "sort_by": "days_past_due",
                "sort_order": "desc",
            }
        }
    }


class LoanListResponse(LoanResponse):
    """Loan fields returned in paginated list responses."""

    borrower_name: Optional[str] = Field(
        None,
        description="Borrower display name for list views",
    )

    model_config = {"frozen": True, "from_attributes": True}
