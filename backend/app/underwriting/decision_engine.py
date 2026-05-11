#!/usr/bin/env python3
"""
OrangeFi Decision Engine — Combines Gating + Scoring + Pricing.

Two-Tiered Decision Flow
------------------------
Stage 1: Gating Rules → Pass/Fail
Stage 2: Risk Score → Score + Tier + Pricing → Final Decision

Final Decision Logic:
  - Score 0-40:   Auto-approve
  - Score 41-55:  Manual review (gray zone)
  - Score 56-100: Decline

For approved applications, generates complete offer terms.
For declined applications, generates adverse action codes.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, List, Optional

from app.underwriting.gating_rules import GatingRules
from app.underwriting.risk_scorer import RiskScorer
from app.underwriting.pricing import PricingEngine
from app.underwriting.adverse_action import AdverseActionGenerator

logger = logging.getLogger("orangefi.underwriting.decision")


class DecisionEngine:
    """OrangeFi two-tiered decision engine.

    Orchestrates the full underwriting pipeline:
        1. Gating Rules (Stage 1)
        2. Risk Scoring (Stage 2)
        3. Pricing & Offer Generation
        4. Final Decision

    Parameters
    ----------
    gating_rules : GatingRules, optional
        Stage 1 gating rules instance.
    risk_scorer : RiskScorer, optional
        Stage 2 risk scorer instance.
    pricing : PricingEngine, optional
        Pricing engine instance.
    adverse_action : AdverseActionGenerator, optional
        Adverse action generator instance.
    """

    # Decision thresholds (risk score 0-100)
    AUTO_APPROVE_MAX_SCORE = 40
    MANUAL_REVIEW_MAX_SCORE = 55
    # Score 56-100 = Decline

    def __init__(
        self,
        gating_rules: Optional[GatingRules] = None,
        risk_scorer: Optional[RiskScorer] = None,
        pricing: Optional[PricingEngine] = None,
        adverse_action: Optional[AdverseActionGenerator] = None,
    ) -> None:
        self._gating = gating_rules or GatingRules()
        self._scorer = risk_scorer or RiskScorer()
        self._pricing = pricing or PricingEngine()
        self._adverse = adverse_action or AdverseActionGenerator()

    # ──────────────────────────────────────────────────────────────────────────
    #  Full Underwriting Decision
    # ──────────────────────────────────────────────────────────────────────────

    def evaluate(
        self,
        application_id: str,
        app_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run full two-tiered underwriting on application data.

        Parameters
        ----------
        application_id : str
            Unique application identifier.
        app_data : dict
            Complete application data including borrower financials,
            credit data, and identity verification results.

        Returns
        -------
        dict
            Complete underwriting result with:
            - decision: 'approved', 'manual_review', or 'declined'
            - gating_result: Stage 1 results
            - risk_score: Stage 2 score
            - tier: pricing tier
            - offer: loan offer (if approved)
            - adverse_action: adverse action codes (if declined)
            - timestamp: decision timestamp
        """
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # ══════════════════════════════════════════════════════════════════
        # Stage 1: Gating Rules
        # ══════════════════════════════════════════════════════════════════
        gating_result = self._gating.evaluate(app_data)

        if gating_result["action"] == "decline":
            logger.info(
                "Application %s declined at Stage 1 (gating): %s",
                application_id,
                gating_result["reason"],
            )

            decision_result = {
                "application_id": application_id,
                "decision": "declined",
                "decision_stage": "gating",
                "gating_result": gating_result,
                "gating_reason": gating_result["reason"],
                "risk_score": None,
                "risk_factors": {},
                "tier": None,
                "offer": None,
                "decline_reasons": [gating_result["reason"]],
                "timestamp": timestamp,
                "credit_builder_eligible": gating_result.get(
                    "credit_builder_eligible", False
                ),
            }

            # Generate adverse action notice
            adverse = self._adverse.generate_notice(
                application_data=app_data,
                decision_result=decision_result,
            )
            decision_result["adverse_action"] = adverse

            return decision_result

        # Extract MLA flag
        mla_applicable = gating_result.get("mla_applicable", False)

        # ══════════════════════════════════════════════════════════════════
        # Stage 2: Risk Scoring
        # ══════════════════════════════════════════════════════════════════
        scoring_result = self._scorer.score(app_data)
        risk_score = scoring_result["risk_score"]
        component_scores = scoring_result["component_scores"]
        cash_flow_adjusted = scoring_result["cash_flow_adjusted"]

        logger.info(
            "Application %s scored at Stage 2: risk_score=%d, "
            "cash_flow_adjusted=%s",
            application_id,
            risk_score,
            cash_flow_adjusted,
        )

        # Determine tier
        tier = self._pricing.get_tier(risk_score)
        tier_config = self._pricing.get_tier_config(tier)

        # ══════════════════════════════════════════════════════════════════
        # Final Decision
        # ══════════════════════════════════════════════════════════════════
        if risk_score <= self.AUTO_APPROVE_MAX_SCORE:
            decision = "approved"
            decision_label = "Auto-Approved"
        elif risk_score <= self.MANUAL_REVIEW_MAX_SCORE:
            decision = "manual_review"
            decision_label = "Manual Review Required"
        else:
            decision = "declined"
            decision_label = "Declined — Risk Score Too High"

        # Build risk factors for adverse action / explanation
        risk_factors = self._build_risk_factors(app_data, component_scores, risk_score)

        # ══════════════════════════════════════════════════════════════════
        # Offer Generation (approved or manual review)
        # ══════════════════════════════════════════════════════════════════
        loan_amount = float(
            app_data.get("loan_amount", app_data.get("requested_amount", 0.0))
        )
        dti_ratio = float(app_data.get("dti_ratio", 0.0))
        term_months = int(
            app_data.get("term_months", app_data.get("requested_term_months", 36))
        )

        offer = None
        if decision in ("approved", "manual_review"):
            try:
                offer = self._pricing.generate_offer(
                    loan_amount=loan_amount,
                    risk_score=risk_score,
                    dti_ratio=dti_ratio,
                    term_months=term_months,
                    mla_applicable=mla_applicable,
                )
            except Exception as exc:
                logger.error(
                    "Offer generation failed for %s: %s",
                    application_id,
                    exc,
                )
                offer = None

        # ══════════════════════════════════════════════════════════════════
        # Build Complete Result
        # ══════════════════════════════════════════════════════════════════
        decision_result = {
            "application_id": application_id,
            "decision": decision,
            "decision_label": decision_label,
            "decision_stage": "scoring",
            "gating_result": gating_result,
            "gating_reason": gating_result.get("reason"),
            "scoring_result": scoring_result,
            "risk_score": risk_score,
            "component_scores": component_scores,
            "risk_factors": risk_factors,
            "cash_flow_adjusted": cash_flow_adjusted,
            "tier": tier,
            "tier_label": self._pricing.get_risk_label(tier),
            "tier_config": {
                "min_apr": tier_config["min_apr"],
                "max_apr": tier_config["max_apr"],
                "max_loan_amount": tier_config["max_loan"],
                "origination_fee_pct": tier_config["origination_pct"],
            },
            "offer": offer,
            "mla_applicable": mla_applicable,
            "decline_reasons": [],
            "timestamp": timestamp,
            "model_version": scoring_result.get("model_version", "v1.0.0"),
        }

        # Generate adverse action for declined applications
        if decision == "declined":
            decline_reasons = self._generate_decline_reasons(
                risk_score, risk_factors, gating_result
            )
            decision_result["decline_reasons"] = decline_reasons

            adverse = self._adverse.generate_notice(
                application_data=app_data,
                decision_result=decision_result,
            )
            decision_result["adverse_action"] = adverse

        # Counter-offer for high DTI borderline declines
        if decision == "declined" and risk_score <= 60:
            counter_amount = self._calculate_counter_offer(
                loan_amount, risk_score, dti_ratio
            )
            if counter_amount and counter_amount >= 1000:
                counter_offer = self._pricing.generate_offer(
                    loan_amount=counter_amount,
                    risk_score=risk_score,
                    dti_ratio=dti_ratio,
                    term_months=term_months,
                    mla_applicable=mla_applicable,
                )
                decision_result["counter_offer"] = counter_offer
                decision_result["counter_offer_message"] = (
                    f"Consider a lower loan amount of "
                    f"${counter_amount:,.2f} at {counter_offer['apr']}% APR."
                )

        # Credit builder redirect for thin-file applicants
        if risk_score >= 70 and decision == "declined":
            decision_result["credit_builder_eligible"] = True

        return decision_result

    # ──────────────────────────────────────────────────────────────────────────
    #  Pre-Qualification (Soft Pull Only)
    # ──────────────────────────────────────────────────────────────────────────

    def pre_qualify(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Lightweight pre-qualification that uses only soft-pull data.

        Does NOT run hard gating checks that would trigger a hard credit
        inquiry (e.g. detailed bankruptcy checks). Returns estimated
        score range and tier.

        Parameters
        ----------
        app_data : dict
            Limited application data (soft pull only). Must include:
            - ``credit_score`` or ``fico_score``
            - ``annual_income``
            - ``requested_amount``

        Returns
        -------
        dict
            Pre-qualification result with estimated risk score, tier,
            and indicative APR range.
        """
        # Run a simplified scoring (no hard gating)
        try:
            scoring_result = self._scorer.score(app_data)
            risk_score = scoring_result["risk_score"]
            tier = self._pricing.get_tier(risk_score)
            tier_config = self._pricing.get_tier_config(tier)

            return {
                "pre_qualified": risk_score <= self.AUTO_APPROVE_MAX_SCORE,
                "estimated_risk_score": risk_score,
                "estimated_tier": tier,
                "estimated_tier_label": self._pricing.get_risk_label(tier),
                "indicative_apr_range": (
                    tier_config["min_apr"],
                    tier_config["max_apr"],
                ),
                "max_loan_amount": tier_config["max_loan"],
                "disclaimer": (
                    "This is an estimated pre-qualification based on "
                    "self-reported data. Final terms require a full "
                    "application and credit check."
                ),
            }
        except Exception as exc:
            logger.warning("Pre-qualification failed: %s", exc)
            return {
                "pre_qualified": False,
                "estimated_risk_score": None,
                "estimated_tier": None,
                "indicative_apr_range": None,
                "error": "Unable to pre-qualify with provided data.",
            }

    # ──────────────────────────────────────────────────────────────────────────
    #  Helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_risk_factors(
        app_data: Dict[str, Any],
        component_scores: Dict[str, float],
        risk_score: int,
    ) -> Dict[str, Any]:
        """Build risk factors dictionary from components."""
        risk_factors = {}

        # Credit score
        cs = app_data.get("credit_score") or app_data.get("fico_score")
        if cs is not None:
            risk_factors["credit_score"] = cs
            risk_factors["fico_score"] = cs

        # Utilization
        util = app_data.get("credit_utilization") or app_data.get("utilization")
        if util is not None:
            risk_factors["credit_utilization"] = util

        # DTI
        dti = app_data.get("dti_ratio")
        if dti is not None:
            risk_factors["dti_ratio"] = dti

        # Income stability
        if "income_stability" in component_scores:
            risk_factors["income_stability"] = component_scores["income_stability"]

        # Account age
        age = app_data.get("months_credit_history") or app_data.get(
            "account_age_months"
        )
        if age is not None:
            risk_factors["months_credit_history"] = age

        # Employment
        emp = app_data.get("employment_months") or app_data.get(
            "years_at_current_job"
        )
        if emp is not None:
            risk_factors["employment_months"] = emp

        return risk_factors

    @staticmethod
    def _generate_decline_reasons(
        risk_score: int,
        risk_factors: Dict[str, Any],
        gating_result: Dict[str, Any],
    ) -> List[str]:
        """Generate human-readable decline reasons."""
        reasons: List[str] = []

        if gating_result.get("action") == "decline":
            reasons.append(gating_result.get("reason", "Application declined."))
            return reasons

        # Score-based reasons
        if risk_score > 55:
            reasons.append(
                "Risk score exceeds our underwriting threshold."
            )

        # Factor-specific reasons
        cs = risk_factors.get("credit_score")
        if cs is not None and cs < 580:
            reasons.append("Credit score is below minimum requirement.")

        util = risk_factors.get("credit_utilization")
        if util is not None:
            try:
                util_val = float(util)
                if util_val > 0.5 and util_val <= 1.0:
                    util_val = util_val * 100
                if util_val > 50:
                    reasons.append("Credit utilization is too high.")
            except (ValueError, TypeError):
                pass

        dti = risk_factors.get("dti_ratio")
        if dti is not None:
            try:
                if float(dti) > 0.43:
                    reasons.append("Debt-to-income ratio exceeds maximum.")
            except (ValueError, TypeError):
                pass

        age = risk_factors.get("months_credit_history")
        if age is not None:
            try:
                if int(age) < 12:
                    reasons.append("Credit history is too short.")
            except (ValueError, TypeError):
                pass

        return reasons

    @staticmethod
    def _calculate_counter_offer(
        loan_amount: float,
        risk_score: int,
        dti_ratio: float,
    ) -> Optional[float]:
        """Calculate a counter-offer amount for borderline applications.

        Suggests a lower loan amount that might be approvable.
        """
        if risk_score > 60:
            return None

        # Reduce loan amount based on risk score and DTI
        reduction_factor = 1.0
        if risk_score > 50:
            reduction_factor = 0.75
        elif risk_score > 40:
            reduction_factor = 0.85

        if dti_ratio > 0.40:
            reduction_factor *= 0.8

        counter = round(loan_amount * reduction_factor, -2)  # Round to nearest 100
        return max(counter, 0.0)
