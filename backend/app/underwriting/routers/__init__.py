"""Underwriting API route module — mounted under /api/v1 by the FastAPI application."""

from app.underwriting.routers.underwriting import underwriting_router

__all__ = ["underwriting_router"]
