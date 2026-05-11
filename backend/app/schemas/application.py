"""
Loan Application API schemas.

Covers the full 12-state application status workflow from draft through
funding. Includes creation, decision, listing with filters, and
status history.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


# ──────────────────────────────────────────────────────────────────────────────
# Application Create
# ──────────────────────────────────────────────────────────────────────────────


class ApplicationCreate(BaseModel):
    """Request schema for creating a new loan application.

    The application starts in 'draft' status. Borrowers can submit
    additional fields as they progress through the flow.
    """

    borrower_id: str = Field(
        ...,
        description="UUID of the borrower creating the application",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    requested_amount: Decimal = Field(
        ...,
        description="Desired loan amount in dollars",
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        examples=[10000.00],
    )
    requested_term_months: int = Field(
        ...,
        description="Desired repayment term in months",
        ge=12,
        le=60,
        examples=[36],
    )
    loan_purpose: str = Field(
        ...,
        description="Primary purpose of the loan",
        pattern=r"^(debt_consolidation|home_improvement|major_purchase|medical|auto|education|vacation|business|other)$",
        examples=["debt_consolidation"],
    )
    loan_purpose_details: Optional[str] = Field(
        None,
        description="Free-text details about loan purpose",
        max_length=5000,
        examples=["Consolidating 3 credit cards with high APR"],
    )

    # ── Debt Consolidation Details ──
    total_existing_debt: Optional[Decimal] = Field(
        None,
        description="Total existing unsecured debt (for debt consolidation)",
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )
    creditor_details: Optional[list[dict[str, Any]]] = Field(
        None,
        description="List of existing creditors with balances and APRs",
        examples=[
            [
                {"name": "Chase", "balance": 3500.00, "apr": 22.99, "min_payment": 85.00},
                {"name": "Amex", "balance": 4200.00, "apr": 18.99, "min_payment": 95.00},
            ]
        ],
    )
    monthly_debt_payments: Optional[Decimal] = Field(
        None,
        description="Total monthly minimum debt payments",
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )

    # ── Employment / Income ──
    application_monthly_income: Optional[Decimal] = Field(
        None,
        description="Monthly gross income at time of application",
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )
    application_employer: Optional[str] = Field(
        None,
        description="Current employer at time of application",
        max_length=256,
    )
    application_employment_status: Optional[str] = Field(
        None,
        description="Employment status at time of application",
        pattern=r"^(employed|self_employed|unemployed|retired)$",
    )
    years_at_current_job: Optional[Decimal] = Field(
        None,
        description="Years at current job (decimal e.g. 2.5)",
        ge=Decimal("0"),
        max_digits=3,
        decimal_places=1,
    )

    # ── Housing ──
    housing_status: Optional[str] = Field(
        None,
        description="Housing status",
        pattern=r"^(own|rent|live_with_family|other)$",
        examples=["rent"],
    )
    monthly_housing_payment: Optional[Decimal] = Field(
        None,
        description="Monthly rent or mortgage payment",
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )

    # ── Metadata ──
    ip_address: Optional[str] = Field(
        None,
        description="IP address of the borrower at time of application",
        max_length=45,
        examples=["192.168.1.1"],
    )
    user_agent: Optional[str] = Field(
        None,
        description="User-Agent header from browser",
        max_length=512,
    )
    application_metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Extensible metadata / analytics payload",
        examples={"source": "web", "campaign": "spring_promo_2026", "referral_code": "FRIEND10"},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "borrower_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "requested_amount": 10000.00,
                "requested_term_months": 36,
                "loan_purpose": "debt_consolidation",
                "loan_purpose_details": "Consolidating 3 credit cards with high APR",
                "total_existing_debt": 7700.00,
                "creditor_details": [
                    {"name": "Chase", "balance": 3500.00, "apr": 22.99, "min_payment": 85.00},
                    {"name": "Amex", "balance": 4200.00, "apr": 18.99, "min_payment": 95.00},
                ],
                "monthly_debt_payments": 180.00,
                "application_monthly_income": 5500.00,
                "application_employer": "Acme Corp",
                "application_employment_status": "employed",
                "years_at_current_job": 3.5,
                "housing_status": "rent",
                "monthly_housing_payment": 1200.00,
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0 ...",
                "application_metadata": {"source": "web", "campaign": "spring_promo_2026"},
            }
        }
    }


# ──────────────────────────────────────────────────────────────────────────────
# Application Decision
# ──────────────────────────────────────────────────────────────────────────────


class ApplicationDecisionRequest(BaseModel):
    """Request schema for an admin/underwriter to make a decision on an application."""

    decision: str = Field(
        ...,
        description="Decision to apply to the application",
        pattern=r"^(approved|declined|manual_review)$",
        examples=["approved"],
    )
    declined_reason: Optional[str] = Field(
        None,
        description="Human-readable decline reason (required if decision is 'declined')",
        max_length=5000,
    )
    declined_reason_codes: Optional[list[str]] = Field(
        None,
        description="Machine-readable adverse action reason codes (ECOA compliant)",
        examples=[
            [
                "X01 - Credit report contains delinquent accounts",
                "X02 - Insufficient income for requested amount",
            ]
        ],
    )
    amount_funded: Optional[Decimal] = Field(
        None,
        description="Approved funding amount (required if decision is 'approved', may differ from requested)",
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )
    notes: Optional[str] = Field(
        None,
        description="Internal underwriting notes (not shared with borrower)",
        max_length=5000,
    )

    @model_validator(mode="after")
    def validate_decision_fields(self) -> "ApplicationDecisionRequest":
        """Ensure required fields are present based on decision type."""
        if self.decision == "declined" and not self.declined_reason:
            raise ValueError("declined_reason is required when decision is 'declined'")
        if self.decision == "approved" and not self.amount_funded:
            raise ValueError("amount_funded is required when decision is 'approved'")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "decision": "approved",
                "amount_funded": 10000.00,
                "notes": "Borrower meets all underwriting criteria",
            }
        }
    }


class ApplicationDecisionResponse(BaseModel):
    """Response returned after an application decision is recorded."""

    application_id: str = Field(
        ...,
        description="UUID of the application",
    )
    status: str = Field(
        ...,
        description="Updated application status",
        examples=["approved", "declined"],
    )
    decisioned_at: datetime = Field(
        ...,
        description="UTC timestamp of when the decision was made",
    )
    decisioned_by: str = Field(
        ...,
        description="UUID of the admin who made the decision",
    )
    declined_reason: Optional[str] = Field(
        None,
        description="Decline reason (if applicable)",
    )
    amount_funded: Optional[Decimal] = Field(
        None,
        description="Approved funding amount (if applicable)",
    )

    model_config = {"frozen": True}


# ──────────────────────────────────────────────────────────────────────────────
# Application Response (single item)
# ──────────────────────────────────────────────────────────────────────────────


class ApplicationStatusHistory(BaseModel):
    """Entry in the application's status history timeline."""

    from_status: Optional[str] = Field(
        None,
        description="Previous status",
    )
    to_status: str = Field(
        ...,
        description="New status after transition",
    )
    changed_at: datetime = Field(
        ...,
        description="UTC timestamp of the status change",
    )
    changed_by: Optional[str] = Field(
        None,
        description="UUID of the actor who triggered the change",
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for the status change",
    )

    model_config = {"frozen": True}


class ApplicationResponse(BaseModel):
    """Core application fields returned in list responses."""

    id: str = Field(
        ...,
        description="Application UUID",
        examples=["b2c3d4e5-f6a7-8901-bcde-f12345678901"],
    )
    borrower_id: str = Field(
        ...,
        description="UUID of the associated borrower",
    )
    status: str = Field(
        ...,
        description="Current application status",
        examples=["submitted"],
    )
    requested_amount: Decimal = Field(
        ...,
        description="Amount requested by borrower",
    )
    requested_term_months: int = Field(
        ...,
        description="Requested repayment term",
    )
    loan_purpose: str = Field(
        ...,
        description="Purpose of the loan",
    )
    amount_funded: Optional[Decimal] = Field(
        None,
        description="Approved funding amount",
    )
    decisioned_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp of decision",
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp of creation",
    )
    updated_at: datetime = Field(
        ...,
        description="UTC timestamp of last update",
    )

    model_config = {"frozen": True, "from_attributes": True}


class ApplicationDetailResponse(ApplicationResponse):
    """Full application detail with all optional fields included."""

    loan_purpose_details: Optional[str] = Field(None)
    total_existing_debt: Optional[Decimal] = Field(None)
    creditor_details: Optional[list[dict[str, Any]]] = Field(None)
    monthly_debt_payments: Optional[Decimal] = Field(None)
    application_monthly_income: Optional[Decimal] = Field(None)
    application_employer: Optional[str] = Field(None)
    application_employment_status: Optional[str] = Field(None)
    years_at_current_job: Optional[Decimal] = Field(None)
    housing_status: Optional[str] = Field(None)
    monthly_housing_payment: Optional[Decimal] = Field(None)
    ip_address: Optional[str] = Field(None)
    user_agent: Optional[str] = Field(None)
    application_metadata: Optional[dict[str, Any]] = Field(None)
    declined_reason: Optional[str] = Field(None)
    declined_reason_codes: Optional[list[str]] = Field(None)
    decisioned_by: Optional[str] = Field(None)
    funded_at: Optional[datetime] = Field(None)

    # ── Related entities (summary) ──
    borrower_name: Optional[str] = Field(
        None,
        description="Borrower first and last name for display",
        examples=["Jane Doe"],
    )
    borrower_email: Optional[str] = Field(
        None,
        description="Borrower email address",
    )

    model_config = {"frozen": True, "from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Application List
# ──────────────────────────────────────────────────────────────────────────────


class ApplicationListFilter(BaseModel):
    """Query parameters for filtering the application list."""

    status: Optional[str] = Field(
        None,
        description="Filter by application status (exact match)",
        examples=["submitted", "approved"],
    )
    borrower_id: Optional[str] = Field(
        None,
        description="Filter by borrower UUID",
    )
    loan_purpose: Optional[str] = Field(
        None,
        description="Filter by loan purpose",
    )
    requested_amount_min: Optional[Decimal] = Field(
        None,
        description="Minimum requested amount",
        ge=Decimal("0"),
    )
    requested_amount_max: Optional[Decimal] = Field(
        None,
        description="Maximum requested amount",
        ge=Decimal("0"),
    )
    created_after: Optional[datetime] = Field(
        None,
        description="Filter by applications created on or after this UTC timestamp",
    )
    created_before: Optional[datetime] = Field(
        None,
        description="Filter by applications created on or before this UTC timestamp",
    )
    search: Optional[str] = Field(
        None,
        description="Free-text search across borrower name and email",
        max_length=200,
    )
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by",
        pattern=r"^(created_at|updated_at|requested_amount|status)$",
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
                "status": "submitted",
                "created_after": "2026-01-01T00:00:00Z",
                "sort_by": "created_at",
                "sort_order": "desc",
            }
        }
    }


class ApplicationListResponse(BaseModel):
    """Paginated list of application summaries."""

    id: str = Field(...)
    borrower_id: str = Field(...)
    borrower_name: Optional[str] = Field(None)
    status: str = Field(...)
    requested_amount: Decimal = Field(...)
    requested_term_months: int = Field(...)
    loan_purpose: str = Field(...)
    amount_funded: Optional[Decimal] = Field(None)
    decisioned_at: Optional[datetime] = Field(None)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    model_config = {"frozen": True, "from_attributes": True}
