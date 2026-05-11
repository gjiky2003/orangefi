"""
OrangeFi Lending Platform — Pydantic v2 API Schemas

All request/response schemas use Pydantic v2 style with model_config,
field validators, and proper Python type hints. UUIDs are represented
as strings for API friendliness. Timestamps are datetime (UTC).
"""

from app.schemas.common import (
    ErrorResponse,
    HealthResponse,
    PaginationMeta,
    PaginatedResponse,
    SuccessResponse,
    ValidationErrorDetail,
)
from app.schemas.borrower import (
    BorrowerCreate,
    BorrowerLogin,
    BorrowerLoginResponse,
    BorrowerPreQualificationRequest,
    BorrowerPreQualificationResponse,
    BorrowerRegister,
    BorrowerResponse,
    BorrowerUpdate,
)
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDecisionRequest,
    ApplicationDecisionResponse,
    ApplicationDetailResponse,
    ApplicationListFilter,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatusHistory,
)
from app.schemas.loan import (
    LoanDetailResponse,
    LoanListFilter,
    LoanListResponse,
    LoanPaymentScheduleItem,
    LoanResponse,
    LoanSummary,
)
from app.schemas.payment import (
    MakePaymentRequest,
    MakePaymentResponse,
    PaymentListFilter,
    PaymentListResponse,
    PaymentResponse,
    PaymentScheduleItem,
)
from app.schemas.admin import (
    AdminCreateRequest,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminMfaSetupResponse,
    AdminMfaVerifyRequest,
    AdminResponse,
    AdminUpdateRequest,
    AdminUserListFilter,
)
from app.schemas.audit import (
    AuditLogDetailResponse,
    AuditLogListFilter,
    AuditLogListResponse,
    AuditLogResponse,
)

__all__ = [
    # Common
    "ErrorResponse",
    "HealthResponse",
    "PaginationMeta",
    "PaginatedResponse",
    "SuccessResponse",
    "ValidationErrorDetail",
    # Borrower
    "BorrowerCreate",
    "BorrowerLogin",
    "BorrowerLoginResponse",
    "BorrowerPreQualificationRequest",
    "BorrowerPreQualificationResponse",
    "BorrowerRegister",
    "BorrowerResponse",
    "BorrowerUpdate",
    # Application
    "ApplicationCreate",
    "ApplicationDecisionRequest",
    "ApplicationDecisionResponse",
    "ApplicationDetailResponse",
    "ApplicationListFilter",
    "ApplicationListResponse",
    "ApplicationResponse",
    "ApplicationStatusHistory",
    # Loan
    "LoanDetailResponse",
    "LoanListFilter",
    "LoanListResponse",
    "LoanPaymentScheduleItem",
    "LoanResponse",
    "LoanSummary",
    # Payment
    "MakePaymentRequest",
    "MakePaymentResponse",
    "PaymentListFilter",
    "PaymentListResponse",
    "PaymentResponse",
    "PaymentScheduleItem",
    # Admin
    "AdminCreateRequest",
    "AdminLoginRequest",
    "AdminLoginResponse",
    "AdminMfaSetupResponse",
    "AdminMfaVerifyRequest",
    "AdminResponse",
    "AdminUpdateRequest",
    "AdminUserListFilter",
    # Audit
    "AuditLogDetailResponse",
    "AuditLogListFilter",
    "AuditLogListResponse",
    "AuditLogResponse",
]
