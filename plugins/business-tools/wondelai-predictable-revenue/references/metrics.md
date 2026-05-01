# Sales Development Metrics and Dashboard Design

What gets measured gets managed. A well-designed metrics dashboard turns sales development from guesswork into a data-driven machine. This guide covers every metric you need to track, how to organize them into a dashboard, benchmark targets by company stage, and the most common measurement mistakes.

## Metric Categories

Sales development metrics fall into four categories. Each tells a different story, and you need all four for a complete picture.

| Category | What It Measures | Time Horizon | Purpose |
|----------|-----------------|--------------|---------|
| **Leading indicators** | Activity and effort | Daily/Weekly | Predict future pipeline |
| **Pipeline indicators** | Funnel progression | Weekly/Monthly | Track pipeline health |
| **Lagging indicators** | Revenue results | Monthly/Quarterly | Measure business outcomes |
| **Efficiency indicators** | Return on investment | Quarterly/Annual | Optimize resource allocation |

## Leading Indicators: Activity Metrics

Leading indicators tell you whether the team is doing enough of the right activities. They predict pipeline 30-90 days out.

### Activity Metrics Dashboard

| Metric | Definition | How to Calculate | Cadence |
|--------|-----------|-----------------|---------|
| **Emails sent** | Total outbound emails (new + follow-up) | Count from sequencing tool | Daily |
| **New sequences started** | New prospects entered into a sequence | Count from sequencing tool | Daily |
| **Calls made** | Outbound call attempts | Count from dialer or CRM | Daily |
| **Conversations** | Calls that connected with a live person | Count from dialer logs | Daily |
| **Responses received** | Email replies (positive, negative, referral) | Count from sequencing tool | Daily |
| **Response rate** | Responses / Emails sent | Percentage | Weekly |
| **Positive response rate** | Positive responses / Total responses | Percentage | Weekly |
| **LinkedIn touches** | Connection requests, InMails, profile views | Count from Sales Navigator | Weekly |

### Activity Benchmarks

| Metric | Per SDR Per Day | Per SDR Per Week | Per SDR Per Month |
|--------|----------------|-----------------|-------------------|
| Emails sent (new + follow-up) | 50-100 | 250-500 | 1,000-2,000 |
| New sequences started | 10-25 | 50-125 | 200-500 |
| Calls made | 15-30 | 75-150 | 300-600 |
| Conversations | 3-8 | 15-40 | 60-160 |
| Responses received | 5-15 | 25-75 | 100-300 |

### When Activity Metrics Are Misleading

Activity metrics are necessary but not sufficient. High activity with poor results means:

- Targeting the wrong ICP (lots of emails, few responses)
- Poor email quality (high send volume, low response rate)
- Weak qualification (many meetings, few qualified opps)
- Bad data (high bounce rates eating into effective volume)

Always pair activity metrics with conversion metrics to understand quality.

## Pipeline Indicators: Funnel Progression

Pipeline indicators track how prospects move through the funnel. They tell you whether activity is translating into business.

### Pipeline Metrics Dashboard

| Metric | Definition | How to Calculate | Cadence |
|--------|-----------|-----------------|---------|
| **Meetings booked** | Discovery or qualification calls scheduled | Count from CRM/calendar | Weekly |
| **Meetings held** | Meetings that actually happened (not no-shows) | Count from CRM | Weekly |
| **No-show rate** | Booked meetings where prospect did not attend | No-shows / Booked meetings | Weekly |
| **Qualified opportunities** | Meetings that passed ANUM criteria | Count from CRM (stage change) | Weekly |
| **Qualification rate** | Meetings that became qualified opps | Qualified opps / Meetings held | Monthly |
| **Pipeline value created** | Dollar value of new qualified opportunities | Sum of opp amounts | Monthly |
| **Pipeline coverage** | Pipeline / Quota | Ratio | Weekly |
| **Handoff acceptance rate** | % of SDR-qualified opps accepted by AEs | Accepted / Passed | Monthly |

### Pipeline Benchmarks

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| Meetings booked per SDR/month | < 8 | 8-12 | 12-18 | > 18 |
| No-show rate | > 30% | 20-30% | 10-20% | < 10% |
| Qualification rate | < 30% | 30-45% | 45-60% | > 60% |
| Pipeline coverage (AE) | < 2x | 2-3x | 3-4x | > 4x |
| Handoff acceptance rate | < 70% | 70-80% | 80-90% | > 90% |

### Reducing No-Shows

No-shows waste SDR and AE time. Typical fixes:

| Tactic | Expected Impact |
|--------|----------------|
| Send calendar invite with clear agenda immediately | -10-15% no-shows |
| Confirmation email 24 hours before | -5-10% no-shows |
| SMS or chat reminder 1 hour before | -5-10% no-shows |
| Allow easy rescheduling (not just cancel) | -5% no-shows |
| Qualify interest level before booking | -10% no-shows |

## Lagging Indicators: Revenue Results

Lagging indicators measure actual business outcomes. They are the ultimate scorecard but arrive too late to change course in real time.

### Revenue Metrics Dashboard

| Metric | Definition | How to Calculate | Cadence |
|--------|-----------|-----------------|---------|
| **Revenue closed (from outbound)** | Closed-won ARR from SDR-sourced pipeline | Sum of closed-won opp amounts | Monthly |
| **Win rate** | % of qualified opps that close | Closed-won / Total qualified opps | Monthly |
| **Average deal size** | Mean revenue per closed deal | Total revenue / Number of deals | Monthly |
| **Sales cycle length** | Days from opp creation to close | Average days for closed deals | Monthly |
| **Revenue per SDR** | Revenue attributable to each SDR | Closed revenue / SDR headcount | Quarterly |
| **Quota attainment** | Actual vs. target performance | Actual / Quota | Monthly |

### Revenue Benchmarks

| Metric | Early Stage | Growth Stage | Scale Stage |
|--------|------------|-------------|-------------|
| Win rate | 15-20% | 20-30% | 25-35% |
| Average sales cycle | 45-90 days | 30-60 days | 30-75 days |
| Revenue per SDR per year | $200K-$500K | $500K-$1M | $800K-$2M |
| SDR quota attainment (team avg) | 60-75% | 70-85% | 75-90% |

## Efficiency Metrics: Return on Investment

Efficiency metrics tell you whether your sales development investment is generating healthy returns.

### Efficiency Metrics Dashboard

| Metric | Definition | How to Calculate | Target |
|--------|-----------|-----------------|--------|
| **Cost per opportunity** | Fully loaded cost to generate one qualified opp | Total SDR cost / Qualified opps | Varies by ACV |
| **Cost per closed deal** | Fully loaded cost to generate one closed deal | Total SDR cost / Closed deals | < 20% of ACV |
| **Customer Acquisition Cost (CAC)** | Full cost to acquire a customer | (Sales + Marketing cost) / New customers | Depends on LTV |
| **LTV:CAC ratio** | Lifetime value vs. acquisition cost | Customer LTV / CAC | > 3:1 |
| **CAC payback period** | Months to recoup acquisition cost | CAC / Monthly gross margin per customer | < 18 months |
| **Magic number** | Revenue efficiency of sales spend | Net new ARR / Sales & Marketing spend (prior quarter) | > 0.75 |

### Efficiency Benchmarks by Deal Size

| Deal Size (ACV) | Target Cost per Opp | Target LTV:CAC | Target Payback |
|-----------------|--------------------|---------|----|
| < $5K | $50-$200 | 3-5:1 | 6-12 months |
| $5K - $25K | $200-$800 | 3-5:1 | 12-18 months |
| $25K - $100K | $500-$2,000 | 4-6:1 | 12-24 months |
| > $100K | $1,000-$5,000 | 5-8:1 | 18-30 months |

## Dashboard Cadence

Different metrics require different review rhythms. Over-reviewing lagging indicators is pointless; under-reviewing leading indicators means you miss problems until it is too late.

### Daily Dashboard (SDR Manager + SDRs)

| Metric | Purpose |
|--------|---------|
| Emails sent today | Is the team active? |
| Responses received today | Are emails generating interest? |
| Meetings booked today | Is the pipeline growing? |
| Calls made today | Are follow-ups happening? |

**Format:** Simple leaderboard visible to the team. Quick stand-up at start or end of day.

### Weekly Dashboard (SDR Manager + VP Sales)

| Metric | Purpose |
|--------|---------|
| Emails sent this week (per SDR) | Volume tracking by individual |
| Response rate this week | Email quality indicator |
| Meetings booked this week | Pipeline generation |
| Meetings held / no-show rate | Meeting quality |
| Qualified opportunities this week | Funnel conversion |
| Pipeline coverage for AEs | Enough pipeline to hit quota? |

**Format:** Dashboard in CRM or BI tool. Reviewed in weekly team meeting.

### Monthly Dashboard (VP Sales + Leadership)

| Metric | Purpose |
|--------|---------|
| Qualified opportunities (month) | Pipeline created |
| Pipeline value created | Dollar value of new pipeline |
| Revenue closed from outbound | Business results |
| Win rate | Closing efficiency |
| Average deal size | Deal quality |
| SDR quota attainment | Team performance |
| Cost per opportunity | Efficiency |

**Format:** Slide or report shared with leadership. Deep dive on trends and actions.

### Quarterly Dashboard (Executive / Board)

| Metric | Purpose |
|--------|---------|
| Total outbound revenue | Business impact |
| LTV:CAC ratio | Investment efficiency |
| CAC payback period | Cash flow impact |
| Magic number | Sales efficiency |
| Pipeline math accuracy | Forecasting reliability |
| SDR headcount and ramp | Team scaling |

**Format:** Board-level summary with trends over multiple quarters.

## Setting Targets and Quotas

### Quota-Setting Process

1. **Start with the revenue goal** (top-down from leadership)
2. **Run pipeline math** to determine opportunities needed
3. **Divide by SDR headcount** (accounting for ramp)
4. **Sanity-check against benchmarks** (is the per-SDR number achievable?)
5. **Build in a buffer** (set team targets 10-15% above company need)

### Quota Guidelines

| Principle | Explanation |
|-----------|-------------|
| **50-70% of SDRs should hit quota** | If everyone hits, quota is too low. If nobody hits, quota is too high. |
| **Quota should feel achievable but stretching** | Top performers should be at 120-150%. |
| **Quotas should be outcome-based** | Qualified opportunities, not emails sent. |
| **New hires get ramped quotas** | Month 1: 0%, Month 2: 25-40%, Month 3: 50-75%, Month 4: 100%. |
| **Review and adjust quarterly** | As conversion rates change, quotas should change. |

## Dashboard Template Layout

### Recommended Layout for a Sales Development Dashboard

```
+-------------------------------------------------------+
|  SALES DEVELOPMENT DASHBOARD — [Month, Year]           |
+-------------------------------------------------------+
|                                                         |
|  TEAM SUMMARY                                           |
|  +----------+-----------+--------+--------+---------+   |
|  | SDR Name | Emails    | Resp.  | Mtgs   | Qual.   |   |
|  |          | Sent      | Rate   | Booked | Opps    |   |
|  +----------+-----------+--------+--------+---------+   |
|  | SDR 1    |           |        |        |         |   |
|  | SDR 2    |           |        |        |         |   |
|  | SDR 3    |           |        |        |         |   |
|  | TOTAL    |           |        |        |         |   |
|  +----------+-----------+--------+--------+---------+   |
|                                                         |
|  FUNNEL CONVERSION                                      |
|  Emails → Responses → Meetings → Qual. Opps → Closed   |
|  [____] → [______] → [_______] → [________] → [____]   |
|   100%      10%         33%          50%        25%     |
|                                                         |
|  PIPELINE HEALTH                                        |
|  Pipeline value created: $____                          |
|  Pipeline coverage: ____x                               |
|  Meetings next week: ____                               |
|                                                         |
|  EFFICIENCY                                             |
|  Cost per opp: $____                                    |
|  Revenue per SDR: $____                                 |
|  LTV:CAC: ____:1                                        |
+-------------------------------------------------------+
```

## Common Metric Mistakes

| Mistake | Why It Is a Problem | Fix |
|---------|--------------------|----|
| **Tracking activity only** | High email volume with zero qualified opps is not success | Always pair activity with conversion and outcome metrics |
| **Vanity metrics** | Open rates feel good but do not generate revenue | Focus on response rate, meetings, qualified opps |
| **No attribution** | Cannot tell which SDR or campaign generated which deal | Ensure CRM tracks opportunity source, SDR, and campaign |
| **Lagging-only review** | By the time revenue misses, it is too late to fix | Review leading indicators daily and weekly |
| **Comparing SDRs unfairly** | New SDR vs. tenured SDR is not apples-to-apples | Segment metrics by ramp stage and tenure |
| **Ignoring data quality** | Bad CRM data means bad dashboards | Require SDRs to log activities in real time; audit weekly |
| **Too many metrics** | Dashboard overload leads to analysis paralysis | Focus on 5-7 metrics per cadence level, not 30 |
| **No trend tracking** | A single month tells you nothing about direction | Always show metrics as trends over 3-6 months minimum |
| **Not sharing metrics** | SDRs who cannot see their numbers cannot improve | Make the dashboard visible and transparent to the team |
| **Inconsistent definitions** | "Qualified opportunity" means different things to different people | Document metric definitions and ensure everyone uses them |
