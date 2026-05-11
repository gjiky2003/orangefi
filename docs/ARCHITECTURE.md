# OrangeFi — System Architecture

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │   Borrower Browser   │  │    Admin Browser     │  │   Mobile Apps      │ │
│  │   (Next.js SSR)      │  │   (Next.js SSR)      │  │   (Future)         │ │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘ │
│             │                        │                        │             │
└─────────────┼────────────────────────┼────────────────────────┼─────────────┘
              │                        │                        │
              ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CDN / LOAD BALANCER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              CloudFront CDN (prod) / Nginx (dev)                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                        │
└──────────────────────────────────────┼────────────────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   Next.js Frontend   │  │   FastAPI Backend     │  │   Admin Frontend     │
│   (App Router)       │  │   (Uvicorn Workers)   │  │   (Same Next.js)     │
│   :3000              │  │   :8000               │  │                      │
│                      │  │                       │  │                      │
│  • Landing Page      │  │  • Auth (JWT/MFA)     │  │  • Dashboard         │
│  • Pre-Qualify       │  │  • Borrower API       │  │  • Applications      │
│  • Apply             │  │  • Admin API          │  │  • Loans             │
│  • Dashboard         │  │  • UW Engine          │  │  • Borrowers         │
│  • Loans             │  │  • Integrations       │  │  • Compliance        │
│  • Payments          │  │  • Webhooks           │  │  • Audit             │
└──────────────────────┘  └──────────┬───────────┘  └──────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│    PostgreSQL 16     │  │      Redis 7          │  │   MinIO / S3         │
│    (Primary DB)      │  │   (Cache / Queue)     │  │  (Object Storage)    │
│                      │  │                       │  │                      │
│  • All entity data   │  │  • Rate limiting      │  │  • Documents         │
│  • Audit logs        │  │  • Session cache      │  │  • Uploaded files    │
│  • Compliance        │  │  • Celery broker      │  │  • OCR output        │
│  • Encrypted PII     │  │  • Job queue          │  │  • Public assets     │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
              │
              └───────────────────┬───────────────────┐
                                  ▼                   ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   Plaid (Bank Link)  │  │   Stripe (Payments)   │  │  Twilio / SendGrid   │
│                      │  │                       │  │                      │
│  • Link token gen    │  │  • Payment intents    │  │  • SMS notifications │
│  • Account auth      │  │  • Disbursement       │  │  • Email (SendGrid)  │
│  • Transaction sync  │  │  • Webhooks           │  │  • Templates         │
│  • Identity verify   │  │  • Refunds            │  │  • Status tracking   │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
```

## Component Descriptions

### Backend API (FastAPI)

The backend is a Python 3.12 FastAPI application that serves as the core of the platform.

**Key characteristics:**
- **Async-first** — All database operations use async/await with asyncpg driver
- **Auto-documentation** — Swagger UI at `/api/docs`, ReDoc at `/api/redoc`
- **Middleware stack:**
  1. `request_id_middleware` — X-Request-ID correlation
  2. `rate_limit_middleware` — Per-IP rate limiting (configurable limits)
  3. `request_timing_middleware` — Request duration logging and X-Response-Time-Ms header
- **Exception handlers** — Custom handlers for HTTPException, validation errors, and unhandled exceptions
- **CORS** — Configurable origins via `CORS_ORIGINS` env var
- **Prometheus metrics** — Exposed at `/api/metrics`
- **Sentry integration** — Optional error tracking

**Router structure:**

| Router | Prefix | Key Endpoints |
|--------|--------|--------------|
| `health_router` | `/api/v1` | `/api/health`, `/api/metrics` |
| `borrower_router` | `/api/v1/borrowers` | Register, login, profile, pre-qualify, applications, loans, payments, documents |
| `admin_router` | `/api/v1/admin` | Login, MFA, dashboard, applications queue, loans, borrowers, audit, compliance, reports |
| `underwriting_router` | `/api/v1/underwriting` | Score, pre-qualify, tiers, models |

### Frontend (Next.js 14)

Modern React application using the App Router pattern with Server Components.

**Key characteristics:**
- **App Router** — File-based routing with layouts, loading states, and error boundaries
- **Server Components** — Default rendering mode for SEO and performance
- **Client Components** — Interactive sections (forms, dashboards) with `"use client"` directive
- **Tailwind CSS 3.4** — Utility-first styling with responsive design
- **Zustand 5** — Lightweight client state management for auth context
- **Axios** — HTTP client with interceptors for JWT token injection and refresh
- **lucide-react** — Consistent icon library

**Pages:**

| Route | Description |
|-------|-------------|
| `/` | Landing page with loan calculator |
| `/login` | Borrower login |
| `/register` | Borrower registration |
| `/pre-qualify` | Soft credit pull pre-qualification |
| `/applications` | Loan application list |
| `/applications/[id]` | Application detail |
| `/loans` | Active loan list |
| `/loans/[id]` | Loan detail with amortization schedule |
| `/payments` | Payment history |
| `/dashboard` | Borrower dashboard with summary |

### Database (PostgreSQL 16)

PostgreSQL 16 is the primary data store with SQLAlchemy 2.0 async ORM.

**Connection configuration:**
- Async driver: `asyncpg`
- Sync driver: `psycopg2` (for Alembic migrations)
- Connection pool: 10 pool size, 20 max overflow
- Pool pre-ping enabled

### Cache & Queue (Redis 7)

Redis serves three purposes:

1. **Rate Limiting** — Per-IP request counting with sliding window (in-memory fallback)
2. **Celery Broker** — Task queue for async operations
3. **Cache** — Session cache, query result caching (future)

### Object Storage (MinIO / S3)

Documents uploaded by borrowers are stored in S3-compatible object storage:

- **Development:** MinIO at `localhost:9000` (console: `localhost:9001`)
- **Production:** Amazon S3
- **Buckets:** `orangefi-documents` (private), `orangefi-public` (downloadable)

---

## Data Flow

### Borrower Registration & Application Flow

```
Borrower                     Frontend                    Backend                    Database
   │                           │                           │                          │
   │  1. Visit Landing Page    │                           │                          │
   │──────────────────────────►│                           │                          │
   │                           │                           │                          │
   │  2. Pre-Qualify Form      │  3. POST /pre-qualify     │                          │
   │──────────────────────────►│──────────────────────────►│                          │
   │                           │                           │  Soft credit pull (mock) │
   │                           │                           │─────────────────────────►│
   │                           │                           │◄─────────────────────────│
   │                           │  4. Rate Estimate + Tier  │                          │
   │                           │◄──────────────────────────│                          │
   │◄──────────────────────────│                           │                          │
   │                           │                           │                          │
   │  5. Register Account      │  6. POST /register        │                          │
   │──────────────────────────►│──────────────────────────►│                          │
   │                           │                           │  Create borrower          │
   │                           │                           │  Encrypt PII (SSN)        │
   │                           │                           │─────────────────────────►│
   │                           │                           │◄─────────────────────────│
   │                           │  7. JWT Tokens            │                          │
   │                           │◄──────────────────────────│                          │
   │◄──────────────────────────│                           │                          │
   │                           │                           │                          │
   │  8. Full Application      │  9. POST /applications    │                          │
   │──────────────────────────►│──────────────────────────►│                          │
   │                           │                           │  Create application       │
   │                           │                           │  (status: draft→submitted)│
   │                           │                           │─────────────────────────►│
   │                           │                           │                          │
   │  10. Upload Documents     │  11. POST /documents      │                          │
   │──────────────────────────►│──────────────────────────►│  Upload to MinIO/S3      │
   │                           │                           │─────────────────────────►│
   │                           │                           │                          │
   │  12. Link Bank Account    │  13. POST /plaid/link     │                          │
   │──────────────────────────►│──────────────────────────►│  Store encrypted token   │
   │                           │                           │─────────────────────────►│
   │                           │                           │                          │
```

### Underwriting Flow

```
Application Submitted
        │
        ▼
┌───────────────────────────────────────────────┐
│  STAGE 1: GATING RULES                        │
│                                               │
│  Evaluate 7 hard checks:                      │
│  • Bankruptcy in 7yr?        → Decline        │
│  • Credit score < 580?       → Decline        │
│  • Income < $25k?            → Decline        │
│  • 90d delinquency in 12mo?  → Decline        │
│  • Active tax lien/judgment? → Decline        │
│  • Fraud probability >85%?   → Decline        │
│  • OFAC/SDN match?           → Decline        │
│  • Military borrower?         → Flag (MLA cap)│
└──────────────────────┬────────────────────────┘
         │                             │
      Decline                     Pass/Flag
         │                             │
         ▼                             ▼
┌──────────────┐        ┌────────────────────────────────┐
│  ADVERSE     │        │  STAGE 2: RISK SCORING         │
│  ACTION      │        │                                │
│  NOTICE      │        │  Compute 0-100 risk score:     │
│  (ECOA/FCRA) │        │  Weighted components           │
└──────────────┘        │  + Cash flow blend (optional)  │
                        └──────────────┬─────────────────┘
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                    0-40           41-55        56-100
                 Auto-Approve   Manual Review   Decline
                      │              │              │
                      ▼              ▼              ▼
              ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
              │ GENERATE     │ │ QUEUE FOR    │ │ ADVERSE ACTION   │
              │ LOAN OFFER   │ │ UNDERWRITER  │ │ NOTICE + COUNTER │
              │ (Pricing)    │ │ REVIEW       │ │ OFFER (if dti)   │
              └──────┬───────┘ └──────┬───────┘ └──────────────────┘
                     │               │
                     ▼               ▼
              ┌──────────────────────────────────┐
              │  BORROWER NOTIFIED                │
              │  • Offer presented in dashboard   │
              │  • Terms disclosed (TILA)         │
              │  • E-sign documents (DocuSign)    │
              └──────────────────────────────────┘
```

### Funding & Repayment Flow

```
Borrower Accepts Offer
        │
        ▼
┌──────────────────────────────┐
│  1. Generate Loan Contract   │
│  2. E-sign (DocuSign)        │
│  3. Compliance disclosure    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  4. Stripe Disbursement       │
│     (ACH to borrower's bank)  │
│  5. Loan status → active      │
│  6. Generate amortization     │
│     schedule (payments table) │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  7. Payment Collection         │
│     • Auto-ACH on due date    │
│     • Manual payments via     │
│       Stripe (debit/ACH)      │
│     • Late fee assessment     │
└──────────────┬───────────────┘
               │
         ┌─────┴─────┐
         ▼           ▼
    On Time       Delinquent
         │           │
         ▼           ▼
┌─────────────┐ ┌────────────────────┐
│  Continue   │ │  8. Dunning        │
│  Servicing  │ │     • SMS reminder │
│             │ │     • Email notice │
│             │ │     • Late fee     │
│             │ │  9. Collections    │
│             │ │     • 30d → notice │
│             │ │     • 60d → call   │
│             │ │     • 90d → agency │
│             │ │     • 120d→charge  │
│             │ │       off          │
└─────────────┘ └────────────────────┘
```

---

## Database Schema

### Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────────┐       ┌──────────────────┐
│    Borrower       │       │     Application       │       │      Loan        │
├──────────────────┤       ├──────────────────────┤       ├──────────────────┤
│ PK id (UUID)     │──1:N──│ PK id (UUID)          │──1:1──│ PK id (UUID)     │
│ email (unique)   │       │ FK borrower_id        │       │ FK application_id│
│ phone (unique)   │       │ status (enum)         │       │ FK borrower_id   │
│ first_name       │       │ requested_amount      │       │ loan_amount      │
│ last_name        │       │ requested_term_months │       │ apr              │
│ date_of_birth    │       │ loan_purpose          │       │ term_months      │
│ ssn_encrypted    │       │ monthly_income        │       │ monthly_payment  │
│ monthly_income   │       │ dti_ratio             │       │ origination_fee  │
│ address_line1    │       │ housing_status        │       │ status (enum)    │
│ city/state/zip   │       │ decisioned_at         │       │ days_past_due    │
│ employer         │       │ amount_funded         │       │ maturity_date    │
│ credit_tier      │       │ funded_at             │       │ paid_off_at      │
│ is_active        │       │ declined_reason       │       └────────┬─────────┘
└────────┬─────────┘       └──────────┬───────────┘               │
         │                            │                            │
         │                            │                            │
         │   ┌──────────────────┐      │   ┌──────────────────┐    │
         │   │   CreditPull      │      │   │   Document       │    │
         ├───│──────────────────│──────│───│────────────────│    │
         │   │ PK id            │      │   │ PK id            │    │
         │   │ FK borrower_id   │      │   │ FK borrower_id   │    │
         │   │ FK application_id│      │   │ FK application_id│    │
         │   │ credit_score     │      │   │ document_type    │    │
         │   │ bureau_name      │      │   │ file_key (S3)    │    │
         │   │ pull_type (soft/)│      │   │ status (enum)    │    │
         │   └──────────────────┘      │   │ ocr_text         │    │
         │                            │   └──────────────────┘    │
         │   ┌──────────────────┐      │                          │
         │   │ PlaidConnection   │      │   ┌──────────────────┐   │
         ├───│──────────────────│      │   │ Underwriting     │   │
         │   │ PK id            │      ├───│ Result           │   │
         │   │ FK borrower_id   │      │   ├──────────────────┤   │
         │   │ plaid_access_tok │      │   │ PK id            │   │
         │   │ plaid_item_id    │      │   │ FK application_id│   │
         │   │ institution_name │      │   │ FK borrower_id   │   │
         │   │ status (enum)    │      │   │ ai_score         │   │
         │   └──────────────────┘      │   │ ai_tier          │   │
         │                            │   │ decision (enum)  │   │
         │   ┌──────────────────┐      │   │ approved_apr_min │   │
         │   │ ComplianceEvent  │      │   │ approved_amount  │   │
         ├───│──────────────────│──────│───│ model_version    │   │
         │   │ PK id            │      │   └──────────────────┘   │
         │   │ FK borrower_id   │      │                          │
         │   │ FK application_id│      │   ┌──────────────────┐   │
         │   │ event_type (enum)│      │   │   Payment        │   │
         │   │ reason_codes     │      │   ├──────────────────┤   │
         │   │ status           │      │   │ PK id            │   │
         │   └──────────────────┘      │   │ FK loan_id       │───┘
         │                            │   │ FK borrower_id   │
         │   ┌──────────────────┐      │   │ payment_number   │
         │   │   Consent        │      │   │ scheduled_date   │
         │   ├──────────────────┤      │   │ total_amount     │
         │   │ PK id            │      │   │ principal_amount │
         │   │ FK borrower_id   │      │   │ interest_amount  │
         │   │ consent_type     │      │   │ status (enum)    │
         │   │ granted_at       │      │   │ external_ref     │
         │   └──────────────────┘      │   └──────────────────┘
         │                            │
         │   ┌──────────────────┐      │
         │   │ Notification     │      │
         │   ├──────────────────┤      │
         │   │ PK id            │      │
         │   │ FK borrower_id   │      │
         │   │ type/channel     │      │
         │   │ status           │      │
         │   └──────────────────┘      │
         │                            │
         ▼                            ▼
┌──────────────────┐       ┌──────────────────────┐
│   AdminUser       │       │     AuditLog          │
├──────────────────┤       ├──────────────────────┤
│ PK id (UUID)     │──1:N──│ PK id (UUID)          │
│ email (unique)   │       │ FK admin_user_id      │
│ hashed_password  │       │ actor_id              │
│ role (enum)      │       │ actor_type            │
│ mfa_enabled      │       │ action (enum)         │
│ mfa_secret       │       │ resource_type         │
│ is_active        │       │ resource_id           │
│ is_locked        │       │ details (JSONB)       │
│ login_attempts   │       │ changes (JSONB)       │
│ last_login_at    │       │ ip_address            │
│ permissions      │       │ created_at (immutable)│
└──────────────────┘       └──────────────────────┘
```

### Key Model Relationships

| Relationship | Type | Foreign Key |
|-------------|------|-------------|
| Borrower → Application | One-to-Many | `application.borrower_id` |
| Borrower → Loan | One-to-Many | `loan.borrower_id` |
| Borrower → Payment | One-to-Many | `payment.borrower_id` |
| Borrower → Document | One-to-Many | `document.borrower_id` |
| Borrower → CreditPull | One-to-Many | `credit_pull.borrower_id` |
| Borrower → PlaidConnection | One-to-Many | `plaid_connection.borrower_id` |
| Borrower → UnderwritingResult | One-to-Many | `underwriting_result.borrower_id` |
| Borrower → ComplianceEvent | One-to-Many | `compliance_event.borrower_id` |
| Application → Loan | One-to-One | `loan.application_id` |
| Application → UnderwritingResult | One-to-One | `underwriting_result.application_id` |
| Loan → Payment | One-to-Many | `payment.loan_id` |
| AdminUser → AuditLog | One-to-Many | `audit_log.admin_user_id` |

---

## Security Architecture

### Authentication Flow

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│  Client   │                    │  API      │                    │  JWT      │
├──────────┤                    ├──────────┤                    ├──────────┤
│           │  1. POST /login    │           │                    │           │
│           │──────────────────►│           │                    │           │
│           │                    │  2. Verify│                    │           │
│           │                    │  password │                    │           │
│           │                    │  (bcrypt) │                    │           │
│           │                    │           │                    │           │
│           │  3. Generate JWT   │           │                    │           │
│           │  (access+refresh)  │           │                    │           │
│           │◄──────────────────│           │                    │           │
│           │                    │           │                    │           │
│           │  4. Store tokens   │           │                    │           │
│           │  (localStorage /   │           │                    │           │
│           │   HTTP-only cookie)│           │                    │           │
│           │                    │           │                    │           │
│           │  5. API Request    │           │                    │           │
│           │  Authorization:    │           │                    │           │
│           │  Bearer <access>   │─────────►│  6. Verify JWT     │           │
│           │                    │           │  (signature, exp,  │           │
│           │                    │           │   type=access)     │           │
│           │                    │◄─────────│                    │           │
│           │  7. Response       │           │                    │           │
│           │◄──────────────────│           │                    │           │
│           │                    │           │                    │           │
│           │  8. Token Expired  │           │                    │           │
│           │  (401)             │           │                    │           │
│           │◄──────────────────│           │                    │           │
│           │                    │           │                    │           │
│           │  9. POST /refresh  │           │                    │           │
│           │  Bearer <refresh>  │─────────►│  10. Verify refresh│           │
│           │                    │           │  token             │           │
│           │  11. New JWT pair │           │                    │           │
│           │◄──────────────────│           │                    │           │
└──────────┘                    └──────────┘                    └──────────┘
```

### Admin MFA Flow

```
1. Admin logs in with email + password
2. If MFA enabled, response includes requires_mfa=true
3. Admin enters TOTP code from authenticator app
4. POST /admin/login with mfa_code in payload
5. Server verifies TOTP code
6. JWT tokens returned on success
```

### Rate Limiting

| Endpoint Group | Limit | Window |
|---------------|-------|--------|
| General API | 60 requests | 1 minute |
| Auth endpoints | 5 requests | 1 minute |
| Health/Metrics | Unlimited | — |

### Encryption

| Layer | Algorithm | Scope |
|-------|-----------|-------|
| **In Transit** | TLS 1.3 | All API traffic |
| **At Rest (DB)** | AES-256-GCM | SSN, income, Plaid tokens |
| **JWT Signing** | HMAC-SHA256 | Access + refresh tokens |
| **Passwords** | bcrypt (12 rounds) | Admin passwords |
| **Secrets** | Environment variables | All API keys, tokens |

### Audit Trail

Every compliance-relevant action is logged to the immutable `audit_logs` table:

- **Who** — Actor ID and type (borrower, admin, system)
- **What** — Action type (enum with 20+ values)
- **When** — Timestamp with timezone (immutable created_at)
- **Where** — IP address, user agent, request ID
- **Details** — JSONB with structured context and before/after diffs

---

## Integration Architecture

### Plaid (Bank Verification)

```
┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
│  Browser  │         │  Backend  │         │  Plaid    │         │   DB     │
├──────────┤         ├──────────┤         ├──────────┤         ├──────────┤
│           │ 1. Create│          │ 2. POST │          │         │          │
│           │ Link     │─────────►│ /link   │─────────►│         │          │
│           │ Token    │          │ /token/ │          │         │          │
│           │◄────────│          │◄────────│          │         │          │
│           │          │          │ create  │          │         │          │
│           │ 3. Open  │          │         │          │         │          │
│           │ Plaid    │          │         │          │         │          │
│           │ Link UI  │          │         │          │         │          │
│           │──────────│          │         │          │         │          │
│           │ 4. Public│          │ 5. POST │          │ 6. Exchg│          │
│           │ Token    │─────────►│ /plaid/ │─────────►│ public  │          │
│           │          │          │ /link/  │          │ → access│          │
│           │          │          │ /token  │◄────────│ token   │          │
│           │          │          │ /exchg  │          │         │          │
│           │          │          │         │          │         │          │
│           │          │          │ 7. Store│          │         │─────────►│
│           │          │          │ encrypt │          │         │          │
│           │          │          │ed token │          │         │          │
└──────────┘         └──────────┘         └──────────┘         └──────────┘
```

### Stripe (Payments & Disbursement)

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│  Backend  │         │  Stripe   │         │   DB     │
├──────────┤         ├──────────┤         ├──────────┤
│           │ 1. Create│          │         │          │
│           │ Payment  │─────────►│         │          │
│           │ Intent   │          │         │          │
│           │◄────────│          │         │          │
│           │          │          │         │          │
│           │ 2. Confirm│         │         │          │
│           │ Payment  │─────────►│         │          │
│           │          │          │         │          │
│           │ 3. Webhook│         │         │          │
│           │◄────────│          │         │          │
│           │          │          │         │          │
│           │ 4. Update│          │         │─────────►│
│           │ Payment  │          │         │          │
│           │ Status   │          │         │          │
│           │          │          │         │          │
│           │ 5. Create│          │         │          │
│           │ Transfer  │─────────►│         │          │
│           │ (Disburse)│         │          │          │
└──────────┘         └──────────┘         └──────────┘
```

---

## Deployment Architecture

### Development (Docker Compose)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Host                               │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Postgres │  │  Redis   │  │  MinIO   │  │  MinIO   │       │
│  │  :5432   │  │  :6379   │  │  :9000   │  │  Init    │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                               │
│  ┌──────────┐  ┌──────────┐                                    │
│  │ Backend  │  │ Frontend │                                    │
│  │  :8000   │◄─│  :3000   │                                    │
│  └──────────┘  └──────────┘                                    │
│                                                               │
│  Network: orangefi-net (bridge)                                │
└─────────────────────────────────────────────────────────────────┘
```

### Production Target (AWS)

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud                                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Amazon CloudFront (CDN)                      │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                         │
│  ┌────────────────────┼─────────────────────────────────────┐   │
│  │    Application Load Balancer (ALB)                       │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                         │
│  ┌────────────────────┼────────────────────────────────────┐    │
│  │              │                    │                     │    │
│  │  ┌───────────▼────┐  ┌───────────▼────┐               │    │
│  │  │  ECS Fargate   │  │  ECS Fargate   │               │    │
│  │  │  Frontend      │  │  Backend API   │               │    │
│  │  │  (Next.js)     │  │  (FastAPI)     │               │    │
│  │  └────────────────┘  └────────┬───────┘               │    │
│  └───────────────────────────────┼────────────────────────┘    │
│                                  │                              │
│  ┌───────────────────────────────┼────────────────────────┐    │
│  │              │                    │                     │    │
│  │  ┌───────────▼────┐  ┌───────────▼────┐  ┌──────────┐  │    │
│  │  │  Amazon RDS    │  │  ElastiCache   │  │  S3      │  │    │
│  │  │  PostgreSQL    │  │  Redis         │  │  Docs    │  │    │
│  │  └────────────────┘  └────────────────┘  └──────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  External Services:                                       │   │
│  │  Plaid  •  Stripe  •  Twilio  •  SendGrid  •  DocuSign  │   │
│  │  Sentry  •  Credit Bureau  •  OFAC/SDN API              │   │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline (GitHub Actions)

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Push to │   │  Build & │   │  Run     │   │  Deploy  │   │  Verify  │
│  main    │──►│  Lint    │──►│  Tests   │──►│  to      │──►│  Smoke   │
│          │   │          │   │          │   │  Render  │   │  Tests   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Async Python** | FastAPI + asyncpg | High concurrency for I/O-bound lending operations |
| **ORM** | SQLAlchemy 2.0 | Mature, well-documented, full async support, Alembic migrations |
| **Auth** | JWT (no session) | Stateless, works well with Docker/K8s, simpler than OAuth for MVP |
| **Admin MFA** | TOTP (pyotp) | Standards-based, no external dependency, authenticator app compatible |
| **Password Hashing** | bcrypt | Industry standard, resistant to GPU cracking |
| **PII Encryption** | AES-256 field-level | Granular control, encrypted at application layer before DB storage |
| **Rate Limiting** | In-memory (token bucket) | Simple, no external dependency, replaceable with Redis later |
| **Cache** | Redis | Dual-purpose: cache + Celery broker |
| **Storage** | MinIO → S3 | S3-compatible API, free dev environment, seamless prod migration |
| **Frontend** | Next.js 14 + Tailwind | SSR for SEO, RSC for performance, utility-first CSS for rapid dev |
| **State** | Zustand | Minimal boilerplate, TypeScript-native, no context provider hell |
| **API Client** | Axios | Interceptors for JWT refresh, wide ecosystem support |
| **Container** | Docker Compose | Consistent dev environments, single command to start all services |
| **CI/CD** | GitHub Actions | Free tier, GitHub integration, large action marketplace |
| **Hosting (MVP)** | Render | Free tier, auto-deploy from GitHub, managed Postgres/Redis |
| **Hosting (Prod)** | AWS ECS Fargate | Serverless containers, no cluster management, auto-scaling |
