# Security Policy

## Supported Versions

| Version | Supported | Status |
|---------|-----------|--------|
| 0.1.x | ✅ | Active development |
| < 0.1 | ❌ | Pre-release |

---

## Reporting a Vulnerability

OrangeFi takes security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**DO NOT** file a public GitHub issue for security vulnerabilities. Instead, send an email to:

**security@orangefi.com**

### What to Include

- **Type of vulnerability** (XSS, SQL injection, privilege escalation, etc.)
- **Steps to reproduce** — Include specific endpoints, payloads, and configurations
- **Impact assessment** — What an attacker could achieve
- **Affected versions** — Which versions are vulnerable
- **Suggested fix** — If you have a remediation recommendation

### Response Timeline

| Timeframe | Action |
|-----------|--------|
| **24 hours** | Acknowledgment of receipt |
| **72 hours** | Initial assessment and severity classification |
| **7 days** | Fix development (critical severity) |
| **14 days** | Fix development (high severity) |
| **30 days** | Fix development (medium/low severity) |
| **Post-fix** | Public disclosure after patch is deployed |

### Disclosure Policy

- We request **90 days** from initial report before public disclosure
- We will credit researchers in security advisories (unless anonymity is requested)
- We coordinate disclosure timing with the reporter

---

## Security Architecture

### Authentication

| Mechanism | Implementation | Details |
|-----------|---------------|---------|
| **JWT Access Tokens** | `python-jose` (HS256) | 15-minute TTL, stateless |
| **JWT Refresh Tokens** | `python-jose` (HS256) | 30-day TTL, rotatable |
| **Password Hashing** | bcrypt (passlib) | 12 rounds, salted |
| **Admin MFA** | TOTP (pyotp + QR) | Time-based one-time passwords |
| **Backup Codes** | 8 one-time codes per admin | For MFA recovery |

### Authorization

| Role | Permissions |
|------|-------------|
| `super_admin` | Full system access |
| `underwriter` | Application review, decision |
| `collections` | Loan servicing, collections |
| `compliance` | Compliance events, audit |
| `support` | Read-only borrower support |
| `viewer` | Read-only dashboard |

### Encryption

| Layer | Algorithm | Key Management |
|-------|-----------|---------------|
| **Transport** | TLS 1.3 | Let's Encrypt / AWS ACM |
| **Field-level (PII)** | AES-256-GCM | 32-byte key in env var |
| **JWT Signing** | HMAC-SHA256 | SECRET_KEY env var |
| **Passwords** | bcrypt | Built-in salt |
| **Database at rest** | AES-256 | AWS RDS encryption |
| **Backups** | AES-256 | AWS S3 SSE |

### Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| General API | 60 requests | 1 minute |
| Auth endpoints | 5 requests | 1 minute |
| Health/Metrics | Unlimited | — |

---

## Security Controls

### Application Security

- **Input validation** — Pydantic v2 schema validation on all endpoints
- **SQL injection** — SQLAlchemy ORM with parameterized queries
- **XSS** — FastAPI automatic HTML escaping, React's built-in XSS protection
- **CSRF** — JWT bearer token authentication (no cookie-based auth)
- **Rate limiting** — Per-IP rate limiting on all non-health endpoints
- **CORS** — Configurable, restricted to known origins
- **Security headers** — X-Request-ID, X-Response-Time-Ms

### Infrastructure Security

- **Secrets management** — All secrets via environment variables, not in code
- **Container security** — Non-root user in Docker, multi-stage builds
- **Dependency scanning** — Regular `pip audit` and `npm audit`
- **Network isolation** — Docker Compose with bridge network
- **Health checks** — Container health checks for all services

### Data Security

- **PII encryption** — SSN, Plaid tokens, and income encrypted at field level
- **Data minimization** — Only essential PII collected and stored
- **Access controls** — Role-based access for admin users
- **Audit trail** — Immutable logging of all data access
- **Retention policies** — Automated data deletion per compliance schedule

---

## Known Security Considerations

### MVP/Limitations

The following are known limitations in the current MVP version that should be addressed before production deployment:

1. **Borrower password storage** — Currently uses SSN field as password proxy. A proper `hashed_password` field should be added to the Borrower model.

2. **In-memory rate limiting** — Rate limiting is per-process and resets on restart. Should use Redis for production.

3. **No account lockout for borrowers** — Admin accounts have lockout (5 attempts), but borrower accounts currently do not.

4. **No refresh token revocation** — Refresh tokens cannot be revoked server-side in the current implementation.

5. **No audit of read-only access** — Current audit logs track mutations but not read actions (viewing borrower data, etc.).

### Production Checklist

Before deploying to production, ensure:

- [ ] Borrower model has proper password field
- [ ] Redis-based rate limiting for distributed deployments
- [ ] Borrower account lockout added
- [ ] Refresh token blacklisting/revocation
- [ ] Read access audit logging
- [ ] WAF rules configured
- [ ] DDoS protection enabled
- [ ] Penetration testing completed
- [ ] Secrets rotated from defaults
- [ ] Database backup and restore tested
- [ ] Incident response plan documented
- [ ] Bug bounty program established

---

## Compliance

OrangeFi implements security controls required by:

| Regulation | Scope |
|------------|-------|
| **ECOA** | Fair lending, adverse action notices |
| **FCRA** | Credit reporting, dispute handling |
| **TILA** | Loan cost disclosure |
| **MLA** | Military borrower protections |
| **GLBA** | Financial privacy (Safeguards Rule) |
| **CCPA** | California consumer privacy |
| **PCI DSS** | Payment card data (via Stripe) |
| **SOC 2** | Information security controls (target) |

---

## Security Contacts

| Role | Contact |
|------|---------|
| **Security Team** | security@orangefi.com |
| **Bug Bounty** | security@orangefi.com |
| **Compliance** | compliance@orangefi.com |
| **Emergency** | security@orangefi.com (24h response) |
