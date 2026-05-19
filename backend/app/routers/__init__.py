"""API route modules — mounted under /api/v1 by the FastAPI application."""

from app.routers.health import health_router
from app.routers.borrower import borrower_router
from app.routers.admin import admin_router
from app.routers.integrations import integrations_router
from app.routers.servicing import router as servicing_router
from app.routers.compliance_monitor import router as compliance_router
from app.underwriting.routers import underwriting_router
from app.routers.agent import router as agent_router

__all__ = [
    "health_router",
    "borrower_router",
    "admin_router",
    "integrations_router",
    "servicing_router",
    "compliance_router",
    "underwriting_router",
    "agent_router",
]
