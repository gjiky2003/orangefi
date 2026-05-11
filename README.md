# OrangeFi

**Technology-powered lending. Bank-partnered compliance.**

OrangeFi is a production-ready fintech lending platform that combines modern AI-driven underwriting with a bank partnership model. Borrowers get fast, transparent personal loans for debt consolidation. The platform handles the full lifecycle — from pre-qualification and application through underwriting, funding, and repayment — while maintaining full regulatory compliance (ECOA, FCRA, TILA, MLA).

> **Partner Bank Model:** OrangeFi operates as the technology platform; a regulated partner bank serves as the lender of record.

---

## Features

### 🏦 Borrower Portal
- **Pre-qualification** — Soft credit pull check with instant rate estimates (no hard inquiry)
- **Loan Application** — Full application flow with document upload, Plaid bank linking
- **Dashboard** — Active loans, payment history, amortization schedule
- **Self-Service** — Profile management, document upload, payment history

### 🔐 Admin Backoffice
- **Dashboard** — Real-time portfolio metrics (applications today, funded MTD, delinquency rates)
- **Applications Queue** — Filter, search, review, and decision applications
- **Loan Management** — Portfolio view, delinquency tracking, collections
- **Borrower Management** — Full borrower profiles, activity history
- **Compliance Console** — Adverse action tracking, compliance events, audit trails
- **Audit Log** — Immutable, searchable audit trail of all compliance-relevant actions
- **Reports** — CSV export for portfolio analysis

### 🤖 AI Underwriting Engine
- **Two-Tiered Architecture:**
  - Stage 1: Gating Rules — 7 hard decline checks (bankruptcy, credit score, income, delinquency, fraud, OFAC, document verification)
  - Stage 2: Risk Scoring — 6 weighted components (FICO 40%, Utilization 15%, DTI 15%, Income Stability 15%, Account Age 10%, Employment 5%) + Cash Flow Blend (30%)
- **6 Pricing Tiers** — A+ through E with APR ranges from 5.99% to 29.99%
- **Decision Logic** — Auto-approve (0-40), Manual Review (41-55), Decline (56-100)
- **Adverse Action Generation** — ECOA/FCRA-compliant adverse action notices with standardized reason codes
- **Counter-offers** — Automatic alternative loan amount suggestions for borderline applications
- **MLA Compliance** — 36% APR cap for active-duty military borrowers

### 📋 Compliance Ready
- **ECOA/FCRA Compliant** — Adverse action notices, reason codes, borrower rights statements
- **Fair Lending** — BISG proxy methodology for fair lending analysis (placeholder)
- **Audit Trails** — Immutable audit logs for every compliance-relevant action
- **Record Retention** — Document expiration tracking, encryption at rest (AES-256)
- **TILA Disclosures** — Truth in Lending disclosures throughout the application flow

### 🔗 Integrations
- **Plaid** — Bank account verification and linking
- **Stripe** — Payment processing and disbursement
- **Twilio** — SMS notifications
- **SendGrid** — Email notifications (adverse actions, disclosures, reminders)
- **DocuSign** — E-signatures for loan documents (integration scaffolded)

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS 3.4 | SSR, RSC, responsive UI |
| **State Management** | Zustand 5, Axios | Client state, API client |
| **Icons** | lucide-react | UI icon library |
| **Backend** | Python 3.12, FastAPI 0.115 | REST API, async endpoints |
| **ORM** | SQLAlchemy 2.0 (async) | Database access with asyncpg |
| **Validation** | Pydantic v2 | Request/response validation |
| **Database** | PostgreSQL 16 | Primary data store |
| **Cache/Queue** | Redis 7 | Session cache, rate limiting, Celery broker |
| **Object Storage** | MinIO (dev) → Amazon S3 (prod) | Document storage |
| **Auth** | JWT (access + refresh tokens), bcrypt | Authentication |
| **MFA** | TOTP (pyotp + QR codes) | Admin multi-factor authentication |
| **Task Queue** | Celery 5.4 | Async task processing (OCR, email, notifications) |
| **Monitoring** | Prometheus, Sentry | Metrics and error tracking |
| **Container** | Docker Compose | Local development environment |
| **CI/CD** | GitHub Actions | Build, test, deploy pipeline |

---

## Project Structure

```
orangefi/
├── backend/                          # FastAPI Python backend
│   ├── app/
│   │   ├── main.py                   # FastAPI app factory, middleware, exception handlers
│   │   ├── config.py                 # Pydantic Settings from env vars
│   │   ├── database.py               # SQLAlchemy async engine + session
│   │   ├── models.py                 # 11 SQLAlchemy ORM models
│   │   ├── routers/
│   │   │   ├── health.py             # Health check endpoint
│   │   │   ├── borrower.py           # Borrower portal API
│   │   │   └── admin.py              # Admin backoffice API
│   │   ├── underwriting/
│   │   │   ├── decision_engine.py    # Two-tiered underwriting orchestrator
│   │   │   ├── gating_rules.py       # Stage 1: 7 hard decline checks
│   │   │   ├── risk_scorer.py        # Stage 2: 0-100 risk score
│   │   │   ├── pricing.py            # 6 pricing tiers, amortization
│   │   │   ├── adverse_action.py     # ECOA/FCRA adverse action generation
│   │   │   ├── models/               # ML model weights
│   │   │   └── routers/
│   │   │       └── underwriting.py   # Underwriting API endpoints
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── utils/
│   │   │   ├── security.py           # JWT, bcrypt, TOTP MFA
│   │   │   ├── audit.py              # Audit log helper
│   │   │   ├── encryption.py         # AES-256 field-level encryption
│   │   │   ├── rate_limit.py         # In-memory rate limiter
│   │   │   └── dependencies.py       # FastAPI auth dependencies
│   │   └── integrations/             # Plaid, Stripe, Twilio, SendGrid
│   ├── requirements.txt
│   ├── Dockerfile                    # Multi-stage build
│   └── .env.example                  # Environment variable template
├── frontend/                         # Next.js 14 TypeScript frontend
│   ├── src/
│   │   ├── app/                      # App Router pages
│   │   │   ├── page.tsx              # Landing page
│   │   │   ├── login/page.tsx        # Borrower login
│   │   │   ├── register/page.tsx     # Borrower registration
│   │   │   ├── pre-qualify/page.tsx  # Pre-qualification form
│   │   │   ├── applications/         # Application flow
│   │   │   ├── loans/                # Loan management
│   │   │   ├── payments/             # Payment history
│   │   │   └── dashboard/            # Borrower dashboard
│   │   ├── components/               # Shared UI components
│   │   ├── lib/                      # API client, auth context
│   │   └── types/                    # TypeScript type definitions
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── infrastructure/
│   ├── docker-compose.yml            # Full dev environment (6 services)
│   └── terraform/                    # Future AWS IaC
├── scripts/
│   └── seed.py                       # Seed data (50 borrowers, 120 applications, 30 loans)
├── docs/
│   ├── ARCHITECTURE.md               # System architecture
│   ├── API.md                        # API reference
│   ├── DEPLOYMENT.md                 # Deployment guide
│   ├── UNDERWRITING.md               # Underwriting engine documentation
│   └── COMPLIANCE.md                 # Compliance framework
├── templates/                        # Document templates
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
└── .gitignore
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose (v2.24+)
- Node.js 18+ (for frontend development outside Docker)
- Python 3.12+ (for backend development outside Docker)

### 1. Clone and Start

```bash
git clone https://github.com/orangefi/orangefi.git
cd orangefi

# Copy environment file
cp backend/.env.example backend/.env

# Start all services
docker compose -f infrastructure/docker-compose.yml up -d
```

This starts:
- **PostgreSQL 16** on `localhost:5432`
- **Redis 7** on `localhost:6379`
- **MinIO** (S3) on `localhost:9000` (console: `localhost:9001`)
- **Backend API** on `localhost:8000`
- **Frontend** on `localhost:3000`

### 2. Seed the Database

```bash
# Run seed script inside the backend container
docker compose -f infrastructure/docker-compose.yml exec backend python scripts/seed.py
```

This creates:
- 50 synthetic borrowers with realistic profiles
- 120 loan applications in various states
- 30 funded loans with payment schedules
- 1 admin user: admin@orangefi.com / Admin123!

### 3. Open the App

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Register a new borrower |
| **API Docs** | http://localhost:8000/api/docs | Swagger UI |
| **Admin Login** | POST `/api/v1/admin/login` | admin@orangefi.com / Admin123! |
| **Health Check** | http://localhost:8000/api/health | |
| **Metrics** | http://localhost:8000/api/metrics | Prometheus format |
| **MinIO Console** | http://localhost:9001 | orangefi / orangefi123 |

---

## Screenshots

> Screenshots coming soon. The frontend includes:
>
> - **Landing Page** — Product overview with loan calculator
> - **Pre-Qualification** — Soft credit pull form with instant rate estimate
> - **Borrower Dashboard** — Active loans, upcoming payments, account summary
> - **Application Flow** — Multi-step loan application with document upload
> - **Admin Dashboard** — Portfolio metrics, applications queue, charts
> - **Admin Applications Queue** — Filterable, searchable applications list
> - **Admin Borrower View** — Full borrower profile with activity timeline
> - **Compliance Console** — Adverse action tracking and compliance events

---

## API Documentation

Full API documentation is available at:
- **Swagger UI:** http://localhost:8000/api/docs (development only)
- **ReDoc:** http://localhost:8000/api/redoc (development only)
- **OpenAPI JSON:** http://localhost:8000/api/openapi.json

### API Sections

| Endpoint Group | Prefix | Description |
|---------------|--------|-------------|
| **Health** | `/api/health`, `/api/metrics` | System health and Prometheus metrics |
| **Borrower** | `/api/v1/borrowers/*` | Registration, login, profile, applications, loans, payments, documents |
| **Underwriting** | `/api/v1/underwriting/*` | Pre-qualification, scoring, tiers, models |
| **Admin** | `/api/v1/admin/*` | Dashboard, applications, loans, borrowers, compliance, audit, reports |

See [docs/API.md](docs/API.md) for the complete API reference.

---

## Deployment

### Development
```bash
docker compose -f infrastructure/docker-compose.yml up -d
```

### Staging (Render)
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#render-deployment) for step-by-step Render deployment instructions.

### Production (AWS)
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#aws-production-target) for AWS architecture (ECS Fargate, RDS, ElastiCache, S3, CloudFront).

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `OrangeFi` |
| `APP_VERSION` | Application version | `0.1.0` |
| `ENVIRONMENT` | Runtime environment | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | Required |
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `30` |
| `ENCRYPTION_KEY` | AES-256 key for PII encryption | Required |
| `RATE_LIMIT_PER_MINUTE` | General API rate limit | `60` |
| `RATE_LIMIT_AUTH_PER_MINUTE` | Auth endpoint rate limit | `5` |
| `PLAID_CLIENT_ID` | Plaid API client ID | Optional (sandbox) |
| `PLAID_SECRET` | Plaid API secret | Optional (sandbox) |
| `PLAID_ENV` | Plaid environment | `sandbox` |
| `STRIPE_SECRET_KEY` | Stripe secret key | Optional |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | Optional |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | Optional |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | Optional |
| `SENDGRID_API_KEY` | SendGrid API key | Optional |
| `SENTRY_DSN` | Sentry error tracking DSN | Optional |
| `ADMIN_EMAIL` | Default admin email | `admin@orangefi.com` |
| `ADMIN_PASSWORD` | Default admin password | `Admin123!ChangeMe` |
| `S3_ENDPOINT` | S3/MinIO endpoint | Optional |
| `S3_ACCESS_KEY` | S3 access key | Optional |
| `S3_SECRET_KEY` | S3 secret key | Optional |
| `S3_BUCKET` | S3 document bucket | `orangefi-documents` |

See [docs/DEPLOYMENT.md#environment-variables-reference](docs/DEPLOYMENT.md#environment-variables-reference) for the complete reference.

---

## Database Models

OrangeFi uses 11 SQLAlchemy ORM models with full async support:

| Model | Table | Description |
|-------|-------|-------------|
| `Borrower` | `borrowers` | Customer profiles with encrypted PII |
| `Application` | `applications` | Loan applications through full lifecycle |
| `Loan` | `loans` | Originated loans with terms and status |
| `Payment` | `payments` | Scheduled and completed payments with amortization |
| `CreditPull` | `credit_pulls` | Soft/hard credit inquiry records |
| `PlaidConnection` | `plaid_connections` | Bank account linking via Plaid |
| `Document` | `documents` | Uploaded documents with OCR metadata |
| `UnderwritingResult` | `underwriting_results` | AI score, tier, decision, offer details |
| `AdminUser` | `admin_users` | Backoffice accounts with role-based access |
| `AuditLog` | `audit_logs` | Immutable audit trail (no updated_at) |
| `ComplianceEvent` | `compliance_events` | ECOA/FCRA adverse action tracking |
| `Consent` | `consents` | Borrower consent records |
| `Notification` | `notifications` | Outbound notification tracking |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full schema diagram and relationships.

---

## Underwriting Engine

```
┌─────────────────────────────────────────────────────────────────┐
│                   TWO-TIERED UNDERWRITING                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STAGE 1: GATING RULES                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 1. Bankruptcy check (last 7 years)                      │    │
│  │ 2. Minimum credit score (580)                           │    │
│  │ 3. Minimum annual income ($25k)                         │    │
│  │ 4. No 90+ day delinquency (last 12 months)              │    │
│  │ 5. No active tax liens or judgments                     │    │
│  │ 6. Identity fraud probability < 85%                     │    │
│  │ 7. OFAC/SDN sanctions check                             │    │
│  │ 8. Military borrower flag (MLA cap)                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                        │
│                          ▼                                        │
│  STAGE 2: RISK SCORING                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Weighted Component Score (0-100):                       │    │
│  │   • FICO Score              ─── 40%                     │    │
│  │   • Credit Utilization      ─── 15%                     │    │
│  │   • DTI Ratio               ─── 15%                     │    │
│  │   • Income Stability        ─── 15%                     │    │
│  │   • Account Age             ─── 10%                     │    │
│  │   • Employment Stability    ───  5%                     │    │
│  │   + Cash Flow Blend (30%)                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                        │
│                          ▼                                        │
│  FINAL DECISION                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Score 0-40:   ✅ Auto-Approved                         │    │
│  │  Score 41-55:  🔍 Manual Review                         │    │
│  │  Score 56-100: ❌ Declined                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                        │
│                          ▼                                        │
│  PRICING TIERS                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ A+ (0-15)   5.99-8.99%   up to $35k   1% orig. fee     │    │
│  │ A  (16-30)  7.99-11.99%  up to $35k   2% orig. fee     │    │
│  │ B  (31-45) 10.99-15.99%  up to $30k   3% orig. fee     │    │
│  │ C  (46-60) 14.99-20.99%  up to $25k   4% orig. fee     │    │
│  │ D  (61-75) 19.99-26.99%  up to $20k   5% orig. fee     │    │
│  │ E (76-100) 24.99-29.99%  up to $15k   5% orig. fee     │    │
│  │ MLA Cap: 36% APR for military borrowers                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

See [docs/UNDERWRITING.md](docs/UNDERWRITING.md) for the complete underwriting engine documentation.

---

## Compliance

OrangeFi is built with compliance as a foundation, not an afterthought:

- **ECOA** — Equal Credit Opportunity Act: fair lending notices, adverse action codes, borrower rights
- **FCRA** — Fair Credit Reporting Act: credit score disclosure, bureau information
- **TILA** — Truth in Lending Act: APR disclosure, total cost of borrowing, amortization schedules
- **MLA** — Military Lending Act: 36% APR cap, SCRA protections
- **State Usury Laws** — Configurable rate caps per jurisdiction
- **Privacy** — AES-256 field-level encryption for PII (SSN, income), data retention policies
- **Audit** — Immutable audit logs with actor, action, resource, timestamp, and IP tracking

See [docs/COMPLIANCE.md](docs/COMPLIANCE.md) for the complete compliance framework.

---

## License

**Proprietary** — All rights reserved. OrangeFi is not open-source software. See the [LICENSE](LICENSE) file for details.

---

## Badges

| Status | Badge |
|--------|-------|
| **Build** | ![Build Status](https://img.shields.io/badge/build-passing-brightgreen) |
| **Version** | ![Version](https://img.shields.io/badge/version-0.1.0-blue) |
| **License** | ![License](https://img.shields.io/badge/license-Proprietary-red) |
| **Python** | ![Python](https://img.shields.io/badge/python-3.12-blue) |
| **FastAPI** | ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green) |
| **Next.js** | ![Next.js](https://img.shields.io/badge/Next.js-14-black) |
| **PostgreSQL** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue) |
| **Status** | ![Status](https://img.shields.io/badge/status-MVP-yellow) |

---

## Contact

- **Engineering:** engineering@orangefi.com
- **Support:** support@orangefi.com
- **Security:** security@orangefi.com
