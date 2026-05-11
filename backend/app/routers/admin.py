"""
OrangeFi Lending Platform — Admin Router.

Backoffice endpoints for:
  - Admin authentication (login with MFA support)
  - MFA setup and verification (TOTP)
  - Dashboard metrics
  - Application management (list, detail, decision)
  - Borrower management (list, detail)
  - Loan management (list, detail)
  - Portfolio summary, collections, audit log, compliance
  - System settings
  - Report generation (CSV)
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select, func, and_, or_, desc, asc, cast, String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    AdminRole,
    AdminUser,
    Application,
    ApplicationStatus,
    AuditLog,
    AuditAction,
    Borrower,
    ComplianceEvent,
    ComplianceEventType,
    Loan,
    LoanStatus,
    Payment,
    PaymentStatus,
    UnderwritingDecision,
    UnderwritingResult,
)
from app.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminMfaSetupResponse,
    AdminMfaVerifyRequest,
    AdminResponse,
    AdminUserListFilter,
    ApplicationDecisionRequest,
    ApplicationDecisionResponse,
    ApplicationDetailResponse,
    ApplicationListFilter,
    ApplicationListResponse,
    AuditLogListFilter,
    AuditLogListResponse,
    AuditLogDetailResponse,
    BorrowerResponse,
    LoanDetailResponse,
    LoanListFilter,
    LoanListResponse,
    LoanResponse,
    LoanSummary,
    SuccessResponse,
    PaginatedResponse,
    PaginationMeta,
    ErrorResponse,
)
from app.utils.dependencies import get_current_admin, require_admin_role, get_current_borrower
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    generate_totp_secret,
    get_totp_uri,
    generate_totp_qr_svg,
    verify_totp,
    generate_backup_codes,
)
from app.utils.audit import create_audit_log
from app.config import settings

# ──────────────────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────────────────

admin_router = APIRouter(prefix="/admin", tags=["admin"])


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


async def _paginated_response(
    db: AsyncSession,
    query: Any,
    page: int,
    page_size: int,
) -> tuple[list[Any], PaginationMeta]:
    count_q = select(func.count()).select_from(query.subquery())
    total_items = (await db.execute(count_q)).scalar() or 0
    offset_val = (page - 1) * page_size
    results = await db.execute(query.offset(offset_val).limit(page_size))
    items = list(results.scalars().all())
    total_pages = max(1, (total_items + page_size - 1) // page_size) if total_items > 0 else 0
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )
    return items, meta


# ──────────────────────────────────────────────────────────────────────────────
# POST /admin/login — Admin login
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.post(
    "/login",
    response_model=AdminLoginResponse,
    summary="Authenticate admin (with optional MFA support)",
)
async def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AdminLoginResponse:
    """Authenticate an admin user. If MFA is enabled, require TOTP code."""
    result = await db.execute(
        select(AdminUser).where(
            AdminUser.email == payload.email,
            AdminUser.is_active.is_(True),
        )
    )
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if account is locked
    if admin.is_locked:
        if admin.locked_until and admin.locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked until {admin.locked_until.isoformat()}",
            )
        # Auto-unlock
        admin.is_locked = False
        admin.login_attempts = 0

    # Verify password
    if not verify_password(payload.password, admin.hashed_password):
        admin.login_attempts += 1
        if admin.login_attempts >= 5:
            admin.is_locked = True
            admin.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Reset login attempts
    admin.login_attempts = 0
    admin.last_login_at = datetime.now(timezone.utc)
    admin.last_login_ip = request.client.host if request.client else None

    # MFA check
    if admin.mfa_enabled:
        if not payload.mfa_code:
            await db.flush()
            return AdminLoginResponse(
                access_token="",
                refresh_token=None,
                token_type="bearer",
                expires_in=0,
                admin_id=str(admin.id),
                display_name=admin.display_name,
                email=admin.email,
                role=admin.role.value,
                mfa_enabled=True,
                requires_mfa=True,
            )
        if not verify_totp(admin.mfa_secret, payload.mfa_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code",
            )

    await db.flush()

    # Audit log
    await create_audit_log(
        db,
        action=AuditAction.admin_login.value,
        resource_type="admin_user",
        resource_id=str(admin.id),
        actor_id=admin.id,
        actor_type="admin",
        admin_user_id=admin.id,
        description=f"Admin {admin.email} logged in",
        ip_address=request.client.host if request.client else None,
        request_id=getattr(request.state, "request_id", None),
    )

    access_token = create_access_token(
        subject=str(admin.id),
        extra_claims={"role": "admin", "email": admin.email, "admin_role": admin.role.value},
    )
    refresh_token = create_refresh_token(subject=str(admin.id))

    return AdminLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        admin_id=str(admin.id),
        display_name=admin.display_name,
        email=admin.email,
        role=admin.role.value,
        mfa_enabled=admin.mfa_enabled,
        requires_mfa=False,
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /admin/mfa/setup — Setup TOTP MFA
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.post(
    "/mfa/setup",
    response_model=AdminMfaSetupResponse,
    summary="Setup TOTP MFA for the authenticated admin",
)
async def admin_mfa_setup(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminMfaSetupResponse:
    """Generate TOTP secret, QR code URI, and backup codes for MFA setup."""
    if admin.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA is already enabled. Disable it first to re-setup.",
        )

    secret = generate_totp_secret()
    qr_uri = get_totp_uri(secret, admin.email)
    qr_svg = generate_totp_qr_svg(secret, admin.email)
    backup_codes = generate_backup_codes(8)

    # Store secret and backup codes temporarily (will be verified before enabling)
    admin.mfa_secret = secret
    admin.mfa_backup_codes = backup_codes
    await db.flush()

    return AdminMfaSetupResponse(
        secret=secret,
        qr_code_url=qr_uri,
        qr_code_svg=qr_svg,
        backup_codes=backup_codes,
        message="Scan the QR code with your authenticator app and verify with a code to enable MFA.",
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /admin/mfa/verify — Verify MFA code and enable
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.post(
    "/mfa/verify",
    response_model=SuccessResponse,
    summary="Verify TOTP code and enable MFA",
)
async def admin_mfa_verify(
    payload: AdminMfaVerifyRequest,
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Verify the TOTP code provided during MFA setup and enable MFA."""
    if not admin.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not initiated. Call POST /admin/mfa/setup first.",
        )

    if not verify_totp(admin.mfa_secret, payload.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code. Please try again.",
        )

    # Verify secret matches what was stored
    if admin.mfa_secret != payload.secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Secret mismatch. Please start MFA setup again.",
        )

    admin.mfa_enabled = True
    admin.mfa_verified_at = datetime.now(timezone.utc)
    await db.flush()

    return SuccessResponse(
        message="MFA has been enabled successfully.",
        data={
            "mfa_enabled": True,
            "verified_at": admin.mfa_verified_at.isoformat(),
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/dashboard — Dashboard metrics
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/dashboard",
    summary="Get backoffice dashboard metrics",
)
async def admin_dashboard(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return key metrics for the admin dashboard."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)

    # Applications today
    apps_today = await db.execute(
        select(func.count(Application.id)).where(
            Application.created_at >= today_start
        )
    )
    applications_today = apps_today.scalar() or 0

    # Applications pending review
    pending = await db.execute(
        select(func.count(Application.id)).where(
            Application.status.in_(["submitted", "processing", "manual_review"])
        )
    )
    pending_review = pending.scalar() or 0

    # Funded MTD (Month To Date)
    funded_mtd = await db.execute(
        select(func.coalesce(func.sum(Application.amount_funded), 0)).where(
            Application.funded_at >= month_start,
            Application.status == ApplicationStatus.funded,
        )
    )
    funded_mtd_amount = float(funded_mtd.scalar() or 0)

    # Active loans
    active_loans = await db.execute(
        select(func.count(Loan.id)).where(
            Loan.status.in_([LoanStatus.active, LoanStatus.delinquent])
        )
    )
    active_loans_count = active_loans.scalar() or 0

    # Delinquency rate
    del_count = await db.execute(
        select(func.count(Loan.id)).where(Loan.status == LoanStatus.delinquent)
    )
    delinquent_count = del_count.scalar() or 0
    delinquency_rate = round(delinquent_count / active_loans_count * 100, 2) if active_loans_count > 0 else 0.0

    # Charge-offs
    charged_off = await db.execute(
        select(func.count(Loan.id)).where(Loan.status == LoanStatus.charged_off)
    )
    charged_off_count = charged_off.scalar() or 0

    # Total portfolio outstanding
    portfolio = await db.execute(
        select(func.coalesce(func.sum(Loan.loan_amount), 0)).where(
            Loan.status.in_([LoanStatus.active, LoanStatus.delinquent])
        )
    )
    portfolio_outstanding = float(portfolio.scalar() or 0)

    # Recent registrations (30 days)
    reg_start = now - timedelta(days=30)
    new_borrowers = await db.execute(
        select(func.count(Borrower.id)).where(Borrower.created_at >= reg_start)
    )
    new_borrowers_count = new_borrowers.scalar() or 0

    return {
        "applications_today": applications_today,
        "pending_review": pending_review,
        "funded_mtd_amount": funded_mtd_amount,
        "active_loans": active_loans_count,
        "delinquent_loans": delinquent_count,
        "delinquency_rate_pct": delinquency_rate,
        "charged_off_loans": charged_off_count,
        "portfolio_outstanding": portfolio_outstanding,
        "new_borrowers_30d": new_borrowers_count,
        "timestamp": now.isoformat(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/applications — List all applications
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/applications",
    response_model=PaginatedResponse[ApplicationListResponse],
    summary="List all applications (with filters)",
)
async def admin_list_applications(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.underwriter, AdminRole.compliance, AdminRole.viewer, AdminRole.support,
    )),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ApplicationListResponse]:
    """List applications with filters for status, date range, and free-text search."""
    base = (
        select(Application)
        .options(selectinload(Application.borrower))
    )
    conditions = []
    if status_filter:
        conditions.append(Application.status == status_filter)
    if created_after:
        conditions.append(Application.created_at >= created_after)
    if created_before:
        conditions.append(Application.created_at <= created_before)
    if search:
        conditions.append(
            or_(
                Application.id.cast(String).ilike(f"%{search}%"),
            )
        )
    if conditions:
        base = base.where(and_(*conditions))
    base = base.order_by(desc(Application.created_at))

    items, meta = await _paginated_response(db, base, page, page_size)

    data = []
    for app in items:
        borrower_name = None
        if app.borrower:
            borrower_name = f"{app.borrower.first_name} {app.borrower.last_name}"
        data.append(
            ApplicationListResponse(
                id=str(app.id),
                borrower_id=str(app.borrower_id),
                borrower_name=borrower_name,
                status=app.status.value,
                requested_amount=app.requested_amount,
                requested_term_months=app.requested_term_months,
                loan_purpose=app.loan_purpose,
                amount_funded=app.amount_funded,
                decisioned_at=app.decisioned_at,
                created_at=app.created_at,
                updated_at=app.updated_at,
            )
        )

    return PaginatedResponse[ApplicationListResponse](data=data, pagination=meta)


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/applications/{id} — Application detail
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/applications/{application_id}",
    response_model=ApplicationDetailResponse,
    summary="Get application detail (admin view)",
)
async def admin_get_application(
    application_id: uuid.UUID,
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.underwriter, AdminRole.compliance, AdminRole.viewer,
    )),
    db: AsyncSession = Depends(get_db),
) -> ApplicationDetailResponse:
    """Return full application details including borrower info, underwriting data."""
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.borrower), selectinload(Application.underwriting_result))
        .where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    borrower_name = f"{app.borrower.first_name} {app.borrower.last_name}" if app.borrower else None
    borrower_email = app.borrower.email if app.borrower else None

    return ApplicationDetailResponse(
        id=str(app.id),
        borrower_id=str(app.borrower_id),
        borrower_name=borrower_name,
        borrower_email=borrower_email,
        status=app.status.value,
        requested_amount=app.requested_amount,
        requested_term_months=app.requested_term_months,
        loan_purpose=app.loan_purpose,
        loan_purpose_details=app.loan_purpose_details,
        total_existing_debt=app.total_existing_debt,
        creditor_details=app.creditor_details,
        monthly_debt_payments=app.monthly_debt_payments,
        application_monthly_income=app.application_monthly_income,
        application_employer=app.application_employer,
        application_employment_status=app.application_employment_status,
        years_at_current_job=app.years_at_current_job,
        housing_status=app.housing_status,
        monthly_housing_payment=app.monthly_housing_payment,
        ip_address=app.ip_address,
        user_agent=app.user_agent,
        application_metadata=app.application_metadata,
        amount_funded=app.amount_funded,
        decisioned_at=app.decisioned_at,
        decisioned_by=str(app.decisioned_by) if app.decisioned_by else None,
        declined_reason=app.declined_reason,
        declined_reason_codes=app.declined_reason_codes,
        funded_at=app.funded_at,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /admin/applications/{id}/decision — Approve/decline
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.post(
    "/applications/{application_id}/decision",
    response_model=ApplicationDecisionResponse,
    summary="Make a decision on an application (approve/decline/manual_review)",
)
async def admin_decision(
    application_id: uuid.UUID,
    payload: ApplicationDecisionRequest,
    request: Request,
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.underwriter,
    )),
    db: AsyncSession = Depends(get_db),
) -> ApplicationDecisionResponse:
    """Approve, decline, or flag for manual review a loan application."""
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.borrower))
        .where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if app.status in (ApplicationStatus.approved, ApplicationStatus.declined, ApplicationStatus.funded, ApplicationStatus.cancelled):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot make a decision on an application in status '{app.status.value}'",
        )

    now = datetime.now(timezone.utc)
    app.decisioned_at = now
    app.decisioned_by = admin.id

    if payload.decision == "approved":
        app.status = ApplicationStatus.approved
        app.amount_funded = payload.amount_funded

        # Create the loan record
        monthly_rate = float(payload.amount_funded) * 0.01  # Very simplified
        term = app.requested_term_months
        # Simple interest calculation for mock
        apr_value = Decimal("9.990")
        monthly_pmt = Decimal(str(round(
            float(payload.amount_funded) * float(apr_value / 100 / 12) *
            (1 + float(apr_value / 100 / 12)) ** term /
            ((1 + float(apr_value / 100 / 12)) ** term - 1)
            if float(apr_value) > 0 else float(payload.amount_funded) / term
        , 2)))

        from datetime import date as dt_date
        first_pmt = date.today().replace(month=date.today().month + 1)
        if first_pmt.month > 12:
            first_pmt = first_pmt.replace(year=first_pmt.year + 1, month=1)

        loan = Loan(
            application_id=app.id,
            borrower_id=app.borrower_id,
            status=LoanStatus.pending_disbursement,
            loan_amount=payload.amount_funded,
            apr=apr_value,
            term_months=term,
            monthly_payment=monthly_pmt,
            origination_fee=Decimal("0.00"),
            disbursement_amount=payload.amount_funded,
            interest_rate_type="fixed",
            origination_date=date.today(),
            first_payment_date=first_pmt,
            maturity_date=date.today().replace(year=date.today().year + (term // 12), month=date.today().month + (term % 12)),
        )
        db.add(loan)

        # Generate payment schedule
        for i in range(1, term + 1):
            sch_date = date.today()
            new_month = sch_date.month + i
            new_year = sch_date.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1
            try:
                from calendar import monthrange
                max_day = monthrange(new_year, new_month)[1]
                day = min(sch_date.day, max_day)
                sch_date = date(new_year, new_month, day)
            except ValueError:
                sch_date = date(new_year, new_month, 1)

            payment = Payment(
                loan_id=loan.id,
                borrower_id=app.borrower_id,
                status=PaymentStatus.scheduled,
                scheduled_date=sch_date,
                total_amount=monthly_pmt,
                principal_amount=monthly_pmt,
                interest_amount=Decimal("0.00"),
                fees_amount=Decimal("0.00"),
                late_fee=Decimal("0.00"),
                payment_number=i,
            )
            db.add(payment)

        await db.flush()
        app.funded_at = now

    elif payload.decision == "declined":
        app.status = ApplicationStatus.declined
        app.declined_reason = payload.declined_reason
        app.declined_reason_codes = payload.declined_reason_codes or [
            "X99 - Application does not meet current underwriting criteria"
        ]
    else:
        app.status = ApplicationStatus.manual_review

    await db.flush()

    await create_audit_log(
        db,
        action=AuditAction.decision_made.value,
        resource_type="application",
        resource_id=str(app.id),
        actor_id=admin.id,
        actor_type="admin",
        admin_user_id=admin.id,
        details={
            "decision": payload.decision,
            "amount_funded": float(payload.amount_funded) if payload.amount_funded else None,
            "declined_reason": payload.declined_reason,
        },
        changes={"status": {"before": app.status.value, "after": payload.decision}},
        description=f"Application {app.id} {'approved' if payload.decision == 'approved' else 'declined' if payload.decision == 'declined' else 'sent to manual review'} by {admin.email}",
        ip_address=request.client.host if request.client else None,
        request_id=getattr(request.state, "request_id", None),
    )

    return ApplicationDecisionResponse(
        application_id=str(app.id),
        status=app.status.value,
        decisioned_at=now,
        decisioned_by=str(admin.id),
        declined_reason=app.declined_reason,
        amount_funded=app.amount_funded,
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/borrowers — List borrowers
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/borrowers",
    response_model=PaginatedResponse[BorrowerResponse],
    summary="List all borrowers",
)
async def admin_list_borrowers(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.underwriter, AdminRole.collections, AdminRole.compliance, AdminRole.support, AdminRole.viewer,
    )),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[BorrowerResponse]:
    """List borrowers with optional search and active filter."""
    base = select(Borrower).where(Borrower.is_deleted.is_(False))
    conditions = []
    if search:
        conditions.append(
            or_(
                Borrower.first_name.ilike(f"%{search}%"),
                Borrower.last_name.ilike(f"%{search}%"),
                Borrower.email.ilike(f"%{search}%"),
                Borrower.phone.ilike(f"%{search}%"),
            )
        )
    if is_active is not None:
        conditions.append(Borrower.is_active.is_(is_active))
    if conditions:
        base = base.where(and_(*conditions))
    base = base.order_by(desc(Borrower.created_at))

    items, meta = await _paginated_response(db, base, page, page_size)

    data = [
        BorrowerResponse(
            id=str(b.id),
            email=b.email,
            phone=b.phone,
            first_name=b.first_name,
            middle_name=b.middle_name,
            last_name=b.last_name,
            date_of_birth=b.date_of_birth,
            address_line1=b.address_line1,
            address_line2=b.address_line2,
            city=b.city,
            state=b.state,
            zip_code=b.zip_code,
            employer=b.employer,
            employment_status=b.employment_status,
            monthly_income=b.monthly_income,
            is_identity_verified=b.is_identity_verified,
            kyc_completed_at=b.kyc_completed_at,
            credit_score_range=b.credit_score_range,
            credit_tier=b.credit_tier,
            is_active=b.is_active,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b in items
    ]

    return PaginatedResponse[BorrowerResponse](data=data, pagination=meta)


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/borrowers/{id} — Borrower detail
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/borrowers/{borrower_id}",
    response_model=dict[str, Any],
    summary="Get borrower detail (admin view)",
)
async def admin_get_borrower(
    borrower_id: uuid.UUID,
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.underwriter, AdminRole.collections, AdminRole.compliance, AdminRole.support, AdminRole.viewer,
    )),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return full borrower profile with related entities summary."""
    result = await db.execute(
        select(Borrower).where(
            Borrower.id == borrower_id,
            Borrower.is_deleted.is_(False),
        )
    )
    borrower = result.scalar_one_or_none()
    if not borrower:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borrower not found",
        )

    # Get counts
    app_count = (await db.execute(
        select(func.count(Application.id)).where(Application.borrower_id == borrower_id)
    )).scalar() or 0

    loan_count = (await db.execute(
        select(func.count(Loan.id)).where(Loan.borrower_id == borrower_id)
    )).scalar() or 0

    active_loans = (await db.execute(
        select(func.count(Loan.id)).where(
            Loan.borrower_id == borrower_id,
            Loan.status.in_([LoanStatus.active, LoanStatus.delinquent]),
        )
    )).scalar() or 0

    return {
        "id": str(borrower.id),
        "email": borrower.email,
        "phone": borrower.phone,
        "first_name": borrower.first_name,
        "middle_name": borrower.middle_name,
        "last_name": borrower.last_name,
        "date_of_birth": str(borrower.date_of_birth),
        "address_line1": borrower.address_line1,
        "address_line2": borrower.address_line2,
        "city": borrower.city,
        "state": borrower.state,
        "zip_code": borrower.zip_code,
        "employer": borrower.employer,
        "employment_status": borrower.employment_status,
        "monthly_income": float(borrower.monthly_income) if borrower.monthly_income else None,
        "is_identity_verified": borrower.is_identity_verified,
        "kyc_completed_at": borrower.kyc_completed_at.isoformat() if borrower.kyc_completed_at else None,
        "credit_score_range": borrower.credit_score_range,
        "credit_tier": borrower.credit_tier,
        "is_active": borrower.is_active,
        "statistics": {
            "total_applications": app_count,
            "total_loans": loan_count,
            "active_loans": active_loans,
        },
        "created_at": borrower.created_at.isoformat(),
        "updated_at": borrower.updated_at.isoformat(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/loans — List all loans
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/loans",
    response_model=PaginatedResponse[LoanListResponse],
    summary="List all loans (with filters)",
)
async def admin_list_loans(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    dpd_min: Optional[int] = Query(None, alias="days_past_due_min"),
    dpd_max: Optional[int] = Query(None, alias="days_past_due_max"),
    search: Optional[str] = Query(None),
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.underwriter, AdminRole.collections, AdminRole.compliance, AdminRole.viewer,
    )),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[LoanListResponse]:
    """List loans with filters for status, DPD range, and free-text search."""
    base = select(Loan).options(selectinload(Loan.borrower))
    conditions = []
    if status_filter:
        conditions.append(Loan.status == status_filter)
    if dpd_min is not None:
        conditions.append(Loan.days_past_due >= dpd_min)
    if dpd_max is not None:
        conditions.append(Loan.days_past_due <= dpd_max)
    if search:
        conditions.append(
            or_(
                Loan.id.cast(String).ilike(f"%{search}%"),
            )
        )
    if conditions:
        base = base.where(and_(*conditions))
    base = base.order_by(desc(Loan.created_at))

    items, meta = await _paginated_response(db, base, page, page_size)

    data = []
    for loan in items:
        borrower_name = None
        if loan.borrower:
            borrower_name = f"{loan.borrower.first_name} {loan.borrower.last_name}"
        data.append(
            LoanListResponse(
                id=str(loan.id),
                application_id=str(loan.application_id),
                borrower_id=str(loan.borrower_id),
                borrower_name=borrower_name,
                status=loan.status.value,
                loan_amount=loan.loan_amount,
                apr=loan.apr,
                term_months=loan.term_months,
                monthly_payment=loan.monthly_payment,
                disbursement_amount=loan.disbursement_amount,
                origination_fee=loan.origination_fee,
                interest_rate_type=loan.interest_rate_type,
                interest_accrued=loan.interest_accrued,
                days_past_due=loan.days_past_due,
                total_amount_due=loan.total_amount_due,
                collections_status=loan.collections_status,
                origination_date=loan.origination_date,
                first_payment_date=loan.first_payment_date,
                maturity_date=loan.maturity_date,
                paid_off_at=loan.paid_off_at,
                created_at=loan.created_at,
                updated_at=loan.updated_at,
            )
        )

    return PaginatedResponse[LoanListResponse](data=data, pagination=meta)


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/loans/{id} — Loan detail
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/loans/{loan_id}",
    response_model=LoanDetailResponse,
    summary="Get loan detail (admin view)",
)
async def admin_get_loan(
    loan_id: uuid.UUID,
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.underwriter, AdminRole.collections, AdminRole.compliance, AdminRole.viewer,
    )),
    db: AsyncSession = Depends(get_db),
) -> LoanDetailResponse:
    """Return full loan details with payment schedule and borrower info."""
    result = await db.execute(
        select(Loan)
        .options(selectinload(Loan.payments), selectinload(Loan.borrower))
        .where(Loan.id == loan_id)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )

    payments = sorted(loan.payments, key=lambda p: p.payment_number)
    schedule = []
    for pmt in payments:
        schedule.append({
            "payment_number": pmt.payment_number,
            "scheduled_date": str(pmt.scheduled_date),
            "total_amount": float(pmt.total_amount),
            "principal_amount": float(pmt.principal_amount),
            "interest_amount": float(pmt.interest_amount),
            "fees_amount": float(pmt.fees_amount),
            "status": pmt.status.value,
        })

    recent = [
        {
            "id": str(p.id),
            "payment_number": p.payment_number,
            "status": p.status.value,
            "scheduled_date": str(p.scheduled_date),
            "paid_date": str(p.paid_date) if p.paid_date else None,
            "total_amount": float(p.total_amount),
            "amount_paid": float(p.amount_paid) if p.amount_paid else None,
            "payment_method": p.payment_method,
        }
        for p in payments[-12:]
    ]

    borrower_name = f"{loan.borrower.first_name} {loan.borrower.last_name}" if loan.borrower else None

    return LoanDetailResponse(
        id=str(loan.id),
        application_id=str(loan.application_id),
        borrower_id=str(loan.borrower_id),
        borrower_name=borrower_name,
        status=loan.status.value,
        loan_amount=loan.loan_amount,
        apr=loan.apr,
        term_months=loan.term_months,
        monthly_payment=loan.monthly_payment,
        disbursement_amount=loan.disbursement_amount,
        origination_fee=loan.origination_fee,
        interest_rate_type=loan.interest_rate_type,
        interest_accrued=loan.interest_accrued,
        days_past_due=loan.days_past_due,
        total_amount_due=loan.total_amount_due,
        collections_status=loan.collections_status,
        origination_date=loan.origination_date,
        first_payment_date=loan.first_payment_date,
        maturity_date=loan.maturity_date,
        paid_off_at=loan.paid_off_at,
        funding_account_id=loan.funding_account_id,
        funding_reference=loan.funding_reference,
        charge_off_reason=loan.charge_off_reason,
        delinquency_started_at=loan.delinquency_started_at,
        last_interest_calc_at=loan.last_interest_calc_at,
        payment_schedule=schedule,  # type: ignore[arg-type]
        recent_payments=recent,
        created_at=loan.created_at,
        updated_at=loan.updated_at,
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/portfolio — Portfolio summary
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/portfolio",
    summary="Get portfolio summary",
)
async def admin_portfolio(
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.underwriter, AdminRole.compliance, AdminRole.viewer,
    )),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return portfolio-level summary with delinquency buckets and charge-offs."""
    now = datetime.now(timezone.utc)

    # Active loans
    active = await db.execute(
        select(func.count(Loan.id), func.coalesce(func.sum(Loan.loan_amount), 0))
        .where(Loan.status == LoanStatus.active)
    )
    active_row = active.one()
    active_count, active_balance = active_row[0] or 0, float(active_row[1] or 0)

    # Delinquency buckets
    buckets = {}
    for label, dpd_min, dpd_max in [
        ("current", 0, 0),
        ("early_stage_1_30", 1, 30),
        ("mid_stage_31_60", 31, 60),
        ("late_stage_61_90", 61, 90),
        ("critical_90_plus", 91, 9999),
    ]:
        q = await db.execute(
            select(func.count(Loan.id), func.coalesce(func.sum(Loan.loan_amount), 0))
            .where(
                Loan.status == LoanStatus.delinquent,
                Loan.days_past_due >= dpd_min,
                Loan.days_past_due <= dpd_max,
            )
        )
        row = q.one()
        buckets[label] = {
            "count": row[0] or 0,
            "balance": float(row[1] or 0),
        }

    # Charge-offs
    charged_off = await db.execute(
        select(func.count(Loan.id), func.coalesce(func.sum(Loan.loan_amount), 0))
        .where(Loan.status == LoanStatus.charged_off)
    )
    co_row = charged_off.one()
    co_count, co_balance = co_row[0] or 0, float(co_row[1] or 0)

    # Paid off
    paid_off = await db.execute(
        select(func.count(Loan.id))
        .where(Loan.status == LoanStatus.paid_off)
    )
    paid_off_count = paid_off.scalar() or 0

    # Total portfolio
    total_all = await db.execute(
        select(func.coalesce(func.sum(Loan.loan_amount), 0))
    )
    total_portfolio = float(total_all.scalar() or 0)

    return {
        "as_of": now.isoformat(),
        "summary": {
            "total_portfolio_balance": total_portfolio,
            "active_loans_count": active_count,
            "active_loans_balance": active_balance,
            "delinquent_loans_count": sum(b["count"] for b in buckets.values()),
            "paid_off_loans_count": paid_off_count,
            "charged_off_loans_count": co_count,
            "charged_off_balance": co_balance,
        },
        "delinquency_buckets": buckets,
        "total_loans": active_count + sum(b["count"] for b in buckets.values()) + paid_off_count + co_count,
    }


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/collections — Delinquent accounts with aging
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/collections",
    summary="Get delinquent accounts for collections dashboard",
)
async def admin_collections(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    min_dpd: int = Query(1, ge=0, alias="min_days_past_due"),
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.collections,
    )),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return delinquent loans with aging analysis for collections team."""
    base = (
        select(Loan)
        .options(selectinload(Loan.borrower))
        .where(
            Loan.status == LoanStatus.delinquent,
            Loan.days_past_due >= min_dpd,
        )
        .order_by(desc(Loan.days_past_due))
    )

    items, meta = await _paginated_response(db, base, page, page_size)

    loans_data = []
    for loan in items:
        borrower_name = None
        borrower_phone = None
        if loan.borrower:
            borrower_name = f"{loan.borrower.first_name} {loan.borrower.last_name}"
            borrower_phone = loan.borrower.phone
        loans_data.append({
            "loan_id": str(loan.id),
            "borrower_id": str(loan.borrower_id),
            "borrower_name": borrower_name,
            "borrower_phone": borrower_phone,
            "loan_amount": float(loan.loan_amount),
            "monthly_payment": float(loan.monthly_payment),
            "apr": float(loan.apr),
            "days_past_due": loan.days_past_due,
            "total_amount_due": float(loan.total_amount_due),
            "collections_status": loan.collections_status,
            "delinquency_started_at": str(loan.delinquency_started_at) if loan.delinquency_started_at else None,
            "aging_bucket": "1-30" if loan.days_past_due <= 30 else "31-60" if loan.days_past_due <= 60 else "61-90" if loan.days_past_due <= 90 else "90+",
            "maturity_date": str(loan.maturity_date) if loan.maturity_date else None,
        })

    return {
        "data": loans_data,
        "pagination": {
            "page": meta.page,
            "page_size": meta.page_size,
            "total_items": meta.total_items,
            "total_pages": meta.total_pages,
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# POST /admin/collections/{loan_id}/action — Log a collection action
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.post(
    "/collections/{loan_id}/action",
    response_model=SuccessResponse,
    summary="Log a collections action on a delinquent loan",
)
async def admin_collections_action(
    loan_id: uuid.UUID,
    request: Request,
    action_type: str = Query(..., description="Type of action (phone_call, email, letter, payment_plan, etc.)"),
    notes: str = Query("", description="Notes about the action"),
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.collections,
    )),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Log a collection action for a delinquent loan."""
    result = await db.execute(
        select(Loan).where(Loan.id == loan_id)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found",
        )

    if loan.status != LoanStatus.delinquent:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Loan is not in delinquent status",
        )

    # Update collections status
    loan.collections_status = loan.collections_status or action_type

    await create_audit_log(
        db,
        action=AuditAction.admin_action.value,
        resource_type="loan",
        resource_id=str(loan.id),
        actor_id=admin.id,
        actor_type="admin",
        admin_user_id=admin.id,
        details={
            "action_type": action_type,
            "notes": notes,
            "days_past_due": loan.days_past_due,
        },
        description=f"Collections action '{action_type}' on loan {loan.id}",
        ip_address=request.client.host if request.client else None,
        request_id=getattr(request.state, "request_id", None),
    )

    return SuccessResponse(
        message=f"Collection action '{action_type}' logged for loan {loan_id}.",
        data={
            "loan_id": str(loan.id),
            "action_type": action_type,
            "notes": notes,
            "days_past_due": loan.days_past_due,
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/audit-log — Query audit log
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/audit-log",
    response_model=PaginatedResponse[AuditLogListResponse],
    summary="Query the audit log with filters",
)
async def admin_audit_log(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    actor_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.compliance, AdminRole.viewer,
    )),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AuditLogListResponse]:
    """Query the immutable audit trail with filters."""
    base = select(AuditLog)
    conditions = []
    if actor_type:
        conditions.append(AuditLog.actor_type == actor_type)
    if action:
        conditions.append(AuditLog.action == action)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if resource_id:
        conditions.append(AuditLog.resource_id == resource_id)
    if severity:
        conditions.append(AuditLog.severity == severity)
    if created_after:
        conditions.append(AuditLog.created_at >= created_after)
    if created_before:
        conditions.append(AuditLog.created_at <= created_before)
    if search:
        conditions.append(
            or_(
                AuditLog.description.ilike(f"%{search}%"),
                AuditLog.resource_id.ilike(f"%{search}%"),
            )
        )
    if conditions:
        base = base.where(and_(*conditions))
    base = base.order_by(desc(AuditLog.created_at))

    items, meta = await _paginated_response(db, base, page, page_size)

    data = [
        AuditLogListResponse(
            id=str(log.id),
            created_at=log.created_at,
            actor_id=str(log.actor_id) if log.actor_id else None,
            actor_type=log.actor_type,
            admin_user_id=str(log.admin_user_id) if log.admin_user_id else None,
            action=log.action.value if hasattr(log.action, 'value') else str(log.action),
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            changes=log.changes,
            description=log.description,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            request_id=log.request_id,
            severity=log.severity,
            admin_display_name=None,
        )
        for log in items
    ]

    return PaginatedResponse[AuditLogListResponse](data=data, pagination=meta)


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/compliance — Compliance events
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/compliance",
    summary="List compliance events",
)
async def admin_compliance(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.compliance,
    )),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return compliance events with filtering."""
    base = select(ComplianceEvent).options(
        selectinload(ComplianceEvent.application),
        selectinload(ComplianceEvent.borrower),
    )
    conditions = []
    if event_type:
        conditions.append(ComplianceEvent.event_type == event_type)
    if status_filter:
        conditions.append(ComplianceEvent.status == status_filter)
    if conditions:
        base = base.where(and_(*conditions))
    base = base.order_by(desc(ComplianceEvent.created_at))

    items, meta = await _paginated_response(db, base, page, page_size)

    data = []
    for evt in items:
        borrower_name = None
        if evt.borrower:
            borrower_name = f"{evt.borrower.first_name} {evt.borrower.last_name}"
        data.append({
            "id": str(evt.id),
            "application_id": str(evt.application_id) if evt.application_id else None,
            "borrower_id": str(evt.borrower_id),
            "borrower_name": borrower_name,
            "event_type": evt.event_type.value if hasattr(evt.event_type, 'value') else str(evt.event_type),
            "status": evt.status,
            "reason_codes": evt.reason_codes,
            "reason_description": evt.reason_description,
            "action_taken": evt.action_taken,
            "sent_at": evt.sent_at.isoformat() if evt.sent_at else None,
            "sent_via": evt.sent_via,
            "delivery_status": evt.delivery_status,
            "acknowledged_at": evt.acknowledged_at.isoformat() if evt.acknowledged_at else None,
            "created_at": evt.created_at.isoformat(),
        })

    return {
        "data": data,
        "pagination": {
            "page": meta.page,
            "page_size": meta.page_size,
            "total_items": meta.total_items,
            "total_pages": meta.total_pages,
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/settings — Get system settings
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/settings",
    summary="Get system settings",
)
async def admin_get_settings(
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin,
    )),
) -> dict[str, Any]:
    """Return current system settings (non-secret values only)."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
        "rate_limit_auth_per_minute": settings.RATE_LIMIT_AUTH_PER_MINUTE,
        "mfa_issuer_name": settings.MFA_ISSUER_NAME,
        "jwt_algorithm": settings.JWT_ALGORITHM,
        "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expire_days": settings.REFRESH_TOKEN_EXPIRE_DAYS,
        "s3_bucket": settings.S3_BUCKET,
        "s3_region": settings.S3_REGION,
        "plaid_env": settings.PLAID_ENV,
        "cors_origins": settings.CORS_ORIGINS,
        "credit_bureau_base_url": settings.CREDIT_BUREAU_BASE_URL,
    }


# ──────────────────────────────────────────────────────────────────────────────
# PUT /admin/settings — Update system settings
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.put(
    "/settings",
    response_model=SuccessResponse,
    summary="Update system settings (selected keys)",
)
async def admin_update_settings(
    payload: dict[str, Any],
    request: Request,
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin,
    )),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Update system settings. Only super_admin can modify settings.

    Note: In a real implementation, settings would be persisted in a DB table
    or config service. For MVP, we acknowledge the update request.
    """
    allowed_keys = {
        "rate_limit_per_minute", "rate_limit_auth_per_minute",
        "debug", "s3_bucket", "cors_origins",
    }
    updated = {k: v for k, v in payload.items() if k in allowed_keys}

    await create_audit_log(
        db,
        action=AuditAction.admin_action.value,
        resource_type="settings",
        resource_id="system",
        actor_id=admin.id,
        actor_type="admin",
        admin_user_id=admin.id,
        details={"updated_keys": list(updated.keys())},
        description=f"System settings updated by {admin.email}",
        ip_address=request.client.host if request.client else None,
        request_id=getattr(request.state, "request_id", None),
    )

    return SuccessResponse(
        message="Settings update acknowledged (applied on next restart for MVP).",
        data={"updated": updated, "note": "Settings will take effect on next application restart."},
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /admin/reports/generate — Generate portfolio report CSV
# ──────────────────────────────────────────────────────────────────────────────


@admin_router.get(
    "/reports/generate",
    summary="Generate a portfolio report CSV",
)
async def admin_generate_report(
    request: Request,
    report_type: str = Query("portfolio", description="Report type: portfolio, applications, payments"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    admin: AdminUser = Depends(require_admin_role(
        AdminRole.super_admin, AdminRole.compliance,
    )),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Generate and return a CSV report of the portfolio."""
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "applications":
        writer.writerow(["Application ID", "Borrower ID", "Status", "Requested Amount", "Loan Purpose", "Created At", "Decisioned At", "Amount Funded"])
        base = select(Application)
        if start_date:
            base = base.where(Application.created_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc))
        if end_date:
            base = base.where(Application.created_at <= datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc))
        results = await db.execute(base)
        for app in results.scalars().all():
            writer.writerow([
                str(app.id), str(app.borrower_id), app.status.value,
                float(app.requested_amount), app.loan_purpose,
                app.created_at.isoformat(),
                app.decisioned_at.isoformat() if app.decisioned_at else "",
                float(app.amount_funded) if app.amount_funded else "",
            ])
    elif report_type == "payments":
        writer.writerow(["Payment ID", "Loan ID", "Borrower ID", "Payment Number", "Status", "Scheduled Date", "Paid Date", "Total Amount", "Amount Paid", "Method"])
        base = select(Payment)
        if start_date:
            base = base.where(Payment.scheduled_date >= start_date)
        if end_date:
            base = base.where(Payment.scheduled_date <= end_date)
        results = await db.execute(base)
        for pmt in results.scalars().all():
            writer.writerow([
                str(pmt.id), str(pmt.loan_id), str(pmt.borrower_id),
                pmt.payment_number, pmt.status.value,
                str(pmt.scheduled_date), str(pmt.paid_date) if pmt.paid_date else "",
                float(pmt.total_amount), float(pmt.amount_paid) if pmt.amount_paid else "",
                pmt.payment_method or "",
            ])
    else:  # default: portfolio
        writer.writerow(["Loan ID", "Application ID", "Borrower ID", "Status", "Loan Amount", "APR", "Term Months", "Monthly Payment", "Days Past Due", "Total Due", "Origination Date", "Maturity Date", "Paid Off At"])
        results = await db.execute(select(Loan))
        for loan in results.scalars().all():
            writer.writerow([
                str(loan.id), str(loan.application_id), str(loan.borrower_id),
                loan.status.value, float(loan.loan_amount), float(loan.apr),
                loan.term_months, float(loan.monthly_payment),
                loan.days_past_due, float(loan.total_amount_due),
                str(loan.origination_date) if loan.origination_date else "",
                str(loan.maturity_date) if loan.maturity_date else "",
                loan.paid_off_at.isoformat() if loan.paid_off_at else "",
            ])

    csv_content = output.getvalue()
    output.close()

    filename = f"{report_type}_report_{date.today().isoformat()}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report-Type": report_type,
        },
    )
