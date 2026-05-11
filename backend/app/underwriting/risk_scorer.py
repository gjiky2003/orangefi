#!/usr/bin/env python3
"""
Stage 2: Risk Scorer — 0-100 Risk Score for OrangeFi.

Calculates a risk score (0-100, higher = riskier) based on weighted
component scores. Adapted from PalmFi's scoring approach, tailored for
OrangeFi's debt consolidation lending focus.

Scoring Components
-------------------
- FICO Score (40%): Lower FICO = higher risk score
- Credit Utilization (15%): Higher utilization = higher risk score
- DTI Ratio (15%): Higher DTI = higher risk score
- Income Stability (15%): Irregular income = higher risk score
- Account Age / Credit History (10%): Thinner/shorter = higher risk score
- Employment Stability (5%): Shorter tenure = higher risk score

Cash Flow Adjustment
--------------------
If cash flow data is available, blend it into the final score with a
configurable weight (default 30%, 50% for thin-file borrowers).
"""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("orangefi.underwriting.scorer")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class RiskScorer:
    """OrangeFi risk scorer — computes 0-100 risk score.

    Uses a weighted component approach where each factor is normalized
    to a 0-100 subscore (higher = riskier), then aggregated with weights.

    Parameters
    ----------
    model_weights_path : str, optional
        Path to model weights JSON. If provided, loads pre-computed
        weights for the XGBoost-style scoring.
    """

    # Default component weights (sums to 1.0)
    DEFAULT_WEIGHTS = {
        "fico_score": 0.40,
        "credit_utilization": 0.15,
        "dti_ratio": 0.15,
        "income_stability": 0.15,
        "account_age": 0.10,
        "employment_stability": 0.05,
    }

    # Cash flow blend defaults
    CASH_FLOW_BLEND_WEIGHT = 0.30
    THIN_FILE_CASH_FLOW_BLEND = 0.50
    THIN_FILE_FICO_THRESHOLD = 620

    def __init__(self, model_weights_path: Optional[str] = None) -> None:
        self._weights = dict(self.DEFAULT_WEIGHTS)
        self._model_loaded = False
        self._booster_params: Optional[Dict[str, Any]] = None

        if model_weights_path is None:
            model_weights_path = os.path.join(BASE_DIR, "models", "model_weights.json")

        if os.path.exists(model_weights_path):
            try:
                with open(model_weights_path, "r") as f:
                    model_data = json.load(f)
                if "weights" in model_data:
                    # Override default weights if present in the model file
                    custom_weights = model_data.get("weights", {})
                    self._weights.update(custom_weights)
                self._booster_params = model_data.get("booster_params")
                self._model_loaded = True
                logger.info(
                    "RiskScorer model weights loaded from %s", model_weights_path
                )
            except (json.JSONDecodeError, IOError) as exc:
                logger.warning(
                    "Could not load model weights from %s: %s. "
                    "Using default weights.",
                    model_weights_path,
                    exc,
                )

    # ──────────────────────────────────────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────────────────────────────────────

    def score(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute risk score for an application.

        Parameters
        ----------
        app_data : dict
            Application data with at minimum:
            - ``credit_score`` or ``fico_score`` — int
            - ``credit_utilization`` or ``utilization`` — float (0-100 or 0-1)
            - ``dti_ratio`` — float (monthly debt / monthly income)
            - ``income_stability`` — str ('stable', 'irregular', 'unknown')
            - ``months_credit_history`` or ``account_age_months`` — int
            - ``employment_months`` or ``years_at_current_job`` — int
            - ``cash_flow_metrics`` (optional) — dict with cash flow data

        Returns
        -------
        dict
            ``{
                'risk_score': int (0-100),
                'component_scores': dict,
                'cash_flow_adjusted': bool,
                'model_version': str,
            }``
        """
        # Compute component subscores (each 0-100, higher = riskier)
        fico_sub = self._subscore_fico(app_data)
        util_sub = self._subscore_utilization(app_data)
        dti_sub = self._subscore_dti(app_data)
        income_sub = self._subscore_income_stability(app_data)
        account_sub = self._subscore_account_age(app_data)
        employment_sub = self._subscore_employment(app_data)

        component_scores = {
            "fico_score": fico_sub,
            "credit_utilization": util_sub,
            "dti_ratio": dti_sub,
            "income_stability": income_sub,
            "account_age": account_sub,
            "employment_stability": employment_sub,
        }

        # Weighted sum
        raw_score = (
            self._weights["fico_score"] * fico_sub
            + self._weights["credit_utilization"] * util_sub
            + self._weights["dti_ratio"] * dti_sub
            + self._weights["income_stability"] * income_sub
            + self._weights["account_age"] * account_sub
            + self._weights["employment_stability"] * employment_sub
        )

        risk_score = int(round(raw_score))
        risk_score = max(0, min(100, risk_score))

        # ── Cash Flow Blend ──
        cash_flow_adjusted = False
        cash_flow_data = app_data.get("cash_flow_metrics")
        if cash_flow_data and isinstance(cash_flow_data, dict):
            cf_score = cash_flow_data.get("cash_flow_score", 50)
            if cf_score is not None:
                cf_risk = max(0, min(100, 100 - cf_score))
                fico = app_data.get("credit_score") or app_data.get("fico_score", 700)
                try:
                    fico = int(fico)
                except (ValueError, TypeError):
                    fico = 700

                blend_weight = (
                    self.THIN_FILE_CASH_FLOW_BLEND
                    if fico < self.THIN_FILE_FICO_THRESHOLD
                    else self.CASH_FLOW_BLEND_WEIGHT
                )

                blended = int(
                    round(risk_score * (1 - blend_weight) + cf_risk * blend_weight)
                )
                if blended != risk_score:
                    risk_score = blended
                    cash_flow_adjusted = True
                    logger.debug(
                        "Cash flow blend applied (weight=%.2f): %d → %d",
                        blend_weight,
                        raw_score if "raw_score" else None,
                        blended,
                    )

        return {
            "risk_score": risk_score,
            "component_scores": component_scores,
            "cash_flow_adjusted": cash_flow_adjusted,
            "model_version": "v1.0.0",
            "model_loaded": self._model_loaded,
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  Component Subscore Functions
    #  Each returns 0-100 where 100 = highest risk
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _subscore_fico(app_data: Dict[str, Any]) -> float:
        """FICO score subscore (weight: 40%).

        Scoring logic:
            850 → 0 (lowest risk)
            800-849 → 5
            740-799 → 15
            670-739 → 35
            580-669 → 65
            < 580 → 100 (highest risk)
        """
        fico = app_data.get("credit_score") or app_data.get("fico_score", 700)
        try:
            fico = int(fico)
        except (ValueError, TypeError):
            return 50  # Default to mid-risk if missing

        if fico >= 850:
            return 0.0
        elif fico >= 800:
            return 5.0
        elif fico >= 740:
            return 15.0
        elif fico >= 670:
            return 35.0
        elif fico >= 580:
            return 65.0
        else:
            return 100.0

    @staticmethod
    def _subscore_utilization(app_data: Dict[str, Any]) -> float:
        """Credit utilization subscore (weight: 15%).

        Higher utilization = higher risk. Supports both 0-100 percentage
        and 0-1 decimal formats.
        """
        util = app_data.get("credit_utilization") or app_data.get("utilization", 0.0)
        try:
            util = float(util)
        except (ValueError, TypeError):
            return 50.0

        # Normalize to percentage if it's a decimal
        if 0.0 <= util <= 1.0:
            util = util * 100.0

        if util >= 90:
            return 100.0
        elif util >= 70:
            return 80.0
        elif util >= 50:
            return 60.0
        elif util >= 30:
            return 40.0
        elif util >= 10:
            return 20.0
        else:
            return 5.0

    @staticmethod
    def _subscore_dti(app_data: Dict[str, Any]) -> float:
        """DTI ratio subscore (weight: 15%).

        Higher DTI = higher risk.
        """
        dti = app_data.get("dti_ratio", 0.0)
        try:
            dti = float(dti)
        except (ValueError, TypeError):
            return 50.0

        if dti >= 0.50:
            return 100.0
        elif dti >= 0.43:
            return 80.0
        elif dti >= 0.36:
            return 60.0
        elif dti >= 0.28:
            return 40.0
        elif dti >= 0.20:
            return 20.0
        else:
            return 5.0

    @staticmethod
    def _subscore_income_stability(app_data: Dict[str, Any]) -> float:
        """Income stability subscore (weight: 15%).

        Irregular income = higher risk score.
        """
        stability = app_data.get("income_stability", "unknown")

        if isinstance(stability, str):
            stability_map = {
                "stable": 10.0,
                "verified": 15.0,
                "regular": 20.0,
                "unknown": 50.0,
                "irregular": 70.0,
                "unstable": 85.0,
                "variable": 75.0,
                "seasonal": 70.0,
                "self_employed": 60.0,
            }
            return stability_map.get(stability.lower(), 50.0)

        # If it's a numeric stability score (0-100), use it directly
        try:
            score = float(stability)
            return max(0.0, min(100.0, score))
        except (ValueError, TypeError):
            return 50.0

    @staticmethod
    def _subscore_account_age(app_data: Dict[str, Any]) -> float:
        """Account age / credit history subscore (weight: 10%).

        Thinner/shorter history = higher risk.
        """
        age_months = app_data.get(
            "months_credit_history",
            app_data.get("account_age_months", 0),
        )
        try:
            age_months = int(age_months)
        except (ValueError, TypeError):
            return 50.0

        if age_months >= 120:  # 10+ years
            return 5.0
        elif age_months >= 84:  # 7+ years
            return 15.0
        elif age_months >= 60:  # 5+ years
            return 30.0
        elif age_months >= 36:  # 3+ years
            return 50.0
        elif age_months >= 12:  # 1+ years
            return 70.0
        elif age_months >= 6:  # 6+ months
            return 85.0
        else:
            return 100.0  # Thin/no file

    @staticmethod
    def _subscore_employment(app_data: Dict[str, Any]) -> float:
        """Employment stability subscore (weight: 5%).

        Shorter tenure = higher risk.
        """
        emp_months = app_data.get(
            "employment_months",
            app_data.get("months_at_current_job", None),
        )

        # If not in months, try years_at_current_job
        if emp_months is None:
            emp_years = app_data.get("years_at_current_job", 0)
            try:
                emp_years = float(emp_years)
                emp_months = emp_years * 12
            except (ValueError, TypeError):
                emp_months = 0

        try:
            emp_months = float(emp_months)
        except (ValueError, TypeError):
            return 50.0

        if emp_months >= 120:  # 10+ years
            return 5.0
        elif emp_months >= 60:  # 5+ years
            return 15.0
        elif emp_months >= 36:  # 3+ years
            return 30.0
        elif emp_months >= 12:  # 1+ years
            return 50.0
        elif emp_months >= 6:  # 6+ months
            return 70.0
        elif emp_months >= 3:  # 3+ months
            return 85.0
        else:
            return 100.0  # New job / unemployed
