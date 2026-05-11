# OrangeFi — Phase 2: Business Model Design
**Date:** May 11, 2026
**CPO:** Hermes
**Status:** Draft

---

## 2.1 Business Model Overview

**Model:** Bank-partnered, AI-driven debt consolidation loan platform.

```
Borrower → OrangeFi (originator/tech platform) → Partner Bank (balance sheet)
                     ↓
        Earns: Origination fee + Servicing fee + Tech fee
```

OrangeFi does NOT:
- Hold loans on its balance sheet
- Take deposit risk
- Set interest rates independently (bank sets rate within OrangeFi's risk-score-based bands)

OrangeFi DOES:
- Acquire and pre-qualify borrowers
- Run AI underwriting and risk scoring
- Handle application, verification, and closing
- Service the loan (payment processing, customer support, collections escalation)
- Provide the technology platform to the bank

---

## 2.2 Revenue Model

### Fee Structure

| Fee Type | Amount | When Charged | Who Pays |
|----------|--------|-------------|----------|
| **Origination Fee** | 2-5% of loan amount | At funding | Borrower (included in APR) |
| **Servicing Fee** | 30-75 bps/year on outstanding balance | Monthly | Bank (from interest spread) |
| **Technology License** | $10k-$25k/month | Monthly | Bank (fixed platform fee) |
| **Performance Fee** | 10-20% of excess spread above floor | Quarterly | Bank (if portfolio outperforms) |

### Revenue Scenario (Year 1 Target: 500 loans, $7.5M funded)

| Revenue Source | Rate | Calculation | Annual Revenue |
|---------------|------|-------------|---------------|
| Origination fees | 4% avg | $7.5M × 4% | $300,000 |
| Servicing fees | 50 bps | $7.5M avg balance × 0.5% | $37,500 |
| Tech license | $15k/mo | $15k × 12 | $180,000 |
| Performance fee | 15% of excess | Assuming $50k excess | $50,000 |
| **Total** | | | **$567,500** |

### Revenue Scenario (Year 3 Target: 5,000 loans, $75M funded)

| Revenue Source | Rate | Calculation | Annual Revenue |
|---------------|------|-------------|---------------|
| Origination fees | 4% avg | $75M × 4% | $3,000,000 |
| Servicing fees | 50 bps | $60M avg balance × 0.5% | $300,000 |
| Tech license | $25k/mo | $25k × 12 | $300,000 |
| Performance fee | 15% of excess | Assuming $500k excess | $500,000 |
| **Total** | | | **$4,100,000** |

---

## 2.3 Pricing Model

### Risk-Based Pricing Tiers

| Tier | Credit Score | Cash Flow Score | APR Range | Origination Fee | Typical Monthly Payment ($15k/36mo) |
|------|-------------|-----------------|-----------|-----------------|--------------------------------------|
| A+ | 760+ | 85+ | 6.99-9.99% | 2% | $463-$484 |
| A | 720-759 | 75-84 | 8.99-11.99% | 3% | $477-$498 |
| B | 680-719 | 65-74 | 10.99-14.99% | 3.5% | $493-$520 |
| C | 640-679 | 55-64 | 13.99-17.99% | 4% | $512-$543 |
| D | 600-639 | 45-54 | 16.99-22.99% | 5% | $534-$585 |
| E | 580-599 | 35-44 | 20.99-28.99% | 5% | $560-$620 |

*Note: Actual rates set by partner bank within regulatory limits. Military Lending Act cap of 36% MAPR applies to active duty servicemembers.*

### Pricing Philosophy
- **Transparency-first:** Show exact APR, monthly payment, and total cost before borrower signs
- **No hidden fees:** No prepayment penalties, no late fee >$15 (or state max)
- **Rate beat:** Show borrower their current credit card APR vs. OrangeFi offer

---

## 2.4 Customer Acquisition Strategy

### Channel Mix (Year 1)

| Channel | % of Volume | Cost Per Acquisition | Monthly Budget |
|---------|------------|---------------------|----------------|
| Google Ads (brand + non-brand) | 35% | $80-$150 | $5,000 |
| Credit Karma / Experian / TransUnion | 25% | $50-$120 | $4,000 |
| Affiliate (NerdWallet, Bankrate) | 15% | $100-$200 | $3,000 |
| Direct mail (pre-screened) | 10% | $200-$400 | $2,000 |
| Social/Content (organic) | 10% | $20 (time cost) | $500 |
| Referral | 5% | $25-$50 per referral | $500 |

**Total monthly acquisition budget: ~$15,000** (self-funded)

### Acquisition Strategy Details

**Google Ads:**
- Target keywords: "debt consolidation loans," "credit card consolidation," "lower my APR"
- Negative keywords: "bad credit," "no credit check" (not your market)
- Ad copy: "Lower your credit card APR. Get a free quote in 2 minutes. No impact to your credit score."

**Credit Karma / Bureau Prequal:**
- Target: Borrowers with 580-740 credit scores, $5k-$35k revolving debt
- Pre-screened offers with firm-fixed APR (soft pull)
- Integrate via CK's Direct API or Ascend platform

**Affiliates:**
- NerdWallet, Bankrate, LendingTree — partner for rate comparison
- CPA model: $100-$200 per funded loan
- Provide rate table API for comparison pages

**Content Marketing:**
- Blog: "Debt Consolidation Guide," "How to Lower Your Credit Card APR"
- Calculators: Debt consolidation savings calculator (SEO gold)
- Videos: Founder explaining the OrangeFi difference (AI underwriting, transparency)

---

## 2.5 Borrower Journey

### End-to-End Flow

```
1. DISCOVERY
   Google ad / Affiliate / Credit Karma / Referral
   ↓
2. PRE-QUALIFICATION (2 minutes)
   Enter: Name, Email, Loan amount, Purpose
   Soft credit pull → Instant rate quote
   No credit score impact
   ↓
3. APPLICATION (10 minutes)
   Verify identity (SSN, DOB, address)
   Connect bank account (Plaid) OR upload 2 paystubs
   Enter employment & income details
   Select loan amount & terms
   ↓
4. UNDERWRITING (30 seconds)
   AI engine evaluates:
     - Credit bureau data (FICO, tradelines, inquiries)
     - Cash flow analysis (90 days transactions)
     - Income verification (paystub or payroll API)
     - Fraud signals (device, identity, synthetic checks)
   ↓
5. DECISION
   ✅ Approved → Show offer (rate, term, monthly payment)
   ❌ Declined → Clear explanation + credit score + free credit monitoring offer
   ⏳ Manual review → Flagged for exception handling
   ↓
6. DOCUMENTATION (5 minutes)
   E-sign loan agreement (DocuSign or native e-sign)
   ACH authorization form
   Direct pay-off instructions for existing creditors
   ↓
7. FUNDING (1-3 business days)
   Partner bank funds the loan
   Funds sent to borrower's account
   (Optional: Direct pay-off to creditors)
   ↓
8. SERVICING (Life of loan)
   Monthly ACH payments
   Dashboard: Balance, payment history, payoff calculator
   Customer support (AI chatbot + email)
   Collections escalation (4-stage: reminder → call → demand → charge-off)
```

### Pre-Qualification vs. Full Application

| Step | Pre-Qual | Full App |
|------|----------|----------|
| Credit pull | Soft (no score impact) | Hard (FICO score pull) |
| Income verification | Self-reported | Verified (paystub or Plaid) |
| Bank account | Not required | Required (Plaid or manual) |
| Legal agreement | Rate quote only | Binding loan contract |
| Time | 2 minutes | 10-15 minutes |
| Conversion to funded | — | 40-60% |

---

## 2.6 Operational Workflows

### Loan Origination Workflow

```
Borrower submits application
    ↓
Fraud detection (30+ signals)
    ↓
Credit bureau pull (Equifax, TransUnion, Experian)
    ↓
Cash flow analysis (Plaid — 90 days transactions)
    ↓
Income verification (paystub OCR or payroll API)
    ↓
AI risk score (ensemble: credit + cash flow + behavioral)
    ↓
Price assignment (tier + rate + fee)
    ↓
Manual review trigger? (if score in gray zone)
    ↓
Decision → Approval / Decline / Manual
    ↓
Disclosures → E-sign → Funding → Pay-off creditors
```

### Servicing Workflow

```
Loan funded
    ↓
Payment due D-5: Email reminder
Payment due D-1: SMS reminder
Payment due D-0: ACH initiation
    ↓
Payment success? → YES → Post, update balance, receipt
                  → NO  → Retry ACH (D+3)
                          → Still fails? Late fee (D+5)
                          → Stage 1: Auto-email (D+7)
                          → Stage 2: Call (D+14)
                          → Stage 3: Letter (D+21)
                          → Stage 4: Collections agency (D+45)
                          → Charge-off (D+120)
```

### Collections Stage Details

| Stage | Timing | Action | Cost |
|-------|--------|--------|------|
| 1 — Reminder | D+7 | Auto-email + SMS | $0.05 |
| 2 — Soft | D+14 | Auto-call (Twilio) + email | $0.50 |
| 3 — Hard | D+30 | Manual call from collections specialist | $15 |
| 4 — Agency | D+60 | Third-party collections agency | 25-30% of recovered |
| 5 — Charge-off | D+120 | Write off, 1099-C, credit bureau reporting | Full loss |

---

## 2.7 Key Metrics & KPIs

### Borrower Acquisition

| Metric | Target (Year 1) | Target (Year 3) |
|--------|----------------|-----------------|
| Cost per funded loan | $150 | $100 |
| Pre-qual → App conversion | 30% | 40% |
| App → Funded conversion | 50% | 60% |
| Average loan size | $12,000 | $15,000 |
| Originations per month | 40 | 400 |

### Portfolio Performance

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Net charge-off rate | <4% | >5.5% |
| 30+ day delinquency | <3% | >5% |
| 60+ day delinquency | <2% | >3.5% |
| 90+ day delinquency | <1% | >2.5% |
| Average APR | 14.99% | — |
| Average origination fee | 4% | — |

### Business Health

| Metric | Target | Notes |
|--------|--------|-------|
| Revenue per funded loan | $800-$1,200 | Depends on loan size and fee mix |
| Gross margin | 60%+ | Before partner bank revenue share |
| Operating margin | 20%+ | Breakeven at ~200 loans/month |
| Partner bank margin | 3-5% net | Bank's IRR on portfolio |

---

## 2.8 Risks & Mitigants

| Risk | Severity | Probability | Mitigation |
|------|----------|------------|------------|
| **Cannot find bank partner** | Critical | Medium | Have 3+ target banks; start with regional banks (not top 10); prepare pitch deck and due diligence package in Phase 8 |
| **Adverse selection** | High | Medium | AI underwriting + bank defines guardrails; monitor vintage performance monthly |
| **Regulatory action** | High | Low | Founder's regulatory background; engage compliance counsel early ($20k budget) |
| **Fraud rings** | High | Medium | Multi-layer fraud detection; synthetic identity checks; device fingerprinting |
| **Economic downturn** | Medium | Medium | Bank partner absorbs credit risk; your fee income is less correlated with defaults |
| **Competitor price war** | Medium | Medium | Differentiation is AI underwriting + transparency, not price alone |
| **Tech platform failure** | Medium | Low | Redundant infrastructure; AWS/GCP migration plan; SOC 2 readiness |
| **Key person dependence** | Medium | High | Document all processes; AI does the work; plan for fractional COO hire at Month 6 |
| **State regulatory preemption challenge** | Low | Medium | Bank partnership structure is well-established; legal counsel validates |

---

## 2.9 Entity Structure

```
OrangeFi Technologies, Inc. (Delaware C-Corp)
    │
    ├── OrangeFi Lending, LLC (operating subsidiary)
    │   • Holds service provider agreements
    │   • Manages partner bank relationship
    │   • Owns IP and technology
    │
    └── OrangeFi Compliance, LLC (future)
        • Holds state licenses (if ever needed)
        • Manages regulatory filings
```

**Recommended structure:** Single Delaware C-Corp initially. Add LLC subsidiaries when you have legal counsel ($5k for formation).

---

## 2.10 Next Steps
1. ✅ Phase 1 — Niche selected: Debt consolidation
2. ✅ Phase 2 — Business model defined
3. ▶ Phase 3 — Product Requirements Document
