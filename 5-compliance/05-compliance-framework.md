# OrangeFi — Phase 5: Compliance & Legal Framework
**Date:** May 11, 2026
**Status:** Draft

---

## 5.1 Corporate Structure

### Recommended Structure (Month 1)

```
OrangeFi Technologies, Inc.
  (Delaware C-Corporation)
```

**Why Delaware C-Corp:**
- Standard for venture-backed fintech (not seeking VC now, but leaves option open)
- Delaware legal system is predictable for corporate matters
- Easy to issue equity to future hires/advisors
- C-Corp structure allows loss carryforwards

**Formation steps:**
1. File Certificate of Incorporation with Delaware (online, ~$90)
2. Obtain EIN from IRS (free, online)
3. Open business bank account (Mercury or Relay — both fintech-friendly)
4. Register as foreign entity in your home state (if not Delaware)
5. File beneficial ownership information (BOI) with FinCEN (new 2024 requirement)
6. Draft incorporation documents (bylaws, board minutes, stock issuance)

**Estimated cost:** $500-$1,000 (Clerk, LegalZoom, or attorney)

### When to Add Subsidiaries (Month 6+)
```
OrangeFi Technologies, Inc.
    └── OrangeFi Lending Services, LLC
         (holds service agreements, IP, partner contracts)
```

---

## 5.2 Required Licenses & Registrations

### Under Bank Partnership Model

Because OrangeFi partners with a bank (the bank originates and holds loans), many state lending license requirements are **preempted** under federal banking law (National Bank Act 12 USC § 85, 86; Dodd-Frank § 1044). However, the following are still needed:

| License/Registration | Required? | Cost | Timeline |
|---------------------|-----------|------|----------|
| Delaware C-Corp formation | ✅ Yes | ~$500 | 1 day |
| EIN (IRS) | ✅ Yes | Free | 1 day |
| State business registration | ✅ Yes | $50-200 | 1 day |
| Money transmitter license | ❌ No (not handling funds directly) | — | — |
| State lending licenses | ❌ Likely preempted via bank partnership | — | — |
| Credit Services Organization (CSO) registration | ⚠️ Possibly (some states) | $100-500 | 1-3 months |
| NMLS registration (if acting as MLO) | ⚠️ Possibly needed for founders | ~$100 | 1 week |
| Data privacy registration (if applicable) | ⚠️ CA, VT, others | Free-$100 | 1 day |

**Key legal strategy:** Engage a fintech regulatory attorney (budget $20k) to confirm state preemption analysis for YOUR partner bank's charter type. Different charter types (national bank, state bank, industrial loan company) have different preemption reach.

---

## 5.3 Consumer Compliance Inventory

### Federal Regulations

| Regulation | What It Requires | Implementation |
|------------|-----------------|----------------|
| **TILA / Reg Z** (12 CFR 1026) | Truth in Lending disclosures, APR calculation, right of rescission, periodic statements | Disclosures at application, closing, and monthly. Right of rescission for dwelling-secured (N/A). |
| **ECOA / Reg B** (12 CFR 1002) | Non-discriminatory underwriting, adverse action notices, appraisal notices | Automated adverse action with specific reasons. ECOA notice on all decisions. |
| **FCRA** (15 USC 1681) | Credit reporting accuracy, dispute resolution, risk-based pricing notices, adverse action credit score disclosure | Adverse action notice includes credit score and source. Furnisher agreement with bureaus. |
| **UDAAP** (Dodd-Frank) | No unfair, deceptive, or abusive acts | Plain language disclosures. No hidden fees. Transparent pricing. Marketing compliance review. |
| **GLBA** (15 USC 6801) | Privacy notices, opt-out rights, data security safeguards | Privacy notice at account opening + annually. Written information security program. |
| **EFTA / Reg E** (12 CFR 1005) | Electronic fund transfers, error resolution, unauthorized transfer liability | ACH authorization documentation. Error resolution procedures. 60-day dispute window. |
| **Truth in Savings / Reg DD** (12 CFR 1030) | (N/A — bank handles deposit accounts) | OrangeFi does not take deposits. |
| **SCRA / MLA** | Active duty rate cap (36% MAPR), protections | SCRA check at application. MLA check for military borrowers. |
| **BSA / AML** (via bank partner) | Anti-money laundering, CIP, OFAC sanctions screening | OFAC check at origination. Bank handles BSA/AML for loans on their books. |
| **Bank Secrecy Act** | SAR filing, currency transaction reporting | Bank handles. OrangeFi reports suspicious borrower activity to bank. |

---

## 5.4 Fair Lending Program

### Regulatory Standards
- **ECOA:** Disparate treatment (intentional) and disparate impact (unintentional) are both illegal
- **HUD / DOJ:** Can bring fair lending actions
- **CFPB:** Active in fair lending enforcement
- **State AGs:** Increasingly active

### OrangeFi Fair Lending Controls

| Control | Description | Frequency |
|---------|-------------|-----------|
| **BISG Analysis** | Bayesian Improved Surname Geocoding to estimate race/ethnicity for monitoring | Quarterly |
| **Disparate Impact Testing** | Regression analysis by protected class (where estimable) | Quarterly |
| **Adverse Action Review** | All adverse actions reviewed for consistency | Per decision |
| **Redlining Check** | Geographic distribution of originations vs. CRA assessment area | Annually |
| **Pricing Disparity Analysis** | APR distribution by protected class | Quarterly |
| **Model Fairness Testing** | ML model performance by demographic segment | Per model version |
| **UDAAP Review** | Marketing, disclosure, and servicing practices | Monthly |
| **Board Reporting** | Compliance dashboard for management reviews | Quarterly |

### Model Governance (Your Expertise Area)

Given your background in model risk governance, this is where OrangeFi can truly differentiate with bank partners.

| Model Governance Element | Implementation |
|-------------------------|---------------|
| **Model inventory** | Centralized registry of all models (AI risk score, pricing, fraud, cash flow) |
| **Model documentation** | Standardized template per SR 11-7 / OCC 2011-12 |
| **Validation** | Independent model validation (can be done by founder initially, third-party later) |
| **Performance monitoring** | Monthly AUC, KS, population stability, feature drift |
| **Version control** | All model versions tracked with git + DVC |
| **Champion/challenger** | New models run in shadow before deployment |
| **Bias testing** | Pre-deployment and quarterly fair lending analysis |

---

## 5.5 Privacy & Cybersecurity

### Required Controls

| Requirement | Implementation | Cost |
|-------------|---------------|------|
| Written Information Security Program (WISP) | Document per GLBA/state law | Free (template) |
| Data encryption at rest | AES-256 for PII | Free (SQLAlchemy + cryptography) |
| Data encryption in transit | TLS 1.2+ everywhere | Free (Let's Encrypt via Render) |
| Access controls | Role-based access (borrower, admin, underwriter) | Built into app |
| Multi-factor authentication | TOTP for admin accounts | Free (pyotp) |
| Incident response plan | Document + test annually | Free (template) |
| Third-party vendor risk assessment | Document for each integration | Free (template) |
| Penetration testing | Yearly (can self-do initially) | $0 (self) → $10k (external) |
| SOC 2 Type II | Year 2, for bank partners | $15-30k |
| Privacy policy | Posted on website | Free (AI-generated + legal review) |
| Cookie consent | Basic banner | Free |
| Data retention & disposal policy | Document + automated purging | Free |
| Employee training | Annual security awareness | Free (AI-generated) |

### Data Classification

| Level | Data Types | Controls |
|-------|------------|----------|
| **Critical** | SSN, bank account numbers, income, tax documents | Encrypted at rest, masked in UI, access logged |
| **Sensitive** | Name, address, phone, email, DOB | Encrypted at rest, access controlled |
| **Internal** | Application data, loan terms, payment history | Access controlled |
| **Public** | Marketing content, rate tables, blog | No controls needed |

---

## 5.6 Required Policies & Procedures

### Policies to Create

| Policy | Purpose | Priority |
|--------|---------|----------|
| Privacy Policy (GLBA) | How borrower data is collected, used, shared | P0 |
| Information Security Policy | Data protection standards and controls | P0 |
| Incident Response Plan | Steps for data breach or security event | P0 |
| Fair Lending Policy | Non-discrimination commitment and controls | P0 |
| Adverse Action Policy | FCRA/ECOA adverse action procedures | P0 |
| BSA/AML Policy | Suspicious activity reporting (bank-aligned) | P1 |
| Complaints Policy | Consumer complaint handling | P1 |
| Records Retention Policy | Data retention and destruction schedule | P1 |
| Third-Party Risk Management Policy | Vendor oversight | P1 |
| Model Risk Management Policy | Model governance, validation, monitoring | P1 |
| Code of Conduct | Employee ethics and confidentiality | P2 |
| Whistleblower Policy | Encourage reporting of misconduct | P2 |

---

## 5.7 Legal Budget

| Item | Q1 Cost | Q2 Cost | Q3 Cost | Q4 Cost |
|------|---------|---------|---------|---------|
| Corporate formation | $1,000 | $0 | $0 | $0 |
| Fintech regulatory counsel retainer | $5,000 | $5,000 | $5,000 | $5,000 |
| Bank partnership agreement drafting | $0 | $10,000 | $0 | $0 |
| Vendor agreement review | $0 | $2,000 | $2,000 | $2,000 |
| Disclosure compliance review | $2,000 | $0 | $2,000 | $2,000 |
| Privacy/cookie compliance | $1,000 | $0 | $0 | $1,000 |
| IP protection (trademark) | $1,000 | $0 | $0 | $0 |
| Employment/contractor agreements | $2,000 | $0 | $0 | $0 |
| **Total** | **$12,000** | **$17,000** | **$9,000** | **$10,000** |

**Annual legal budget:** ~$48,000

---

## 5.8 Recommended Compliance Counsel

| Firm | Specialty | Est. Rate | Best For |
|------|-----------|-----------|----------|
| **Hudson Cook** | Consumer financial services | $500-900/hr | Lending compliance, bank partnerships |
| **Ballard Spahr** | Fintech + consumer finance | $600-1,000/hr | Full-service fintech regulatory |
| **Troutman Pepper** | Consumer finance | $500-800/hr | State licensing, fair lending |
| **Alston & Bird** | Fintech, bank partnerships | $600-900/hr | Bank partnership structures |
| **Boutique fintech firms** | (various) | $300-600/hr | Good for early-stage, more affordable |

**Recommendation:** Start with a boutique fintech firm for formation + regulatory roadmap ($5-10k), then engage a firm like Ballard Spahr for bank partnership agreement ($15-25k).

---

## 5.9 Key Next Actions

| # | Action | Owner | Timeline | Cost |
|---|--------|-------|----------|------|
| 1 | Form Delaware C-Corp | Founder | Week 1 | ~$500 |
| 2 | Get EIN + open bank account | Founder | Week 1 | Free |
| 3 | Engage fintech regulatory counsel | Founder | Week 2 | $5k retainer |
| 4 | Draft privacy policy + WISP | AI → Founder review | Week 3 | Free |
| 5 | Validate bank partnership preemption strategy | Counsel | Month 2 | Included |
| 6 | Draft fair lending policy | AI → Founder review | Month 2 | Free |
| 7 | Begin model governance documentation | Founder | Month 3 | Free |
| 8 | SOC 2 readiness assessment | Founder + auditor | Month 6 | ~$5k |

---

## 5.10 Next Steps

1-5 ✅ — Phases 1-5 complete  
6 ▶ — Phase 6: Pilot Program Design  
