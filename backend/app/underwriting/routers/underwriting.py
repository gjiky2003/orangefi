#!/usr/bin/env python3
"""
OrangeFi Underwriting API — FastAPI Router.

Provides internal underwriting API endpoints:
  - POST /score — Full underwriting on application data
  - POST /pre-qualify — Lightweight pre-qualification (soft pull only)
  - GET /tiers — List pricing tiers
  - GET /models — List model versions
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from app.underwriting.decision_engine import DecisionEngine
from app.underwriting.pricing import PricingEngine
from app.underwriting.models import get_model_versions

logger = logging.getLogger("orangefi.underwriting.api")

# ──────────────────────────────────────────────────────────────────────────────
#  Router
# ──────────────────────────────────────────────────────────────────────────────

underwriting_router = APIRouter(
    prefix="/underwriting",
    tags=["Underwriting"],
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)

# Singleton engine instances
_decision_engine: Optional[DecisionEngine] = None
_pricing_engine: Optional[PricingEngine] = None


def _get_engine() -> DecisionEngine:
    """Get or create the singleton decision engine."""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine


def _get_pricing() -> PricingEngine:
    """Get or create the singleton pricing engine."""
    global _pricing_engine
    if _pricing_engine is None:
        _pricing_engine = PricingEngine()
    return _pricing_engine


# ──────────────────────────────────────────────────────────────────────────────
#  Pydantic Schemas (inline for simplicity)
# ──────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    """Request body for full underwriting score endpoint."""

    application_id: str = Field(
        ..., description="Unique application identifier", examples=["UW-2026-00123"]
    )
    credit_score: Optional[int] = Field(
        None, ge=300, le=850, description="FICO credit score"
    )
    fico_score: Optional[int] = Field(None, ge=300, le=850, description="FICO score (alias)")
    annual_income: float = Field(..., gt=0, description="Annual income in USD")
    dti_ratio: float = Field(
        ..., ge=0, le=1.0, description="Debt-to-income ratio (decimal)"
    )
    credit_utilization: Optional[float] = Field(
        None, ge=0, le=100, description="Credit utilization percentage (0-100)"
    )
    utilization: Optional[float] = Field(
        None, ge=0, le=1.0, description="Credit utilization decimal (0-1)"
    )
    loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    term_months: int = Field(36, ge=12, le=60, description="Requested term in months")
    requested_term_months: Optional[int] = Field(
        None, ge=12, le=60, description="Alias for term_months"
    )
    income_stability: Optional[str] = Field(
        None,
        description="Income stability: stable|regular|variable|irregular|self_employed|unknown",
    )
    employment_months: Optional[int] = Field(
        None, ge=0, description="Months at current employer"
    )
    years_at_current_job: Optional[float] = Field(
        None, ge=0, description="Years at current employer"
    )
    months_credit_history: Optional[int] = Field(
        None, ge=0, description="Months of credit history"
    )
    account_age_months: Optional[int] = Field(
        None, ge=0, description="Alias for months_credit_history"
    )
    bankruptcy_in_7yr: Optional[bool] = Field(
        False, description="Bankruptcy in last 7 years"
    )
    delinquency_90d_12mo: Optional[bool] = Field(
        False, description="90+ day delinquency in last 12 months"
    )
    tax_lien_active: Optional[bool] = Field(False, description="Active tax lien")
    judgment_active: Optional[bool] = Field(False, description="Active judgment")
    identity_fraud_probability: Optional[float] = Field(
        None, ge=0, le=100, description="Identity fraud probability (0-100)"
    )
    ofac_sdn_match: Optional[bool] = Field(
        False, description="OFAC/SDN sanctions list match"
    )
    military_borrower: Optional[bool] = Field(
        False, description="Active-duty military borrower"
    )
    cash_flow_metrics: Optional[Dict[str, Any]] = Field(
        None, description="Cash flow analysis metrics (optional)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "application_id": "UW-2026-00123",
                "credit_score": 720,
                "annual_income": 85000.00,
                "dti_ratio": 0.28,
                "credit_utilization": 35,
                "loan_amount": 15000.00,
                "term_months": 36,
                "income_stability": "stable",
                "employment_months": 60,
                "months_credit_history": 96,
                "bankruptcy_in_7yr": False,
                "delinquency_90d_12mo": False,
                "identity_fraud_probability": 5.0,
            }
        }


class PreQualifyRequest(BaseModel):
    """Request body for lightweight pre-qualification."""

    credit_score: Optional[int] = Field(
        None, ge=300, le=850, description="FICO credit score"
    )
    annual_income: float = Field(..., gt=0, description="Annual income in USD")
    requested_amount: float = Field(..., gt=0, description="Requested loan amount")
    dti_ratio: Optional[float] = Field(
        None, ge=0, le=1.0, description="Debt-to-income ratio"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "credit_score": 700,
                "annual_income": 75000.00,
                "requested_amount": 10000.00,
                "dti_ratio": 0.25,
            }
        }


# ──────────────────────────────────────────────────────────────────────────────
#  Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@underwriting_router.post("/score")
async def score_application(request: ScoreRequest) -> Dict[str, Any]:
    """Run full two-tiered underwriting on application data.

    Stage 1: Gating Rules — hard pass/fail checks.
    Stage 2: Risk Score + Pricing + Decision.

    Returns complete underwriting result including offer terms for
    approved applications or adverse action codes for declines.
    """
    try:
        engine = _get_engine()

        # Normalize request data to app_data dict
        app_data = request.model_dump(exclude_none=True)

        # Handle field aliases
        if "fico_score" in app_data and "credit_score" not in app_data:
            app_data["credit_score"] = app_data["fico_score"]

        if "requested_term_months" in app_data and "term_months" not in app_data:
            app_data["term_months"] = app_data["requested_term_months"]

        if "account_age_months" in app_data and "months_credit_history" not in app_data:
            app_data["months_credit_history"] = app_data["account_age_months"]

        if "utilization" in app_data and "credit_utilization" not in app_data:
            app_data["credit_utilization"] = app_data["utilization"]

        if "years_at_current_job" in app_data and "employment_months" not in app_data:
            app_data["employment_months"] = (
                app_data["years_at_current_job"] * 12
            )

        result = engine.evaluate(
            application_id=request.application_id,
            app_data=app_data,
        )

        return {
            "success": True,
            "data": result,
        }

    except Exception as exc:
        logger.exception("Underwriting score failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Underwriting engine error: {str(exc)}",
        )


@underwriting_router.post("/pre-qualify")
async def pre_qualify(request: PreQualifyRequest) -> Dict[str, Any]:
    """Lightweight pre-qualification (soft pull only).

    Returns an estimated risk score range, tier, and indicative APR range
    without running hard credit checks or gating rules.
    """
    try:
        engine = _get_engine()

        app_data: Dict[str, Any] = {
            "credit_score": request.credit_score or 700,
            "annual_income": request.annual_income,
            "requested_amount": request.requested_amount,
            "loan_amount": request.requested_amount,
            "dti_ratio": request.dti_ratio or 0.35,
        }

        result = engine.pre_qualify(app_data)

        return {
            "success": True,
            "data": result,
        }

    except Exception as exc:
        logger.exception("Pre-qualification failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Pre-qualification error: {str(exc)}",
        )


@underwriting_router.get("/tiers")
async def list_tiers() -> Dict[str, Any]:
    """List all pricing tiers with their configurations."""
    try:
        pricing = _get_pricing()
        tiers = pricing.list_tiers()

        return {
            "success": True,
            "data": {
                "tiers": tiers,
                "available_terms": pricing.TERM_OPTIONS,
                "mla_max_apr": pricing.MLA_MAX_APR,
            },
        }

    except Exception as exc:
        logger.exception("Failed to list tiers: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve pricing tiers: {str(exc)}",
        )


@underwriting_router.get("/models")
async def list_models() -> Dict[str, Any]:
    """List available model versions and their metadata."""
    try:
        models = get_model_versions()

        return {
            "success": True,
            "data": {
                "models": models,
                "current_model": models[0] if models else None,
            },
        }

    except Exception as exc:
        logger.exception("Failed to list models: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve model info: {str(exc)}",
        )
