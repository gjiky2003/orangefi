#!/usr/bin/env python3
"""
Stage 1: Gating Rules — Hard Pass/Fail Checks for OrangeFi.

Runs *before* any risk scoring to enforce regulatory, fraud, and policy
boundaries. Returns one of three actions:
    - decline  → Immediate decline, no scoring
    - flag     → Passed gates but flagged for attention (e.g. MLA)
    - pass     → All gates clear, proceed to scoring

Rules Implemented
-----------------
Hard Decline Rules:
    1. Bankruptcy in last 7 years
    2. Credit score < 580 (or redirect to credit-builder product)
    3. Annual income < $25k
    4. Any 90+ day delinquency in last 12 months
    5. Active tax lien or judgment
    6. Identity fraud probability > 85%
    7. OFAC/SDN sanctions match

Flag Rules:
    8. Military borrower → apply MLA 36% cap (not decline)
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("orangefi.underwriting.gating")


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _parse_date(value: Any) -> Optional[datetime.date]:
    """Parse a value into a `datetime.date`."""
    if value is None:
        return None
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d", "%d/%m/%Y"):
            try:
                return datetime.datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    if isinstance(value, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(float(value)).date()
        except (OSError, ValueError, OverflowError):
            pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
#  GatingRules
# ──────────────────────────────────────────────────────────────────────────────


class GatingRules:
    """Stage 1 gating rules engine.

    Evaluates an application against hard decline criteria and flag rules.
    Applications that fail any hard gate are immediately declined. Those
    that pass all gates proceed to Stage 2 risk scoring.

    Parameters
    ----------
    min_credit_score : int
        Minimum acceptable credit score (default: 580).
    min_annual_income : float
        Minimum acceptable annual income in USD (default: 25000).
    bankruptcy_years : int
        Lookback period for bankruptcy in years (default: 7).
    """

    def __init__(
        self,
        min_credit_score: int = 580,
        min_annual_income: float = 25000.0,
        bankruptcy_years: int = 7,
    ) -> None:
        self._min_credit_score = min_credit_score
        self._min_annual_income = min_annual_income
        self._bankruptcy_years = bankruptcy_years

    # ──────────────────────────────────────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────────────────────────────────────

    def evaluate(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run all gating rules against an application.

        Parameters
        ----------
        app_data : dict
            Application data with keys for all gating checks:
            - ``credit_score`` / ``fico_score`` — int
            - ``annual_income`` — float
            - ``bankruptcy_in_7yr`` — bool
            - ``bankruptcy_date`` — optional str
            - ``delinquency_90d_12mo`` — bool
            - ``tax_lien_active`` — bool
            - ``judgment_active`` — bool
            - ``identity_fraud_probability`` — float (0-100)
            - ``ofac_sdn_match`` — bool
            - ``military_borrower`` — bool (SCRA / MLA indicator)

        Returns
        -------
        dict
            ``{'passed': bool, 'reason': str, 'action': str}``
            where action is one of ``'decline'``, ``'flag'``, ``'pass'``.
        """
        # ── Hard Decline Checks ──

        # 1. Bankruptcy in last 7 years
        bankruptcy_result = self._check_bankruptcy(app_data)
        if bankruptcy_result["action"] == "decline":
            logger.info("GATING DECLINE: %s", bankruptcy_result["reason"])
            return bankruptcy_result

        # 2. Credit score < 580
        credit_result = self._check_credit_score(app_data)
        if credit_result["action"] == "decline":
            logger.info("GATING DECLINE: %s", credit_result["reason"])
            return credit_result

        # 3. Annual income < $25k
        income_result = self._check_income(app_data)
        if income_result["action"] == "decline":
            logger.info("GATING DECLINE: %s", income_result["reason"])
            return income_result

        # 4. 90+ day delinquency in last 12 months
        delinquency_result = self._check_delinquency(app_data)
        if delinquency_result["action"] == "decline":
            logger.info("GATING DECLINE: %s", delinquency_result["reason"])
            return delinquency_result

        # 5. Active tax lien or judgment
        lien_result = self._check_liens_and_judgments(app_data)
        if lien_result["action"] == "decline":
            logger.info("GATING DECLINE: %s", lien_result["reason"])
            return lien_result

        # 6. Identity fraud probability > 85%
        fraud_result = self._check_identity_fraud(app_data)
        if fraud_result["action"] == "decline":
            logger.info("GATING DECLINE: %s", fraud_result["reason"])
            return fraud_result

        # 7. OFAC/SDN match
        ofac_result = self._check_ofac_sdn(app_data)
        if ofac_result["action"] == "decline":
            logger.info("GATING DECLINE: %s", ofac_result["reason"])
            return ofac_result

        # ── Flag Rules (not declines) ──

        # 8. Military borrower → MLA cap applies
        military_result = self._check_military_borrower(app_data)

        if military_result["action"] == "flag":
            logger.info("GATING FLAG: %s", military_result["reason"])
            # We still pass, but flag for MLA adjustment in pricing
            return {
                "passed": True,
                "reason": (
                    f"All gates passed. {military_result['reason']}. "
                    "Proceeding to scoring with MLA adjustment."
                ),
                "action": "flag",
                "mla_applicable": True,
            }

        # ── All Clear ──
        return {
            "passed": True,
            "reason": "All gating rules passed. Proceeding to Stage 2 scoring.",
            "action": "pass",
            "mla_applicable": False,
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  Individual Gate Checks
    # ──────────────────────────────────────────────────────────────────────────

    def _check_bankruptcy(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for bankruptcy in the last N years."""
        bankruptcy_flag = app_data.get("bankruptcy_in_7yr", False)
        if not bankruptcy_flag:
            bankruptcy_flag = app_data.get("bankruptcy_flag", False)

        if bankruptcy_flag:
            bk_date = app_data.get("bankruptcy_date")
            if bk_date:
                parsed = _parse_date(bk_date)
                if parsed:
                    cutoff = datetime.date.today() - datetime.timedelta(
                        days=self._bankruptcy_years * 365
                    )
                    if parsed >= cutoff:
                        return {
                            "passed": False,
                            "reason": (
                                f"Bankruptcy on record within the last "
                                f"{self._bankruptcy_years} years (filed {bk_date})."
                            ),
                            "action": "decline",
                        }
            # No date or unparseable — safe to decline
            return {
                "passed": False,
                "reason": (
                    "Bankruptcy flag present on credit report. "
                    "Application declined per OrangeFi policy."
                ),
                "action": "decline",
            }

        return {"passed": True, "reason": "No bankruptcy detected.", "action": "pass"}

    def _check_credit_score(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check minimum credit score threshold."""
        credit_score = app_data.get("credit_score") or app_data.get("fico_score")
        if credit_score is None:
            return {
                "passed": False,
                "reason": (
                    "Credit score not available. "
                    "Unable to verify minimum score requirement."
                ),
                "action": "decline",
            }

        try:
            credit_score = int(credit_score)
        except (ValueError, TypeError):
            return {
                "passed": False,
                "reason": "Invalid credit score value provided.",
                "action": "decline",
            }

        if credit_score < self._min_credit_score:
            return {
                "passed": False,
                "reason": (
                    f"Credit score ({credit_score}) is below the minimum "
                    f"requirement of {self._min_credit_score}. "
                    "Consider applying for OrangeFi Credit Builder."
                ),
                "action": "decline",
                "credit_builder_eligible": True,
            }

        return {
            "passed": True,
            "reason": f"Credit score ({credit_score}) meets minimum requirement.",
            "action": "pass",
        }

    def _check_income(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check minimum annual income threshold."""
        income = app_data.get("annual_income")
        if income is None:
            return {
                "passed": False,
                "reason": (
                    "Annual income not provided. "
                    "Unable to verify minimum income requirement."
                ),
                "action": "decline",
            }

        try:
            income = float(income)
        except (ValueError, TypeError):
            return {
                "passed": False,
                "reason": "Invalid annual income value provided.",
                "action": "decline",
            }

        if income < self._min_annual_income:
            return {
                "passed": False,
                "reason": (
                    f"Annual income (${income:,.2f}) is below the minimum "
                    f"requirement of ${self._min_annual_income:,.2f}."
                ),
                "action": "decline",
            }

        return {
            "passed": True,
            "reason": f"Annual income (${income:,.2f}) meets minimum requirement.",
            "action": "pass",
        }

    def _check_delinquency(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for 90+ day delinquency in last 12 months."""
        delinquency = app_data.get("delinquency_90d_12mo", False)
        if delinquency:
            return {
                "passed": False,
                "reason": (
                    "Credit report shows at least one 90+ day delinquency "
                    "within the last 12 months."
                ),
                "action": "decline",
            }

        # Also check bureau-level delinquency
        bureau_delinquency = app_data.get("bureau_delinquency_90d", False)
        if bureau_delinquency:
            return {
                "passed": False,
                "reason": (
                    "Bureau data indicates 90+ day delinquency "
                    "within the last 12 months."
                ),
                "action": "decline",
            }

        return {
            "passed": True,
            "reason": "No recent 90+ day delinquencies detected.",
            "action": "pass",
        }

    def _check_liens_and_judgments(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for active tax liens or judgments."""
        tax_lien = app_data.get("tax_lien_active", False)
        judgment = app_data.get("judgment_active", False)

        if tax_lien and judgment:
            return {
                "passed": False,
                "reason": (
                    "Credit report shows both an active tax lien "
                    "and an active judgment."
                ),
                "action": "decline",
            }

        if tax_lien:
            return {
                "passed": False,
                "reason": "Active tax lien present on credit report.",
                "action": "decline",
            }

        if judgment:
            return {
                "passed": False,
                "reason": "Active judgment present on credit report.",
                "action": "decline",
            }

        return {
            "passed": True,
            "reason": "No active tax liens or judgments detected.",
            "action": "pass",
        }

    def _check_identity_fraud(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check identity fraud probability threshold."""
        fraud_prob = app_data.get("identity_fraud_probability")
        if fraud_prob is None:
            fraud_prob = app_data.get("fraud_probability", 0.0)

        try:
            fraud_prob = float(fraud_prob)
        except (ValueError, TypeError):
            fraud_prob = 0.0

        if fraud_prob > 85.0:
            return {
                "passed": False,
                "reason": (
                    f"Identity fraud probability ({fraud_prob:.1f}%) "
                    f"exceeds the maximum threshold of 85%."
                ),
                "action": "decline",
            }

        return {
            "passed": True,
            "reason": f"Identity fraud probability ({fraud_prob:.1f}%) is within range.",
            "action": "pass",
        }

    def _check_ofac_sdn(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for OFAC/SDN sanctions match."""
        ofac_match = app_data.get("ofac_sdn_match", False)
        if ofac_match:
            return {
                "passed": False,
                "reason": (
                    "Applicant matched against OFAC Specially Designated "
                    "Nationals (SDN) list. Application cannot be processed."
                ),
                "action": "decline",
            }

        return {
            "passed": True,
            "reason": "No OFAC/SDN match detected.",
            "action": "pass",
        }

    def _check_military_borrower(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if borrower is military (SCRA/MLA)."""
        military = app_data.get("military_borrower", False)
        if military:
            return {
                "passed": True,
                "reason": (
                    "Borrower identified as active-duty military. "
                    "MLA 36% APR cap will be applied to pricing."
                ),
                "action": "flag",
            }

        return {
            "passed": True,
            "reason": "Borrower is not identified as active-duty military.",
            "action": "pass",
        }
