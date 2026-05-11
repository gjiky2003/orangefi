#!/usr/bin/env python3
"""
OrangeFi Pricing Engine — Tier-based APR, Origination Fees, and Loan Limits.

Tier Structure (adapted from PalmFi, tailored for debt consolidation)
-------
- A+: score 0-15  → 5.99-8.99% APR, max $35k, 1% orig fee
- A:  score 16-30 → 7.99-11.99% APR, max $35k, 2% orig fee
- B:  score 31-45 → 10.99-15.99% APR, max $30k, 3% orig fee
- C:  score 46-60 → 14.99-20.99% APR, max $25k, 4% orig fee
- D:  score 61-75 → 19.99-26.99% APR, max $20k, 5% orig fee
- E:  score 76-100 → 24.99-29.99% APR, max $15k, 5% orig fee

Supports MLA 36% APR cap for military borrowers.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


class PricingEngine:
    """Risk-based pricing engine for OrangeFi debt consolidation loans."""

    # Tier definitions
    # Each tier: (min_score, max_score, tier_label, config)
    TIERS: Dict[str, Dict[str, Any]] = {
        "A+": {
            "label": "Prime+",
            "min_score": 0,
            "max_score": 15,
            "min_apr": 5.99,
            "max_apr": 8.99,
            "max_loan": 35000.0,
            "origination_pct": 1.0,
        },
        "A": {
            "label": "Prime",
            "min_score": 16,
            "max_score": 30,
            "min_apr": 7.99,
            "max_apr": 11.99,
            "max_loan": 35000.0,
            "origination_pct": 2.0,
        },
        "B": {
            "label": "Near Prime",
            "min_score": 31,
            "max_score": 45,
            "min_apr": 10.99,
            "max_apr": 15.99,
            "max_loan": 30000.0,
            "origination_pct": 3.0,
        },
        "C": {
            "label": "Subprime",
            "min_score": 46,
            "max_score": 60,
            "min_apr": 14.99,
            "max_apr": 20.99,
            "max_loan": 25000.0,
            "origination_pct": 4.0,
        },
        "D": {
            "label": "Near Default",
            "min_score": 61,
            "max_score": 75,
            "min_apr": 19.99,
            "max_apr": 26.99,
            "max_loan": 20000.0,
            "origination_pct": 5.0,
        },
        "E": {
            "label": "High Risk",
            "min_score": 76,
            "max_score": 100,
            "min_apr": 24.99,
            "max_apr": 29.99,
            "max_loan": 15000.0,
            "origination_pct": 5.0,
        },
    }

    # Sorted tier list for lookup (worst tier first for reverse iteration)
    _TIER_LIST: List[Tuple[str, Dict[str, Any]]] = [
        ("E", TIERS["E"]),
        ("D", TIERS["D"]),
        ("C", TIERS["C"]),
        ("B", TIERS["B"]),
        ("A", TIERS["A"]),
        ("A+", TIERS["A+"]),
    ]

    # Available terms in months
    TERM_OPTIONS: List[int] = [12, 24, 36, 48]

    # MLA maximum APR (Military Lending Act)
    MLA_MAX_APR = 36.0

    # ──────────────────────────────────────────────────────────────────────────
    #  Tier Lookup
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_tier(cls, risk_score: int) -> str:
        """Map risk score (0-100, higher = riskier) to letter tier.

        Parameters
        ----------
        risk_score : int
            Risk score between 0 and 100.

        Returns
        -------
        str
            Tier label: 'A+', 'A', 'B', 'C', 'D', or 'E'.
        """
        for tier_label, config in cls._TIER_LIST:
            if config["min_score"] <= risk_score <= config["max_score"]:
                return tier_label
        return "E"  # Fallback

    @classmethod
    def get_tier_config(cls, tier: str) -> Dict[str, Any]:
        """Get full configuration for a tier.

        Parameters
        ----------
        tier : str
            Tier label.

        Returns
        -------
        dict
            Tier configuration dictionary.
        """
        return cls.TIERS.get(tier, cls.TIERS["E"])

    @classmethod
    def get_risk_label(cls, tier: str) -> str:
        """Get human-readable risk label for a tier."""
        return cls.TIERS.get(tier, cls.TIERS["E"])["label"]

    @classmethod
    def list_tiers(cls) -> List[Dict[str, Any]]:
        """Return list of all pricing tiers with their configurations."""
        return [
            {
                "tier": label,
                "label": config["label"],
                "min_score": config["min_score"],
                "max_score": config["max_score"],
                "min_apr": config["min_apr"],
                "max_apr": config["max_apr"],
                "max_loan_amount": config["max_loan"],
                "origination_fee_pct": config["origination_pct"],
            }
            for label, config in sorted(
                cls.TIERS.items(),
                key=lambda x: x[1]["min_score"],
            )
        ]

    # ──────────────────────────────────────────────────────────────────────────
    #  Rate Calculation
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def calculate_rate(
        cls,
        tier: str,
        loan_amount: float,
        term_months: int,
        dti_ratio: float,
        mla_applicable: bool = False,
    ) -> float:
        """Calculate APR within tier range based on loan specifics.

        Factors that influence rate within the tier range:
        - DTI ratio: higher DTI → higher rate
        - Term length: longer term → slightly higher rate
        - Loan amount: larger loans get a slight discount

        Parameters
        ----------
        tier : str
            Tier label.
        loan_amount : float
            Requested loan amount in dollars.
        term_months : int
            Loan term in months.
        dti_ratio : float
            Debt-to-income ratio (decimal, e.g. 0.35).
        mla_applicable : bool
            Whether the MLA 36% APR cap applies.

        Returns
        -------
        float
            Annual Percentage Rate (e.g. 9.99 for 9.99%).
        """
        config = cls.get_tier_config(tier)
        base_rate = config["min_apr"]
        max_rate = config["max_apr"]
        rate_range = max_rate - base_rate

        # DTI adjustment: higher DTI → higher rate within tier
        dti_factor = min(1.0, dti_ratio / 0.5)

        # Term adjustment: longer term → slightly higher rate
        term_factor = min(1.0, max(0.0, (term_months - 12) / 36)) * 0.3

        # Amount adjustment: larger loans get slight discount
        amount_factor = min(0.5, loan_amount / 70000.0) * 0.2

        # Composite adjustment (0 to 1)
        rate_adjustment = dti_factor * 0.6 + term_factor - amount_factor
        rate_adjustment = max(0.0, min(1.0, rate_adjustment))

        apr = base_rate + rate_adjustment * rate_range
        apr = round(apr, 2)

        # Apply MLA cap if applicable
        if mla_applicable and apr > cls.MLA_MAX_APR:
            apr = cls.MLA_MAX_APR

        return apr

    # ──────────────────────────────────────────────────────────────────────────
    #  Payment Calculation
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def calculate_monthly_payment(
        principal: float,
        apr: float,
        term_months: int,
    ) -> float:
        """Calculate monthly payment using standard amortization formula.

        Formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]

        Parameters
        ----------
        principal : float
            Loan principal amount.
        apr : float
            Annual Percentage Rate (e.g. 9.99 for 9.99%).
        term_months : int
            Loan term in months.

        Returns
        -------
        float
            Monthly payment amount.
        """
        if apr == 0 or term_months == 0:
            return round(principal / max(1, term_months), 2)

        monthly_rate = (apr / 100.0) / 12.0
        payment = (
            principal
            * (monthly_rate * (1 + monthly_rate) ** term_months)
            / ((1 + monthly_rate) ** term_months - 1)
        )
        return round(payment, 2)

    # ──────────────────────────────────────────────────────────────────────────
    #  Fees
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def calculate_origination_fee(cls, principal: float, tier: str) -> float:
        """Calculate origination fee based on tier percentage.

        Parameters
        ----------
        principal : float
            Loan principal amount.
        tier : str
            Tier label.

        Returns
        -------
        float
            Origination fee amount.
        """
        config = cls.get_tier_config(tier)
        fee = principal * (config["origination_pct"] / 100.0)
        return round(fee, 2)

    # ──────────────────────────────────────────────────────────────────────────
    #  Amortization Schedule
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def calculate_amortization_schedule(
        cls,
        principal: float,
        apr: float,
        term_months: int,
    ) -> List[Dict[str, Any]]:
        """Generate a full amortization schedule.

        Parameters
        ----------
        principal : float
            Loan principal amount.
        apr : float
            Annual Percentage Rate.
        term_months : int
            Loan term in months.

        Returns
        -------
        list of dict
            Each entry: payment_number, principal, interest,
            remaining_balance, total_payment.
        """
        monthly_rate = (apr / 100.0) / 12.0
        monthly_payment = cls.calculate_monthly_payment(principal, apr, term_months)

        schedule: List[Dict[str, Any]] = []
        remaining = principal

        for period in range(1, term_months + 1):
            interest_cents = round(remaining * monthly_rate, 2)
            principal_cents = round(monthly_payment - interest_cents, 2)

            if period == term_months:
                # Final payment adjustment for rounding
                principal_cents = remaining
                monthly_payment = round(principal_cents + interest_cents, 2)

            remaining = round(remaining - principal_cents, 2)
            if remaining < 0:
                remaining = 0.0

            schedule.append({
                "payment_number": period,
                "total_payment": monthly_payment,
                "principal": principal_cents,
                "interest": interest_cents,
                "remaining_balance": remaining,
            })

        return schedule

    # ──────────────────────────────────────────────────────────────────────────
    #  Offer Generation
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def generate_offer(
        cls,
        loan_amount: float,
        risk_score: int,
        dti_ratio: float,
        term_months: int,
        mla_applicable: bool = False,
    ) -> Dict[str, Any]:
        """Generate a complete loan offer for an approved application.

        Parameters
        ----------
        loan_amount : float
            Requested loan amount.
        risk_score : int
            Risk score (0-100).
        dti_ratio : float
            Debt-to-income ratio.
        term_months : int
            Requested term in months.
        mla_applicable : bool
            Whether MLA cap applies.

        Returns
        -------
        dict
            Complete offer with rate, payment, fees, and amortization.
        """
        tier = cls.get_tier(risk_score)
        config = cls.get_tier_config(tier)

        # Cap loan amount to tier maximum
        final_amount = min(loan_amount, config["max_loan"])

        # Calculate APR
        apr = cls.calculate_rate(tier, final_amount, term_months, dti_ratio, mla_applicable)

        # Calculate origination fee
        origination_fee = cls.calculate_origination_fee(final_amount, tier)

        # Net amount (after origination fee)
        net_amount = round(final_amount - origination_fee, 2)

        # Monthly payment
        monthly_payment = cls.calculate_monthly_payment(final_amount, apr, term_months)

        # Total cost calculations
        total_payments = round(monthly_payment * term_months, 2)
        total_interest = round(total_payments - final_amount, 2)
        total_cost = round(total_payments + origination_fee, 2)

        # Amortization schedule
        amortization = cls.calculate_amortization_schedule(final_amount, apr, term_months)

        return {
            "tier": tier,
            "risk_label": config["label"],
            "loan_amount": final_amount,
            "net_amount": net_amount,
            "apr": apr,
            "term_months": term_months,
            "monthly_payment": monthly_payment,
            "origination_fee": origination_fee,
            "origination_fee_pct": config["origination_pct"],
            "total_interest": total_interest,
            "total_payments": total_payments,
            "total_cost": total_cost,
            "mla_capped": mla_applicable and apr <= cls.MLA_MAX_APR,
            "max_loan_amount": config["max_loan"],
            "amortization_schedule": amortization,
        }

    @classmethod
    def calculate_total_cost(
        cls,
        principal: float,
        apr: float,
        term_months: int,
        origination_fee: float,
    ) -> Dict[str, Any]:
        """Calculate total cost summary for a loan.

        Parameters
        ----------
        principal : float
            Loan principal amount.
        apr : float
            Annual Percentage Rate.
        term_months : int
            Loan term in months.
        origination_fee : float
            Origination fee amount.

        Returns
        -------
        dict
            Total cost breakdown.
        """
        monthly_payment = cls.calculate_monthly_payment(principal, apr, term_months)
        total_payments = round(monthly_payment * term_months, 2)
        total_interest = round(total_payments - principal, 2)
        total_cost = round(total_payments + origination_fee, 2)

        return {
            "monthly_payment": monthly_payment,
            "total_interest": total_interest,
            "total_principal": principal,
            "total_payments": total_payments,
            "origination_fee": origination_fee,
            "total_cost": total_cost,
            "apr": apr,
            "term_months": term_months,
        }
