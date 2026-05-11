#!/usr/bin/env python3
"""
FCRA/ECOA Adverse Action Code Generator for OrangeFi.

Generates standardized adverse action codes and human-readable explanations
for declined or modified loan applications, compliant with ECOA and FCRA
regulations.

Key Features
------------
- Maps risk factors to standardized adverse action codes
- Generates human-readable explanations
- Formats ECOA-compliant notices with all required elements
- Supports multiple languages (English default)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────────────────────────────────────
#  Factor-to-Code Mappings
# ──────────────────────────────────────────────────────────────────────────────

# Standard adverse action reason codes (ECOA/FCRA compliant)
ADVERSE_ACTION_CODES: Dict[str, Dict[str, Any]] = {
    "credit_score": {
        "code": "X01",
        "description": "Credit score below minimum requirement",
        "ecoa_reason": "Credit score does not meet our minimum standards.",
        "fcra_detail": "The credit score used in making the credit decision was {value}.",
    },
    "credit_history": {
        "code": "X02",
        "description": "Insufficient credit history length",
        "ecoa_reason": "Length of credit history is insufficient.",
        "fcra_detail": "The length of your credit history does not meet our requirements.",
    },
    "delinquency": {
        "code": "X03",
        "description": "Past due obligations",
        "ecoa_reason": "Credit report contains delinquent accounts.",
        "fcra_detail": "One or more accounts on your credit report are past due.",
    },
    "bankruptcy": {
        "code": "X04",
        "description": "Bankruptcy filing on record",
        "ecoa_reason": "Bankruptcy filing on credit report.",
        "fcra_detail": "A bankruptcy filing appears on your credit report.",
    },
    "utilization": {
        "code": "X05",
        "description": "High credit utilization ratio",
        "ecoa_reason": "Credit card balances are too high relative to credit limits.",
        "fcra_detail": "Your credit utilization ratio is above our acceptable threshold.",
    },
    "dti": {
        "code": "X06",
        "description": "Excessive debt-to-income ratio",
        "ecoa_reason": "Debt-to-income ratio is too high.",
        "fcra_detail": "Your total monthly debt obligations are too high relative to your income.",
    },
    "income": {
        "code": "X07",
        "description": "Insufficient income",
        "ecoa_reason": "Income is insufficient for the requested loan amount.",
        "fcra_detail": "Your income does not meet our minimum requirements.",
    },
    "income_stability": {
        "code": "X08",
        "description": "Unstable or irregular income",
        "ecoa_reason": "Income source is insufficiently stable.",
        "fcra_detail": "The stability of your income could not be verified to our standards.",
    },
    "employment": {
        "code": "X09",
        "description": "Insufficient employment history",
        "ecoa_reason": "Length of current employment is insufficient.",
        "fcra_detail": "Your employment history does not meet our requirements.",
    },
    "fraud": {
        "code": "X10",
        "description": "Identity verification concern",
        "ecoa_reason": "Unable to verify identity.",
        "fcra_detail": "We were unable to confirm your identity to our satisfaction.",
    },
    "ofac": {
        "code": "X11",
        "description": "Sanctions list match",
        "ecoa_reason": "Applicant matched against government sanctions list.",
        "fcra_detail": "Regulatory restrictions prevent us from processing this application.",
    },
    "lien": {
        "code": "X12",
        "description": "Active tax lien or judgment",
        "ecoa_reason": "Active tax lien or judgment on credit report.",
        "fcra_detail": "An active tax lien or judgment appears on your credit report.",
    },
    "existing_loan": {
        "code": "X13",
        "description": "Existing loan with OrangeFi",
        "ecoa_reason": "Borrower has an existing OrangeFi loan in good standing.",
        "fcra_detail": "Our records show an existing OrangeFi loan. Multiple concurrent loans are not permitted.",
    },
    "loan_amount": {
        "code": "X14",
        "description": "Requested amount exceeds limits",
        "ecoa_reason": "Requested loan amount exceeds maximum for your risk tier.",
        "fcra_detail": "The requested amount exceeds the maximum allowed based on current credit profile.",
    },
    "military": {
        "code": "X15",
        "description": "Military lending rate cap applied",
        "ecoa_reason": "Military Lending Act rate cap applied to offer terms.",
        "fcra_detail": "As an active-duty service member or dependent, your rate is capped at 36% APR under the MLA.",
    },
    "credit_builder": {
        "code": "X16",
        "description": "Thin credit file — credit builder offered",
        "ecoa_reason": "Limited credit history. Alternative product available.",
        "fcra_detail": "Your credit file is insufficient for a standard loan. You may qualify for OrangeFi Credit Builder.",
    },
    "general_decline": {
        "code": "X99",
        "description": "General decline — multiple factors",
        "ecoa_reason": "Application does not meet our current underwriting criteria.",
        "fcra_detail": "Based on the information provided, we are unable to offer you a loan at this time.",
    },
}

# Risk factor → adverse action code key mapping
RISK_FACTOR_TO_CODE: Dict[str, str] = {
    "fico_score": "credit_score",
    "credit_score": "credit_score",
    "credit_utilization": "utilization",
    "utilization": "utilization",
    "dti_ratio": "dti",
    "dti": "dti",
    "income_stability": "income_stability",
    "account_age": "credit_history",
    "months_credit_history": "credit_history",
    "employment_stability": "employment",
    "employment_months": "employment",
    "bankruptcy": "bankruptcy",
    "delinquency": "delinquency",
    "tax_lien": "lien",
    "judgment": "lien",
    "fraud": "fraud",
    "ofac": "ofac",
    "income": "income",
    "annual_income": "income",
}


class AdverseActionGenerator:
    """Generates ECOA/FCRA-compliant adverse action notices.

    Maps risk factors from the underwriting engine to standardized
    adverse action codes and generates human-readable explanations.
    """

    @classmethod
    def generate_notice(
        cls,
        application_data: Dict[str, Any],
        decision_result: Dict[str, Any],
        borrower_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a complete adverse action notice.

        Parameters
        ----------
        application_data : dict
            Original application data.
        decision_result : dict
            Result from the decision engine.
        borrower_name : str, optional
            Borrower's name for personalization.

        Returns
        -------
        dict
            ECOA-compliant adverse action notice with:
            - reason_codes: list of standardized codes
            - explanations: human-readable explanations
            - notice: formatted ECOA notice
            - rights_statement: borrower rights information
        """
        decision = decision_result.get("decision", "declined")
        decline_reasons = decision_result.get("decline_reasons", [])
        risk_factors = decision_result.get("risk_factors", {})
        gating_reason = decision_result.get("gating_reason", "")

        # Collect reason codes and explanations
        reason_codes: List[str] = []
        explanations: List[str] = []
        fcra_details: List[str] = []

        # Process gating decline reasons
        if gating_reason and decision == "declined":
            code_entry = cls._find_code_for_reason(gating_reason)
            if code_entry:
                if code_entry["code"] not in [c.split(" - ")[0] for c in reason_codes]:
                    formatted = f"{code_entry['code']} - {code_entry['description']}"
                    reason_codes.append(formatted)
                    explanations.append(code_entry["ecoa_reason"])
                    fcra_details.append(code_entry["fcra_detail"])

        # Process risk factor mappings
        for factor, value in risk_factors.items():
            code_key = RISK_FACTOR_TO_CODE.get(factor)
            if code_key and code_key in ADVERSE_ACTION_CODES:
                entry = ADVERSE_ACTION_CODES[code_key]
                code_str = f"{entry['code']} - {entry['description']}"

                if code_str not in reason_codes:
                    reason_codes.append(code_str)
                    explanations.append(entry["ecoa_reason"])

                    # Add FCRA detail with value substitution
                    detail = entry["fcra_detail"]
                    if "{value}" in detail:
                        detail = detail.replace("{value}", str(value))
                    fcra_details.append(detail)

        # Process specific decline reasons from gating
        for reason in decline_reasons:
            code_entry = cls._find_code_for_reason(reason)
            if code_entry:
                code_str = f"{code_entry['code']} - {code_entry['description']}"
                if code_str not in reason_codes:
                    reason_codes.append(code_str)
                    explanations.append(code_entry["ecoa_reason"])
                    fcra_details.append(code_entry["fcra_detail"])

        # If no codes found, add general decline
        if not reason_codes:
            general = ADVERSE_ACTION_CODES["general_decline"]
            reason_codes.append(
                f"{general['code']} - {general['description']}"
            )
            explanations.append(general["ecoa_reason"])
            fcra_details.append(general["fcra_detail"])

        # Ensure we have at least one and no more than 4 primary reasons
        # (ECOA recommends limiting to 4 primary reasons)
        primary_reasons = reason_codes[:4]

        # Build formatted notice
        notice = cls._format_notice(
            borrower_name=borrower_name or "Applicant",
            decision=decision,
            primary_reasons=primary_reasons,
            explanations=explanations[:4],
            fcra_details=fcra_details[:4],
            credit_score=application_data.get("credit_score") or application_data.get("fico_score"),
            credit_score_source="Credit Bureau",
            decision_result=decision_result,
        )

        return {
            "reason_codes": reason_codes,
            "primary_reasons": primary_reasons,
            "explanations": explanations[:4],
            "fcra_details": fcra_details[:4],
            "notice": notice,
            "rights_statement": cls._rights_statement(),
        }

    @classmethod
    def _find_code_for_reason(cls, reason: str) -> Optional[Dict[str, Any]]:
        """Find the matching adverse action code for a reason string."""
        reason_lower = reason.lower()

        keyword_map: List[tuple] = [
            ("bankruptcy", "bankruptcy"),
            ("delinquen", "delinquency"),
            ("credit score", "credit_score"),
            ("fico", "credit_score"),
            ("income", "income"),
            ("tax lien", "lien"),
            ("judgment", "lien"),
            ("ofac", "ofac"),
            ("sdn", "ofac"),
            ("fraud", "fraud"),
            ("identity", "fraud"),
            ("credit builder", "credit_builder"),
            ("thin", "credit_builder"),
            ("military", "military"),
            ("mla", "military"),
            ("existing", "existing_loan"),
            ("exceed", "loan_amount"),
            ("limit", "loan_amount"),
        ]

        for keyword, code_key in keyword_map:
            if keyword in reason_lower:
                entry = ADVERSE_ACTION_CODES.get(code_key)
                if entry:
                    return entry

        return None

    @classmethod
    def _format_notice(
        cls,
        borrower_name: str,
        decision: str,
        primary_reasons: List[str],
        explanations: List[str],
        fcra_details: List[str],
        credit_score: Optional[int],
        credit_score_source: str,
        decision_result: Dict[str, Any],
    ) -> str:
        """Format an ECOA-compliant adverse action notice."""
        lines: List[str] = [
            "=" * 60,
            "   NOTICE OF ADVERSE ACTION",
            "   OrangeFi Lending Platform",
            "=" * 60,
            "",
            f"Date: {decision_result.get('timestamp', 'N/A')}",
            f"To: {borrower_name}",
            f"Application ID: {decision_result.get('application_id', 'N/A')}",
            "",
            f"Dear {borrower_name},",
            "",
            "After reviewing your loan application, we regret to inform you",
            f"that we are unable to approve your request. Your application was",
            f"**{decision.upper()}** for the following reason(s):",
            "",
        ]

        for i, reason in enumerate(primary_reasons, 1):
            lines.append(f"  {i}. {reason}")
            if i - 1 < len(explanations):
                lines.append(f"     {explanations[i-1]}")
            lines.append("")

        if credit_score is not None:
            lines.extend([
                "Credit Score Information:",
                f"  Credit Score Used: {credit_score}",
                f"  Source: {credit_score_source}",
                "",
            ])

        if fcra_details:
            lines.append("Additional FCRA Details:")
            for detail in fcra_details:
                lines.append(f"  - {detail}")
            lines.append("")

        if decision_result.get("counter_offer"):
            counter = decision_result["counter_offer"]
            lines.extend([
                "Alternative Offer:",
                f"  We may be able to offer you a different loan amount of",
                f"  ${counter.get('amount', 0):,.2f} at {counter.get('apr', 0)}% APR.",
                "",
            ])

        lines.extend([
            cls._rights_statement(),
            "",
            "Sincerely,",
            "OrangeFi Underwriting Department",
            "This is an automated decision. For inquiries, contact",
            "support@orangefi.com or call 1-800-ORANGEFI.",
            "",
            "=" * 60,
        ])

        return "\n".join(lines)

    @staticmethod
    def _rights_statement() -> str:
        """Return the ECOA-mandated rights statement."""
        return (
            "Your Rights Under the Equal Credit Opportunity Act:\n"
            "  The federal Equal Credit Opportunity Act prohibits creditors\n"
            "  from discriminating against credit applicants on the basis of\n"
            "  race, color, religion, national origin, sex, marital status,\n"
            "  age (provided the applicant has the capacity to enter into a\n"
            "  binding contract), or because all or part of the applicant's\n"
            "  income derives from any public assistance program, or because\n"
            "  the applicant has in good faith exercised any right under the\n"
            "  Consumer Credit Protection Act.\n\n"
            "  You have the right to request a free copy of your credit\n"
            "  report within 60 days of receiving this notice by contacting\n"
            "  the credit bureau listed above.\n\n"
            "  If you believe your application was treated unfairly, you\n"
            "  may contact:\n"
            "    CFPB Consumer Response Center\n"
            "    855-411-CFPB (2372) | consumerfinance.gov/complaint/"
        )

    @classmethod
    def generate_adverse_action_codes(
        cls,
        risk_factors: Dict[str, Any],
    ) -> List[str]:
        """Generate standardized adverse action codes from risk factors.

        Parameters
        ----------
        risk_factors : dict
            Dictionary of risk factors and their values.

        Returns
        -------
        list of str
            Standardized adverse action codes with descriptions.
        """
        codes: List[str] = []

        for factor in risk_factors:
            code_key = RISK_FACTOR_TO_CODE.get(factor)
            if code_key and code_key in ADVERSE_ACTION_CODES:
                entry = ADVERSE_ACTION_CODES[code_key]
                code_str = f"{entry['code']} - {entry['description']}"
                if code_str not in codes:
                    codes.append(code_str)

        if not codes:
            general = ADVERSE_ACTION_CODES["general_decline"]
            codes.append(f"{general['code']} - {general['description']}")

        return codes[:4]  # ECOA recommends max 4 primary reasons
