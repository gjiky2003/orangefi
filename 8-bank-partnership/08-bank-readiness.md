# OrangeFi — Phase 8: Bank Partnership Readiness
**Date:** May 11, 2026
**Status:** Draft

---

## 8.1 Target Bank Partner Profile

### Ideal Bank Profile

| Attribute | Ideal | Acceptable | Avoid |
|-----------|-------|------------|-------|
| Asset size | $500M-$10B | $100M-$50B | >$100B (too bureaucratic) |
| Geography | Your state or adjacent | Regional (3-5 states) | National (too complex) |
| Current consumer lending | Yes, but limited | No, wants to enter | Full in-house already |
| Digital banking adoption | Moderate | Low (seeking innovation) | High (competing platform) |
| Regulatory rating | Satisfactory | Needs improvement | Below average |
| BSA/AML program | Strong | Adequate | Weak |
| Partnership experience | Some fintech partnerships | Open to new relationships | No prior partnerships |
| Decision timeline | 3-6 months | 6-12 months | 12+ months |

### Target List (Examples — research specific banks in your region)

| Bank | Size | Why OrangeFi Fits |
|------|------|-------------------|
| **Your local community bank** | $500M-2B | Relationship-based, faster decision, aligned community focus |
| **Regional super-community bank** | $2B-10B | Need digital lending, have balance sheet capacity |
| **Minority/community development bank** | $500M-5B | CRA credit, mission alignment, flexible partnership terms |
| **Industrial Bank** | Various | Known for fintech partnerships |
| **Cross River Bank** | $10B+ | Established fintech partner (but may be too large for you as a startup) |
| **Lead Bank** | $500M+ | Active in BaaS/fintech partnerships |
| **Blue Ridge Bank** | $1B+ | Known bank-partnership-friendly |
| **Piermont Bank** | $500M+ | Fintech-focused |

**Strategy:** Start with 3-5 community/regional banks in your home state. Approach through:
- Warm introduction (your banking contacts — leverage model risk governance background)
- Fintech conference (e.g., Fintech Nexus, Bank Director)
- Direct CEO/CIO outreach

---

## 8.2 Due Diligence Checklist (What the Bank Will Request)

### Corporate & Legal

| Item | Status | Notes |
|------|--------|-------|
| Certificate of Incorporation | ⬜ Prepare | Delaware C-Corp |
| EIN confirmation letter | ⬜ Prepare | From IRS |
| Business license/registration | ⬜ Prepare | Home state |
| BOI filing confirmation | ⬜ Prepare | FinCEN beneficial ownership |
| Board resolutions | ⬜ Prepare | Authorizing partnership |
| D&O insurance certificate | ⬜ Obtain | $1M+ coverage |
| E&O/cyber insurance certificate | ⬜ Obtain | $2M+ coverage |

### Financial

| Item | Status | Notes |
|------|--------|-------|
| Audited financials (if any) | ⬜ N/A | Not applicable for startup |
| Bank statements | ⬜ Prepare | Business account |
| Tax returns (entity) | ⬜ N/A | Not yet filed |
| Financial projections (3 years) | ✅ Complete | See Phase 7 |
| Pricing model / fee schedule | ✅ Complete | See Phase 2 |
| Proof of funding / capitalization | ⬜ Prepare | Founder funds letter |

### Technology & Security

| Item | Status | Notes |
|------|--------|-------|
| Information security policy | ⬜ Draft | Use template |
| SOC 2 Type II report | ⬜ Year 2 | Not needed for initial discussion |
| Penetration test report | ⬜ Year 1 | Can self-do initially |
| Data flow diagram | ⬜ Create | Show PII flow |
| Vendor management program | ⬜ Draft | List of all third-party vendors |
| Business continuity plan | ⬜ Draft | |
| Incident response plan | ⬜ Draft | |
| Encryption standards | ✅ Built-in | AES-256 + TLS 1.2+ |
| Access control policy | ✅ Built-in | Role-based in app |

### Compliance

| Item | Status | Notes |
|------|--------|-------|
| Fair lending policy | ⬜ Draft | |
| Adverse action procedures | ⬜ Draft | |
| Privacy policy (GLBA) | ⬜ Draft | |
| Complaint management procedures | ⬜ Draft | |
| Model risk management policy | ⬜ Draft | YOUR EXPERTISE AREA |
| BSA/AML procedures | ⬜ Draft | Bank-aligned |
| OFAC screening procedures | ✅ Built-in | In underwriting flow |
| SCRA/MLA compliance procedures | ✅ Built-in | In underwriting flow |
| State licensing analysis | ⬜ Engage counsel | |

### Operational

| Item | Status | Notes |
|------|--------|-------|
| Loan origination procedures | ✅ Complete | See Phase 3 |
| Underwriting guidelines | ✅ Complete | See Phase 3 |
| Servicing procedures | ✅ Complete | See Phase 3 |
| Collections procedures | ✅ Complete | See Phase 6 |
| Quality control plan | ⬜ Draft | |
| Training materials | ⬜ Draft | |
| Monthly/quarterly reporting templates | ⬜ Draft | |

---

## 8.3 Bank Pitch Deck Outline

### Slide Deck Structure (12-15 slides)

**Slide 1: Title**
- OrangeFi: AI-Powered Debt Consolidation
- "Lower rates. Simplify payments. Powered by AI."

**Slide 2: The Problem**
- 46% of Americans carry credit card debt month-to-month
- Average APR: 22.8%
- $650B in revolving consumer debt
- Borrowers are trapped in high-interest cycles

**Slide 3: The Solution**
- OrangeFi provides debt consolidation loans at lower rates (7.99%-24.99%)
- AI underwriting enables better risk selection and pricing
- Bank partnership model: bank originates, OrangeFi provides technology and borrowers

**Slide 4: Market Opportunity**
- $120B/year debt consolidation market
- 8.2% CAGR
- 40M+ target borrowers (credit score 580-740)
- Growing demand (post-COVID credit card balances at all-time highs)

**Slide 5: How It Works**
- Borrower applies online (2-minute pre-qual)
- AI underwrites in seconds (credit + cash flow + fraud)
- Bank originates and funds the loan
- OrangeFi services and supports
- Both share in the revenue

**Slide 6: Technology Platform**
- AI underwriting engine (XGBoost, 30+ features)
- Real-time cash flow analysis (Plaid)
- Automated fraud detection (multi-layer)
- Fully digital borrower journey
- Admin dashboard for portfolio management

**Slide 7: AI Advantage — Details**
- Two-stage underwriting (gating rules + risk score)
- Cash flow analysis (90 days transaction data)
- 0.75+ AUC target
- SHAP explainability for regulatory compliance
- Founder's model risk governance background

**Slide 8: Target Borrower**
- Credit score: 640-740
- Income: $50k-$120k
- Debt: $5k-$25k revolving
- 2+ years employment
- W-2 income

**Slide 9: Risk Management**
- Multi-layer fraud detection
- AI model monitoring (monthly)
- Fair lending analysis (quarterly BISG)
- Manual review for gray-zone applications
- Compliance-first design

**Slide 10: Partnership Model**
| Partner Bank | OrangeFi |
|-------------|----------|
| Originates loans on balance sheet | Origination fee (3-5%) |
| Sets interest rate floors/floors | Servicing fee (30-50 bps) |
| Holds credit risk | Tech license fee ($15k-$25k/mo) |
| Regulatory compliance umbrella | Performance fee (excess spread share) |

**Slide 11: Financial Projections**
| Metric | Year 1 | Year 3 |
|--------|--------|--------|
| Loans funded | 500 | 5,000 |
| Funded volume | $7.5M | $75M |
| Portfolio (average) | $2M | $50M |
| Bank's portfolio yield | 8-10% net | 8-10% net |

**Slide 12: Management Team**
- Founder: [Your Name]
- Background: Model risk governance, banking, [X] years experience
- Deep understanding of underwriting, regulatory expectations, and third-party risk
- Growing company with AI-first approach

**Slide 13: Timeline**
| Month | Milestone |
|-------|-----------|
| 1-2 | MVP build complete |
| 3-4 | Regulatory counsel engaged |
| 5-6 | Pilot launch (20-30 loans) |
| 7-8 | Pilot results + bank partner discussions |
| 9-12 | Partner bank integration + scale |

**Slide 14: Why Partner with OrangeFi?**
- Revenue share with minimal upfront investment
- Diversify consumer lending portfolio
- CRA credit (if applicable)
- Modern technology without building in-house
- Experienced regulatory-compliant management
- Low-risk pilot before full commitment

**Slide 15: Contact**
- [Your Name], Founder & CEO
- [Email]
- [Phone]
- [Website]

---

## 8.4 Executive Summary (One-Pager for Bank)

```
─────────────────────────────────────────────────────
ORANGEFI — Executive Summary
Bank Partnership Opportunity
─────────────────────────────────────────────────────

THE COMPANY
OrangeFi is a technology-driven debt consolidation lending 
platform. We partner with banks to originate and service 
consumer loans. Our AI underwriting engine enables better 
risk selection, fairer pricing, and lower operating costs.

THE OPPORTUNITY
• $120B/year U.S. debt consolidation market growing at 8% CAGR
• 40M+ borrowers paying 22.8% average APR on credit cards
• Banks seeking consumer loan origination channels with 
  proven technology and regulatory compliance

THE SOLUTION
• AI underwriting: XGBoost model with cash flow analysis — 
  0.75+ AUC target
• Fully digital borrower journey (pre-qual to funding in <24h)
• Automated compliance (ECOA, FCRA, TILA, UDAAP controls)
• Real-time portfolio monitoring and reporting

THE PARTNERSHIP
Bank Role:                    OrangeFi Role:
• Originate on balance sheet  • Technology platform
• Hold credit risk            • Borrower acquisition
• Regulatory umbrella         • AI underwriting
                              • Loan servicing
                              • Compliance management

PROJECTED VOLUME
           Year 1    Year 2    Year 3
Loans      500       2,000     5,000
Volume     $7.5M     $30M      $75M

THE FOUNDER
[Name] — [X] years in banking, model risk governance, 
and consumer lending compliance. Deep regulatory expertise 
and technology background.

─────────────────────────────────────────────────────
```

---

## 8.5 Sample Commercial Terms

### Term Sheet Outline

```
ORANGEFI — PARTNER BANK TERM SHEET (DRAFT)
────────────────────────────────────────

1. PARTIES
   Bank:     [Partner Bank Name]
   Partner:  OrangeFi Technologies, Inc.

2. TERM
   Initial term: 3 years
   Automatic renewal: 1-year terms (unless 90-day notice)

3. LOAN PROGRAM
   Product: Unsecured debt consolidation installment loans
   Amounts: $5,000 - $35,000
   Terms: 24, 36, 48 months
   APR range: 7.99% - 24.99%
   Target credit: 580 - 740

4. LOAN OWNERSHIP
   Bank originates and holds loans on balance sheet
   OrangeFi has no balance sheet exposure

5. UNDERWRITING
   OrangeFi provides AI risk score and recommendation
   Bank retains final approval authority
   Bank defines minimum underwriting standards

6. FEES TO ORANGEFI
   Origination fee: 3-5% of loan amount (paid at funding)
   Servicing fee: 30-50 bps on outstanding balance
   Technology license: $15,000-$25,000/month
   Performance fee: 15% of net interest margin above 
     bank's target yield (paid quarterly)

7. BANK'S ECONOMICS
   Interest income (net of OrangeFi fees)
   No origination fee (OrangeFi keeps it)
   Target net yield: [Bank to define]

8. CREDIT RISK
   Bank bears 100% credit risk
   OrangeFi provides ongoing portfolio monitoring
   Early warning triggers at: 5% 30-day delinquency

9. COMPLIANCE
   OrangeFi maintains compliance program
   Bank retains regulatory oversight
   Quarterly compliance reviews
   Annual fair lending analysis

10. DATA & REPORTING
    Real-time API for loan/portfolio data
    Monthly portfolio performance report
    Quarterly compliance report
    Annual SOC 2 Type II report (from Year 2)

11. REPRESENTATIONS
    Standard representations and warranties for 
    fintech/bank service agreements

12. TERMINATION
    For cause: 30 days
    Without cause: 90 days
    Regulatory: Immediate
```

---

## 8.6 Information Security Questionnaire (Pre-Filled)

### Sample Responses

**Q1: How is customer data encrypted?**
All PII is encrypted at rest using AES-256 via the cryptography Python library. Data in transit uses TLS 1.2+ (minimum) with automatic certificate management via Let's Encrypt. SSNs and bank account numbers are encrypted with a dedicated encryption key, separate from application data.

**Q2: What is your access control policy?**
Role-based access control (RBAC) with three tiers: Borrower (own data only), Admin (all data with audit log), System (API-level, no human access). All admin actions require authenticated login with 30-minute session timeout. Multi-factor authentication (TOTP) is available for admin accounts.

**Q3: Do you perform background checks on employees?**
Yes. As a solo founder, I have completed [background check]. Future hires will undergo criminal background check, credit check (for roles handling funds), and employment verification.

**Q4: What third-party vendors do you use?**
Plaid (bank account linking), Stripe (payment processing), Equifax/TransUnion (credit data), Socure/Alloy (identity verification), Twilio (communications), OpenAI (AI services), DocuSign (e-signature), AWS/Render (hosting). Each vendor is vetted for SOC 2 compliance.

**Q5: What is your incident response plan?**
Four-tier incident classification (L1-L4). Immediate containment for data breaches. Regulatory notification within 72 hours for material breaches (state law dependent). Full incident documentation and post-mortem.

**Q6: How often do you perform security testing?**
Quarterly vulnerability scanning using [tool], annual penetration testing (externally facilitated Year 2+), and continuous SAST scanning via GitHub Actions.

**Q7: Do you have cyber insurance?**
[$2M] cyber liability and errors & omissions insurance. [Policy details to be provided upon obtaining].

---

## 8.7 Bank Partner Engagement Timeline

| Week | Activity | Owner |
|------|----------|-------|
| 1-2 | Identify 10 target banks (research + warm intros) | Founder |
| 3-4 | Prepare pitch deck and due diligence package | Founder |
| 5-6 | Initial outreach (email + LinkedIn + introductions) | Founder |
| 7-8 | First meetings (pitch + relationship building) | Founder |
| 9-12 | Follow-up meetings, due diligence responses | Founder + Counsel |
| 13-16 | Commercial term negotiation | Founder + Counsel |
| 17-20 | Legal agreement drafting + review | Counsel |
| 21-24 | Integration planning + compliance alignment | Founder + Bank |
| 25+ | Pilot launch | Founder + Bank |

---

## 8.8 Next Steps

1-8 ✅ — All 8 phases complete  
10 ▶ — Executive Summary & Blueprint  
