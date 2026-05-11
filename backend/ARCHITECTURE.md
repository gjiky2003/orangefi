# OrangeFi — Architecture & Implementation Plan
**CTO:** Hermes
**Date:** May 11, 2026

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Next.js Frontend                        │
│  (TypeScript + Tailwind + React Server Components)           │
│                                                              │
│  Public Site  │  App Flow  │  Dashboard  │  Admin Console   │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST + WebSockets
┌──────────────────────────▼──────────────────────────────────┐
│                     FastAPI Backend                           │
│  (Python 3.12 + Pydantic + SQLAlchemy + Celery)              │
│                                                              │
│  Auth     │  Apps    │  UW Engine  │  Payments  │  Admin     │
│  KYC      │  Fraud   │  Servicing  │  Reports   │  Webhooks  │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  PostgreSQL   │  │    Redis       │  │    S3/MinIO   │
│  (Primary DB) │  │  (Queue/Cache) │  │  (Documents)  │
└───────────────┘  └───────────────┘  └───────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Plaid       │  │   Stripe      │  │  Twilio/SendG │
│ (Bank Linking)│  │  (ACH/Payments)│  │ (SMS/Email)   │
└───────────────┘  └───────────────┘  └───────────────┘
```

## Tech Stack Decisions

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Frontend** | Next.js 14 + TypeScript | SSR for SEO, RSC for perf, great dev experience |
| **Backend** | Python FastAPI | Async, auto-docs, Pydantic validation, Python ecosystem |
| **Database** | PostgreSQL 16 | ACID, JSON support, great for fintech |
| **ORM** | SQLAlchemy 2.0 + Alembic | Mature, well-documented, async support |
| **Queue** | Celery + Redis | Async task processing (doc OCR, email, etc.) |
| **Auth** | JWT (access + refresh) | Simpler than Auth0 for MVP, same security level |
| **Storage** | MinIO (dev) → S3 (prod) | S3-compatible, free for dev |
| **Container** | Docker + Docker Compose | Consistent environments |
| **CI/CD** | GitHub Actions | Free, integrated |
| **Hosting (MVP)** | Render | Free tier, easy deploy |
| **Hosting (Prod)** | AWS ECS Fargate | Production-grade, scalable |
| **IaC** | Terraform (future) | For AWS deployment |

## Directory Structure

```
orangefi/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings from env
│   │   ├── database.py          # DB connection
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── borrower.py
│   │   │   ├── application.py
│   │   │   ├── loan.py
│   │   │   ├── payment.py
│   │   │   ├── user.py
│   │   │   └── audit.py
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API routes
│   │   ├── services/            # Business logic
│   │   ├── underwriting/        # AI/ML engine
│   │   ├── integrations/        # Plaid, Stripe, etc.
│   │   └── utils/               # Helpers
│   ├── alembic/                 # Migrations
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   ├── components/          # Shared components
│   │   ├── lib/                 # API client, utils
│   │   └── types/               # TypeScript types
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── infrastructure/
│   ├── docker-compose.yml
│   ├── nginx/
│   └── terraform/               # Future
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── runbook.md
│   └── admin-guide.md
├── scripts/
│   ├── seed.py
│   └── demo_data.py
└── README.md
```

## Database Schema (Core Tables)

```sql
-- Core entities
borrowers          (id, email, password_hash, personal_info, created_at)
applications       (id, borrower_id, status, loan_details, decision, created_at)
loans              (id, application_id, borrower_id, loan_details, status)
payments           (id, loan_id, amount, due_date, paid_date, status)
credit_pulls       (id, application_id, bureau, score, data, type)
plaid_connections  (id, borrower_id, access_token, item_id, status)
documents          (id, borrower_id, type, s3_key, status, ocr_data)
underwriting_results (id, application_id, score, tier, apr, details)
admin_users        (id, email, password_hash, role, mfa_secret)
audit_log          (id, user_type, user_id, action, entity_type, entity_id, details)
compliance_events  (id, type, description, borrower_id, timestamp)
```

## Implementation Phases

1. **Scaffolding** — Project structure, Docker, configs, CI/CD
2. **Database** — All models, migrations, seed data
3. **Auth** — Registration, login, JWT, roles, admin MFA
4. **Frontend Scaffold** — Next.js setup, layout, shared components
5. **Application Flow** — Landing → Pre-qual → Apply → Decision
6. **Underwriting Engine** — Risk scoring, pricing tiers, decision logic
7. **Borrower Dashboard** — Loan view, payments, documents
8. **Admin Console** — Applications, portfolio, collections, settings
9. **Integrations** — Plaid, Stripe, DocuSign, Twilio
10. **Compliance** — Adverse action, audit trails, fair lending
11. **Security** — Encryption, rate limiting, scanning
12. **Testing & Docs** — Tests, runbooks, admin guide
