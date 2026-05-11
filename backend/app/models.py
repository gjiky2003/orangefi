"""
OrangeFi Lending Platform — SQLAlchemy 2.0 Data Models
=======================================================

All models use SQLAlchemy 2.0 style with Mapped annotations and full async
support via asyncpg. Status enums, JSON flexible columns, foreign keys,
relationships, and indexes are defined per model.

Base class is imported from app.database (DeclarativeBase).
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════


class ApplicationStatus(str, enum.Enum):
    draft = "draft"
    prequal_submitted = "prequal_submitted"
    prequal_completed = "prequal_completed"
    application_started = "application_started"
    submitted = "submitted"
    processing = "processing"
    manual_review = "manual_review"
    approved = "approved"
    declined = "declined"
    docs_sent = "docs_sent"
    funded = "funded"
    cancelled = "cancelled"


class LoanStatus(str, enum.Enum):
    pending_disbursement = "pending_disbursement"
    active = "active"
    delinquent = "delinquent"
    charged_off = "charged_off"
    paid_off = "paid_off"


class PaymentStatus(str, enum.Enum):
    scheduled = "scheduled"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"
    refunded = "refunded"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    uploaded = "uploaded"
    processing_ocr = "processing_ocr"
    verified = "verified"
    rejected = "rejected"


class DocumentType(str, enum.Enum):
    paystub = "paystub"
    tax_return = "tax_return"
    bank_statement = "bank_statement"
    government_id = "government_id"
    proof_of_address = "proof_of_address"
    credit_report = "credit_report"
    consolidation_payoff = "consolidation_payoff"
    other = "other"


class AdminRole(str, enum.Enum):
    super_admin = "super_admin"
    underwriter = "underwriter"
    collections = "collections"
    compliance = "compliance"
    support = "support"
    viewer = "viewer"


class AuditAction(str, enum.Enum):
    application_created = "application_created"
    application_updated = "application_updated"
    application_submitted = "application_submitted"
    decision_made = "decision_made"
    loan_funded = "loan_funded"
    payment_received = "payment_received"
    payment_failed = "payment_failed"
    user_registered = "user_registered"
    user_login = "user_login"
    user_logout = "user_logout"
    document_uploaded = "document_uploaded"
    document_verified = "document_verified"
    credit_pull_soft = "credit_pull_soft"
    credit_pull_hard = "credit_pull_hard"
    bank_account_linked = "bank_account_linked"
    bank_account_unlinked = "bank_account_unlinked"
    adverse_action_sent = "adverse_action_sent"
    compliance_review = "compliance_review"
    admin_login = "admin_login"
    admin_action = "admin_action"
    system_error = "system_error"


class CreditPullType(str, enum.Enum):
    soft = "soft"
    hard = "hard"


class PlaidConnectionStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    revoked = "revoked"


class UnderwritingDecision(str, enum.Enum):
    approved = "approved"
    declined = "declined"
    manual_review = "manual_review"
    pending = "pending"


class ComplianceEventType(str, enum.Enum):
    adverse_action = "adverse_action"
    fair_lending_review = "fair_lending_review"
    regulatory_report = "regulatory_report"
    ecoa_notice = "ecoa_notice"
    fcra_dispute = "fcra_dispute"
    tila_disclosure = "tila_disclosure"
    internal_review = "internal_review"


# ═══════════════════════════════════════════════════════════════════════════════
# Mixins
# ═══════════════════════════════════════════════════════════════════════════════


class TimestampMixin:
    """Adds created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """UUID primary key with server-side default."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Borrower (Customer)
# ═══════════════════════════════════════════════════════════════════════════════


class Borrower(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "borrowers"

    # ── Identity & Contact ──
    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    # ── Authentication ──
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, default=None
    )
    login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Encrypted PII (AES-256 at application level) ──
    ssn_encrypted: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary, nullable=True
    )
    income_encrypted: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary, nullable=True
    )

    # ── Address ──
    address_line1: Mapped[str] = mapped_column(String(256), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)

    # ── Employment ──
    employer: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    employment_status: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # employed, self_employed, unemployed, retired
    monthly_income: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # ── KYC / Onboarding Status ──
    is_identity_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    kyc_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    agreed_to_tos_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    agreed_to_privacy_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Credit Profile Snapshot ──
    credit_score_range: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True
    )  # e.g. "660-719"
    credit_tier: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True
    )  # prime, near_prime, subprime

    # ── Flags ──
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="borrower", lazy="selectin"
    )
    loans: Mapped[list["Loan"]] = relationship(
        "Loan", back_populates="borrower", lazy="selectin"
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="borrower", lazy="selectin"
    )
    credit_pulls: Mapped[list["CreditPull"]] = relationship(
        "CreditPull", back_populates="borrower", lazy="selectin"
    )
    plaid_connections: Mapped[list["PlaidConnection"]] = relationship(
        "PlaidConnection", back_populates="borrower", lazy="selectin"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="borrower", lazy="selectin"
    )
    underwriting_results: Mapped[list["UnderwritingResult"]] = relationship(
        "UnderwritingResult", back_populates="borrower", lazy="selectin"
    )
    compliance_events: Mapped[list["ComplianceEvent"]] = relationship(
        "ComplianceEvent", back_populates="borrower", lazy="selectin"
    )

    # ── Indexes ──
    __table_args__ = (
        Index("ix_borrowers_name", "last_name", "first_name"),
        Index("ix_borrowers_active", "is_active", "is_deleted"),
    )

    def __repr__(self) -> str:
        return f"<Borrower {self.id} {self.first_name} {self.last_name}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Application (Loan Application)
# ═══════════════════════════════════════════════════════════════════════════════


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    # ── Foreign Keys ──
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("borrowers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Status ──
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status_enum"),
        default=ApplicationStatus.draft,
        nullable=False,
        index=True,
    )

    # ── Loan Request ──
    requested_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    requested_term_months: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 12, 24, 36, 48, 60
    loan_purpose: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # debt_consolidation, home_improvement, etc.
    loan_purpose_details: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # ── Debt Consolidation Details ──
    total_existing_debt: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    creditor_details: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # [{name, balance, apr, min_payment}, ...]
    monthly_debt_payments: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # ── Employment / Income at Application Time ──
    application_monthly_income: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    application_employer: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )
    application_employment_status: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    years_at_current_job: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 1), nullable=True
    )

    # ── Housing ──
    housing_status: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )  # own, rent, live_with_family
    monthly_housing_payment: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # ── Application Metadata ──
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    application_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # any extra form/analytics data

    # ── Decision Info ──
    decisioned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decisioned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # admin_user.id who made the decision
    declined_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # human-readable decline reason
    declined_reason_codes: Mapped[Optional[list[str]]] = mapped_column(
        JSONB, nullable=True
    )  # machine-readable adverse action codes

    # ── Funding ──
    amount_funded: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    funded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──
    borrower: Mapped["Borrower"] = relationship(
        "Borrower", back_populates="applications"
    )
    loan: Mapped[Optional["Loan"]] = relationship(
        "Loan", back_populates="application", uselist=False, lazy="selectin"
    )
    credit_pulls: Mapped[list["CreditPull"]] = relationship(
        "CreditPull", back_populates="application", lazy="selectin"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="application", lazy="selectin"
    )
    underwriting_result: Mapped[Optional["UnderwritingResult"]] = relationship(
        "UnderwritingResult",
        back_populates="application",
        uselist=False,
        lazy="selectin",
    )
    compliance_events: Mapped[list["ComplianceEvent"]] = relationship(
        "ComplianceEvent", back_populates="application", lazy="selectin"
    )

    # ── Indexes ──
    __table_args__ = (
        Index("ix_applications_borrower_status", "borrower_id", "status"),
        Index("ix_applications_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Application {self.id} [{self.status.value}] ${self.requested_amount:.2f}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Loan (Originated Loan)
# ═══════════════════════════════════════════════════════════════════════════════


class Loan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "loans"

    # ── Foreign Keys ──
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("borrowers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ── Status ──
    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus, name="loan_status_enum"),
        default=LoanStatus.pending_disbursement,
        nullable=False,
        index=True,
    )

    # ── Loan Terms ──
    loan_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    apr: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_payment: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    origination_fee: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    disbursement_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )  # loan_amount - origination_fee

    # ── Interest ──
    interest_rate_type: Mapped[str] = mapped_column(
        String(16), default="fixed", nullable=False
    )  # fixed, variable
    interest_accrued: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    last_interest_calc_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Dates ──
    origination_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    first_payment_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    maturity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    paid_off_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Funding Details ──
    funding_account_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    funding_reference: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )
    funding_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # ── Delinquency ──
    days_past_due: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delinquency_started_at: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    total_amount_due: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    collections_status: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    charge_off_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # ── Relationships ──
    application: Mapped["Application"] = relationship(
        "Application", back_populates="loan"
    )
    borrower: Mapped["Borrower"] = relationship("Borrower", back_populates="loans")
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="loan", lazy="selectin"
    )

    # ── Indexes ──
    __table_args__ = (
        Index("ix_loans_borrower_status", "borrower_id", "status"),
        Index("ix_loans_status_dpd", "status", "days_past_due"),
    )

    def __repr__(self) -> str:
        return (
            f"<Loan {self.id} [{self.status.value}] "
            f"${self.loan_amount:.2f} @ {self.apr:.2f}%>"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Payment (Schedule & History)
# ═══════════════════════════════════════════════════════════════════════════════


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    # ── Foreign Keys ──
    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("borrowers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Status & Schedule ──
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        default=PaymentStatus.scheduled,
        nullable=False,
        index=True,
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    paid_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # ── Amounts ──
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    interest_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    fees_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    late_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    amount_paid: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # ── Payment Method ──
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )  # ach, debit_card, wire, check, internal
    payment_source: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )  # plaid account ID, card last 4, etc.

    # ── External References ──
    external_reference: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )  # Stripe payment intent ID, ACH ref, etc.
    external_status: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Payment Number (for amortization schedule) ──
    payment_number: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )

    # ── Relationships ──
    loan: Mapped["Loan"] = relationship("Loan", back_populates="payments")
    borrower: Mapped["Borrower"] = relationship(
        "Borrower", back_populates="payments"
    )

    # ── Indexes ──
    __table_args__ = (
        Index("ix_payments_loan_scheduled", "loan_id", "scheduled_date"),
        Index("ix_payments_loan_number", "loan_id", "payment_number", unique=True),
        Index("ix_payments_status_due", "status", "scheduled_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<Payment #{self.payment_number} [{self.status.value}] "
            f"${self.total_amount:.2f} due {self.scheduled_date}>"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CreditPull (Soft & Hard Credit Inquiries)
# ═══════════════════════════════════════════════════════════════════════════════


class CreditPull(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "credit_pulls"

    # ── Foreign Keys ──
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("borrowers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Pull Type ──
    pull_type: Mapped[CreditPullType] = mapped_column(
        Enum(CreditPullType, name="credit_pull_type_enum"),
        nullable=False,
        index=True,
    )

    # ── Bureau Details ──
    bureau_name: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # experian, transunion, equifax, mock
    bureau_reference: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )  # external reference ID from bureau

    # ── Credit Data ──
    credit_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # VantageScore or FICO
    credit_score_model: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )  # vantagescore_4.0, fico_8, etc.
    credit_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # full report data (tradelines, inquiries, etc.)
    credit_summary: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # computed: DTI, utilization, etc.

    # ── Consent ──
    consent_received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    consent_ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )

    # ── Compliance ──
    adverse_action_notice_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    disclosure_provided: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Relationships ──
    borrower: Mapped["Borrower"] = relationship(
        "Borrower", back_populates="credit_pulls"
    )
    application: Mapped[Optional["Application"]] = relationship(
        "Application", back_populates="credit_pulls"
    )

    # ── Indexes ──
    __table_args__ = (
        Index("ix_credit_pulls_borrower_type", "borrower_id", "pull_type"),
        Index("ix_credit_pulls_created", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<CreditPull {self.pull_type.value} "
            f"score={self.credit_score} bureau={self.bureau_name}>"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PlaidConnection (Bank Account Links)
# ═══════════════════════════════════════════════════════════════════════════════


class PlaidConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plaid_connections"

    # ── Foreign Keys ──
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("borrowers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Plaid Tokens ──
    plaid_access_token: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False
    )  # AES-256 encrypted
    plaid_item_id: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    plaid_institution_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )

    # ── Account Details ──
    institution_name: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    account_name: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    account_mask: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True
    )  # last 4 digits
    account_type: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )  # depository, credit, loan, investment
    account_subtype: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )  # checking, savings, etc.

    # ── Status ──
    status: Mapped[PlaidConnectionStatus] = mapped_column(
        Enum(PlaidConnectionStatus, name="plaid_connection_status_enum"),
        default=PlaidConnectionStatus.active,
        nullable=False,
        index=True,
    )

    # ── Sync ──
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_transactions_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    transactions_cursor: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )

    # ── Account Data Snapshot ──
    account_balances: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # {current, available, limit}
    account_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # ── Error Tracking ──
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Relationships ──
    borrower: Mapped["Borrower"] = relationship(
        "Borrower", back_populates="plaid_connections"
    )

    __table_args__ = (
        Index(
            "ix_plaid_connections_borrower_status",
            "borrower_id",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<PlaidConnection {self.plaid_item_id} "
            f"[{self.status.value}] {self.institution_name}>"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Document (Uploaded Documents with OCR)
# ═══════════════════════════════════════════════════════════════════════════════


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    # ── Foreign Keys ──
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("borrowers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Status ──
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status_enum"),
        default=DocumentStatus.pending,
        nullable=False,
        index=True,
    )

    # ── Document Type ──
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type_enum"),
        nullable=False,
        index=True,
    )

    # ── File Details ──
    file_key: Mapped[str] = mapped_column(
        String(512), nullable=False
    )  # S3/MinIO object key
    file_bucket: Mapped[str] = mapped_column(
        String(128), nullable=False
    )  # S3 bucket name
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )  # SHA-256 for integrity

    # ── OCR / Content Extraction ──
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    ocr_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extracted_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # structured data from OCR: income, employer, etc.

    # ── Verification ──
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # admin_user.id
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Retention ──
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──
    borrower: Mapped["Borrower"] = relationship(
        "Borrower", back_populates="documents"
    )
    application: Mapped[Optional["Application"]] = relationship(
        "Application", back_populates="documents"
    )

    # ── Indexes ──
    __table_args__ = (
        Index(
            "ix_documents_borrower_type_status",
            "borrower_id",
            "document_type",
            "status",
        ),
        Index("ix_documents_application_status", "application_id", "status"),
        Index("ix_documents_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Document {self.document_type.value} [{self.status.value}] "
            f"{self.file_name}>"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# UnderwritingResult (AI Score, Tier, APR)
# ═══════════════════════════════════════════════════════════════════════════════


class UnderwritingResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "underwriting_results"

    # ── Foreign Keys ──
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("borrowers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── AI Score & Tier ──
    ai_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # 0.0 - 1.0
    ai_tier: Mapped[Optional[str]] = mapped_column(
        String(4), nullable=True
    )  # A+, A, B, C, D, F
    ai_confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # model confidence 0.0 - 1.0

    # ── Decision ──
    decision: Mapped[UnderwritingDecision] = mapped_column(
        Enum(UnderwritingDecision, name="underwriting_decision_enum"),
        default=UnderwritingDecision.pending,
        nullable=False,
        index=True,
    )
    decision_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    decision_factors: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # feature importance / SHAP values

    # ── Loan Terms Offered ──
    approved_amount_min: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    approved_amount_max: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    approved_apr_min: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 3), nullable=True
    )
    approved_apr_max: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 3), nullable=True
    )
    approved_term_months: Mapped[Optional[list[int]]] = mapped_column(
        JSONB, nullable=True
    )  # [12, 24, 36]

    # ── Feature Flags ──
    feature_flags: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # {auto_pay_discount: true, rate_lower_available: true}
    offer_terms: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # full term sheet offered

    # ── Model Metadata ──
    model_version: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    model_name: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    inference_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    model_input_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # features used for this inference

    # ── Override Info (if manually overridden) ──
    overridden_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # admin_user.id
    overridden_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    override_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # ── Relationships ──
    application: Mapped["Application"] = relationship(
        "Application", back_populates="underwriting_result"
    )
    borrower: Mapped["Borrower"] = relationship(
        "Borrower", back_populates="underwriting_results"
    )

    __table_args__ = (
        Index("ix_underwriting_borrower_decision", "borrower_id", "decision"),
        Index("ix_underwriting_decision_created", "decision", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<UnderwritingResult app={self.application_id} "
            f"score={self.ai_score} tier={self.ai_tier} "
            f"decision={self.decision.value}>"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AdminUser (Backoffice Accounts)
# ═══════════════════════════════════════════════════════════════════════════════


class AdminUser(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "admin_users"

    # ── Identity ──
    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)

    # ── Auth ──
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)

    # ── Role ──
    role: Mapped[AdminRole] = mapped_column(
        Enum(AdminRole, name="admin_role_enum"),
        default=AdminRole.viewer,
        nullable=False,
        index=True,
    )

    # ── MFA ──
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # TOTP secret
    mfa_backup_codes: Mapped[Optional[list[str]]] = mapped_column(
        JSONB, nullable=True
    )
    mfa_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Status ──
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_locked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # ── Session ──
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    current_session_token: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )

    # ── Permissions ──
    permissions: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # granular permissions override if needed

    # ── Relationships ──
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="admin_user",
        foreign_keys="AuditLog.admin_user_id",
        lazy="selectin",
    )

    # ── Indexes ──
    __table_args__ = (
        Index("ix_admin_users_role_active", "role", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<AdminUser {self.email} [{self.role.value}]>"


# ═══════════════════════════════════════════════════════════════════════════════
# AuditLog (Immutable Audit Trail)
# ═══════════════════════════════════════════════════════════════════════════════


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """
    Immutable audit trail for all compliance-relevant actions.

    NOTE: This model intentionally does NOT include updated_at — audit logs
    must never be modified after creation.
    """

    __tablename__ = "audit_logs"

    # ── Timestamp (immutable — only created_at) ──
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # ── Actor ──
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    actor_type: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )  # "borrower", "admin", "system"

    # ── For admin-specific actions ──
    admin_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Action ──
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action_enum"),
        nullable=False,
        index=True,
    )

    # ── Resource ──
    resource_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # "application", "loan", "borrower", etc.
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )

    # ── Details ──
    details: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # arbitrary structured context
    changes: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # before/after diff for updates
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # human-readable summary

    # ── Environment ──
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )  # correlation ID for tracing

    # ── Severity ──
    severity: Mapped[str] = mapped_column(
        String(16), default="info", nullable=False
    )  # info, warning, error, critical

    # ── Relationships ──
    admin_user: Mapped[Optional["AdminUser"]] = relationship(
        "AdminUser",
        back_populates="audit_logs",
        foreign_keys=[admin_user_id],
    )

    # ── Indexes ──
    __table_args__ = (
        Index(
            "ix_audit_logs_actor_action",
            "actor_id",
            "actor_type",
            "action",
        ),
        Index(
            "ix_audit_logs_resource",
            "resource_type",
            "resource_id",
        ),
        Index("ix_audit_logs_created_action", "created_at", "action"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog {self.action.value} on "
            f"{self.resource_type}#{self.resource_id}>"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ComplianceEvent (Fair Lending, Adverse Actions)
# ═══════════════════════════════════════════════════════════════════════════════


class ComplianceEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "compliance_events"

    # ── Foreign Keys ──
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("borrowers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credit_pull_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("credit_pulls.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Event Type ──
    event_type: Mapped[ComplianceEventType] = mapped_column(
        Enum(ComplianceEventType, name="compliance_event_type_enum"),
        nullable=False,
        index=True,
    )

    # ── Status ──
    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, sent, acknowledged, resolved, escalated

    # ── Adverse Action / ECOA Details ──
    reason_codes: Mapped[Optional[list[str]]] = mapped_column(
        JSONB, nullable=True
    )  # ECOA adverse action reason codes
    reason_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # plain-language explanation
    action_taken: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # approved, declined, counteroffer, withdrawn

    # ── Notice Delivery ──
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_via: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )  # email, mail, portal, sms
    sent_to_address: Mapped[Optional[str]] = mapped_column(
        String(320), nullable=True
    )  # email or mailing address
    delivery_status: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )  # delivered, bounced, failed, pending
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Response Tracking ──
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    dispute_filed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    dispute_resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Regulatory Metadata ──
    regulatory_reference: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )  # CFPB complaint ID, exam reference, etc.
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # extensible metadata

    # ── Relationships ──
    application: Mapped[Optional["Application"]] = relationship(
        "Application", back_populates="compliance_events"
    )
    borrower: Mapped["Borrower"] = relationship(
        "Borrower", back_populates="compliance_events"
    )
    credit_pull: Mapped[Optional["CreditPull"]] = relationship(
        "CreditPull"
    )

    # ── Indexes ──
    __table_args__ = (
        Index(
            "ix_compliance_events_borrower_type",
            "borrower_id",
            "event_type",
        ),
        Index(
            "ix_compliance_events_application_type",
            "application_id",
            "event_type",
        ),
        Index(
            "ix_compliance_events_type_status",
            "event_type",
            "status",
        ),
        Index("ix_compliance_events_created", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ComplianceEvent {self.event_type.value} "
            f"[{self.status}] app={self.application_id}>"
        )
