# Pipeline Math: Revenue Modeling from Goal Backward

Pipeline math is the engine of predictable revenue. By working backward from a revenue target, you can calculate exactly how many emails, prospects, opportunities, and deals you need, and how many SDRs and AEs are required to hit the number. This guide walks through the formula, benchmarks, capacity planning, scenario modeling, and common mistakes.

## The Pipeline Math Formula

Start with revenue. Work backward to activity.

```
Revenue Goal
  / Average Deal Size
  = Deals Needed
    / Win Rate
    = Opportunities Needed
      / Qualification Rate
      = Prospects (Meetings) Needed
        / Meeting Book Rate
        = Responses Needed
          / Response Rate
          = Emails Needed
            / Emails per SDR per Month
            = SDRs Needed
```

### Worked Example

**Goal:** $2M in new ARR this year from outbound.

| Step | Metric | Value | Calculation |
|------|--------|-------|-------------|
| Revenue goal | Target ARR | $2,000,000 | Given |
| Average deal size | ACV | $25,000 | Given |
| Deals needed | Closed-won | 80 | $2M / $25K |
| Win rate | Opportunity to close | 25% | Historical data |
| Opportunities needed | Qualified opps | 320 | 80 / 0.25 |
| Qualification rate | Meeting to qualified opp | 50% | Historical data |
| Meetings needed | Discovery calls | 640 | 320 / 0.50 |
| Meeting book rate | Response to meeting | 33% | Historical data |
| Responses needed | Email replies | 1,940 | 640 / 0.33 |
| Response rate | Email to response | 10% | Historical data |
| Emails needed | Total outbound | 19,400 | 1,940 / 0.10 |
| Emails per SDR per year | Capacity | 6,000 | ~500/month x 12 |
| SDRs needed | Headcount | 3.2 (round to 4) | 19,400 / 6,000 |

**Result:** You need approximately 4 SDRs to generate $2M in new outbound ARR.

## Capacity Planning

### SDR Capacity

| Variable | Conservative | Standard | Aggressive |
|----------|-------------|----------|------------|
| Emails per day | 40 | 75 | 100 |
| Working days per month | 20 | 21 | 22 |
| Emails per month | 800 | 1,575 | 2,200 |
| Ramp time (new SDR) | 4 months | 3 months | 2 months |
| Productive months per year | 9 | 10 | 11 |
| Effective annual email capacity | 7,200 | 15,750 | 24,200 |

### AE Capacity

| Variable | Conservative | Standard | Aggressive |
|----------|-------------|----------|------------|
| Active deals at once | 10 | 15 | 20 |
| Average sales cycle | 90 days | 60 days | 45 days |
| Deals per quarter | 10 | 15 | 20 |
| Win rate | 20% | 25% | 30% |
| Closed deals per quarter | 2 | 3.75 | 6 |
| Closed deals per year | 8 | 15 | 24 |

### SDR:AE Ratio Calculation

Match SDR output to AE capacity.

**Formula:**

```
Qualified Opps per SDR per month / Opps an AE can handle per month = SDR:AE ratio
```

**Example:**
- SDR generates 15 qualified opps/month
- AE can manage 8 new opps/month (given deal complexity)
- Ratio: 15/8 = roughly 2 SDRs per AE

## Benchmark Conversion Rates

### By Industry

| Industry | Response Rate | Meeting Rate | Opp Rate | Win Rate |
|----------|-------------|-------------|----------|----------|
| SaaS (SMB) | 10-15% | 30-40% | 40-50% | 20-30% |
| SaaS (Mid-market) | 8-12% | 25-35% | 40-55% | 20-25% |
| SaaS (Enterprise) | 5-10% | 20-30% | 45-60% | 15-25% |
| Professional Services | 8-12% | 30-40% | 35-45% | 25-35% |
| Financial Services | 5-8% | 20-30% | 40-50% | 20-30% |
| Healthcare / Life Sciences | 4-8% | 15-25% | 35-45% | 15-25% |

### By Deal Size

| Deal Size (ACV) | Response Rate | Meeting-to-Opp | Win Rate | Avg Cycle |
|-----------------|-------------|----------------|----------|-----------|
| < $5K | 10-15% | 40-50% | 25-35% | 15-30 days |
| $5K - $25K | 8-12% | 35-45% | 20-30% | 30-60 days |
| $25K - $100K | 6-10% | 30-40% | 15-25% | 60-120 days |
| $100K - $500K | 4-8% | 25-35% | 10-20% | 90-180 days |
| > $500K | 3-6% | 20-30% | 8-15% | 120-360 days |

## Pipeline Velocity

Pipeline velocity measures how fast revenue moves through your pipeline. It combines four key variables into a single number.

### Pipeline Velocity Formula

```
Pipeline Velocity = (Number of Opportunities x Average Deal Size x Win Rate) / Sales Cycle Length (days)
```

**Example:**
- 50 opportunities in pipeline
- $30K average deal size
- 25% win rate
- 60-day average sales cycle

```
Velocity = (50 x $30,000 x 0.25) / 60 = $6,250 per day
```

### How to Improve Pipeline Velocity

| Lever | Action | Impact |
|-------|--------|--------|
| **More opportunities** | Hire SDRs, improve response rate | Increases numerator |
| **Larger deals** | Move upmarket, improve packaging | Increases numerator |
| **Higher win rate** | Better qualification, stronger demos | Increases numerator |
| **Shorter cycle** | Faster follow-up, reduce friction, multi-thread | Decreases denominator |

Each lever is independently valuable. Improving all four compounds the effect dramatically.

### Velocity Benchmarks

| Segment | Typical Velocity ($/day) |
|---------|------------------------|
| SMB SaaS | $2,000 - $8,000 |
| Mid-market SaaS | $5,000 - $20,000 |
| Enterprise SaaS | $10,000 - $50,000 |

## Scenario Planning

Never rely on a single forecast. Build three scenarios to bracket your expectations.

### Three-Scenario Model

| Variable | Conservative | Realistic | Optimistic |
|----------|-------------|-----------|------------|
| Response rate | 7% | 10% | 14% |
| Meeting book rate | 25% | 33% | 40% |
| Qualification rate | 40% | 50% | 60% |
| Win rate | 18% | 25% | 32% |
| Average deal size | $20K | $25K | $30K |
| SDR ramp time | 4 months | 3 months | 2 months |

### Scenario Output (Goal: $2M ARR, 4 SDRs)

| Metric | Conservative | Realistic | Optimistic |
|--------|-------------|-----------|------------|
| Emails sent (annual) | 48,000 | 48,000 | 48,000 |
| Responses | 3,360 | 4,800 | 6,720 |
| Meetings booked | 840 | 1,584 | 2,688 |
| Qualified opportunities | 336 | 792 | 1,613 |
| Deals closed | 60 | 198 | 516 |
| Revenue generated | $1.2M | $4.95M | $15.5M |

This example shows how small improvements in each conversion rate compound into massive differences in outcome. Even the conservative scenario may over- or under-perform depending on ICP accuracy and email quality.

### How to Use Scenarios

1. **Plan headcount to the conservative scenario** so you do not over-hire.
2. **Set quotas to the realistic scenario** so targets feel achievable.
3. **Share the optimistic scenario to motivate** and show what excellent execution produces.
4. **Update scenarios monthly** as you gather actual conversion data.

## Pipeline Math Spreadsheet Template

Build this spreadsheet to model your pipeline math. Each column represents one variable.

### Column-by-Column Guide

| Column | Description | Source | Example |
|--------|-------------|--------|---------|
| A: Revenue Goal | Annual outbound revenue target | Leadership / board | $2,000,000 |
| B: Average Deal Size | Historical or target ACV | CRM data | $25,000 |
| C: Deals Needed | A / B | Calculated | 80 |
| D: Win Rate | Historical close rate | CRM data | 25% |
| E: Opportunities Needed | C / D | Calculated | 320 |
| F: Qualification Rate | % of meetings that become opps | CRM data | 50% |
| G: Meetings Needed | E / F | Calculated | 640 |
| H: Meeting Book Rate | % of responses that book meetings | Sequence data | 33% |
| I: Responses Needed | G / H | Calculated | 1,940 |
| J: Response Rate | % of emails that get a response | Sequence data | 10% |
| K: Emails Needed | I / J | Calculated | 19,400 |
| L: Emails per SDR/Year | Capacity per person | 500/mo x 12 | 6,000 |
| M: SDRs Needed | K / L | Calculated | 3.2 → 4 |
| N: Opps per AE/Year | Capacity per closer | 60/year | 60 |
| O: AEs Needed | E / N | Calculated | 5.3 → 6 |

### Monthly Tracking Sheet

Add a monthly tracking section to compare plan vs. actual:

| Month | Emails (Plan) | Emails (Actual) | Responses (Plan) | Responses (Actual) | Meetings (Plan) | Meetings (Actual) | Opps (Plan) | Opps (Actual) | Revenue (Plan) | Revenue (Actual) |
|-------|--------------|----------------|------------------|-------------------|----------------|-------------------|------------|--------------|----------------|-----------------|
| Jan | | | | | | | | | | |
| Feb | | | | | | | | | | |
| Mar | | | | | | | | | | |

Fill in planned numbers using the pipeline math formula. Update actual numbers weekly. Gaps between plan and actual tell you exactly where the funnel is breaking.

## Common Pipeline Math Mistakes

| Mistake | Why It Hurts | Fix |
|---------|-------------|-----|
| **Using aspirational conversion rates** | Over-estimates pipeline, under-hires SDRs | Use actual historical rates, or industry benchmarks for new teams |
| **Ignoring ramp time** | New SDRs at 0% productivity for months | Factor in 3-4 month ramp; hire ahead of need |
| **Not accounting for churn** | Net revenue is lower than gross | Include churn rate in annual revenue modeling |
| **Treating all deals equally** | A $5K deal is not a $100K deal | Segment pipeline math by deal size tier |
| **Static model** | Conversion rates change as you learn | Update pipeline math monthly with actual data |
| **Forgetting seasonality** | Q4 and summer slowdowns are real | Build monthly targets, not just annual averages |
| **Only counting outbound** | Seeds and nets also generate pipeline | Build separate pipeline math for each lead type, then combine |
| **No pipeline coverage buffer** | If pipeline = quota, you miss quota | Maintain 3-4x pipeline coverage at all times |

## Adjusting Pipeline Math Over Time

Your initial pipeline math model is an educated guess. It becomes accurate through iteration.

### Month 1-3: Baseline

- Use industry benchmarks for conversion rates
- Track actual numbers against predictions
- Do not panic if actuals diverge from plan (they will)
- Collect data; do not change the model yet

### Month 4-6: First Adjustment

- Replace benchmark conversion rates with your actual data
- Identify the weakest conversion step (biggest drop-off)
- Focus improvement efforts on that step
- Recalculate SDR and AE headcount needs

### Month 7-12: Refined Model

- Your conversion rates are now based on 6+ months of data
- Seasonal patterns begin to emerge
- Pipeline math becomes genuinely predictive
- You can forecast next quarter's revenue with 80-90% accuracy

### Ongoing

- Update conversion rates quarterly
- Re-run headcount models every 6 months
- Test new segments, personas, and messaging to improve rates
- Share pipeline math transparently with the team so everyone understands the system

The goal is a model where you can say: "If we send X emails, we will close Y deals worth Z revenue" with confidence. That is predictable revenue.
