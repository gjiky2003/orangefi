"""
OrangeFi Integration Schemas
=============================
Pydantic v2 request/response schemas for Plaid and Stripe integration
endpoints.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Plaid Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class PlaidLinkTokenRequest(BaseModel):
    """Request body for creating a Plaid Link token."""

    borrower_id: UUID = Field(
        ...,
        description="UUID of the borrower creating the Link",
    )
    redirect_uri: Optional[str] = Field(
        None,
        description="Optional OAuth redirect URI for mobile/web login flows",
        max_length=2048,
    )

    model_config = {"json_schema_extra": {"example": {"borrower_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "redirect_uri": "https://app.orangefi.com/plaid-oauth"}}}


class PlaidLinkTokenResponse(BaseModel):
    """Response containing a Plaid Link token."""

    link_token: str = Field(
        ...,
        description="Plaid Link token for initializing Plaid Link on the frontend",
    )
    expiration: str = Field(
        ...,
        description="ISO 8601 datetime when the link token expires",
    )

    model_config = {"json_schema_extra": {"example": {"link_token": "link-sandbox-abc123", "expiration": "2026-05-12T02:00:00Z"}}}


class PlaidPublicTokenExchangeRequest(BaseModel):
    """Request body for exchanging a Plaid public token."""

    public_token: str = Field(
        ...,
        description="Public token returned by Plaid Link after successful connection",
        min_length=1,
    )
    borrower_id: UUID = Field(
        ...,
        description="UUID of the borrower connecting their bank account",
    )
    institution_id: Optional[str] = Field(
        None,
        description="Plaid institution ID",
    )
    institution_name: Optional[str] = Field(
        None,
        description="Human-readable institution name",
        max_length=256,
    )

    model_config = {"json_schema_extra": {"example": {"public_token": "public-sandbox-abc123", "borrower_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "institution_id": "ins_123456", "institution_name": "Chase Bank"}}}


class PlaidAccountsResponse(BaseModel):
    """Response containing linked bank accounts from Plaid."""

    accounts: list[dict[str, Any]] = Field(
        ...,
        description="List of bank account objects with balances, types, and metadata",
    )

    model_config = {"json_schema_extra": {"example": {"accounts": [{"account_id": "abc123", "name": "Checking", "balances": {"current": 1500.00, "available": 1420.50}, "type": "depository", "subtype": "checking", "mask": "1234"}]}}}


class PlaidTransactionsResponse(BaseModel):
    """Response containing transactions from linked accounts."""

    transactions: list[dict[str, Any]] = Field(
        ...,
        description="List of transaction objects with amounts, dates, and categories",
    )
    total_transactions: int = Field(
        ...,
        ge=0,
        description="Total number of transactions returned",
    )

    model_config = {"json_schema_extra": {"example": {"transactions": [{"transaction_id": "txn_abc123", "amount": 89.50, "date": "2026-05-09", "name": "Whole Foods Market", "category": ["Food and Drink", "Groceries"]}], "total_transactions": 1}}}


# ═══════════════════════════════════════════════════════════════════════════════
# Stripe Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class StripePaymentIntentRequest(BaseModel):
    """Request body for creating a Stripe PaymentIntent."""

    loan_id: UUID = Field(
        ...,
        description="UUID of the loan being paid",
    )
    amount: Decimal = Field(
        ...,
        gt=Decimal("0.00"),
        le=Decimal("999999.99"),
        description="Payment amount in dollars (e.g. 250.00)",
    )
    currency: str = Field(
        default="usd",
        description="ISO 4217 currency code",
        max_length=3,
        min_length=3,
    )
    payment_method_id: Optional[str] = Field(
        None,
        description="Optional pre-existing Stripe PaymentMethod ID to use",
    )
    description: Optional[str] = Field(
        None,
        description="Optional description for the payment",
        max_length=256,
    )

    @field_validator("currency")
    @classmethod
    def currency_must_be_lowercase(cls, v: str) -> str:
        return v.lower()

    model_config = {"json_schema_extra": {"example": {"loan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "amount": 350.00, "currency": "usd"}}}


class StripePaymentIntentResponse(BaseModel):
    """Response containing a Stripe PaymentIntent client secret."""

    client_secret: str = Field(
        ...,
        description="Stripe PaymentIntent client secret for frontend confirmation",
    )
    intent_id: str = Field(
        ...,
        description="Stripe PaymentIntent ID (pi_...)",
    )
    amount: int = Field(
        ...,
        description="Amount in cents",
    )
    status: str = Field(
        ...,
        description="Current status of the payment intent",
    )

    model_config = {"json_schema_extra": {"example": {"client_secret": "pi_abc123_secret_xyz", "intent_id": "pi_abc123", "amount": 35000, "status": "requires_payment_method"}}}


class StripeConfirmPaymentRequest(BaseModel):
    """Request body for confirming a PaymentIntent."""

    intent_id: str = Field(
        ...,
        description="Stripe PaymentIntent ID to confirm",
    )
    payment_method_id: Optional[str] = Field(
        None,
        description="Optional PaymentMethod ID to use for confirmation",
    )

    model_config = {"json_schema_extra": {"example": {"intent_id": "pi_abc123", "payment_method_id": "pm_xyz789"}}}


class StripeDisburseRequest(BaseModel):
    """Request body for loan fund disbursement."""

    loan_id: UUID = Field(
        ...,
        description="UUID of the loan to fund",
    )
    amount: Decimal = Field(
        ...,
        gt=Decimal("0.00"),
        le=Decimal("999999.99"),
        description="Disbursement amount in dollars",
    )
    destination_bank_account: str = Field(
        ...,
        description="Stripe account ID (acct_...) or external bank account token",
        min_length=1,
    )
    description: Optional[str] = Field(
        None,
        description="Optional description for the disbursement",
        max_length=256,
    )

    model_config = {"json_schema_extra": {"example": {"loan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "amount": 10000.00, "destination_bank_account": "acct_abc123", "description": "Loan funding disbursement"}}}


class StripeDisburseResponse(BaseModel):
    """Response containing disbursement result."""

    transfer_id: str = Field(
        ...,
        description="Stripe transfer or payout ID",
    )
    amount: int = Field(
        ...,
        description="Amount in cents",
    )
    status: str = Field(
        ...,
        description="Status of the disbursement (paid, pending, failed)",
    )
    destination: str = Field(
        ...,
        description="Destination account ID",
    )

    model_config = {"json_schema_extra": {"example": {"transfer_id": "tr_abc123", "amount": 1000000, "status": "paid", "destination": "acct_abc123"}}}


class StripeCreateCustomerRequest(BaseModel):
    """Request body for creating a Stripe Customer."""

    borrower_id: UUID = Field(
        ...,
        description="UUID of the borrower",
    )
    email: str = Field(
        ...,
        description="Borrower email address",
    )
    name: str = Field(
        ...,
        description="Borrower full name",
        max_length=256,
    )
    phone: Optional[str] = Field(
        None,
        description="Borrower phone number",
    )

    model_config = {"json_schema_extra": {"example": {"borrower_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "email": "jane@example.com", "name": "Jane Doe", "phone": "+12025551234"}}}


# ═══════════════════════════════════════════════════════════════════════════════
# General Integration Schemas
# ═══════════════════════════════════════════════════════════════════════════════


class BankConnectResponse(BaseModel):
    """Response after connecting a bank account."""

    success: bool = Field(
        ...,
        description="Whether the connection was successful",
    )
    message: str = Field(
        ...,
        description="Human-readable result message",
    )
    connection_id: Optional[str] = Field(
        None,
        description="Plaid item ID or internal connection reference",
    )
    accounts_linked: int = Field(
        default=0,
        ge=0,
        description="Number of bank accounts linked",
    )

    model_config = {"json_schema_extra": {"example": {"success": True, "message": "Bank account connected successfully", "connection_id": "item_abc123", "accounts_linked": 2}}}


class IntegrationStatusResponse(BaseModel):
    """Response indicating which integrations are configured."""

    plaid_configured: bool = Field(
        ...,
        description="Whether Plaid is configured with valid credentials",
    )
    stripe_configured: bool = Field(
        ...,
        description="Whether Stripe is configured with a valid secret key",
    )
    plaid_env: Optional[str] = Field(
        None,
        description="Plaid environment (sandbox, development, production)",
    )

    model_config = {"json_schema_extra": {"example": {"plaid_configured": True, "stripe_configured": True, "plaid_env": "sandbox"}}}


class IntegrationHealthResponse(BaseModel):
    """Detailed health status for each integration."""

    plaid: dict[str, Any] = Field(
        ...,
        description="Plaid service health details",
    )
    stripe: dict[str, Any] = Field(
        ...,
        description="Stripe service health details",
    )

    model_config = {"json_schema_extra": {"example": {"plaid": {"configured": True, "environment": "sandbox", "reachable": True}, "stripe": {"configured": True, "reachable": True}}}}
