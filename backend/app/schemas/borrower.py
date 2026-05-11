"""
Borrower (customer) API schemas.

Covers registration, login, profile CRUD, and pre-qualification
request/response cycles. Sensitive PII fields (SSN) are intentionally
excluded from response schemas — they are encrypted at rest and only
sent during registration.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)
from typing_extensions import Annotated


# ──────────────────────────────────────────────────────────────────────────────
# Shared field constraints
# ──────────────────────────────────────────────────────────────────────────────

PhoneStr = Annotated[
    str,
    StringConstraints(
        min_length=10,
        max_length=20,
        pattern=r"^\+?[1-9]\d{9,19}$",
    ),
]

SsnStr = Annotated[
    str,
    StringConstraints(
        min_length=11,
        max_length=11,
        pattern=r"^\d{3}-\d{2}-\d{4}$",
    ),
]

ZipCodeStr = Annotated[
    str,
    StringConstraints(
        min_length=5,
        max_length=10,
        pattern=r"^\d{5}(-\d{4})?$",
    ),
]

StateStr = Annotated[
    str,
    StringConstraints(
        min_length=2,
        max_length=2,
        pattern=r"^(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)$",
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# Borrower Registration & Creation
# ──────────────────────────────────────────────────────────────────────────────


class BorrowerRegister(BaseModel):
    """Request schema for new borrower self-registration.

    All PII fields required. SSN is transmitted encrypted at the
    transport layer and will be encrypted at rest (AES-256) before
    storage.
    """

    email: EmailStr = Field(
        ...,
        description="Primary email address (used for login and notifications)",
        max_length=320,
        examples=["jane.doe@example.com"],
    )
    phone: PhoneStr = Field(
        ...,
        description="Phone number in E.164 format",
        examples=["+12025551234"],
    )
    first_name: str = Field(
        ...,
        description="Legal first name",
        min_length=1,
        max_length=128,
        examples=["Jane"],
    )
    middle_name: Optional[str] = Field(
        None,
        description="Legal middle name (if applicable)",
        max_length=128,
        examples=["Marie"],
    )
    last_name: str = Field(
        ...,
        description="Legal last name / surname",
        min_length=1,
        max_length=128,
        examples=["Doe"],
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth (ISO 8601)",
        examples=["1990-01-15"],
    )
    ssn: SsnStr = Field(
        ...,
        description="Social Security Number (format: XXX-XX-XXXX). Encrypted at rest.",
        examples=["123-45-6789"],
    )
    address_line1: str = Field(
        ...,
        description="Street address line 1",
        min_length=1,
        max_length=256,
        examples=["123 Main Street"],
    )
    address_line2: Optional[str] = Field(
        None,
        description="Apartment, suite, unit, etc.",
        max_length=256,
        examples=["Apt 4B"],
    )
    city: str = Field(
        ...,
        description="City name",
        min_length=1,
        max_length=128,
        examples=["Springfield"],
    )
    state: StateStr = Field(
        ...,
        description="Two-letter USPS state abbreviation",
        examples=["IL"],
    )
    zip_code: ZipCodeStr = Field(
        ...,
        description="ZIP or ZIP+4 code",
        examples=["62701"],
    )
    employer: Optional[str] = Field(
        None,
        description="Current employer name",
        max_length=256,
        examples=["Acme Corp"],
    )
    employment_status: Optional[str] = Field(
        None,
        description="Employment status category",
        pattern=r"^(employed|self_employed|unemployed|retired)$",
        examples=["employed"],
    )
    monthly_income: Optional[Decimal] = Field(
        None,
        description="Self-reported monthly gross income",
        ge=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        examples=[5500.00],
    )
    agreed_to_tos: bool = Field(
        ...,
        description="Must be True — acceptance of Terms of Service",
    )
    agreed_to_privacy: bool = Field(
        ...,
        description="Must be True — acceptance of Privacy Policy",
    )

    # ── Validators ──

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v: date) -> date:
        """Ensure borrower is at least 18 years old."""
        today = date.today()
        age = (
            today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        )
        if age < 18:
            raise ValueError("Borrower must be at least 18 years old")
        if age > 120:
            raise ValueError("Invalid date of birth")
        return v

    @field_validator("agreed_to_tos", "agreed_to_privacy")
    @classmethod
    def validate_consent(cls, v: bool) -> bool:
        """Consent fields must be explicitly True."""
        if not v:
            raise ValueError("You must accept the terms to register")
        return v

    @field_validator("monthly_income")
    @classmethod
    def validate_income(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Monthly income must be reasonable."""
        if v is not None and v <= 0:
            raise ValueError("Monthly income must be positive")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "jane.doe@example.com",
                "phone": "+12025551234",
                "first_name": "Jane",
                "middle_name": "Marie",
                "last_name": "Doe",
                "date_of_birth": "1990-01-15",
                "ssn": "123-45-6789",
                "address_line1": "123 Main Street",
                "address_line2": "Apt 4B",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62701",
                "employer": "Acme Corp",
                "employment_status": "employed",
                "monthly_income": 5500.00,
                "agreed_to_tos": True,
                "agreed_to_privacy": True,
            }
        }
    }


class BorrowerCreate(BorrowerRegister):
    """Admin-level borrower creation.

    Same fields as self-registration but can be performed by
    backoffice admins on behalf of a borrower.
    """

    pass


# ──────────────────────────────────────────────────────────────────────────────
# Borrower Login
# ──────────────────────────────────────────────────────────────────────────────


class BorrowerLogin(BaseModel):
    """Borrower login credentials."""

    email: EmailStr = Field(
        ...,
        description="Registered email address",
        max_length=320,
        examples=["jane.doe@example.com"],
    )
    password: str = Field(
        ...,
        description="Account password",
        min_length=8,
        max_length=128,
        examples=["securePassword123!"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password strength server-side."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class BorrowerLoginResponse(BaseModel):
    """Response returned on successful borrower login."""

    access_token: str = Field(
        ...,
        description="JWT access token for API authentication",
        examples=["eyJhbGciOiJIUzI1NiIs..."],
    )
    refresh_token: Optional[str] = Field(
        None,
        description="JWT refresh token for obtaining new access tokens",
        examples=["eyJhbGciOiJIUzI1NiIs..."],
    )
    token_type: str = Field(
        "bearer",
        description="Token type for Authorization header",
    )
    expires_in: int = Field(
        ...,
        description="Token lifetime in seconds",
        examples=[3600],
    )
    borrower_id: str = Field(
        ...,
        description="UUID of the authenticated borrower",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    first_name: str = Field(
        ...,
        description="Borrower's first name for display",
        examples=["Jane"],
    )
    last_name: str = Field(
        ...,
        description="Borrower's last name for display",
        examples=["Doe"],
    )
    email: str = Field(
        ...,
        description="Borrower's email address",
        examples=["jane.doe@example.com"],
    )

    model_config = {"frozen": True}


# ──────────────────────────────────────────────────────────────────────────────
# Borrower Update
# ──────────────────────────────────────────────────────────────────────────────


class BorrowerUpdate(BaseModel):
    """Request schema for updating an existing borrower profile.

    All fields are optional — only provided fields are updated.
    """

    phone: Optional[PhoneStr] = Field(
        None,
        description="Updated phone number",
        examples=["+12025559876"],
    )
    first_name: Optional[str] = Field(
        None,
        description="Updated first name",
        min_length=1,
        max_length=128,
    )
    middle_name: Optional[str] = Field(
        None,
        description="Updated middle name",
        max_length=128,
    )
    last_name: Optional[str] = Field(
        None,
        description="Updated last name",
        min_length=1,
        max_length=128,
    )
    address_line1: Optional[str] = Field(
        None,
        description="Updated street address",
        min_length=1,
        max_length=256,
    )
    address_line2: Optional[str] = Field(
        None,
        description="Updated apartment/unit",
        max_length=256,
    )
    city: Optional[str] = Field(
        None,
        description="Updated city",
        min_length=1,
        max_length=128,
    )
    state: Optional[StateStr] = Field(
        None,
        description="Updated state abbreviation",
    )
    zip_code: Optional[ZipCodeStr] = Field(
        None,
        description="Updated ZIP code",
    )
    employer: Optional[str] = Field(
        None,
        description="Updated employer name",
        max_length=256,
    )
    employment_status: Optional[str] = Field(
        None,
        description="Updated employment status",
        pattern=r"^(employed|self_employed|unemployed|retired)$",
    )
    monthly_income: Optional[Decimal] = Field(
        None,
        description="Updated monthly gross income",
        ge=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
    )

    @model_validator(mode="before")
    @classmethod
    def ensure_at_least_one_field(cls, data: Any) -> Any:
        """Ensure at least one field is provided for update."""
        if isinstance(data, dict):
            provided = {k: v for k, v in data.items() if v is not None}
            if not provided:
                raise ValueError(
                    "At least one field must be provided for update"
                )
        return data

    model_config = {
        "json_schema_extra": {
            "example": {
                "phone": "+12025559876",
                "employer": "New Corp Inc",
                "monthly_income": 6200.00,
            }
        }
    }


# ──────────────────────────────────────────────────────────────────────────────
# Borrower Response (read)
# ──────────────────────────────────────────────────────────────────────────────


class BorrowerResponse(BaseModel):
    """Public-facing borrower profile returned in API responses.

    Sensitive fields (SSN, income encrypted blob) are NEVER included.
    """

    id: str = Field(
        ...,
        description="Borrower UUID",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    email: str = Field(
        ...,
        description="Email address",
        examples=["jane.doe@example.com"],
    )
    phone: str = Field(
        ...,
        description="Phone number",
        examples=["+12025551234"],
    )
    first_name: str = Field(
        ...,
        description="Legal first name",
        examples=["Jane"],
    )
    middle_name: Optional[str] = Field(
        None,
        description="Legal middle name",
        examples=["Marie"],
    )
    last_name: str = Field(
        ...,
        description="Legal last name",
        examples=["Doe"],
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth",
        examples=["1990-01-15"],
    )
    address_line1: str = Field(
        ...,
        description="Street address",
        examples=["123 Main Street"],
    )
    address_line2: Optional[str] = Field(
        None,
        description="Apartment/unit",
        examples=["Apt 4B"],
    )
    city: str = Field(
        ...,
        description="City",
        examples=["Springfield"],
    )
    state: str = Field(
        ...,
        description="State abbreviation",
        examples=["IL"],
    )
    zip_code: str = Field(
        ...,
        description="ZIP code",
        examples=["62701"],
    )
    employer: Optional[str] = Field(
        None,
        description="Current employer",
        examples=["Acme Corp"],
    )
    employment_status: Optional[str] = Field(
        None,
        description="Employment status",
        examples=["employed"],
    )
    monthly_income: Optional[Decimal] = Field(
        None,
        description="Self-reported monthly income",
        examples=[5500.00],
    )
    is_identity_verified: bool = Field(
        ...,
        description="Whether identity has been verified through KYC",
    )
    kyc_completed_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp when KYC was completed",
    )
    credit_score_range: Optional[str] = Field(
        None,
        description="Credit score range from latest pull",
        examples=["660-719"],
    )
    credit_tier: Optional[str] = Field(
        None,
        description="Credit tier classification",
        examples=["near_prime"],
    )
    is_active: bool = Field(
        ...,
        description="Whether the borrower account is active",
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp of account creation",
    )
    updated_at: datetime = Field(
        ...,
        description="UTC timestamp of last update",
    )

    model_config = {"frozen": True, "from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Pre-Qualification
# ──────────────────────────────────────────────────────────────────────────────


class BorrowerPreQualificationRequest(BaseModel):
    """Request schema for soft-pull pre-qualification.

    Borrower provides basic information for a soft credit check
    that determines preliminary loan eligibility without impacting
    their credit score.
    """

    first_name: str = Field(
        ...,
        description="First name",
        min_length=1,
        max_length=128,
        examples=["Jane"],
    )
    last_name: str = Field(
        ...,
        description="Last name",
        min_length=1,
        max_length=128,
        examples=["Doe"],
    )
    email: EmailStr = Field(
        ...,
        description="Email address",
        max_length=320,
        examples=["jane.doe@example.com"],
    )
    phone: PhoneStr = Field(
        ...,
        description="Phone number",
        examples=["+12025551234"],
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth",
        examples=["1990-01-15"],
    )
    ssn_last4: Annotated[
        str,
        StringConstraints(
            min_length=4,
            max_length=4,
            pattern=r"^\d{4}$",
        ),
    ] = Field(
        ...,
        description="Last 4 digits of SSN (for credit bureau matching)",
        examples=["6789"],
    )
    zip_code: ZipCodeStr = Field(
        ...,
        description="ZIP code for location-based underwriting factors",
        examples=["62701"],
    )
    requested_amount: Decimal = Field(
        ...,
        description="Desired loan amount",
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        examples=[10000.00],
    )
    requested_term_months: int = Field(
        ...,
        description="Desired loan term in months",
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
    monthly_income: Optional[Decimal] = Field(
        None,
        description="Self-reported monthly gross income",
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        examples=[5500.00],
    )

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v: date) -> date:
        today = date.today()
        age = (
            today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        )
        if age < 18:
            raise ValueError("Must be at least 18 years old")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
                "phone": "+12025551234",
                "date_of_birth": "1990-01-15",
                "ssn_last4": "6789",
                "zip_code": "62701",
                "requested_amount": 10000.00,
                "requested_term_months": 36,
                "loan_purpose": "debt_consolidation",
                "monthly_income": 5500.00,
            }
        }
    }


class BorrowerPreQualificationResponse(BaseModel):
    """Response returned after soft-pull pre-qualification is evaluated."""

    pre_qualified: bool = Field(
        ...,
        description="Whether the borrower pre-qualifies for a loan",
    )
    message: str = Field(
        ...,
        description="Human-readable result summary",
        examples=["Congratulations! You pre-qualify for a loan up to $15,000."],
    )
    pre_approved_amount_min: Optional[Decimal] = Field(
        None,
        description="Minimum loan amount available",
        max_digits=12,
        decimal_places=2,
    )
    pre_approved_amount_max: Optional[Decimal] = Field(
        None,
        description="Maximum loan amount available",
        max_digits=12,
        decimal_places=2,
    )
    apr_range_min: Optional[Decimal] = Field(
        None,
        description="Minimum estimated APR (as a percentage, e.g. 6.99 for 6.99%)",
        max_digits=5,
        decimal_places=3,
    )
    apr_range_max: Optional[Decimal] = Field(
        None,
        description="Maximum estimated APR (as a percentage)",
        max_digits=5,
        decimal_places=3,
    )
    available_terms_months: Optional[list[int]] = Field(
        None,
        description="Available repayment terms in months",
        examples=[[12, 24, 36, 48]],
    )
    estimated_monthly_payment: Optional[Decimal] = Field(
        None,
        description="Estimated monthly payment for the requested amount",
        max_digits=12,
        decimal_places=2,
    )
    credit_tier: Optional[str] = Field(
        None,
        description="Pre-qualification credit tier",
        examples=["prime", "near_prime", "subprime"],
    )
    decision_factors: Optional[dict[str, Any]] = Field(
        None,
        description="Key factors influencing the pre-qualification decision",
        examples={"income_stability": "positive", "debt_to_income": "borderline"},
    )
    pre_qualification_id: Optional[str] = Field(
        None,
        description="UUID of the pre-qualification record for reference",
        examples=["b2c3d4e5-f6a7-8901-bcde-f12345678901"],
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp when the pre-qualification offer expires",
    )

    model_config = {
        "frozen": True,
        "json_schema_extra": {
            "example": {
                "pre_qualified": True,
                "message": "Congratulations! You pre-qualify for a loan up to $15,000.",
                "pre_approved_amount_min": 2000.00,
                "pre_approved_amount_max": 15000.00,
                "apr_range_min": 6.990,
                "apr_range_max": 18.990,
                "available_terms_months": [12, 24, 36, 48],
                "estimated_monthly_payment": 308.67,
                "credit_tier": "prime",
                "decision_factors": {
                    "income_stability": "positive",
                    "debt_to_income": "positive",
                    "credit_history_length": "positive",
                },
                "pre_qualification_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "expires_at": "2026-06-11T13:57:00Z",
            }
        },
    }
