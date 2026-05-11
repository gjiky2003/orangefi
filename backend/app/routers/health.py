"""
Health check and utility endpoints.
"""

from fastapi import APIRouter

health_router = APIRouter(tags=["health"])
