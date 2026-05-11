# OrangeFi — Phase 3: Product Requirements Document (PRD)
**Date:** May 11, 2026
**Version:** MVP v1.0
**Status:** Draft

---

## 3.1 Product Overview

**Product Name:** OrangeFi Debt Consolidation Platform  
**Tagline:** Lower your rate. Simplify your payments.  
**Target Users:** U.S. consumers with $5k-$35k in revolving credit card debt, credit scores 580-740  
**Platform:** Web-first (mobile-responsive), mobile app in Phase 2  
**Business Model:** Bank-partnered origination, servicing, and technology platform  

---

## 3.2 User Stories

### Borrower Stories

| ID | Epic | Story | Priority | Effort |
|----|------|-------|----------|--------|
| US-01 | Pre-qual | As a borrower, I want to enter basic info and get a rate quote in 2 minutes without affecting my credit score | P0 | S |
| US-02 | Pre-qual | As a borrower, I want to see my estimated monthly payment, APR, and total cost clearly | P0 | S |
| US-03 | Apply | As a borrower, I want to apply online by providing my personal, employment, and financial details | P0 | M |
| US-04 | Apply | As a borrower, I want to securely connect my bank account (Plaid) to verify income and cash flow | P0 | M |
| US-05 | Apply | As a borrower, I want to upload documents (paystubs, ID) if I can't connect my bank | P1 | M |
| US-06 | Decision | As a borrower, I want an instant decision with clear explanation of my rate and terms | P0 | S |
| US-07 | Decision | As a borrower, if declined, I want to know why and what I can do to improve | P0 | S |
| US-08 | Docs | As a borrower, I want to e-sign my loan agreement and disclosures electronically | P0 | M |
| US-09 | Funding | As a borrower, I want to choose where to receive funds and optionally have OrangeFi pay my creditors directly | P0 | M |
| US-10 | Dashboard | As a borrower, I want a dashboard to view my balance, payment history, and next payment date | P0 | M |
| US-11 | Payments | As a borrower, I want to set up auto-pay (ACH) and make extra payments anytime | P0 | M |
| US-12 | Payments | As a borrower, I want to change my payment date or method | P1 | S |
| US-13 | Support | As a borrower, I want to chat with an AI assistant for common questions | P0 | M |
| US-14 | Support | As a borrower, I want to talk to a human if I have a complex issue | P1 | S |
| US-15 | Second Look | As a near-approved borrower, I want to provide more info (bank connect, documents) for reconsideration | P1 | M |

### Admin Stories

| ID | Epic | Story | Priority | Effort |
|----|------|-------|----------|--------|
| AD-01 | Dashboard | As an admin, I want a dashboard showing key metrics (apps, funded, delinquencies, revenue) | P0 | M |
| AD-02 | Review | As an admin, I want to review flagged applications and approve/decline manually | P0 | M |
| AD-03 | Portfolio | As an admin, I want to see all active loans, their status, and performance metrics | P0 | M |
| AD-04 | Collections | As an admin, I want to see delinquent accounts and trigger collection actions | P0 | M |
| AD-05 | Settings | As an admin, I want to configure pricing tiers, fees, and underwriting rules | P0 | M |
| AD-06 | Reporting | As an admin, I want to generate reports (portfolio, regulatory, investor) | P1 | L |
| AD-07 | Users | As an admin, I want to manage borrower accounts and reset passwords | P1 | S |
| AD-08 | Audit | As an admin, I want to view an audit log of all system actions and decisions | P0 | M |

---

## 3.3 Functional Specifications

### 3.3.1 Pre-Qualification Engine

**Purpose:** Generate a rate quote with a soft credit pull (no FICO impact)

**Inputs:**
- Loan amount ($5,000 - $35,000)
- Loan purpose (debt consolidation only for MVP)
- Email address
- Name (first, last)
- Estimated credit score range (self-reported; validated at full application)

**Processing:**
1. Soft credit pull via partner bureau API (Equifax or TransUnion)
2. Run eligibility rules:
   - Minimum credit score: 580
   - Maximum DTI: 55%
   - Maximum existing delinquencies: 3 (30+ day)
   - No active bankruptcy or foreclosure
3. Calculate risk score via lightweight pre-qual model
4. Assign pricing tier and estimate APR range

**Output:**
- Personalized APR range (e.g., "10.99% - 14.99%")
- Estimated monthly payment
- Estimated origination fee
- Estimated total cost
- "This won't affect your credit score" badge
- CTA: "Continue to full application"

**Business Rules:**
- Pre-qual offer valid for 30 days
- Rate may change at full application based on verified information
- If gating rules fail → decline message with general reasons

### 3.3.2 Full Application

**Sections:**
1. **Identity** — SSN, DOB, current address, previous address (if <2 years)
2. **Employment** — Employer, occupation, income (annual), employment length
3. **Financial** — Rent/mortgage payment, monthly debt obligations
4. **Bank Connect** — Plaid Link integration for account verification
5. **Loan Selection** — Amount, term (24/36/48 months), payment day
6. **Creditors** — List of credit cards/loans to consolidate (optional direct pay-off)

**Validation Rules:**
- SSN: 9 digits, validate checksum
- DOB: Must be 18+ years old
- Address: Verify via USPS API
- Income: Must be ≥ $25,000/year
- Employment: 0+ years (unemployed OK if other income)
- Loan amount: $5,000-$35,000, not exceeding 50% of annual income
- Term: 24, 36, or 48 months

### 3.3.3 Underwriting Decision Engine

(See Section 3.5 for detailed underwriting workflow)

**Output Types:**
| Decision | Criteria | Next Step |
|----------|----------|-----------|
| ✅ Auto-approve | Score ≥ threshold (e.g., 60/100) | Documentation → Funding |
| ⏳ Manual review | Score in gray zone (40-59) | Admin review queue |
| ❌ Decline | Score < 40 or gating rule failure | Decline notice + FCRA adverse action |

### 3.3.4 Documentation & E-Sign

**Documents:**
- Loan Agreement (promissory note)
- Truth in Lending Disclosure (TILA)
- ACH Authorization
- Privacy Notice (GLBA)
- Credit Score Disclosure
- State-specific disclosures (as needed)

**E-Sign Flow:**
1. Present all documents in browser
2. Borrower reviews each document (minimum scroll time enforced)
3. Check consent box: "I agree to electronic delivery and signing"
4. Sign with click-to-sign (mouse/stylus signature or typed name)
5. Timestamp and IP logging
6. Store signed PDF in document management system
7. Email copy to borrower

---

## 3.4 Wireframes (Textual Description)

### Screen 1: Landing Page
```
┌─────────────────────────────────────────────────┐
│  🍊 OrangeFi  [About] [How it Works] [Sign In]  │
│─────────────────────────────────────────────────│
│                                                   │
│   ╔═══════════════════════════════════════╗       │
│   ║   Lower Your Credit Card Rate.       ║       │
│   ║   Consolidate debt. Save money.      ║       │
│   ║                                      ║       │
│   ║   [Loan Amount: $15,000 ───●────]    ║       │
│   ║   [Email: you@email.com        ]     ║       │
│   ║   [      Check Your Rate       ]     ║       │
│   ║                                      ║       │
│   ║   🔒 Won't affect your credit score  ║       │
│   ║   • 5.99% - 24.99% APR • $5k-$35k   ║       │
│   ╚═══════════════════════════════════════╝       │
│                                                   │
│   How it Works → AI Scores You → Get Funded      │
│                                                   │
│   "Saved me $240/month on my credit cards."       │
│   — Sarah, verified borrower                      │
└─────────────────────────────────────────────────┘
```

### Screen 2: Pre-Qual Results
```
┌─────────────────────────────────────────────────┐
│  🍊 OrangeFi                                  ← │
│─────────────────────────────────────────────────│
│                                                   │
│   🎉 Great news! You pre-qualify!                 │
│                                                   │
│   ╔═══════════════════════════════════════╗       │
│   ║  Your Estimated Offer                 ║       │
│   ║                                       ║       │
│   ║  Loan Amount:     $15,000             ║       │
│   ║  APR:             10.99% - 14.99%     ║       │
│   ║  Monthly Payment: $490 - $520         ║       │
│   ║  Term:            36 months           ║       │
│   ║  Origination Fee: 4% ($600)           ║       │
│   ║                                       ║       │
│   ║  Vs. your current: 22.8% APR = $580/mo║       │
│   ║  You could save:   ~$90/month         ║       │
│   ╚═══════════════════════════════════════╝       │
│                                                   │
│   [Continue to Full Application]                  │
│   [Save & Come Back Later]                        │
│                                                   │
│   ✅ No credit score impact from checking         │
└─────────────────────────────────────────────────┘
```

### Screen 3: Application (Step 1 of 4)
```
┌─────────────────────────────────────────────────┐
│  🍊 OrangeFi    Application    Step 1 of 4    ← │
│─────────────────────────────────────────────────│
│                                                   │
│   Your Information                                │
│                                                   │
│   First Name    [___________]   Last [________]  │
│   SSN           [___-__-____]                     │
│   DOB           [MM/DD/YYYY]                      │
│   Email         [___________]                     │
│   Phone         [(___)-___-____]                  │
│                                                   │
│   Current Address                                 │
│   Street         [____________________]           │
│   City           [________] State [__] ZIP [___] │
│                                                   │
│   [Continue →]                                    │
│   🔒 256-bit encryption. Your data is safe.      │
└─────────────────────────────────────────────────┘
```

### Screen 4: Bank Connect (Step 3 of 4)
```
┌─────────────────────────────────────────────────┐
│  🍊 OrangeFi    Application    Step 3 of 4    ← │
│─────────────────────────────────────────────────│
│                                                   │
│   Connect Your Bank                               │
│                                                   │
│   We'll analyze 90 days of transactions to        │
│   verify your income and financial health.        │
│                                                   │
│   ╔═══════════════════════════════════════╗       │
│   ║                                       ║       │
│   ║     🔗 Connect Bank Account           ║       │
│   ║                                       ║       │
│   ║   • Chase • Wells Fargo • BofA • US  ║       │
│   ║   • 12,000+ supported institutions    ║       │
│   ╚═══════════════════════════════════════╝       │
│                                                   │
│   [Skip — I'll upload documents instead]          │
│                                                   │
│   🔒 Read-only access • 256-bit encrypted        │
│   🕐 Takes 2 minutes • Secure Plaid technology    │
└─────────────────────────────────────────────────┘
```

### Screen 5: Decision
```
┌─────────────────────────────────────────────────┐
│  🍊 OrangeFi                                  ← │
│─────────────────────────────────────────────────│
│                                                   │
│   🎉 Congratulations! You're Approved!            │
│                                                   │
│   ╔═══════════════════════════════════════╗       │
│   ║  Your Offer                           ║       │
│   ║                                       ║       │
│   ║  Loan Amount:      $15,000            ║       │
│   ║  APR:              12.99%             ║       │
│   ║  Monthly Payment:  $510.42            ║       │
│   ║  Term:             36 months          ║       │
│   ║  Origination Fee:  $600 (4%)          ║       │
│   ║  Total Cost:       $18,975.12        ║       │
│   ║                                       ║       │
│   ║  You save: $2,700 vs. current cards   ║       │
│   ╚═══════════════════════════════════════╝       │
│                                                   │
│   [Accept Offer & Sign Documents]                 │
│                                                   │
│   Factors that earned you this rate:              │
│   ✅ Strong payment history (7 years)             │
│   ✅ Low credit utilization improvement           │
│   ✅ Stable income & employment                   │
└─────────────────────────────────────────────────┘
```

---

## 3.5 Underwriting Workflow

### Data Sources

| Source | Data Points | Weight in Model |
|--------|------------|-----------------|
| **Credit Bureau** (Equifax/TransUnion) | FICO Score, tradelines, inquiries, public records, utilization | 40% |
| **Cash Flow** (Plaid) | 90 days income, spending patterns, NSF history, volatility | 35% |
| **Income Verification** (Plaid payroll / paystub OCR) | Monthly income, employer, employment length | 15% |
| **Identity/Fraud** (Persona / Alloy / Socure) | Identity verification, synthetic fraud check, device intelligence | 10% |

### AI Risk Score Model

**Architecture:** Two-stage ensemble

**Stage 1 — Gating Rules (Hard Pass/Fail)**
```
IF active bankruptcy → DECLINE
IF credit score < 580 → DECLINE
IF income < $25,000 → DECLINE
IF any 90+ day delinquency in last 12 months → DECLINE
IF identity fraud probability > 85% → DECLINE
IF active OFAC/SDN match → DECLINE
IF military borrower → apply MLA 36% cap
```

**Stage 2 — Risk Score (0-100)**
```
Input features (30+):
  - FICO score (8 categories)
  - Credit utilization ratio
  - Number of open tradelines
  - Average age of credit
  - Number of recent inquiries (last 6 months)
  - Income stability index (variance over 90 days)
  - Cash flow score (net positive months / 3)
  - NSF count (last 90 days)
  - Debt-to-income ratio
  - Payment-to-income ratio
  - Employment stability (months at current job)
  - Housing stability (months at current address)
  - Device fingerprint score
  - Email domain reputation
  - IP geolocation risk score

Model: XGBoost classifier (gradient boosted trees)
Training: Historical credit performance data + synthetic data
Output: Probability of default (0-1) → Risk score (0-100)
KS Statistic target: >40
AUC target: >0.75

Decision mapping:
  Score ≥ 70 → Auto-approve (Tier A/B)
  Score 50-69 → Auto-approve (Tier C/D)
  Score 40-49 → Manual review
  Score < 40 → Decline
```

### Adverse Action

For all declines and manual reviews:
- Generate tier-2 adverse action codes (model reasons)
- Provide FRB/FCRA-compliant notice with:
  1. Credit score used and source
  2. Key negative factors (max 4)
  3. Statement of ECOA rights
  4. CFPB contact information

---

## 3.6 Fraud Detection Design

### Multi-Layer Approach

| Layer | Check | Tool/Method | Decision |
|-------|-------|-------------|----------|
| 1 — Device | Device fingerprint, VPN/proxy detection, browser consistency | FingerprintJS / InAuth | Score 0-100 |
| 2 — Identity | SSN validation, DOB cross-check, address verification | Socure / Alloy | Pass/Fail |
| 3 — Synthetic | Credit file age, authorized user detection, thin file analysis | Bureau + custom rules | Score 0-100 |
| 4 — Email | Domain reputation, temporary email detection, email age | ZeroBounce / Kickbox | Pass/Fail |
| 5 — Bank | Bank account ownership, account age, transaction velocity | Plaid Auth + custom | Score 0-100 |
| 6 — Behavioral | Application speed, copy/paste detection, form focus patterns | Custom JS | Alert |

**Fraud Decision Rules:**
- Any Layer 2 or 4 failure → Auto-decline
- Layer 1 score < 30 → Manual review
- Layer 3 score < 40 → Manual review
- Layer 6 suspicious → Manual review

---

## 3.7 Servicing Workflow

### Payment Processing

| Feature | Specification |
|---------|--------------|
| Processor | Stripe + ACH (Stripe or Dwolla for ACH) |
| Auto-pay enrollment | Required at loan closing (opt-out available) |
| Payment methods | ACH bank account (primary), debit card (backup) |
| Payment schedule | Monthly, fixed date |
| Late fee | $15 or state max (whichever is lower) |
| Grace period | 5 days |
| Prepayment | No penalty, any amount, any time |

### Customer Support

| Channel | Hours | AI/Manual |
|---------|-------|-----------|
| Chatbot | 24/7 | AI (GPT-4 powered, trained on loan policies) |
| Email | 24/7 (respond within 4 hours) | AI triage → manual escalation |
| Phone | Business hours | Manual (fractional staffing) |
| SMS | 24/7 | Automated (payment reminders, status updates) |

---

## 3.8 Admin Dashboard

### Tabs/Views

| View | Content | Users |
|------|---------|-------|
| **Overview** | Application volume, funded volume, delinquency rate, revenue MTD | Admin |
| **Applications** | List of all applications with status, decision, actions | Admin |
| **Manual Review** | Flagged applications with all data + approve/decline actions | Admin + Underwriter |
| **Portfolio** | Active loans, performance metrics, vintage analysis | Admin |
| **Collections** | Delinquent accounts, aging schedule, actions taken | Admin |
| **Borrowers** | Borrower search, profiles, activity history | Admin |
| **Reports** | Downloadable reports (portfolio, regulatory, investor) | Admin |
| **Config** | Pricing tiers, underwriting rules, fee schedules | Admin only |

---

## 3.9 APIs & Integrations

### Internal API Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Frontend   │────→│  OrangeFi API   │────→│  Database     │
│  (React)    │     │  (Flask/FastAPI)│     │  (PostgreSQL) │
└─────────────┘     └───────┬─────────┘     └──────────────┘
                            │
                    ┌───────┼───────┐
                    │       │       │
                    ▼       ▼       ▼
               ┌────────┐┌──────┐┌────────┐
               │ Plaid  ││Stripe││Bureau  │
               └────────┘└──────┘└────────┘
```

### Third-Party Integrations (MVP)

| Service | Purpose | Cost/Month |
|---------|---------|------------|
| **Plaid** | Bank account linking, transactions, income | $0 (dev) — $500+ (prod) |
| **Stripe** | ACH payments, payment processing | 0.8% + $0.30 per ACH |
| **Credit Bureau** (Equifax/TransUnion) | Credit pull (soft + hard), FICO score | $3-5 per pull |
| **DocuSign / Signaturely** | E-signature | $30-50/month |
| **Socure or Alloy** | Identity verification, fraud | $1-3 per verification |
| **Twilio** | SMS/email notifications | Pay-as-you-go |
| **OpenAI** | AI chatbot, document analysis | $20-50/month |
| **AWS / Render** | Hosting | $20-100/month |

---

## 3.10 MVP Scope Summary

### In Scope (v1.0 — Launch)

✅ Borrower landing page with pre-qualification  
✅ Full application (4-step flow)  
✅ Plaid bank account linking  
✅ AI underwriting engine  
✅ Instant decision (approve/decline/manual review)  
✅ E-sign documents  
✅ Loan dashboard (borrower view)  
✅ ACH payment processing  
✅ Admin dashboard (applications, portfolio, manual review)  
✅ AI chatbot (basic Q&A)  
✅ Compliance disclosures (TILA, ECOA, FCRA, privacy)  
✅ Email notifications  

### Out of Scope (v1.0 — Post-launch)

⏳ Mobile app (iOS/Android)  
⏳ Direct creditor pay-off  
⏳ Co-borrower applications  
⏳ Multiple product types  
⏳ Referral program  
⏳ Advanced reporting suite  
⏳ API for bank partner integration  
⏳ Bank-branded white-label  

---

## 3.11 Next Steps

1. ✅ Phase 1 — Niche selected: Debt consolidation  
2. ✅ Phase 2 — Business model defined  
3. ✅ Phase 3 — PRD complete with user stories, specs, wireframes, data model  
4. ▶ Phase 4 — MVP Build Plan & Tech Stack  
