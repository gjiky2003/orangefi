# OrangeFi — Underwriting Engine

## Overview

OrangeFi's underwriting engine uses a **two-tiered architecture** that separates hard decline checks from risk scoring. This approach ensures regulatory compliance is enforced before any scoring occurs, and only high-quality applications proceed to the computationally expensive scoring stage.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      UNDERWRITING PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Application Submitted                                                   │
│        │                                                                 │
│        ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  STAGE 1: GATING RULES                                      │        │
│  │  ─────────────────────────────                              │        │
│  │  • 7 hard decline checks                                    │        │
│  │  • 1 flag rule (MLA)                                        │        │
│  │  • Binary pass/fail                                          │        │
│  │  • No scoring involved                                       │        │
│  └─────────────────────┬───────────────────────────────────────┘        │
│                        │                                                │
│            ┌───────────┴───────────┐                                    │
│            ▼                       ▼                                    │
│      ❌ Decline              ✅ Pass                                    │
│         │                       │                                       │
│         ▼                       ▼                                       │
│  ┌──────────────────┐  ┌───────────────────────────────────────┐       │
│  │  Adverse Action  │  │  STAGE 2: RISK SCORING                │       │
│  │  Notice (ECOA)   │  │  ──────────────────────               │       │
│  │  + FCRA Rights   │  │  • 6 weighted components              │       │
│  └──────────────────┘  │  • Cash flow blend (optional)         │       │
│                        │  • Score: 0 (low risk) - 100 (high)   │       │
│                        └────────────────┬──────────────────────┘       │
│                                         │                               │
│                                         ▼                               │
│                          ┌─────────────────────────┐                    │
│                          │  FINAL DECISION         │                    │
│                          │  ──────────────────     │                    │
│                          │  0-40:   ✅ Auto-approve│                    │
│                          │  41-55:  🔍 Manual review│                   │
│                          │  56-100: ❌ Decline     │                    │
│                          └─────────────────────────┘                    │
│                                         │                               │
│                                         ▼                               │
│                          ┌─────────────────────────┐                    │
│                          │  PRICING & OFFER        │                    │
│                          │  ──────────────────     │                    │
│                          │  • Tier assignment      │                    │
│                          │  • APR calculation      │                    │
│                          │  • Fee calculation      │                    │
│                          │  • Amortization sched.  │                    │
│                          │  • Counter-offers       │                    │
│                          │  • Adverse action (decl)│                    │
│                          └─────────────────────────┘                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Gating Rules

The gating rules engine (`gating_rules.py`) runs **7 hard decline checks** and **1 flag rule** before any scoring occurs. These checks enforce regulatory, fraud, and policy boundaries.

### Hard Decline Rules

| # | Rule | Threshold | Data Source | Rationale |
|---|------|-----------|-------------|-----------|
| 1 | **Bankruptcy Check** | Bankruptcy filed within 7 years | Credit bureau + self-report | Regulatory policy |
| 2 | **Minimum Credit Score** | Score < 580 | Credit bureau (FICO/Vantage) | Credit risk policy |
| 3 | **Minimum Income** | Annual income < $25,000 | Self-report + document verification | Ability to repay (ATR) |
| 4 | **Delinquency Check** | 90+ days delinquent in last 12 months | Credit bureau | Delinquency risk |
| 5 | **Active Liens/Judgments** | Active tax lien or judgment | Credit bureau | Legal risk |
| 6 | **Identity Fraud** | Fraud probability > 85% | Identity verification service | Fraud prevention |
| 7 | **OFAC/SDN Match** | Match on government sanctions list | OFAC SDN list | Regulatory compliance |

### Flag Rule

| # | Rule | Action | Impact |
|---|------|--------|--------|
| 8 | **Military Borrower** | Flag but pass | MLA 36% APR cap applied in pricing |

### Implementation

```python
class GatingRules:
    def __init__(self, min_credit_score=580, min_annual_income=25000.0, bankruptcy_years=7):
        ...

    def evaluate(self, app_data: dict) -> dict:
        """Returns {'passed': bool, 'reason': str, 'action': 'decline'|'flag'|'pass'}"""
        # 1. Bankruptcy check
        # 2. Credit score check
        # 3. Income check
        # 4. Delinquency check
        # 5. Liens/judgments check
        # 6. Identity fraud check
        # 7. OFAC/SDN check
        # 8. Military borrower flag
```

**Evaluate method input:**
```python
{
    "credit_score": 720,               # int, 300-850
    "fico_score": 720,                  # alias
    "annual_income": 85000.0,           # float, USD
    "bankruptcy_in_7yr": False,         # bool
    "bankruptcy_date": None,            # str or None (date of filing)
    "delinquency_90d_12mo": False,      # bool
    "tax_lien_active": False,           # bool
    "judgment_active": False,           # bool
    "identity_fraud_probability": 5.0,  # float, 0-100
    "ofac_sdn_match": False,            # bool
    "military_borrower": False,         # bool (triggers MLA flag)
}
```

**Output:**
```python
# PASS:
{"passed": True, "reason": "All gating rules passed.", "action": "pass", "mla_applicable": False}

# FLAG (military borrower):
{"passed": True, "reason": "...MLA 36% APR cap will be applied...", "action": "flag", "mla_applicable": True}

# DECLINE (e.g., low credit score):
{"passed": False, "reason": "Credit score (550) is below the minimum...", "action": "decline", "credit_builder_eligible": True}
```

### Gating Notes

- **Credit builder eligible:** Applicants declined due to low credit score (< 580) are flagged as eligible for OrangeFi Credit Builder (future product)
- **Soft vs hard decline:** Applications declined at the gating stage do NOT proceed to scoring, saving computational resources
- **Order matters:** Rules are evaluated in priority order; the first failure returns immediately

---

## Stage 2: Risk Scoring

The risk scorer (`risk_scorer.py`) computes a 0-100 risk score using **6 weighted components** with an optional **cash flow blend**.

### Component Weights

| Component | Symbol | Weight | Description |
|-----------|--------|--------|-------------|
| FICO Score | $w_f$ | **40%** | Credit score from bureau |
| Credit Utilization | $w_u$ | **15%** | Ratio of credit used to total available |
| DTI Ratio | $w_d$ | **15%** | Monthly debt payments / monthly income |
| Income Stability | $w_s$ | **15%** | Stability and predictability of income |
| Account Age | $w_a$ | **10%** | Length of credit history |
| Employment Stability | $w_e$ | **5%** | Tenure at current employer |

**Formula:**
```
RiskScore = w_f * fico_sub + w_u * util_sub + w_d * dti_sub + w_s * income_sub + w_a * account_sub + w_e * employment_sub
```

Where each subscore is 0-100 (higher = riskier).

### Component Score Mappings

#### FICO Score Subscore (40% weight)

| FICO Range | Subscore | Risk Level |
|------------|----------|------------|
| 850 | 0 | Lowest risk |
| 800-849 | 5 | Very low |
| 740-799 | 15 | Low |
| 670-739 | 35 | Moderate |
| 580-669 | 65 | High |
| < 580 | 100 | Highest risk (should be caught by gating) |
| Missing | 50 (default) | — |

#### Credit Utilization Subscore (15% weight)

| Utilization | Subscore | Risk Level |
|-------------|----------|------------|
| 0-9% | 5 | Low |
| 10-29% | 20 | Moderate |
| 30-49% | 40 | Elevated |
| 50-69% | 60 | High |
| 70-89% | 80 | Very high |
| 90%+ | 100 | Max risk |

Supports both percentage (0-100) and decimal (0-1) input formats.

#### DTI Ratio Subscore (15% weight)

| DTI Range | Subscore | Risk Level |
|-----------|----------|------------|
| < 20% | 5 | Low |
| 20-27% | 20 | Moderate |
| 28-35% | 40 | Elevated |
| 36-42% | 60 | High |
| 43-49% | 80 | Very high |
| 50%+ | 100 | Max risk |

#### Income Stability Subscore (15% weight)

| Income Type | Subscore |
|-------------|----------|
| Stable | 10 |
| Verified | 15 |
| Regular | 20 |
| Unknown | 50 |
| Self-employed | 60 |
| Seasonal | 70 |
| Irregular | 70 |
| Variable | 75 |
| Unstable | 85 |

#### Account Age Subscore (10% weight)

| Credit History Length | Subscore |
|----------------------|----------|
| 10+ years | 5 |
| 7-9 years | 15 |
| 5-6 years | 30 |
| 3-4 years | 50 |
| 1-2 years | 70 |
| 6-11 months | 85 |
| < 6 months | 100 |

#### Employment Stability Subscore (5% weight)

| Employment Tenure | Subscore |
|------------------|----------|
| 10+ years | 5 |
| 5-9 years | 15 |
| 3-4 years | 30 |
| 1-2 years | 50 |
| 6-11 months | 70 |
| 3-5 months | 85 |
| < 3 months | 100 |

### Cash Flow Blend

When cash flow data is available (from Plaid transaction history), it is blended into the final score:

```
BlendedScore = RiskScore × (1 - blend_weight) + CashFlowRisk × blend_weight
```

Where:
- **CashFlowRisk** = 100 - CashFlowScore (converted to risk scale)
- **Standard blend weight:** 30%
- **Thin-file blend weight:** 50% (for FICO < 620)

The cash flow score is computed from:
- Average daily balance trend
- Income volatility
- Spending patterns
- Overdraft frequency
- Savings rate

---

## Decision Logic

The decision engine (`decision_engine.py`) combines gating results and risk scores into a final decision.

### Decision Thresholds

| Risk Score | Decision | Description |
|------------|----------|-------------|
| **0-40** | ✅ **Auto-Approve** | Application approved automatically, offer generated |
| **41-55** | 🔍 **Manual Review** | Flagged for underwriter review (gray zone) |
| **56-100** | ❌ **Decline** | Application declined, adverse action generated |

### Decision Override

Admin users can override decisions through the admin API:

```json
POST /admin/applications/{id}/decision
{
  "decision": "approved",
  "note": "Borrower has compensating factors",
  "approved_amount": 15000.00,
  "approved_apr": 9.99,
  "approved_term_months": 36
}
```

Overrides are logged in the audit trail with the admin user ID and reason.

---

## Pricing Tiers

The pricing engine (`pricing.py`) assigns an APR range and loan limits based on the risk score tier.

### Tier Table

| Tier | Risk Score Range | Label | APR Range | Max Loan | Origination Fee |
|------|-----------------|-------|-----------|----------|-----------------|
| **A+** | 0-15 | Prime+ | 5.99% - 8.99% | $35,000 | 1.0% |
| **A** | 16-30 | Prime | 7.99% - 11.99% | $35,000 | 2.0% |
| **B** | 31-45 | Near Prime | 10.99% - 15.99% | $30,000 | 3.0% |
| **C** | 46-60 | Subprime | 14.99% - 20.99% | $25,000 | 4.0% |
| **D** | 61-75 | Near Default | 19.99% - 26.99% | $20,000 | 5.0% |
| **E** | 76-100 | High Risk | 24.99% - 29.99% | $15,000 | 5.0% |

### Within-Tier Rate Calculation

The exact APR within a tier range is determined by:

```python
apr = base_rate + adjustment × rate_range
```

Where `adjustment` is a composite of:
- **DTI factor (60%):** Higher DTI → higher rate within tier
- **Term factor (30%):** Longer term → slightly higher rate
- **Amount factor (10%):** Larger loans → slight discount

### MLA Military Cap

For military borrowers flagged in gating, the APR is capped at **36%** per the Military Lending Act:

```python
if mla_applicable and apr > cls.MLA_MAX_APR:
    apr = cls.MLA_MAX_APR  # 36.0%
```

### Available Terms

| Term | Available |
|------|-----------|
| 12 months | ✅ |
| 24 months | ✅ |
| 36 months | ✅ |
| 48 months | ✅ |
| 60 months | ❌ (future) |

---

## Offer Generation

For approved applications, the pricing engine generates a complete loan offer:

```python
offer = PricingEngine.generate_offer(
    loan_amount=15000.00,
    risk_score=28,
    dti_ratio=0.28,
    term_months=36,
    mla_applicable=False,
)
```

**Result:**
```python
{
    "tier": "A",
    "risk_label": "Prime",
    "loan_amount": 15000.00,
    "net_amount": 14700.00,              # After origination fee
    "apr": 9.99,                         # 9.99% APR
    "term_months": 36,
    "monthly_payment": 484.15,
    "origination_fee": 300.00,           # 2% of loan amount
    "origination_fee_pct": 2.0,
    "total_interest": 2429.40,
    "total_payments": 17429.40,          # Sum of all monthly payments
    "total_cost": 17729.40,              # Total payments + origination fee
    "mla_capped": False,
    "max_loan_amount": 35000.0,
    "amortization_schedule": [
        {"payment_number": 1, "total_payment": 484.15,
         "principal": 359.90, "interest": 124.25, "remaining_balance": 14640.10},
        ...
        {"payment_number": 36, "total_payment": 484.15,
         "principal": 480.12, "interest": 4.03, "remaining_balance": 0.00}
    ]
}
```

### Counter-Offers

For borderline decline applications (risk score 56-60), the engine automatically generates a counter-offer with a reduced loan amount:

```python
def _calculate_counter_offer(loan_amount, risk_score, dti_ratio):
    if risk_score > 60:
        return None
    reduction = 0.75 if risk_score > 50 else 0.85
    if dti_ratio > 0.40:
        reduction *= 0.8
    return round(loan_amount * reduction, -2)
```

---

## Adverse Action Generation

The adverse action generator (`adverse_action.py`) creates ECOA/FCRA-compliant notices for declined applications.

### Standard Reason Codes

| Code | Factor | Description |
|------|--------|-------------|
| **X01** | Credit Score | Credit score below minimum requirement |
| **X02** | Credit History | Insufficient credit history length |
| **X03** | Delinquency | Past due obligations |
| **X04** | Bankruptcy | Bankruptcy filing on record |
| **X05** | Utilization | High credit utilization ratio |
| **X06** | DTI | Excessive debt-to-income ratio |
| **X07** | Income | Insufficient income |
| **X08** | Income Stability | Unstable or irregular income |
| **X09** | Employment | Insufficient employment history |
| **X10** | Fraud | Identity verification concern |
| **X11** | OFAC | Sanctions list match |
| **X12** | Lien | Active tax lien or judgment |
| **X13** | Existing Loan | Existing loan with OrangeFi |
| **X14** | Loan Amount | Requested amount exceeds limits |
| **X15** | Military | Military lending rate cap applied |
| **X16** | Credit Builder | Thin credit file — credit builder offered |
| **X99** | General | General decline — multiple factors |

### Notice Format

```
============================================================
   NOTICE OF ADVERSE ACTION
   OrangeFi Lending Platform
============================================================

Date: 2026-05-11T14:00:00Z
To: John Doe
Application ID: UW-2026-00123

Dear John Doe,

After reviewing your loan application, we regret to inform you
that we are unable to approve your request. Your application was
**DECLINED** for the following reason(s):

  1. X06 - Excessive debt-to-income ratio
     Debt-to-income ratio is too high.
     Your total monthly debt obligations are too high relative
     to your income.

Credit Score Information:
  Credit Score Used: 720
  Source: Credit Bureau

Your Rights Under the Equal Credit Opportunity Act:
  The federal Equal Credit Opportunity Act prohibits creditors
  from discriminating against credit applicants on the basis of
  race, color, religion, national origin, sex, marital status,
  age (provided the applicant has the capacity to enter into a
  binding contract), or because all or part of the applicant's
  income derives from any public assistance program...

Sincerely,
OrangeFi Underwriting Department
```

**Key ECOA/FCRA requirements met:**
1. Specific reasons for adverse action (limited to 4 primary reasons)
2. Credit score disclosure (if used in decision)
3. Source of credit score
4. Right to free credit report within 60 days
5. ECOA nondiscrimination statement
6. CFPB complaint contact information
7. Counter-offer disclosure (if applicable)

---

## Model Training (Future)

The underwriting engine supports model training via **XGBoost** for the Stage 2 scorer. The current implementation uses expert-defined weights, but can be replaced with a trained model.

### Model Architecture (Planned)

```
Input Features (17):
├── FICO Score
├── Credit Utilization
├── DTI Ratio
├── Income Stability (encoded)
├── Months Credit History
├── Employment Months
├── Loan Amount
├── Loan-to-Income Ratio
├── Number of Open Trades
├── Number of Inquiries (last 12mo)
├── Number of Delinquencies (last 24mo)
├── Public Records Count
├── Available Credit
├── Monthly Surplus (income - expenses)
├── Cash Flow Volatility
├── Account Age (oldest)
└── Payment History Score

Output:
└── Risk Score (0-100)
```

### Feature Importance (Expected)

Based on industry benchmarks and the current expert weights:

| Feature | Expected Importance | Current Weight |
|---------|-------------------|----------------|
| FICO Score | ~35% | 40% |
| Cash Flow | ~18% | 0-30% (blend) |
| DTI Ratio | ~15% | 15% |
| Credit Utilization | ~12% | 15% |
| Income Stability | ~10% | 15% |
| Account Age | ~7% | 10% |
| Employment | ~3% | 5% |

---

## Fair Lending (BISG Proxy Methodology)

OrangeFi includes a placeholder for **BISG (Bayesian Improved Surname Geocoding)** proxy methodology for fair lending analysis:

```python
# TODO: Implement BISG methodology for fair lending analysis
# This will:
# 1. Use Bayesian probability to estimate race/ethnicity
#    from applicant surname and geographic location
# 2. Analyze approval rates, pricing, and adverse action
#    rates across estimated demographic groups
# 3. Flag disparities > 80% of highest group rate
#    (four-fifths rule / 80% threshold)
# 4. Generate fair lending reports for compliance review
```

---

## Engine Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DecisionEngine                               │
│  (app/underwriting/decision_engine.py)                           │
│                                                                  │
│  Orchestrates the full pipeline:                                 │
│  gating → scoring → pricing → adverse action                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │  GatingRules   │  │  RiskScorer    │  │  PricingEngine │     │
│  │  (gating_rules │  │  (risk_scorer  │  │  (pricing.py)  │     │
│  │   .py)         │  │   .py)         │  │                │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AdverseActionGenerator (adverse_action.py)                │   │
│  │  ECOA/FCRA-compliant notice generation                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Files:                                                         │
│  ├── decision_engine.py   → DecisionEngine                      │
│  ├── gating_rules.py      → GatingRules                         │
│  ├── risk_scorer.py       → RiskScorer                          │
│  ├── pricing.py           → PricingEngine                       │
│  ├── adverse_action.py    → AdverseActionGenerator              │
│  ├── models/              → Model weights (model_weights.json)  │
│  └── routers/             → FastAPI router (underwriting.py)    │
└─────────────────────────────────────────────────────────────────┘
```

### Router Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/underwriting/score` | Full two-tiered underwriting |
| `POST` | `/api/v1/underwriting/pre-qualify` | Lightweight pre-qualification |
| `GET` | `/api/v1/underwriting/tiers` | List pricing tiers |
| `GET` | `/api/v1/underwriting/models` | List model versions |

---

## Performance Considerations

- **Gating rules** run in O(1) time — each check is a simple comparison
- **Risk scoring** runs in O(n) where n is the number of components (currently 6)
- **Pricing/offer generation** runs in O(t) where t is the term in months (for amortization schedule)
- **Adverse action generation** runs in O(f) where f is the number of risk factors
- Full pipeline typically completes in < 100ms
- Cash flow blend adds ~50ms when Plaid data is available
