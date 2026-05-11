"""
OrangeFi Underwriting Engine — Two-Tiered Risk Assessment.

Architecture
------------
Stage 1: Gating Rules (hard pass/fail checks)
Stage 2: Risk Score (0-100) + Pricing (tier-based) + Decision

Inspired by PalmFi's proven underwriting approach, adapted for OrangeFi's
debt consolidation lending focus.
"""

from __future__ import annotations

from app.underwriting.gating_rules import GatingRules
from app.underwriting.risk_scorer import RiskScorer
from app.underwriting.pricing import PricingEngine
from app.underwriting.decision_engine import DecisionEngine
from app.underwriting.adverse_action import AdverseActionGenerator

__all__ = [
    "GatingRules",
    "RiskScorer",
    "PricingEngine",
    "DecisionEngine",
    "AdverseActionGenerator",
]

__version__ = "1.0.0"
