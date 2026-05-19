"""
OrangeFi — Agent API Router.

Agent-facing endpoints for the autonomous agent system (cron-based agents).
All endpoints are authenticated via a shared X-API-Key header.

Routers:
  GET  /api/agent/applications/pending        — submitted / manual_review apps
  POST /api/agent/applications/{id}/decision   — update status + create uw result
  GET  /api/agent/loans/due?date=YYYY-MM-DD   — loans due on a given date
  GET  /api/agent/loans/delinquent             — loans with days_past_due > 0
  GET  /api/agent/loans/active                 — active or delinquent loans
  GET  /api/agent/payments/recent?days=7       — completed payments in last N days
  GET  /api/agent/borrowers                    — active borrowers
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    Application,
    ApplicationStatus,
    Borrower,
    Loan,
    LoanStatus,
    Payment,
    PaymentStatus,
    UnderwritingDecision,
    UnderwritingResult,
)

logger = logging.getLogger("orangefi.agent_api")

router = APIRouter(prefix="/api/agent", tags=["agent"])

# ── Auth ──────────────────────────────────────────────────────────────────────

AGENT_API_KEY = os.environ.get(
    "ORANGEFI_AGENT_API_KEY", "orangefi-agent-key-dev"
)


async def verify_agent_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """Dependency: verify the shared agent API key."""
    if x_api_key != AGENT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent API key",
        )


# ── Serialisation helpers ─────────────────────────────────────────────────────


def _serialise_application(app: Application) -> Dict[str, Any]:
    """Convert an Application ORM row to a plain dict for agents."""
    return {
        "id": str(app.id),
        "borrower_id": str(app.borrower_id),
        "status": app.status.value,
        "requested_amount": float(app.requested_amount),
        "requested_term_months": app.requested_term_months,
        "loan_purpose": app.loan_purpose,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "updated_at": app.updated_at.isoformat() if app.updated_at else None,
    }


def _serialise_loan(loan: Loan) -> Dict[str, Any]:
    """Convert a Loan ORM row to a plain dict for agents."""
    return {
        "id": str(loan.id),
        "application_id": str(loan.application_id),
        "borrower_id": str(loan.borrower_id),
        "status": loan.status.value,
        "loan_amount": float(loan.loan_amount),
        "monthly_payment": float(loan.monthly_payment),
        "days_past_due": loan.days_past_due,
        "total_amount_due": float(loan.total_amount_due),
        "next_payment_date": loan.first_payment_date.isoformat()
        if loan.first_payment_date
        else None,
        "origination_date": loan.origination_date.isoformat()
        if loan.origination_date
        else None,
        "created_at": loan.created_at.isoformat() if loan.created_at else None,
    }


def _serialise_payment(payment: Payment) -> Dict[str, Any]:
    """Convert a Payment ORM row to a plain dict for agents."""
    return {
        "id": str(payment.id),
        "loan_id": str(payment.loan_id),
        "borrower_id": str(payment.borrower_id),
        "status": payment.status.value,
        "scheduled_date": payment.scheduled_date.isoformat(),
        "paid_date": payment.paid_date.isoformat() if payment.paid_date else None,
        "total_amount": float(payment.total_amount),
        "amount_paid": float(payment.amount_paid) if payment.amount_paid else None,
        "payment_number": payment.payment_number,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
    }


def _serialise_borrower(borrower: Borrower) -> Dict[str, Any]:
    """Convert a Borrower ORM row to a plain dict for agents."""
    return {
        "id": str(borrower.id),
        "email": borrower.email,
        "first_name": borrower.first_name,
        "last_name": borrower.last_name,
        "is_active": borrower.is_active,
        "credit_score_range": borrower.credit_score_range,
        "credit_tier": borrower.credit_tier,
        "created_at": borrower.created_at.isoformat() if borrower.created_at else None,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "/applications/pending",
    summary="Get pending applications needing UW review",
    dependencies=[Depends(verify_agent_key)],
)
async def get_pending_applications(
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return applications with status 'submitted' or 'manual_review'."""
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.borrower))
        .where(
            Application.status.in_([
                ApplicationStatus.submitted,
                ApplicationStatus.manual_review,
            ])
        )
        .order_by(Application.created_at.asc())
    )
    apps = result.scalars().all()
    return [_serialise_application(a) for a in apps]


@router.post(
    "/applications/{application_id}/decision",
    summary="Make a decision on an application (approve/decline/manual_review)",
    dependencies=[Depends(verify_agent_key)],
)
async def agent_application_decision(
    application_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Update application status and create an underwriting result.

    Expects JSON body:
    {
      "status": "approved" | "declined" | "manual_review",
      "decision_details": { ... }  // optional details from UW agent
    }
    """
    body = await request.json()
    decision_status = body.get("status", "")
    decision_details: dict = body.get("decision_details", {}) or {}

    if decision_status not in ("approved", "declined", "manual_review"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="status must be 'approved', 'declined', or 'manual_review'",
        )

    # Fetch the application
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    now = datetime.now(timezone.utc)

    # Map decision to ApplicationStatus
    status_map = {
        "approved": ApplicationStatus.approved,
        "declined": ApplicationStatus.declined,
        "manual_review": ApplicationStatus.manual_review,
    }
    new_status = status_map[decision_status]
    app.status = new_status
    app.decisioned_at = now

    if decision_status == "declined":
        app.declined_reason = decision_details.get(
            "reason", "Declined by underwriting agent"
        )
        app.declined_reason_codes = decision_details.get(
            "reason_codes",
            ["X99 - Application does not meet current underwriting criteria"],
        )

    # Create UnderwritingResult
    uw_decision_map = {
        "approved": UnderwritingDecision.approved,
        "declined": UnderwritingDecision.declined,
        "manual_review": UnderwritingDecision.manual_review,
    }

    uw_result = UnderwritingResult(
        application_id=app.id,
        borrower_id=app.borrower_id,
        ai_score=decision_details.get("risk_score"),
        ai_tier=decision_details.get("ai_tier"),
        ai_confidence=decision_details.get("ai_confidence"),
        decision=uw_decision_map[decision_status],
        decision_reason=decision_details.get("reason"),
        decision_factors=decision_details.get("decision_factors"),
        model_version=decision_details.get("model_version"),
        model_name=decision_details.get("model_name"),
    )
    db.add(uw_result)

    await db.flush()

    return {
        "success": True,
        "application_id": str(app.id),
        "status": app.status.value,
        "decisioned_at": now.isoformat(),
    }


@router.get(
    "/loans/due",
    summary="Get loans whose next payment is due on a given date",
    dependencies=[Depends(verify_agent_key)],
)
async def get_loans_due(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return loans whose next_payment_date (first_payment_date) matches the given date."""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date must be in YYYY-MM-DD format",
        )

    result = await db.execute(
        select(Loan)
        .where(
            and_(
                Loan.first_payment_date == target_date,
                Loan.status.in_([
                    LoanStatus.active,
                    LoanStatus.delinquent,
                    LoanStatus.pending_disbursement,
                ]),
            )
        )
        .order_by(Loan.created_at.asc())
    )
    loans = result.scalars().all()
    return [_serialise_loan(l) for l in loans]


@router.get(
    "/loans/delinquent",
    summary="Get delinquent loans (days_past_due > 0 or status=delinquent)",
    dependencies=[Depends(verify_agent_key)],
)
async def get_delinquent_loans(
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return loans that are delinquent."""
    result = await db.execute(
        select(Loan)
        .where(
            and_(
                Loan.status == LoanStatus.delinquent,
            )
        )
        .order_by(Loan.days_past_due.desc())
    )
    loans = result.scalars().all()
    return [_serialise_loan(l) for l in loans]


@router.get(
    "/loans/active",
    summary="Get active loans (status=active or delinquent)",
    dependencies=[Depends(verify_agent_key)],
)
async def get_active_loans(
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return loans that are active or delinquent."""
    result = await db.execute(
        select(Loan)
        .where(
            Loan.status.in_([
                LoanStatus.active,
                LoanStatus.delinquent,
            ])
        )
        .order_by(Loan.created_at.asc())
    )
    loans = result.scalars().all()
    return [_serialise_loan(l) for l in loans]


@router.get(
    "/payments/recent",
    summary="Get payments made in the last N days",
    dependencies=[Depends(verify_agent_key)],
)
async def get_recent_payments(
    days: int = Query(7, description="Number of days to look back", ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return completed payments within the last N days."""
    cutoff = date.today() - timedelta(days=days)
    result = await db.execute(
        select(Payment)
        .where(
            and_(
                Payment.status == PaymentStatus.completed,
                Payment.paid_date >= cutoff,
            )
        )
        .order_by(Payment.paid_date.desc())
    )
    payments = result.scalars().all()
    return [_serialise_payment(p) for p in payments]


@router.get(
    "/borrowers",
    summary="Get all active borrowers",
    dependencies=[Depends(verify_agent_key)],
)
async def get_borrowers(
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return all active borrowers."""
    result = await db.execute(
        select(Borrower)
        .where(Borrower.is_active == True)
        .order_by(Borrower.created_at.asc())
    )
    borrowers = result.scalars().all()
    return [_serialise_borrower(b) for b in borrowers]
