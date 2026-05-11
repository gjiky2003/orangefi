"""API route modules — mounted under /api/v1 by the FastAPI application."""

from app.routers.health import health_router
from app.routers.borrower import borrower_router
from app.routers.admin import admin_router
from app.routers.integrations import integrations_router
from app.underwriting.routers import underwriting_router

__all__ = [
    "health_router",
    "borrower_router",
    "admin_router",
    "integrations_router",
    "underwriting_router",
]
