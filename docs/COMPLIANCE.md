# OrangeFi — Compliance Framework

## Regulatory Overview

OrangeFi is designed as a **technology platform** operating under a **bank partnership model**. The partner bank serves as the lender of record, while OrangeFi provides the technology, underwriting, and servicing infrastructure. This framework describes the compliance controls built into the platform.

---

## Regulatory Framework

### Equal Credit Opportunity Act (ECOA) — Regulation B

ECOA prohibits credit discrimination on the basis of race, color, religion, national origin, sex, marital status, age, public assistance income, or exercise of Consumer Credit Protection Act rights.

**OrangeFi Compliance Controls:**

| Control | Implementation | Location |
|---------|---------------|----------|
| **Adverse Action Notice** | Auto-generated ECOA-compliant notices with specific reasons | `adverse_action.py` |
| **Primary Reasons** | Limited to 4 primary reasons (ECOA best practice) | `adverse_action.py:generate_notice()` |
| **Rights Statement** | ECOA-mandated rights statement included in every adverse action | `adverse_action.py:_rights_statement()` |
| **Fair Lending Monitoring** | BISG proxy methodology (placeholder for future implementation) | `fair_lending.py` (planned) |
| **Application Data** | All application data retained for fair lending analysis | `models.py:Application` |
| **Audit Trail** | All credit decisions logged in immutable audit log | `models.py:AuditLog` |

### Fair Credit Reporting Act (FCRA) — Regulation V

FCRA governs the collection, dissemination, and use of consumer credit information.

**OrangeFi Compliance Controls:**

| Control | Implementation | Location |
|---------|---------------|----------|
| **Permissible Purpose** | Credit pulls only with borrower consent | `Consent` model |
| **Soft/Hard Pull Classification** | Separate tracking for soft and hard inquiries | `CreditPull.pull_type` |
| **Credit Score Disclosure** | Score and source disclosed in adverse action notices | `adverse_action.py` |
| **FCRA Details** | Specific FCRA explanations included in notices | `adverse_action.py:FCRA_details` |
| **Free Report Right** | 60-day free credit report right stated in notices | `adverse_action.py:_rights_statement()` |
| **Dispute Handling** | FCRA dispute tracking via `ComplianceEvent` | `ComplianceEvent` model |
| **Adverse Action Codes** | Standardized reason codes mapped to risk factors | `adverse_action.py:ADVERSE_ACTION_CODES` |

### Truth in Lending Act (TILA) — Regulation Z

TILA requires clear disclosure of loan terms and costs.

**OrangeFi Compliance Controls:**

| Control | Implementation | Location |
|---------|---------------|----------|
| **APR Disclosure** | Annual Percentage Rate clearly displayed in offers | `pricing.py:generate_offer()` |
| **Finance Charge** | Total cost of borrowing (interest + fees) disclosed | `pricing.py:calculate_total_cost()` |
| **Payment Schedule** | Full amortization schedule provided | `pricing.py:calculate_amortization_schedule()` |
| **Total of Payments** | Sum of all payments displayed | `pricing.py:generate_offer()` |
| **Amount Financed** | Net disbursement amount (after origination fee) | `pricing.py:generate_offer()` |

### Military Lending Act (MLA)

MLA caps APR at 36% for active-duty service members and their dependents.

| Control | Implementation | Location |
|---------|---------------|----------|
| **Military Borrower Detection** | Flagged during gating rules | `gating_rules.py:_check_military_borrower()` |
| **MLA APR Cap** | 36% maximum APR enforced in pricing | `pricing.py:calculate_rate()` |
| **SCRA Protections** | Interest rate reduction to 6% during active duty (planned) | Future |

### State Usury Laws

| Control | Implementation |
|---------|---------------|
| **Rate Caps** | Configurable per-state APR limits (future) |
| **Licensing** | Platform operates through partner bank with nationwide lending authority |

---

## Fair Lending Practices

### Non-Discrimination

OrangeFi is committed to fair lending. The platform is designed to prevent discrimination by:

1. **Automated Underwriting** — All decisions are made by the AI engine using objective criteria
2. **Manual Override Monitoring** — Admin overrides are logged and audited for bias
3. **Standardized Adverse Action** — All declined applicants receive consistent, compliant notices
4. **BISG Analysis** — (Planned) Bayesian Improved Surname Geocoding for fair lending monitoring

### BISG Proxy Methodology

The planned BISG implementation will:

```
1. Combine surname probability with geographic data
   to estimate applicant race/ethnicity
2. Compare approval rates across estimated demographic groups
3. Compare APR distributions across estimated demographic groups
4. Flag disparities exceeding the 80% threshold
   (four-fifths rule per Uniform Guidelines)
5. Generate quarterly fair lending reports
```

### Redlining Prevention

- Geographic lending data is tracked through application metadata
- Marketing and outreach data can be correlated with lending patterns
- Compliance dashboard provides visibility into geographic distribution of loans

---

## Adverse Action Procedures

### When Adverse Action is Required

Adverse action notices are generated when:

| Scenario | Notice Required | ECOA | FCRA |
|----------|----------------|------|------|
| Application declined | ✅ | ✅ | ✅ |
| Counter-offer declined by borrower | ✅ | ✅ | ✅ |
| Application approved with different terms | ✅ | ✅ | ✅ |
| Application withdrawn by borrower | ❌ | ❌ | ❌ |
| Account closed or terms changed unfavorably | ✅ | ✅ | ✅ |

### Notice Components

Every adverse action notice includes:

1. **Date and Application ID**
2. **Borrower Name**
3. **Specific Reasons** (up to 4 primary reasons, each with a standardized code)
4. **Credit Score** (if used in decision) with source
5. **FCRA Details** — How each factor impacted the decision
6. **ECOA Rights Statement** — Nondiscrimination rights
7. **CFPB Contact** — Where to file complaints
8. **60-Day Free Report Right** — Right to free credit report
9. **Counter-Offer** — If applicable, alternative terms

### Delivery Methods

| Method | Status | Notes |
|--------|--------|-------|
| **In-Portal** | ✅ Implemented | Displayed in borrower dashboard |
| **Email** | 🔧 Via SendGrid | Template integration pending |
| **Mail** | ❌ Future | For adverse actions in collections |

### Timeline

- Adverse action notices are generated **immediately** upon decision
- Notices should be delivered **within 30 days** of application completion (ECOA requirement)
- FCRA requires disclosure **at the time** of adverse action

---

## Data Privacy and Security

### Data Classification

| Classification | Examples | Protection |
|---------------|----------|------------|
| **Highly Sensitive** | SSN, income, bank account numbers | AES-256 field-level encryption |
| **Sensitive** | Name, address, phone, email, DOB | Encrypted at rest (DB-level) |
| **Internal** | Application data, loan terms, payment history | Access controls |
| **Public** | Marketing materials, rate sheets | No protection needed |

### Encryption

| Layer | Algorithm | Scope |
|-------|-----------|-------|
| **Transport** | TLS 1.3 | All API traffic |
| **Field-Level** | AES-256-GCM | SSN, Plaid access tokens, income |
| **Database** | AES-256 (RDS) | Full database at rest |
| **Backups** | AES-256 (S3) | Automated backup encryption |

### Field-Level Encryption

```python
# SSN and income are encrypted at the application layer
# before being sent to the database
from app.utils.encryption import encrypt_field

borrower.ssn_encrypted = encrypt_field(ssn_plaintext)
borrower.income_encrypted = encrypt_field(str(income))
```

### Data Retention

| Data Type | Retention Period | Disposal Method |
|-----------|-----------------|-----------------|
| Application Data | 25 months (ECOA requirement) | Anonymization |
| Loan Records | 7 years after loan paid/charged off | Archival + deletion |
| Audit Logs | 7 years (indefinite for compliance) | Immutable storage |
| Credit Reports | 5 years | Deletion after retention |
| PII (SSN, DOB) | Duration of relationship + 7 years | Secure deletion |
| Marketing Data | 2 years | Anonymization |

### Privacy Rights

- **Opt-out** — Borrowers can opt out of marketing communications
- **Data Access** — Borrowers can request a copy of their data
- **Correction** — Borrowers can update their profile information
- **Deletion** — Account deletion (with loan record retention as required by law)

---

## Audit Trails

### Immutable Audit Log

The `AuditLog` model is intentionally designed without an `updated_at` field — once written, audit records can never be modified.

```python
class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Immutable audit trail for all compliance-relevant actions.
    NOTE: This model intentionally does NOT include updated_at.
    """
```

### Audited Actions

Every action in the following categories is logged:

**Application Lifecycle:**
- `application_created`
- `application_updated`
- `application_submitted`
- `decision_made`
- `loan_funded`

**Payment Lifecycle:**
- `payment_received`
- `payment_failed`

**User Actions:**
- `user_registered`
- `user_login`
- `user_logout`

**Document Actions:**
- `document_uploaded`
- `document_verified`

**Credit Actions:**
- `credit_pull_soft`
- `credit_pull_hard`

**Bank Actions:**
- `bank_account_linked`
- `bank_account_unlinked`

**Compliance Actions:**
- `adverse_action_sent`
- `compliance_review`

**Admin Actions:**
- `admin_login`
- `admin_action`

### Audit Log Fields

| Field | Type | Description |
|-------|------|-------------|
| `created_at` | datetime | Immutable timestamp |
| `actor_id` | UUID | Who performed the action |
| `actor_type` | string | `borrower`, `admin`, or `system` |
| `admin_user_id` | UUID | FK to admin (if admin action) |
| `action` | enum | Action type (21 values) |
| `resource_type` | string | Entity type (application, loan, etc.) |
| `resource_id` | string | Entity UUID |
| `details` | JSONB | Structured context data |
| `changes` | JSONB | Before/after diff for updates |
| `description` | text | Human-readable summary |
| `ip_address` | string | Client IP |
| `user_agent` | string | Client user agent |
| `request_id` | string | Correlation ID |
| `severity` | string | info, warning, error, critical |

### Audit Log Queries

Admins can search and filter the audit log:

```
GET /admin/audit-log?action=decision_made&actor_type=admin&created_after=2026-01-01&page=1
```

---

## Compliance Events

The `ComplianceEvent` model tracks compliance-specific events beyond standard audit logging.

### Event Types

| Event Type | Description |
|------------|-------------|
| `adverse_action` | Adverse action notice sent |
| `fair_lending_review` | Fair lending analysis triggered |
| `regulatory_report` | Regulatory report generated |
| `ecoa_notice` | ECOA-specific notice |
| `fcra_dispute` | FCRA dispute received |
| `tila_disclosure` | TILA disclosure provided |
| `internal_review` | Internal compliance review |

### Event Lifecycle

```
pending → sent → acknowledged → resolved → escalated
```

### Event Fields

| Field | Description |
|-------|-------------|
| `event_type` | Compliance event type enum |
| `status` | Current status (pending, sent, acknowledged, resolved, escalated) |
| `reason_codes` | ECOA adverse action reason codes |
| `reason_description` | Plain-language explanation |
| `action_taken` | What action was taken |
| `sent_at` | When notice was delivered |
| `sent_via` | Delivery channel (email, mail, portal, SMS) |
| `delivery_status` | delivered, bounced, failed, pending |
| `acknowledged_at` | When borrower acknowledged |
| `dispute_filed` | Whether borrower filed a dispute |
| `regulatory_reference` | CFPB complaint ID, exam reference |
| `notes` | Internal compliance notes |

---

## Record Retention

### Retention Schedule

| Record Type | Retention Period | Legal Basis |
|-------------|-----------------|-------------|
| **Loan Applications** | 25 months from submission | ECOA Regulation B |
| **Approved Loans** | 7 years from final payment | Statute of limitations |
| **Declined Applications** | 25 months | ECOA Regulation B |
| **Adverse Action Notices** | 25 months | ECOA Regulation B |
| **Credit Reports** | 5 years from pull | FCRA |
| **Audit Logs** | 7 years | General compliance |
| **Compliance Events** | 7 years | Regulatory |
| **Borrower PII** | Duration + 7 years | State privacy laws |
| **Payment Records** | 7 years | Tax/accounting |

### Document Retention

Documents uploaded by borrowers have an `expires_at` field for automated retention management.

```python
class Document(Base):
    expires_at: Mapped[Optional[datetime]]
```

Documents are stored in S3 with:
- Server-side encryption (AES-256)
- Versioning enabled
- Lifecycle policies for automated archival and deletion

---

## Vendor Management

### Third-Party Providers

| Vendor | Service | Data Shared | Security Certification |
|--------|---------|-------------|----------------------|
| **Plaid** | Bank account verification | Bank account tokens | SOC 2 Type II |
| **Stripe** | Payment processing | Payment data | PCI DSS Level 1 |
| **SendGrid** | Email delivery | Email address | SOC 2 Type II |
| **Twilio** | SMS delivery | Phone number | SOC 2 Type II |
| **DocuSign** | E-signatures | Signed documents | SOC 2 Type II |
| **Sentry** | Error tracking | Error logs | SOC 2 Type II |
| **AWS** | Infrastructure | All data | SOC 2 Type II, PCI DSS |

### Vendor Due Diligence

- All vendors undergo security assessment before integration
- Data processing agreements (DPAs) are in place with all vendors
- Annual SOC 2 reports are reviewed for all critical vendors
- Vendor security incidents are tracked in compliance events

---

## Compliance Calendar

| Frequency | Activity | Owner |
|-----------|----------|-------|
| **Daily** | Review pending adverse action deliveries | Compliance team |
| **Daily** | Monitor application queue for fair lending flags | Underwriting |
| **Weekly** | Review manual review decisions for consistency | Head of Credit |
| **Monthly** | Generate fair lending monitoring report | Compliance |
| **Monthly** | Review rate changes and pricing adjustments | Product |
| **Quarterly** | Full fair lending analysis (BISG) | Compliance |
| **Quarterly** | Vendor security review | Security |
| **Annually** | ECOA/FCRA compliance audit | External auditor |
| **Annually** | SOC 2 Type II audit | External auditor |
| **Annually** | Risk assessment review | Risk management |
| **As needed** | Regulatory filing updates | Compliance |
| **As needed** | State licensing renewals | Legal |

---

## Reporting

### Compliance Reports

| Report | Frequency | Content |
|--------|-----------|---------|
| **Fair Lending Analysis** | Monthly | Approval rates by demographic proxy, APR disparities |
| **Adverse Action Summary** | Monthly | Volume by reason code, delivery status |
| **Audit Log Summary** | Weekly | Notable actions, admin activity |
| **Dispute Log** | Monthly | FCRA disputes received, status, resolution |
| **Regulatory Filing** | As required | HMDA (future), state reports |
| **Portfolio Quality** | Weekly | Delinquency, charge-offs, concentrations |
| **Vendor Security** | Quarterly | Vendor incidents, access reviews |

### Report Generation

Admin users can generate CSV reports:

```
GET /admin/reports/portfolio?format=csv&date_from=2026-01-01&date_to=2026-12-31
GET /admin/reports/applications?format=csv&date_from=2026-01-01&date_to=2026-12-31
```

---

## Consent Management

Borrower consent is tracked via the `Consent` model:

| Consent Type | Required For | Storage |
|-------------|--------------|---------|
| **Terms of Service** | Account creation | `borrower.agreed_to_tos_at` |
| **Privacy Policy** | Account creation | `borrower.agreed_to_privacy_at` |
| **Credit Pull** | Credit inquiry | `credit_pull.consent_received_at` |
| **Bank Account Linking** | Plaid connection | Via Plaid Link flow |
| **Electronic Disclosure** | E-signatures | Via DocuSign |

---

## Questions & Contacts

| Role | Contact |
|------|---------|
| **Chief Compliance Officer** | compliance@orangefi.com |
| **Data Protection Officer** | privacy@orangefi.com |
| **Security Team** | security@orangefi.com |
| **Legal Department** | legal@orangefi.com |
