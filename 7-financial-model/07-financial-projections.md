# OrangeFi — Phase 7: Financial Model
**Date:** May 11, 2026
**Status:** Draft

---

## 7.1 Key Assumptions

### Revenue Assumptions

| Assumption | Year 1 | Year 2 | Year 3 | Rationale |
|------------|--------|--------|--------|-----------|
| Loans funded (monthly avg) | 42 | 167 | 417 | Conservative growth, 10x in 3 years |
| Total loans funded (annual) | 500 | 2,000 | 5,000 | |
| Total funded volume | $7.5M | $30M | $75M | Avg loan $15k |
| Avg loan size | $15,000 | $15,000 | $15,000 | Steady state |
| Avg APR | 14.99% | 13.99% | 12.99% | Improving with data |
| Avg origination fee | 4.0% | 3.5% | 3.0% | Competitive pressure |
| Avg term | 36 months | 36 months | 36 months | |
| Net charge-off rate | 4.0% | 4.5% | 5.0% | Increases as you expand to lower credit tiers |
| Monthly tech license (bank partner) | $15,000 | $20,000 | $25,000 | Increases with volume |
| Servicing fee (bps) | 50 bps | 40 bps | 35 bps | Economies of scale |

### Expense Assumptions

| Expense | Year 1 | Year 2 | Year 3 | Notes |
|---------|--------|--------|--------|-------|
| Hosting & infrastructure | $1,200 | $3,600 | $12,000 | Render → AWS |
| Third-party integrations | $3,600 | $9,600 | $24,000 | Plaid, Stripe, Bureau, etc. |
| Marketing (paid acquisition) | $60,000 | $180,000 | $360,000 | $150 CPA target |
| Legal & compliance | $48,000 | $36,000 | $36,000 | Front-loaded for formation |
| Founder salary | $60,000 | $80,000 | $120,000 | Self-funded, modest |
| Contractors (fractional) | $24,000 | $48,000 | $72,000 | Part-time help |
| AI/API costs | $3,600 | $12,000 | $36,000 | OpenAI, AI services |
| Insurance (cyber, D&O) | $5,000 | $8,000 | $12,000 | |
| Misc/office/software | $6,000 | $12,000 | $18,000 | |
| **Total OpEx** | **$211,400** | **$389,200** | **$690,000** | |

---

## 7.2 Three-Year Financial Projections

### Year 1 (Startup + Pilot)

| Month | Loans Funded | Volume | Revenue | OpEx | Net |
|-------|-------------|--------|---------|------|-----|
| 1 | 0 | $0 | $0 | $10,000 | -$10,000 |
| 2 | 0 | $0 | $0 | $15,000 | -$15,000 |
| 3 | 0 | $0 | $0 | $18,000 | -$18,000 |
| 4 | 0 | $0 | $3,000 | $18,000 | -$15,000 |
| 5 | 0 | $0 | $3,000 | $18,000 | -$15,000 |
| 6 | 5 | $75,000 | $5,000 | $20,000 | -$15,000 |
| 7 | 15 | $225,000 | $12,000 | $20,000 | -$8,000 |
| 8 | 25 | $375,000 | $20,000 | $20,000 | $0 |
| 9 | 40 | $600,000 | $32,000 | $20,000 | $12,000 |
| 10 | 60 | $900,000 | $47,000 | $20,000 | $27,000 |
| 11 | 80 | $1,200,000 | $62,000 | $20,000 | $42,000 |
| 12 | 100 | $1,500,000 | $77,000 | $22,400 | $54,600 |
| **Total** | **325** | **$4.875M** | **$261,000** | **$221,400** | **$39,600** |

*Note: Pilot begins Month 6-7, full operations Month 8+. Year 1 is not a full year of operations.*

### Year 2 (Growth)

| Quarter | Loans Funded | Volume | Revenue | OpEx | Net |
|---------|-------------|--------|---------|------|-----|
| Q1 | 300 | $4.5M | $226,000 | $90,000 | $136,000 |
| Q2 | 400 | $6.0M | $297,000 | $95,000 | $202,000 |
| Q3 | 500 | $7.5M | $367,000 | $100,000 | $267,000 |
| Q4 | 800 | $12.0M | $575,000 | $104,200 | $470,800 |
| **Total** | **2,000** | **$30M** | **$1,465,000** | **$389,200** | **$1,075,800** |

### Year 3 (Scale)

| Quarter | Loans Funded | Volume | Revenue | OpEx | Net |
|---------|-------------|--------|---------|------|-----|
| Q1 | 800 | $12M | $540,000 | $155,000 | $385,000 |
| Q2 | 1,000 | $15M | $665,000 | $165,000 | $500,000 |
| Q3 | 1,200 | $18M | $785,000 | $180,000 | $605,000 |
| Q4 | 2,000 | $30M | $1,275,000 | $190,000 | $1,085,000 |
| **Total** | **5,000** | **$75M** | **$3,265,000** | **$690,000** | **$2,575,000** |

---

## 7.3 Revenue Breakdown

### Year 1 Revenue Detail

| Source | Calculation | Amount |
|--------|-------------|--------|
| Origination fees | $4.875M × 4.0% | $195,000 |
| Servicing fees | Avg portfolio $2M × 0.5% | $10,000 |
| Tech license fee | $15k × 4 months (post-pilot) | $60,000 |
| Performance fee | None in Year 1 | $0 |
| **Total** | | **$265,000** |

### Year 3 Revenue Detail

| Source | Calculation | Amount |
|--------|-------------|--------|
| Origination fees | $75M × 3.0% | $2,250,000 |
| Servicing fees | Avg portfolio $50M × 0.35% | $175,000 |
| Tech license fee | $25k × 12 | $300,000 |
| Performance fee | 15% of excess spread | $500,000 |
| **Total** | | **$3,225,000** |

---

## 7.4 Break-Even Analysis

### Break-Even Point

**Break-even occurs at:** ~200 loans/month or ~$3M/month funded volume

### Break-Even Calculation

| Component | Monthly Cost | Break-Even Volume |
|-----------|-------------|-------------------|
| Fixed costs (hosting, legal, insurance, salary) | $18,000/mo | |
| Variable costs (marketing, integrations, AI) | $150/loan | |
| Total cost per month | $18,000 + $150 × loans | |
| Revenue per loan (avg) | $600 (origination + pro-rata servicing + tech license share) | |
| **Break-even loans/month** | **$18,000 / ($600 - $150) = 40 loans/month** | |

### Time to Break-Even

| Scenario | Loans/Month | Time to Break-Even | Cumulative Investment |
|----------|-------------|-------------------|----------------------|
| Conservative | 30 | Month 10 | $140,000 |
| Base Case | 40 | Month 8 | $100,000 |
| Optimistic | 60 | Month 6 | $70,000 |

---

## 7.5 Sensitivity Analysis

### Scenario Analysis

| Scenario | Loans/Mo (Y1) | CPA | Charge-off | Y1 Revenue | Y1 Net | Y3 Net |
|----------|--------------|-----|------------|------------|--------|--------|
| **Base Case** | 42 | $150 | 4% | $261k | $40k | $2.6M |
| **Conservative** | 25 | $200 | 5% | $165k | -$70k | $1.1M |
| **Optimistic** | 60 | $100 | 3% | $390k | $120k | $4.2M |
| **Worst Case** | 15 | $250 | 7% | $100k | -$130k | $0.3M |

### Key Sensitivities

| Variable | Change | Impact on Y3 Net Income |
|----------|--------|------------------------|
| CPA +$50 | 33% increase | -$500k |
| Charge-off +1% | 25% increase | -$200k (indirect — bank absorbs credit risk) |
| Loan volume +20% | 20% increase | +$600k |
| Origination fee -1% | 25% decrease | -$750k |
| Avg loan size +$3k | 20% increase | +$450k |

### Breakeven Volume Sensitivity

| Scenario | Variable | Breakeven Loans/Month |
|----------|----------|----------------------|
| Base | Standard assumptions | 40 |
| Higher fees | 5% instead of 4% | 28 |
| Lower acquisition cost | $100 CPA | 30 |
| Higher fixed costs | $25k/mo (hiring) | 55 |
| Lower revenue per loan | $500 instead of $600 | 55 |

---

## 7.6 Cash Flow Statement

### Year 1 Monthly Cash Flow

| Month | Cash In | Cash Out | Net | Cumulative |
|-------|---------|----------|-----|------------|
| 1 | $0 | $10,000 | -$10,000 | -$10,000 |
| 2 | $0 | $15,000 | -$15,000 | -$25,000 |
| 3 | $0 | $18,000 | -$18,000 | -$43,000 |
| 4 | $3,000 | $18,000 | -$15,000 | -$58,000 |
| 5 | $3,000 | $18,000 | -$15,000 | -$73,000 |
| 6 | $5,000 | $20,000 | -$15,000 | -$88,000 |
| 7 | $12,000 | $20,000 | -$8,000 | -$96,000 |
| 8 | $20,000 | $20,000 | $0 | -$96,000 |
| 9 | $32,000 | $20,000 | $12,000 | -$84,000 |
| 10 | $47,000 | $20,000 | $27,000 | -$57,000 |
| 11 | $62,000 | $20,000 | $42,000 | -$15,000 |
| 12 | $77,000 | $22,400 | $54,600 | **$39,600** |

**Total cash needed:** ~$96,000 (peak negative cash flow Month 8)

**Self-funded:** $100,000 initial capital is sufficient to reach breakeven.

---

## 7.7 Capital Requirements

| Phase | Duration | Capital Needed | Source |
|-------|----------|---------------|--------|
| Company formation | Month 1 | $5,000 | Self |
| MVP development | Months 2-5 | $40,000 | Self |
| Pilot launch | Months 6-8 | $50,000 | Self |
| **Total to breakeven** | **8 months** | **$95,000-$100,000** | **Self** |
| Growth (Year 2) | 12 months | $200,000 | Revenue + bank partner advance |
| Scale (Year 3) | 12 months | Self-funding from operations | — |

**Key insight:** This business can be self-funded to breakeven for ~$100k. No external funding needed for the MVP and pilot.

---

## 7.8 Key Financial Metrics

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| Revenue | $265k | $1.47M | $3.27M |
| Net Income | $40k | $1.08M | $2.58M |
| Gross Margin | 72% | 78% | 82% |
| Operating Margin | 15% | 73% | 79% |
| Revenue per Loan | $530 | $733 | $653 |
| Cost per Loan | $442 | $195 | $138 |
| Loans per Employee | 325 (1 FTE) | 1,000 (2 FTE) | 2,500 (2 FTE) |
| Cumulative Cash Flow | $40k | $1.12M | $3.70M |

---

## 7.9 Next Steps

1-7 ✅ — Phases 1-7 complete  
8 ▶ — Phase 8: Bank Partnership Readiness  
