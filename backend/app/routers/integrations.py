"""
OrangeFi Integrations Router
=============================
API endpoints for Plaid bank linking, Stripe payments, webhooks, and
integration status/health checks.

All responses use the standard format::
    {"success": true, "data": {...}}
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Borrower, Loan, Payment, PaymentStatus, PlaidConnection, PlaidConnectionStatus
from app.schemas.integrations import (
    BankConnectResponse,
    IntegrationHealthResponse,
    IntegrationStatusResponse,
    PlaidAccountsResponse,
    PlaidLinkTokenRequest,
    PlaidLinkTokenResponse,
    PlaidPublicTokenExchangeRequest,
    PlaidTransactionsResponse,
    StripeConfirmPaymentRequest,
    StripeCreateCustomerRequest,
    StripeDisburseRequest,
    StripeDisburseResponse,
    StripePaymentIntentRequest,
    StripePaymentIntentResponse,
)
from app.services.plaid_service import PlaidService
from app.services.stripe_service import StripeService
from app.utils.dependencies import get_current_borrower, get_current_admin
from app.utils.audit import create_audit_log
from app.models import AuditAction

logger = logging.getLogger("orangefi.routers.integrations")

# ──────────────────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────────────────

integrations_router = APIRouter(prefix="/integrations", tags=["integrations"])

# ── Service instances ──

plaid = PlaidService()
stripe = StripeService()


# ═══════════════════════════════════════════════════════════════════════════════
# Plaid Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@integrations_router.post(
    "/plaid/link-token",
    response_model=None,
    summary="Create Plaid Link token",
    description="Generate a Plaid Link token for the authenticated borrower to connect their bank account.",
)
async def create_plaid_link_token(
    body: PlaidLinkTokenRequest,
    borrower: Borrower = Depends(get_current_borrower),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Create a Plaid Link token for the borrower's session."""
    # Verify the borrower matches
    if body.borrower_id != borrower.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Borrower ID mismatch",
        )

    user_data = {
        "legal_name": f"{borrower.first_name} {borrower.last_name}",
        "email_address": borrower.email,
        "phone_number": borrower.phone,
    }

    result = await plaid.create_link_token(
        borrower_id=str(borrower.id),
        user_data=user_data,
    )

    await create_audit_log(
        db=db,
        action=AuditAction.bank_account_linked,
        borrower_id=borrower.id,
        detail=f"Plaid Link token created",
        metadata={"env": settings.PLAID_ENV},
    )

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "link_token": result.get("link_token", ""),
                "expiration": result.get("expiration", ""),
            },
        }
    )


@integrations_router.post(
    "/plaid/exchange",
    response_model=None,
    summary="Exchange Plaid public token",
    description="Exchange the public token from Plaid Link for an access token and store the connection.",
)
async def exchange_plaid_token(
    body: PlaidPublicTokenExchangeRequest,
    borrower: Borrower = Depends(get_current_borrower),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Exchange public token, retrieve accounts, and store the connection."""
    if body.borrower_id != borrower.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Borrower ID mismatch",
        )

    # Exchange the public token
    connection_data = await plaid.exchange_token_and_store(
        public_token=body.public_token,
        borrower_id=str(borrower.id),
        institution_id=body.institution_id,
        institution_name=body.institution_name,
    )

    access_token = connection_data["access_token"]
    item_id = connection_data["item_id"]
    accounts = connection_data.get("accounts", [])

    if not accounts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No accounts found for this Plaid connection",
        )

    # Store the first account info in PlaidConnection model
    primary_account = accounts[0]
    plaid_conn = PlaidConnection(
        borrower_id=borrower.id,
        plaid_access_token=access_token.encode("utf-8"),  # In production, encrypt with AES-256
        plaid_item_id=item_id,
        plaid_institution_id=body.institution_id,
        institution_name=body.institution_name or primary_account.get("name", ""),
        account_name=primary_account.get("name", ""),
        account_mask=primary_account.get("mask", ""),
        account_type=primary_account.get("type", ""),
        account_subtype=primary_account.get("subtype", ""),
        status=PlaidConnectionStatus.active,
        account_balances=primary_account.get("balances"),
    )
    db.add(plaid_conn)

    await create_audit_log(
        db=db,
        action=AuditAction.bank_account_linked,
        borrower_id=borrower.id,
        detail=f"Bank account connected via Plaid: {body.institution_name or 'Unknown'}",
        metadata={
            "item_id": item_id,
            "accounts_count": len(accounts),
            "institution": body.institution_name,
        },
    )

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "message": "Bank account(s) connected successfully",
                "connection_id": item_id,
                "item_id": item_id,
                "accounts_linked": len(accounts),
                "accounts": accounts,
            },
        }
    )


@integrations_router.get(
    "/plaid/accounts",
    response_model=None,
    summary="List connected Plaid accounts",
    description="Retrieve all linked bank accounts for the authenticated borrower.",
)
async def list_plaid_accounts(
    borrower: Borrower = Depends(get_current_borrower),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """List all Plaid accounts linked to the borrower."""
    result = await db.execute(
        select(PlaidConnection).where(
            PlaidConnection.borrower_id == borrower.id,
            PlaidConnection.status == PlaidConnectionStatus.active,
        )
    )
    connections = result.scalars().all()

    if not connections:
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "accounts": [],
                    "message": "No bank accounts connected",
                },
            }
        )

    # We could call Plaid API to get live data, but use stored data for now
    accounts_data = []
    for conn in connections:
        accounts_data.append({
            "connection_id": str(conn.id),
            "item_id": conn.plaid_item_id,
            "institution_name": conn.institution_name,
            "account_name": conn.account_name,
            "account_mask": conn.account_mask,
            "account_type": conn.account_type,
            "account_subtype": conn.account_subtype,
            "balances": conn.account_balances,
            "status": conn.status.value,
            "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
        })

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "accounts": accounts_data,
                "total": len(accounts_data),
            },
        }
    )


@integrations_router.get(
    "/plaid/transactions",
    response_model=None,
    summary="Get Plaid transactions",
    description="Fetch recent transactions from the borrower's linked bank accounts.",
)
async def get_plaid_transactions(
    borrower: Borrower = Depends(get_current_borrower),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Fetch transactions from the borrower's primary Plaid-connected account."""
    result = await db.execute(
        select(PlaidConnection).where(
            PlaidConnection.borrower_id == borrower.id,
            PlaidConnection.status == PlaidConnectionStatus.active,
        ).limit(1)
    )
    conn = result.scalar_one_or_none()

    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Plaid connection found. Please connect a bank account first.",
        )

    # Decrypt access token (in production, use encryption utility)
    access_token = conn.plaid_access_token.decode("utf-8")

    transactions = await plaid.get_transactions(access_token=access_token)

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "transactions": transactions,
                "total_transactions": len(transactions),
            },
        }
    )


@integrations_router.delete(
    "/plaid/connections/{connection_id}",
    response_model=None,
    summary="Remove Plaid connection",
    description="Disconnect and remove a previously linked Plaid bank account.",
)
async def remove_plaid_connection(
    connection_id: UUID,
    borrower: Borrower = Depends(get_current_borrower),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Remove a Plaid connection by ID."""
    result = await db.execute(
        select(PlaidConnection).where(
            PlaidConnection.id == connection_id,
            PlaidConnection.borrower_id == borrower.id,
        )
    )
    conn = result.scalar_one_or_none()

    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plaid connection not found",
        )

    conn.status = PlaidConnectionStatus.revoked

    await create_audit_log(
        db=db,
        action=AuditAction.bank_account_unlinked,
        borrower_id=borrower.id,
        detail=f"Bank account disconnected: {conn.institution_name or conn.plaid_item_id}",
        metadata={"item_id": conn.plaid_item_id},
    )

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "message": "Bank account disconnected successfully",
                "connection_id": str(conn.id),
            },
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Stripe Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@integrations_router.post(
    "/stripe/create-payment-intent",
    response_model=None,
    summary="Create Stripe PaymentIntent",
    description="Create a PaymentIntent for a loan payment. Returns a client secret for frontend confirmation.",
)
async def create_stripe_payment_intent(
    body: StripePaymentIntentRequest,
    borrower: Borrower = Depends(get_current_borrower),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Create a Stripe PaymentIntent for a loan payment."""
    # Verify the loan belongs to the borrower
    result = await db.execute(
        select(Loan).where(
            Loan.id == body.loan_id,
            Loan.borrower_id == borrower.id,
        )
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found or does not belong to this borrower",
        )

    # Create the payment intent via Stripe
    pi = await stripe.create_payment_intent(
        amount=body.amount,
        currency=body.currency,
        borrower_id=str(borrower.id),
        loan_id=str(body.loan_id),
        payment_method_id=body.payment_method_id,
        metadata={"description": body.description} if body.description else None,
    )

    # Create a pending payment record
    payment = Payment(
        loan_id=loan.id,
        borrower_id=borrower.id,
        status=PaymentStatus.processing,
        scheduled_date=loan.first_payment_date or loan.origination_date,
        total_amount=body.amount,
        principal_amount=body.amount,
        interest_amount=0,
        payment_method="card",
        external_reference=pi.get("id"),
        external_status=pi.get("status", "requires_payment_method"),
        payment_number=1,
    )
    db.add(payment)

    await create_audit_log(
        db=db,
        action=AuditAction.payment_received,
        borrower_id=borrower.id,
        detail=f"PaymentIntent created for loan {body.loan_id}: amount=${body.amount:.2f}",
        metadata={
            "loan_id": str(body.loan_id),
            "amount": float(body.amount),
            "intent_id": pi.get("id"),
            "status": pi.get("status"),
        },
    )

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "client_secret": pi.get("client_secret", ""),
                "intent_id": pi.get("id", ""),
                "amount": pi.get("amount", 0),
                "status": pi.get("status", ""),
            },
        }
    )


@integrations_router.post(
    "/stripe/confirm-payment",
    response_model=None,
    summary="Confirm a PaymentIntent",
    description="Confirm an existing PaymentIntent, optionally with a payment method.",
)
async def confirm_stripe_payment(
    body: StripeConfirmPaymentRequest,
    borrower: Borrower = Depends(get_current_borrower),
) -> JSONResponse:
    """Confirm an existing Stripe PaymentIntent."""
    result = await stripe.confirm_payment(
        intent_id=body.intent_id,
        payment_method_id=body.payment_method_id,
    )

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "intent_id": result.get("id", ""),
                "status": result.get("status", ""),
                "amount": result.get("amount", 0),
            },
        }
    )


@integrations_router.post(
    "/stripe/disburse",
    response_model=None,
    summary="Disburse loan funds",
    description="Disburse approved loan funds to the borrower's bank account via Stripe.",
)
async def disburse_loan(
    body: StripeDisburseRequest,
    admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Disburse loan funds to a borrower (admin-only)."""
    # Verify the loan exists and is ready for disbursement
    result = await db.execute(
        select(Loan).where(Loan.id == body.loan_id)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )

    # Create disbursement via Stripe
    disbursement = await stripe.create_disbursement(
        amount=body.amount,
        destination_bank_account=body.destination_bank_account,
        description=body.description or f"Loan disbursement for {body.loan_id}",
        metadata={
            "loan_id": str(body.loan_id),
            "borrower_id": str(loan.borrower_id),
        },
    )

    # Update loan with funding details
    loan.funding_account_id = body.destination_bank_account
    loan.funding_reference = disbursement.get("id", "")
    loan.status = "active"  # Will be updated properly

    await create_audit_log(
        db=db,
        action=AuditAction.loan_funded,
        borrower_id=loan.borrower_id,
        detail=f"Loan {body.loan_id} disbursed: ${body.amount:.2f}",
        metadata={
            "loan_id": str(body.loan_id),
            "amount": float(body.amount),
            "transfer_id": disbursement.get("id"),
            "destination": body.destination_bank_account,
        },
    )

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "transfer_id": disbursement.get("id", ""),
                "amount": disbursement.get("amount", 0),
                "status": disbursement.get("status", ""),
                "destination": disbursement.get("destination", ""),
            },
        }
    )


@integrations_router.post(
    "/stripe/webhook",
    response_model=None,
    summary="Stripe webhook receiver",
    description="Receive and process Stripe webhook events (no auth required).",
)
async def stripe_webhook(
    request: Request,
) -> JSONResponse:
    """Receive Stripe webhook events.

    This endpoint does NOT require authentication. Stripe signature
    verification is performed using the configured webhook secret.
    """
    raw_body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.construct_webhook_event(
            payload=raw_body,
            sig_header=sig_header,
        )
    except ValueError as exc:
        logger.warning("Stripe webhook signature verification failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "error": "Webhook signature verification failed"},
        )

    # Process the event
    result = await stripe.handle_webhook(event)

    return JSONResponse(
        content={
            "success": True,
            "data": result,
        }
    )


@integrations_router.post(
    "/stripe/create-customer",
    response_model=None,
    summary="Create Stripe customer",
    description="Create a Stripe Customer record for the borrower.",
)
async def create_stripe_customer(
    body: StripeCreateCustomerRequest,
    borrower: Borrower = Depends(get_current_borrower),
) -> JSONResponse:
    """Create a Stripe Customer for the authenticated borrower."""
    if body.borrower_id != borrower.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Borrower ID mismatch",
        )

    customer_data = {
        "email": body.email,
        "name": body.name,
        "phone": body.phone or borrower.phone,
        "metadata": {"borrower_id": str(borrower.id)},
    }

    customer = await stripe.create_customer(customer_data)

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "customer_id": customer.get("id", ""),
                "email": customer.get("email", ""),
                "name": customer.get("name", ""),
            },
        }
    )


@integrations_router.get(
    "/stripe/balance",
    response_model=None,
    summary="Get Stripe balance",
    description="Retrieve the Stripe account balance (admin-only).",
)
async def get_stripe_balance(
    admin=Depends(get_current_admin),
) -> JSONResponse:
    """Get the Stripe account balance (admin-only)."""
    balance = await stripe.get_balance()

    return JSONResponse(
        content={
            "success": True,
            "data": balance,
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Status & Health Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@integrations_router.get(
    "/status",
    response_model=None,
    summary="Integration status",
    description="Check which integrations (Plaid, Stripe) are configured.",
)
async def integration_status() -> IntegrationStatusResponse:
    """Return whether Plaid and Stripe are configured."""
    return IntegrationStatusResponse(
        plaid_configured=bool(settings.PLAID_CLIENT_ID and settings.PLAID_SECRET),
        stripe_configured=bool(settings.STRIPE_SECRET_KEY),
        plaid_env=settings.PLAID_ENV if settings.PLAID_CLIENT_ID else None,
    )


@integrations_router.get(
    "/health",
    response_model=None,
    summary="Integration health check",
    description="Detailed health check for Plaid and Stripe integrations.",
)
async def integration_health() -> IntegrationHealthResponse:
    """Check health of each integration by making a lightweight API call."""
    plaid_health: dict[str, Any] = {
        "configured": bool(settings.PLAID_CLIENT_ID and settings.PLAID_SECRET),
        "environment": settings.PLAID_ENV,
    }
    stripe_health: dict[str, Any] = {
        "configured": bool(settings.STRIPE_SECRET_KEY),
    }

    # Test Plaid connectivity (if configured)
    if plaid_health["configured"]:
        try:
            # Hit the /link/token/create endpoint with a minimal test payload
            _ = await plaid.create_link_token(
                borrower_id="health-check-borrower",
                user_data={"legal_name": "Health Check"},
            )
            plaid_health["reachable"] = True
            plaid_health["status"] = "ok"
        except Exception as exc:
            plaid_health["reachable"] = False
            plaid_health["status"] = "error"
            plaid_health["error"] = str(exc)
    else:
        plaid_health["reachable"] = False
        plaid_health["status"] = "not_configured"

    # Test Stripe connectivity (if configured)
    if stripe_health["configured"]:
        try:
            _ = await stripe.get_balance()
            stripe_health["reachable"] = True
            stripe_health["status"] = "ok"
        except Exception as exc:
            stripe_health["reachable"] = False
            stripe_health["status"] = "error"
            stripe_health["error"] = str(exc)
    else:
        stripe_health["reachable"] = False
        stripe_health["status"] = "not_configured"

    return IntegrationHealthResponse(
        plaid=plaid_health,
        stripe=stripe_health,
    )
