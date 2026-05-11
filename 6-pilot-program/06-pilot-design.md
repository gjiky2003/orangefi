# OrangeFi — Phase 6: Pilot Program Design
**Date:** May 11, 2026
**Status:** Draft

---

## 6.1 Pilot Overview

**Objective:** Validate the OrangeFi debt consolidation product with real borrowers before launching at scale with a bank partner.

**Approach:** Manual underwriting with AI decision support — founder personally underwrites each loan using the AI model as an input.

**Duration:** 8 weeks (Weeks 1-8 of Month 7-8)

**Target:** 20-30 funded loans totaling $250k-$450k

**Funding:** Self-funded by founder (loans originate through partner bank or, if partner not yet secured, through a state-licensed origination arrangement)

---

## 6.2 Pilot Objectives

| Objective | Success Metric | Target |
|-----------|---------------|--------|
| Validate AI underwriting accuracy | Default rate at 6 months | <3% |
| Test borrower experience | Application completion rate | >50% |
| Test tech platform stability | Uptime | >99.5% |
| Test ACH payment processing | Payment success rate (1st attempt) | >90% |
| Validate unit economics | Revenue per loan | >$800 |
| Test collections workflow | Recovery rate (30+ day delinquent) | >70% |
| Validate compliance controls | Regulatory findings | 0 |
| Gather bank-ready performance data | Portfolio performance report | Complete |

---

## 6.3 Borrower Eligibility (Pilot)

| Criterion | Requirement | Rationale |
|-----------|-------------|-----------|
| Credit Score | 640-740 | Core target market, lower risk for self-funded pilot |
| Annual Income | $50k-$150k | Ability to repay |
| Revolving Debt | $5k-$25k | Meaningful consolidation opportunity |
| DTI Ratio | <40% | Conservative for pilot |
| Employment | W-2, 2+ years at same employer | Income stability |
| Geography | 3-5 states only (e.g., TX, FL, GA, VA, OH) | Limit regulatory exposure during pilot |
| Bankruptcy | None in last 7 years | Standard exclusion |
| Loan Purpose | Credit card debt consolidation only | Cleanest product fit |
| Banking Relationship | 12+ months at current bank | Proof of financial history |

**Target pilot borrower profile:** Salary $65k-$90k, credit score 680-720, $10k-$18k in credit card debt, 2+ years at job, homeowner or stable renter.

---

## 6.4 Manual Underwriting Procedures (Pilot)

Since the pilot is small, the founder manually underwrites each application using the AI model as a decision-support tool.

### Underwriting Checklist (per application)

| Step | Action | Data Source | Reviewer |
|------|--------|-------------|----------|
| 1 | Verify identity (SSN, DOB, address) | SSN validation service + credit bureau | Founder |
| 2 | Pull credit report | Equifax or TransUnion | AI + Founder |
| 3 | Run AI risk score model | OrangeFi underwriting engine | AI |
| 4 | Review cash flow (Plaid or bank statements) | Bank transaction data | Founder |
| 5 | Verify income (paystub or payroll API) | Document or digital verification | Founder |
| 6 | Check for fraud signals | Device + identity + behavioral | AI + Founder |
| 7 | Make decision | AI score + manual review | Founder |
| 8 | Document rationale | Underwriting notes form | Founder |

### Decision Authority Matrix (Pilot)

| Risk Score | AI Recommendation | Founder Authority |
|------------|------------------|-------------------|
| 70-100 | Auto-approve | Approve without review (spot-check 10%) |
| 50-69 | Conditional approve | Manual review required, can approve/decline |
| 40-49 | Manual review | Manual review required, can approve with notes |
| 0-39 | Decline | Decline (override with written rationale only) |

### Loan Limits (Pilot)

| Parameter | Limit |
|-----------|-------|
| Max loan amount | $25,000 |
| Min loan amount | $5,000 |
| Max term | 36 months |
| Min term | 24 months |
| Max APR | 24.99% |
| Min APR | 7.99% |
| Max origination fee | 5% |
| Pilot portfolio cap | $500,000 |

---

## 6.5 Pilot KPIs

### Weekly Monitoring Dashboard

| KPI | Formula | Target | Alert |
|-----|---------|--------|-------|
| Applications received | Count | 10+/week | <5 |
| Pre-qual → App rate | Apps / pre-quals | >30% | <20% |
| App → Funded rate | Funded / apps | >40% | <25% |
| Average loan size | $ average | $15,000 | <$10k |
| Average APR | % average | 14.99% | >20% |
| Time to fund | Days (app → funding) | <5 days | >10 days |
| 30-day delinquency | Count | 0 | >2 |
| Borrower satisfaction | Survey (1-5) | >4.0 | <3.5 |
| Tech uptime | % | >99.5% | <99% |

### Post-Pilot Analysis

| Analysis | Method | Timing |
|----------|--------|--------|
| AI score vs. actual performance | ROC curve, KS statistic | Month 3 post-pilot |
| Borrower demographics | Age, income, geography, credit score distribution | End of pilot |
| Loss rate | Actual defaults / total funded | 6 months post-pilot |
| Revenue analysis | Fee income vs. costs | End of pilot |
| Customer journey analysis | Drop-off rates by step | Continuous |

---

## 6.6 Pilot Risk Limits

| Risk | Limit | Action if Exceeded |
|------|-------|-------------------|
| Total pilot portfolio | $500,000 | Halt new originations |
| Individual loan limit | $25,000 | Require co-founder approval |
| 30+ day delinquency | 5% of portfolio | Freeze new originations in affected segment |
| 60+ day delinquency | 3% of portfolio | Halt all originations, begin portfolio review |
| Charge-off rate | 2% of portfolio | Halt originations, review underwriting |
| Fraud rate | 1% of applications | Halt originations, investigate fraud controls |
| Monthly loss | $5,000 | Halt originations, review portfolio |

---

## 6.7 Incident Response Procedures

### Incident Types

| Level | Example | Response | Escalation |
|-------|---------|----------|------------|
| L1 — Minor | Single payment failure, chatbot error | Fix within 24 hours | None |
| L2 — Moderate | Platform outage >30 min, data discrepancy | Fix within 4 hours | Founder notified |
| L3 — Major | Data breach, fraud ring, regulatory inquiry | Immediate response | Founder + legal counsel |
| L4 — Critical | Systemic fraud, fund misappropriation | Halt all operations | Founder + legal + bank partner |

### Incident Response Steps

```
1. DETECT — Automated monitoring or user report
2. ASSESS — Determine severity (L1-L4)
3. CONTAIN — Limit damage (e.g., pause new applications, freeze specific accounts)
4. INVESTIGATE — Root cause analysis
5. REMEDIATE — Fix the issue, restore services
6. NOTIFY — Affected parties (borrowers, bank partner, regulators as required)
7. DOCUMENT — Incident report with lessons learned
8. REVIEW — Update procedures to prevent recurrence
```

### Data Breach Notification (if applicable)

| Jurisdiction | Notification Requirement | Timeline |
|-------------|------------------------|----------|
| All states | Affected individuals + state AG (per state law) | 30-60 days depending on state |
| SEC/Gramm-Leach-Bliley | Financial institution regulator | As required |
| CFPB | If consumer harm | Immediately upon discovery |
| Bank partner | Per partnership agreement | Within 24 hours |

---

## 6.8 Pilot Completion Criteria

The pilot is considered successful when:

1. ✅ **20+ loans funded** with a total portfolio of $250k+
2. ✅ **Six-month default rate < 3%** (measured post-pilot)
3. ✅ **No compliance violations** or regulatory findings
4. ✅ **Borrower satisfaction > 4.0/5.0**
5. ✅ **Tech platform stable** (uptime > 99.5%)
6. ✅ **Unit economics validated** (revenue per loan > $800)
7. ✅ **Pilot performance data package** ready for bank partner

---

## 6.9 Pilot Timeline

| Week | Activities | Milestones |
|------|-----------|------------|
| 1-2 | Soft launch (invite-only, 5 borrowers) | 5 funded loans, validate flow |
| 3-4 | Controlled expansion (referral + targeted ads) | 10 funded loans |
| 5-6 | Full pilot operations (paid acquisition) | 20 funded loans |
| 7-8 | Wind down, data collection, analysis | Pilot report completed |

---

## 6.10 Pilot Reporting Template

```
────────────────────────────────────────
ORANGEFI PILOT — WEEKLY STATUS REPORT
Report Date:  [Date]
Week:         [1-8]
────────────────────────────────────────

APPLICATIONS
  Pre-qualifications:  [Count]
  Full applications:   [Count]  (conv: [X]%)
  Funded loans:        [Count]
  Total funded volume: [$X]

PORTFOLIO HEALTH
  Active loans:              [Count]
  Current:                   [Count]
  30+ day delinquent:        [Count] ([X]%)
  60+ day delinquent:        [Count] ([X]%)
  Charged off:               [Count] ([X]%)
  Avg credit score:          [Score]
  Avg loan size:             [$X]
  Avg APR:                   [X]%

REVENUE
  Origination fees collected:   [$X]
  Servicing fees earned MTD:    [$X]
  Total revenue MTD:            [$X]

TECH PLATFORM
  Uptime:           [X]%
  Critical bugs:    [Count]
  Deployments:      [Count]

COMPLIANCE
  Complaints:       [Count]
  Regulatory:       [None / Pending]
  Data incidents:   [Count]

NEXT WEEK PRIORITIES:
1. [Item]
2. [Item]
3. [Item]

ISSUES / RISKS:
• [Issue]
• [Risk]
────────────────────────────────────────
```

---

## 6.11 Next Steps

1-6 ✅ — Phases 1-6 complete  
7 ▶ — Phase 7: Financial Model  
