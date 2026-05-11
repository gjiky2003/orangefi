# OrangeFi API Reference

Base URL: `http://localhost:8000/api/v1` (development)
Production URL: `https://api.orangefi.com/api/v1`

## Authentication

OrangeFi uses JWT (JSON Web Tokens) for authentication with an access/refresh token pair.

### Token Format

```
Authorization: Bearer <access_token>
```

### Token Types

| Token | TTL | Purpose |
|-------|-----|---------|
| **Access Token** | 15 minutes (configurable) | API authorization |
| **Refresh Token** | 30 days (configurable) | Issuing new access tokens |

### Token Payload

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "type": "access",
  "iat": 1700000000,
  "exp": 1700000900,
  "jti": "unique-token-id",
  "role": "borrower",
  "email": "user@example.com"
}
```

### Authentication Flows

**Borrower Flow:**
1. `POST /borrowers/register` — Create account → receive JWT pair
2. `POST /borrowers/login` — Authenticate → receive JWT pair
3. `POST /borrowers/refresh` — Rotate tokens

**Admin Flow:**
1. `POST /admin/login` — Authenticate (with optional TOTP MFA)
2. `POST /admin/mfa/setup` — Generate TOTP secret + QR code
3. `POST /admin/mfa/verify` — Verify TOTP code and enable MFA

---

## Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... }
}
```

### Paginated Response

```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_items": 120,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Not found",
  "detail": "Borrower with ID 123 not found",
  "code": "NOT_FOUND",
  "status_code": 404,
  "validation_errors": null,
  "request_id": "req-uuid-here",
  "timestamp": "2026-05-11T14:00:00Z"
}
```

### Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | `BAD_REQUEST` | Invalid request body |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource conflict (e.g., duplicate) |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Internal server error |

### Rate Limiting Headers

```
X-Request-ID: req-uuid
X-Response-Time-Ms: 42.17
Retry-After: 12  (on 429 responses)
```

---

## Endpoints

## 1. Health & Infrastructure

### `GET /api/health`

System health check. Returns database connectivity, uptime, and environment info.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "database": "connected",
  "redis": null,
  "uptime_seconds": 8421.5,
  "timestamp": "2026-05-11T14:00:00Z"
}
```

### `GET /api/metrics`

Prometheus metrics endpoint. Returns metrics in Prometheus text format.

**Response:** `text/plain; version=0.0.4`

---

## 2. Borrower API

All borrower endpoints are prefixed with `/api/v1/borrowers`.

### Authentication Endpoints

#### `POST /borrowers/register`

Create a new borrower account. Returns JWT tokens.

**Request:**
```json
{
  "email": "john@example.com",
  "phone": "+12025551234",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "ssn": "123-45-6789",
  "address_line1": "123 Main St",
  "city": "San Francisco",
  "state": "CA",
  "zip_code": "94105",
  "monthly_income": 6000.00,
  "employer": "Acme Corp",
  "employment_status": "employed",
  "agreed_to_tos": true,
  "agreed_to_privacy": true
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "borrower_id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com"
}
```

#### `POST /borrowers/login`

Authenticate a borrower. Returns JWT tokens.

**Request:**
```json
{
  "email": "john@example.com",
  "password": "user-password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "borrower_id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com"
}
```

#### `POST /borrowers/refresh`

Refresh access token using a valid refresh token.

**Headers:** `Authorization: Bearer <refresh_token>`

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "borrower_id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com"
}
```

### Profile Endpoints

#### `GET /borrowers/me`

Get the authenticated borrower's profile.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john@example.com",
  "phone": "+12025551234",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "address_line1": "123 Main St",
  "city": "San Francisco",
  "state": "CA",
  "zip_code": "94105",
  "employer": "Acme Corp",
  "employment_status": "employed",
  "monthly_income": 6000.00,
  "is_identity_verified": false,
  "credit_score_range": null,
  "credit_tier": null,
  "is_active": true,
  "created_at": "2026-05-11T14:00:00Z",
  "updated_at": "2026-05-11T14:00:00Z"
}
```

#### `PUT /borrowers/me`

Update the authenticated borrower's profile. Only provided fields are updated.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "phone": "+12025559876",
  "employer": "New Corp",
  "monthly_income": 7500.00
}
```

### Pre-Qualification

#### `POST /borrowers/pre-qualify`

Run a soft credit pull simulation for pre-qualification. Returns estimated rate and tier without hard inquiry.

**Request:**
```json
{
  "email": "john@example.com",
  "phone": "+12025551234",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "annual_income": 75000.00,
  "credit_score": 720,
  "requested_amount": 15000.00,
  "has_bankruptcy": false,
  "has_delinquency": false
}
```

**Response (200):**
```json
{
  "pre_qualified": true,
  "estimated_risk_score": 28,
  "estimated_tier": "A",
  "estimated_tier_label": "Prime",
  "indicative_apr_range": [7.99, 11.99],
  "max_loan_amount": 35000.0,
  "disclaimer": "This is an estimated pre-qualification based on self-reported data. Final terms require a full application and credit check."
}
```

### Application Endpoints

#### `POST /borrowers/applications`

Create a new loan application.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "requested_amount": 15000.00,
  "requested_term_months": 36,
  "loan_purpose": "debt_consolidation",
  "application_monthly_income": 6000.00,
  "application_employer": "Acme Corp",
  "application_employment_status": "employed",
  "years_at_current_job": 3.5,
  "housing_status": "rent",
  "monthly_housing_payment": 1800.00,
  "total_existing_debt": 25000.00,
  "monthly_debt_payments": 950.00
}
```

**Response (201):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "borrower_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "submitted",
  "requested_amount": 15000.00,
  "requested_term_months": 36,
  "loan_purpose": "debt_consolidation",
  "created_at": "2026-05-11T14:00:00Z",
  "updated_at": "2026-05-11T14:00:00Z"
}
```

#### `GET /borrowers/applications`

List the authenticated borrower's applications.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | — | Filter by status |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 25 | Items per page (max 100) |

**Response (200):**
```json
{
  "data": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "borrower_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "submitted",
      "requested_amount": 15000.00,
      "requested_term_months": 36,
      "loan_purpose": "debt_consolidation",
      "created_at": "2026-05-11T14:00:00Z",
      "updated_at": "2026-05-11T14:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

#### `GET /borrowers/applications/{id}`

Get application detail with underwriting result.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "borrower_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "approved",
  "requested_amount": 15000.00,
  "requested_term_months": 36,
  "loan_purpose": "debt_consolidation",
  "underwriting_result": {
    "ai_score": 28.5,
    "ai_tier": "A",
    "decision": "approved",
    "approved_amount_min": 10000.00,
    "approved_amount_max": 15000.00,
    "approved_apr_min": 7.99,
    "approved_apr_max": 11.99
  },
  "loan": null,
  "created_at": "2026-05-11T14:00:00Z",
  "updated_at": "2026-05-11T14:00:00Z"
}
```

#### `POST /borrowers/applications/{id}/withdraw`

Withdraw a pending application.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "message": "Application withdrawn successfully",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "status": "cancelled"
  }
}
```

### Loan Endpoints

#### `GET /borrowers/loans`

List the authenticated borrower's loans.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | — | Filter by loan status |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 25 | Items per page (max 100) |

**Response (200):**
```json
{
  "data": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "application_id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "active",
      "loan_amount": 15000.00,
      "apr": 9.99,
      "term_months": 36,
      "monthly_payment": 484.15,
      "remaining_balance": 14500.00,
      "days_past_due": 0,
      "origination_date": "2026-05-11",
      "maturity_date": "2029-05-11"
    }
  ],
  "pagination": { ... }
}
```

#### `GET /borrowers/loans/{id}`

Get loan detail with amortization schedule.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "active",
  "loan_amount": 15000.00,
  "apr": 9.99,
  "term_months": 36,
  "monthly_payment": 484.15,
  "origination_fee": 300.00,
  "remaining_balance": 14500.00,
  "next_payment_date": "2026-06-11",
  "next_payment_amount": 484.15,
  "payments": [
    {
      "payment_number": 1,
      "scheduled_date": "2026-06-11",
      "total_amount": 484.15,
      "principal_amount": 359.90,
      "interest_amount": 124.25,
      "status": "scheduled"
    }
  ],
  "amortization_schedule": [ ... ]
}
```

### Payment Endpoints

#### `GET /borrowers/loans/{id}/payments`

List payments for a specific loan.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | — | Filter by payment status |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 25 | Items per page (max 100) |

#### `POST /borrowers/loans/{id}/payments`

Make a payment on a loan (idempotent).

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "amount": 484.15,
  "payment_method": "ach",
  "idempotency_key": "unique-key-123"
}
```

**Response (200):**
```json
{
  "payment_id": "880e8400-e29b-41d4-a716-446655440003",
  "status": "processing",
  "amount": 484.15,
  "payment_method": "ach",
  "external_reference": "pi_3MlLkL2eZvKYlo2C1aBcDeFg"
}
```

### Document Endpoints

#### `POST /borrowers/documents`

Upload a document for an application.

**Headers:** `Authorization: Bearer <access_token>`

**Request (multipart/form-data):**
| Field | Type | Description |
|-------|------|-------------|
| `file` | file | Document file (PDF, JPG, PNG) |
| `document_type` | string | `paystub`, `tax_return`, `bank_statement`, `government_id`, `proof_of_address` |
| `application_id` | string | UUID of the associated application |

**Response (201):**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "document_type": "paystub",
  "status": "uploaded",
  "file_name": "paystub_2026_01.pdf",
  "file_size_bytes": 245760,
  "created_at": "2026-05-11T14:00:00Z"
}
```

#### `GET /borrowers/documents`

List the authenticated borrower's documents.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `application_id` | string | — | Filter by application |
| `document_type` | string | — | Filter by document type |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 25 | Items per page (max 100) |

#### `DELETE /borrowers/documents/{id}`

Delete a document (soft delete).

**Headers:** `Authorization: Bearer <access_token>`

---

## 3. Underwriting API

All underwriting endpoints are prefixed with `/api/v1/underwriting`.

### `POST /underwriting/score`

Run full two-tiered underwriting on application data.

**Request:**
```json
{
  "application_id": "UW-2026-00123",
  "credit_score": 720,
  "annual_income": 85000.00,
  "dti_ratio": 0.28,
  "credit_utilization": 35,
  "loan_amount": 15000.00,
  "term_months": 36,
  "income_stability": "stable",
  "employment_months": 60,
  "months_credit_history": 96,
  "bankruptcy_in_7yr": false,
  "delinquency_90d_12mo": false,
  "identity_fraud_probability": 5.0
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "application_id": "UW-2026-00123",
    "decision": "approved",
    "decision_label": "Auto-Approved",
    "decision_stage": "scoring",
    "gating_result": {
      "passed": true,
      "reason": "All gating rules passed. Proceeding to Stage 2 scoring.",
      "action": "pass",
      "mla_applicable": false
    },
    "risk_score": 28,
    "tier": "A",
    "tier_label": "Prime",
    "offer": {
      "tier": "A",
      "loan_amount": 15000.00,
      "apr": 9.99,
      "term_months": 36,
      "monthly_payment": 484.15,
      "origination_fee": 300.00,
      "total_interest": 2429.40,
      "total_cost": 17729.40
    }
  }
}
```

### `POST /underwriting/pre-qualify`

Lightweight pre-qualification (soft pull only, no hard gating checks).

**Request:**
```json
{
  "credit_score": 700,
  "annual_income": 75000.00,
  "requested_amount": 10000.00,
  "dti_ratio": 0.25
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "pre_qualified": true,
    "estimated_risk_score": 32,
    "estimated_tier": "B",
    "estimated_tier_label": "Near Prime",
    "indicative_apr_range": [10.99, 15.99],
    "max_loan_amount": 30000.0,
    "disclaimer": "This is an estimated pre-qualification based on self-reported data."
  }
}
```

### `GET /underwriting/tiers`

List all pricing tiers with configurations.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "tiers": [
      {
        "tier": "A+",
        "label": "Prime+",
        "min_score": 0,
        "max_score": 15,
        "min_apr": 5.99,
        "max_apr": 8.99,
        "max_loan_amount": 35000.0,
        "origination_fee_pct": 1.0
      },
      { "tier": "A", ... },
      { "tier": "B", ... },
      { "tier": "C", ... },
      { "tier": "D", ... },
      { "tier": "E", ... }
    ],
    "available_terms": [12, 24, 36, 48],
    "mla_max_apr": 36.0
  }
}
```

### `GET /underwriting/models`

List available model versions and metadata.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "version": "v1.0.0",
        "name": "OrangeFi Scoring Model v1",
        "weights": { "fico_score": 0.40, ... },
        "loaded": true
      }
    ],
    "current_model": { ... }
  }
}
```

---

## 4. Admin API

All admin endpoints are prefixed with `/api/v1/admin`.

### Authentication

#### `POST /admin/login`

Authenticate an admin user. Supports optional TOTP MFA.

**Request:**
```json
{
  "email": "admin@orangefi.com",
  "password": "Admin123!",
  "mfa_code": "123456"
}
```

**Response (200) — without MFA:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "admin_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "display_name": "System Administrator",
  "email": "admin@orangefi.com",
  "role": "super_admin",
  "mfa_enabled": false,
  "requires_mfa": false
}
```

**Response (200) — MFA required (no code provided):**
```json
{
  "access_token": "",
  "requires_mfa": true,
  "admin_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "display_name": "System Administrator",
  "email": "admin@orangefi.com",
  "role": "super_admin"
}
```

#### `POST /admin/mfa/setup`

Generate TOTP secret, QR code SVG, and backup codes for MFA setup.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_url": "otpauth://totp/OrangeFi:admin@orangefi.com?secret=...",
  "qr_code_svg": "<svg>...</svg>",
  "backup_codes": ["A1B2-C3D4", ...],
  "message": "Scan the QR code with your authenticator app..."
}
```

#### `POST /admin/mfa/verify`

Verify the TOTP code and enable MFA.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "totp_code": "123456"
}
```

### Dashboard

#### `GET /admin/dashboard`

Get backoffice dashboard metrics.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "applications_today": 12,
  "pending_review": 5,
  "funded_mtd_amount": 84500.00,
  "active_loans": 28,
  "delinquent_loans": 2,
  "delinquency_rate_pct": 7.14,
  "charged_off_loans": 1,
  "portfolio_outstanding": 425000.00,
  "new_borrowers_30d": 45,
  "timestamp": "2026-05-11T14:00:00Z"
}
```

### Application Management

#### `GET /admin/applications`

List all applications with filters.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | — | Filter by status |
| `search` | string | — | Search by ID |
| `created_after` | datetime | — | Filter by creation date |
| `created_before` | datetime | — | Filter by creation date |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 25 | Items per page (max 100) |

**Response (200):**
```json
{
  "data": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "borrower_id": "550e8400-e29b-41d4-a716-446655440000",
      "borrower_name": "John Doe",
      "status": "submitted",
      "requested_amount": 15000.00,
      "requested_term_months": 36,
      "loan_purpose": "debt_consolidation",
      "created_at": "2026-05-11T14:00:00Z",
      "updated_at": "2026-05-11T14:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

#### `GET /admin/applications/{id}`

Get full application detail including underwriting result, documents, and compliance events.

**Headers:** `Authorization: Bearer <access_token>`

#### `POST /admin/applications/{id}/decision`

Make an underwriting decision (approve, decline, send to manual review).

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "decision": "approved",
  "note": "Borrower meets all criteria",
  "approved_amount": 15000.00,
  "approved_apr": 9.99,
  "approved_term_months": 36,
  "send_adverse_action": false
}
```

**Response (200):**
```json
{
  "message": "Application decision submitted successfully",
  "data": {
    "application_id": "660e8400-e29b-41d4-a716-446655440001",
    "decision": "approved",
    "decisioned_at": "2026-05-11T14:00:00Z",
    "decisioned_by": "aa0e8400-e29b-41d4-a716-446655440005"
  }
}
```

### Loan Management

#### `GET /admin/loans`

List all loans with filters.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | — | Filter by loan status |
| `days_past_due_min` | integer | — | Minimum days past due |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 25 | Items per page (max 100) |

#### `GET /admin/loans/{id}`

Get loan detail with full payment schedule.

**Headers:** `Authorization: Bearer <access_token>`

### Borrower Management

#### `GET /admin/borrowers`

List all borrowers with filters and search.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | string | — | Search by name, email, or ID |
| `is_active` | boolean | — | Filter by active status |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 25 | Items per page (max 100) |

#### `GET /admin/borrowers/{id}`

Get full borrower profile with applications, loans, documents, and compliance history.

**Headers:** `Authorization: Bearer <access_token>`

### Audit Log

#### `GET /admin/audit-log`

Search and filter the immutable audit trail.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | string | — | Filter by action type |
| `actor_type` | string | — | Filter by actor type (borrower, admin, system) |
| `resource_type` | string | — | Filter by resource type |
| `created_after` | datetime | — | Filter by date range |
| `created_before` | datetime | — | Filter by date range |
| `search` | string | — | Free-text search in description |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 25 | Items per page (max 100) |

**Response (200):**
```json
{
  "data": [
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440006",
      "created_at": "2026-05-11T14:00:00Z",
      "actor_id": "550e8400-e29b-41d4-a716-446655440000",
      "actor_type": "borrower",
      "action": "user_login",
      "resource_type": "borrower",
      "resource_id": "550e8400-...",
      "description": "Borrower john@example.com logged in",
      "ip_address": "192.168.1.100",
      "severity": "info"
    }
  ],
  "pagination": { ... }
}
```

### Compliance

#### `GET /admin/compliance-events`

List compliance events (adverse actions, ECOA notices, FCRA disputes, etc.).

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `event_type` | string | — | Filter by event type |
| `status` | string | — | Filter by status |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 25 | Items per page (max 100) |

### Reports

#### `GET /admin/reports/portfolio`

Generate portfolio summary report as CSV.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `csv` | Report format |
| `date_from` | date | — | Start date |
| `date_to` | date | — | End date |

**Response:** `text/csv` download

#### `GET /admin/reports/applications`

Generate applications report as CSV.

**Headers:** `Authorization: Bearer <access_token>`

---

## 5. Integration Endpoints

### Plaid

#### `POST /api/v1/integrations/plaid/create-link-token`

Create a Plaid Link token for frontend initialization.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "link_token": "link-sandbox-...",
  "expiration": "2026-05-11T15:00:00Z"
}
```

#### `POST /api/v1/integrations/plaid/exchange-public-token`

Exchange a Plaid public token for an access token.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "public_token": "public-sandbox-..."
}
```

### Stripe

#### `POST /api/v1/integrations/stripe/create-payment-intent`

Create a Stripe payment intent for loan repayment.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "loan_id": "770e8400-...",
  "amount": 484.15,
  "payment_method_types": ["ach_debit", "card"]
}
```

#### `POST /api/v1/integrations/stripe/webhook`

Stripe webhook handler for payment status updates.

**Headers:** `Stripe-Signature: <webhook_signature>`
**Request:** Raw Stripe webhook event payload

---

## Pagination

All list endpoints support pagination with the following query parameters:

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | integer | 1 | — | Page number (1-indexed) |
| `page_size` | integer | 25 | 100 | Items per page |

### Pagination Response Format

```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_items": 120,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## Status Enums

### Application Status

```
draft → prequal_submitted → prequal_completed → application_started → submitted → processing → manual_review → approved → docs_sent → funded → cancelled
                                                                                                                      → declined
```

| Value | Description |
|-------|-------------|
| `draft` | Initial state, not yet submitted |
| `prequal_submitted` | Pre-qualification form submitted |
| `prequal_completed` | Pre-qualification completed |
| `application_started` | Full application started |
| `submitted` | Application submitted for review |
| `processing` | Underwriting in progress |
| `manual_review` | Flagged for manual underwriting review |
| `approved` | Underwriting approved |
| `declined` | Underwriting declined |
| `docs_sent` | Loan documents sent to borrower |
| `funded` | Loan funded and disbursed |
| `cancelled` | Application cancelled |

### Loan Status

| Value | Description |
|-------|-------------|
| `pending_disbursement` | Approved but not yet funded |
| `active` | Loan is active, payments expected |
| `delinquent` | Payments are past due |
| `charged_off` | Loan charged off as loss |
| `paid_off` | Loan fully repaid |

### Payment Status

| Value | Description |
|-------|-------------|
| `scheduled` | Payment scheduled (future date) |
| `processing` | Payment being processed |
| `completed` | Payment successfully completed |
| `failed` | Payment failed |
| `skipped` | Payment skipped (forbearance, deferment) |
| `refunded` | Payment refunded |

### Admin Roles

| Value | Permissions |
|-------|-------------|
| `super_admin` | Full system access |
| `underwriter` | Application review and decision |
| `collections` | Loan servicing and collections |
| `compliance` | Compliance events and audit |
| `support` | Borrower support (limited read) |
| `viewer` | Read-only access |
