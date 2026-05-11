# OrangeFi — Phase 4: MVP Build Plan & Tech Stack
**Date:** May 11, 2026
**Status:** Draft

---

## 4.1 Recommended Tech Stack

### Philosophy
- **Python-first** — matches your existing PalmFi/SunCredit experience and AI/ML comfort
- **Server-rendered HTML** — no JS framework complexity for MVP (can add React later)
- **SQLite → PostgreSQL** — start simple, migrate when needed
- **Render for hosting** — familiar, free tier for MVP, scales to paid
- **Maximize AI** — let AI write most of the code

### Stack Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend                              │
│  Server-rendered HTML + Tailwind CSS + HTMX             │
│  (No React/Vue for MVP — can upgrade later)             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    Backend                               │
│  Flask (Python 3.11) — proven pattern from PalmFi       │
│  RESTful API endpoints                                  │
│  Flask-Login for session management                     │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    AI/ML Layer                           │
│  Scikit-learn + XGBoost for underwriting                │
│  OpenAI/GPT-4 for:                                     │
│    • Chatbot (customer support)                        │
│    • Document analysis (paystub OCR)                   │
│    • Adverse action explanation                        │
│  SHAP for model explainability                         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    Integrations                          │
│  Plaid (bank linking + transactions + income)          │
│  Stripe (ACH payments)                                 │
│  Credit Bureau API (Equifax or TransUnion)             │
│  Socure/Alloy (identity verification + fraud)          │
│  Twilio (SMS + email notifications)                    │
│  DocuSign (e-signature)                                │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    Database                              │
│  SQLite (MVP) → PostgreSQL (production)                 │
└─────────────────────────────────────────────────────────┘
```

### Detailed Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **Backend** | Python 3.11, Flask | Proven pattern, you know it, AI-friendly |
| **Frontend** | HTML + Tailwind CSS + HTMX | Zero JS build tooling, fast to develop |
| **Templating** | Jinja2 (Flask native) | Server-rendered, SEO-friendly |
| **Database** | SQLite → PostgreSQL | SQLite for dev, Postgres for scale |
| **ORM** | SQLAlchemy | Industry standard for Python |
| **Auth** | Flask-Login + JWT | Session management |
| **Underwriting** | Scikit-learn + XGBoost | Proven ML for credit scoring |
| **AI/NLP** | OpenAI API (GPT-4) | Chatbot, document analysis |
| **Explainability** | SHAP | Model governance requirement |
| **Payments** | Stripe ACH | Simple API, good docs |
| **Bank Linking** | Plaid | Market standard |
| **Credit Bureau** | Equifax API (ePort) or TransUnion | Partner negotiation |
| **Identity/Fraud** | Socure or Alloy | Alloy is better for loan origination workflow |
| **Notifications** | Twilio (SMS) + SendGrid (email) | Both proven |
| **E-Sign** | DocuSign API or Signaturely | DocuSign is familiar to banks |
| **Hosting** | Render (MVP) → AWS/GCP (scale) | Free to start, enterprise when needed |
| **CI/CD** | GitHub Actions | Free, familiar |
| **Monitoring** | Sentry (errors) + Render logs | Free tier |

---

## 4.2 Database Schema (MVP)

### Core Tables

```sql
-- Borrowers (customer accounts)
CREATE TABLE borrowers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    ssn_encrypted TEXT NOT NULL,       -- AES-256 encrypted
    date_of_birth TEXT NOT NULL,
    phone TEXT,
    street_address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    income_self_reported REAL,         -- Annual income (self-reported)
    employment_status TEXT,            -- employed, self_employed, unemployed, retired
    employer_name TEXT,
    employment_length_months INTEGER,
    monthly_housing_payment REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Applications (loan applications)
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_id INTEGER NOT NULL REFERENCES borrowers(id),
    application_id TEXT UNIQUE NOT NULL,    -- ORG-2026-00001 format
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, prequal, submitted, processing, 
                                           -- approved, declined, manual_review, 
                                           -- docs_sent, funded, cancelled
    loan_amount_requested REAL NOT NULL,
    loan_purpose TEXT DEFAULT 'debt_consolidation',
    requested_term INTEGER NOT NULL,       -- 24, 36, 48 months
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    decided_at TIMESTAMP,
    decision TEXT,                         -- approved, declined, manual_review
    decision_reason TEXT,                  -- JSON of factors
    decline_reason_codes TEXT,             -- JSON array of FCRA codes
    PRIMARY KEY (id, borrower_id)
);

-- Credit Pulls (soft + hard)
CREATE TABLE credit_pulls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id),
    pull_type TEXT NOT NULL,               -- soft, hard
    bureau TEXT NOT NULL,                  -- equifax, transunion, experian
    fico_score INTEGER,
    vantagescore INTEGER,
    credit_data TEXT,                      -- JSON of full bureau response
    pulled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cost_cents INTEGER DEFAULT 0
);

-- Plaid Connections
CREATE TABLE plaid_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_id INTEGER NOT NULL REFERENCES borrowers(id),
    application_id INTEGER REFERENCES applications(id),
    plaid_access_token TEXT NOT NULL,       -- encrypted
    plaid_item_id TEXT NOT NULL,
    institution_name TEXT,
    institution_id TEXT,
    account_id TEXT,
    account_mask TEXT,
    account_name TEXT,
    account_type TEXT,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Cash Flow Analysis
CREATE TABLE cash_flow_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id),
    total_deposits_90d REAL,
    total_withdrawals_90d REAL,
    net_cash_flow REAL,
    income_volatility REAL,                -- standard deviation of monthly income
    nsf_count INTEGER,                     -- number of NSF/overdraft events
    average_daily_balance REAL,
    cash_flow_score INTEGER,               -- 0-100
    income_verified REAL,                  -- verified monthly income from bank data
    paycheck_detected BOOLEAN,
    analysis_json TEXT,                    -- full analysis data
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Underwriting Decisions
CREATE TABLE underwriting_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id),
    risk_score INTEGER,                    -- 0-100
    risk_tier TEXT,                        -- A+, A, B, C, D, E
    probability_default REAL,              -- 0-1
    approved_amount REAL,
    approved_apr REAL,
    approved_term INTEGER,
    origination_fee_percent REAL,
    origination_fee_amount REAL,
    monthly_payment REAL,
    model_version TEXT,
    model_outputs TEXT,                    -- JSON of all model features and scores
    adverse_action_codes TEXT,             -- JSON array
    shap_explanation TEXT,                 -- JSON of SHAP values
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    underwriter_id INTEGER REFERENCES admin_users(id),  -- NULL for auto-decision
    decision_notes TEXT
);

-- Loan Agreements (after acceptance)
CREATE TABLE loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id),
    borrower_id INTEGER NOT NULL REFERENCES borrowers(id),
    loan_amount REAL NOT NULL,
    apr REAL NOT NULL,
    term_months INTEGER NOT NULL,
    monthly_payment REAL NOT NULL,
    origination_fee REAL NOT NULL,
    disbursement_amount REAL NOT NULL,      -- loan_amount - fee
    status TEXT DEFAULT 'pending_disbursement',
    -- pending_disbursement, active, delinquent, charged_off, paid_off
    disbursed_at TIMESTAMP,
    first_payment_date TEXT,
    next_payment_date TEXT,
    remaining_balance REAL,
    paid_to_date TEXT,                      -- last paid through period
    delinquency_stage INTEGER DEFAULT 0,    -- 0=current, 1-5=stages
    charged_off_at TIMESTAMP,
    paid_off_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payments
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    scheduled_date TEXT NOT NULL,
    paid_date TEXT,
    amount REAL NOT NULL,
    principal_part REAL DEFAULT 0,
    interest_part REAL DEFAULT 0,
    fee_part REAL DEFAULT 0,
    status TEXT DEFAULT 'scheduled',
    -- scheduled, processing, completed, failed, skipped
    stripe_payment_intent_id TEXT,
    failure_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Collections Activities
CREATE TABLE collections_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    stage INTEGER NOT NULL,                -- 1-5
    action TEXT NOT NULL,                  -- email, sms, call, letter, agency
    action_detail TEXT,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    performed_by TEXT DEFAULT 'system',
    result TEXT,                           -- contacted, no_answer, promised_payment
    notes TEXT
);

-- Admin Users
CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'admin',
    -- admin, underwriter, collections, compliance, viewer
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- System Audit Log
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_type TEXT,                        -- borrower, admin, system
    user_id INTEGER,
    action TEXT NOT NULL,                  -- application_created, loan_funded, etc.
    entity_type TEXT,                      -- application, loan, payment, etc.
    entity_id INTEGER,
    details TEXT,                          -- JSON with before/after state
    ip_address TEXT
);
```

---

## 4.3 Development Plan (8-Week MVP)

### Week 1-2: Foundation
| Task | AI-assisted? | Effort |
|------|-------------|--------|
| Set up Flask project structure | Yes | 1 day |
| Database schema implementation | Yes | 1 day |
| Auth (registration, login, password reset) | Yes | 2 days |
| Admin user setup | Yes | 1 day |
| Landing page + static pages | Yes | 2 days |
| Render deployment setup | Manual | 1 day |

### Week 3-4: Application Flow
| Task | AI-assisted? | Effort |
|------|-------------|--------|
| Pre-qualification (soft pull) | Yes | 2 days |
| Full application (4-step form) | Yes | 3 days |
| Plaid integration (bank linking) | Manual | 2 days |
| Document upload | Yes | 1 day |
| Application status tracking | Yes | 1 day |

### Week 5-6: Underwriting Engine
| Task | AI-assisted? | Effort |
|------|-------------|--------|
| Credit bureau API integration | Manual | 2 days |
| Cash flow analysis module | Yes | 2 days |
| AI risk score model (XGBoost) | Yes + Manual | 3 days |
| Gating rules engine | Yes | 1 day |
| Decision engine (approve/decline/review) | Yes | 2 days |
| Adverse action generation | Yes | 1 day |
| Manual review admin workflow | Yes | 2 days |

### Week 7: Closing & Funding
| Task | AI-assisted? | Effort |
|------|-------------|--------|
| E-sign integration | Manual | 2 days |
| Loan agreement generation | Yes | 1 day |
| ACH payment setup (Stripe) | Manual | 2 days |
| Loan funding flow | Yes | 1 day |
| Borrower dashboard | Yes | 2 days |

### Week 8: Compliance & Polish
| Task | AI-assisted? | Effort |
|------|-------------|--------|
| TILA disclosures | Yes | 1 day |
| ECOA notices | Yes | 1 day |
| Privacy policy / GLBA compliance | Yes | 1 day |
| Admin dashboard | Yes | 2 days |
| AI chatbot (basic) | Yes | 2 days |
| Testing & bug fixes | Yes + Manual | 3 days |
| Pre-launch security review | Manual | 2 days |

### Development Cost Estimates

| Category | AI-Coding (Your Cost) | Traditional (With Dev Team) |
|----------|----------------------|---------------------------|
| Backend development | $0 (you + AI) | $40,000-$60,000 |
| Frontend development | $0 (you + AI) | $20,000-$30,000 |
| Integrations (Plaid, Stripe, bureau) | $0 (you + AI) | $15,000-$25,000 |
| AI/ML model development | $0 (you + AI) | $25,000-$40,000 |
| Compliance documentation | $0 (you + AI) | $10,000-$15,000 |
| Design/UI | $0 (Tailwind templates) | $10,000-$15,000 |
| **Total Dev Cost** | **~$0 (your time)** | **$120,000-$185,000** |

---

## 4.4 Hosting Plan

### Phase 1 — MVP on Render (Months 1-3)
| Item | Plan | Cost/Month |
|------|------|------------|
| Web service | Free (spins down after 15 min) | $0 |
| Database | SQLite (included) | $0 |
| PostgreSQL upgrade | $7/mo when needed | $7 |
| Custom domain | Free | $0 |
| SSL | Auto-included | $0 |
| **Total** | | **$0-$7/mo** |

### Phase 2 — Production on Render (Months 4-8)
| Item | Plan | Cost/Month |
|------|------|------------|
| Web service | Starter ($7/mo, no sleep) | $7 |
| Database | PostgreSQL $7/mo | $7 |
| Redis (if needed) | $7/mo | $7 |
| **Total** | | **$21/mo** |

### Phase 3 — Scale on AWS/GCP (Year 2+)
- Elastic Beanstalk or ECS Fargate
- RDS PostgreSQL
- Estimated: $200-$500/mo at 500+ loans/month

---

## 4.5 Integration Costs

| Service | MVP (Free/Dev) | Production |
|---------|---------------|------------|
| Plaid | $0 (dev sandbox) | ~$0.50 per connection |
| Stripe | $0 | 0.8% + $0.30/ACH |
| Credit Bureau | ~$0 (sandbox) | $3-5 per hard pull |
| Socure/Alloy | ~$0 (trial) | $1-3 per verification |
| Twilio | $0 (trial credits) | $0.0079/SMS + $0.002/email |
| OpenAI | $5-20/mo | $20-50/mo |
| DocuSign | $0 (dev) | $30/mo (10 envelopes) |
| **Total** | **~$25/mo** | **$200-500/mo** |

---

## 4.6 Testing Plan

| Test Type | Tool | When |
|-----------|------|------|
| Unit tests | pytest | Every PR |
| Integration tests | pytest + Flask test client | Every PR |
| API tests | Postman / Bruno | Weekly |
| Security scan | Bandit (Python) | Pre-release |
| Load test | Locust | Before pilot |
| Compliance validation | Manual checklist | Pre-launch |
| UAT | Pilot borrowers | Month 8+ |

---

## 4.7 Deployment Pipeline

```
Push to GitHub main
    ↓
GitHub Actions:
  - Run tests (pytest)
  - Run security scan (Bandit)
  - Build Docker image
    ↓
Deploy to Render (auto via GitHub webhook)
    ↓
Smoke test (curl health endpoint)
    ↓
Rolling update (no downtime)
```

---

## 4.8 Cost Summary (First 8 Months)

| Category | MVP Months 1-2 | Build Months 3-6 | Pilot Months 7-8 | Total |
|----------|---------------|-----------------|-----------------|-------|
| Hosting | $0 | $7 | $21 | ~$50 |
| Integrations | $25 | $50 | $200 | ~$550 |
| Marketing | $0 | $2,000 | $5,000 | $7,000 |
| Legal (formation + counsel) | $5,000 | $5,000 | $5,000 | $15,000 |
| Compliance | $0 | $2,000 | $3,000 | $5,000 |
| **Total** | **$5,025** | **$9,057** | **$13,221** | **~$27,600** |

**Your cost:** ~$27,600 over 8 months. All self-funded. No investors needed for MVP.

---

## 4.9 Next Steps

1-4 ✅ — Phases 1-4 complete  
5 ▶ — Phase 5: Compliance & Legal Framework  
6 — Phase 6: Pilot Program Design  
7 — Phase 7: Financial Model  
8 — Phase 8: Bank Partnership Readiness  
