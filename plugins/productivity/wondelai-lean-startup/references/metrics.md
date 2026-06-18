# Actionable Metrics Guide

Metrics are the language of validated learning. The wrong metrics create the illusion of progress while the startup drifts toward failure. The right metrics force honest conversations and drive real decisions. This guide covers how to select, implement, and use metrics that actually matter.

## Actionable vs Vanity Metrics

### Vanity Metrics

Vanity metrics make you feel good but do not inform decisions. They go up and to the right even when the product is failing.

**Common vanity metrics:**
- Total registered users (includes dead accounts)
- Total page views (says nothing about engagement quality)
- Total downloads (says nothing about retention)
- Total revenue without context (growing because of more users, not better product)
- Social media followers (does not correlate with business outcomes)
- Press mentions (feels good, rarely converts)

**Why they are dangerous:** Vanity metrics can be manipulated, misinterpreted, and used to justify continuing a failing strategy. A startup with 100,000 registered users and 500 active users is failing, but the first number gets reported to investors.

### Actionable Metrics

Actionable metrics directly inform decisions. If the metric changes, you change your behavior.

**Properties of actionable metrics:**
- Tied to a specific, repeatable action
- Measured per cohort, not in aggregate
- Have a clear cause-and-effect relationship with product changes
- Can be independently verified

**Examples of actionable metrics:**

| Vanity Version | Actionable Version | Why It Is Better |
|---------------|-------------------|-----------------|
| Total users | Weekly new signups by acquisition channel | Shows which channels work and whether growth is accelerating |
| Total revenue | Revenue per user by cohort | Shows whether product improvements increase monetization |
| Page views | Pages per session by user segment | Shows engagement depth and content effectiveness |
| App downloads | Day-7 retention rate by cohort | Shows whether users find lasting value |
| Email subscribers | Email open rate by campaign type | Shows content relevance and audience engagement |

## The Three A's of Metrics

Every metric you track should pass the Three A's test:

### Actionable

A metric is actionable if it demonstrates clear cause and effect. When you make a product change and the metric moves, you can attribute the change to your action.

**Test:** "If this metric drops by 20%, do I know what to do?" If the answer is no, the metric is not actionable.

**Example:** Onboarding completion rate is actionable. If it drops, you investigate and fix the onboarding flow. Total signups is less actionable because it depends on marketing spend, seasonality, and press coverage.

### Accessible

A metric is accessible if the entire team can understand it and access it easily.

**Test:** "Can every team member explain what this metric means and find the current value in under 60 seconds?"

**Implementation:**
- Use simple, human-readable dashboards
- Display metrics on a shared screen or Slack channel
- Define every metric in a shared glossary
- Avoid jargon and complex calculations in primary dashboards
- Report metrics in absolute numbers alongside percentages (percentages without context mislead)

### Auditable

A metric is auditable if the data can be verified and traced to individual customer behavior.

**Test:** "Can I look at the underlying data and verify this number is correct? Can I talk to real customers whose behavior contributed to this metric?"

**Implementation:**
- Ensure data pipelines are transparent and well-documented
- Maintain the ability to drill down from aggregate metrics to individual events
- Cross-check automated reports against manual spot checks periodically
- Keep raw event data accessible (do not only store aggregates)

## Cohort Analysis Step-by-Step

### Step 1: Define Your Cohort

A cohort groups users by a shared experience within a defined time window.

**Common cohort definitions:**
- **Acquisition cohort:** Users who signed up in the same week/month
- **Behavioral cohort:** Users who completed a specific action (e.g., made first purchase)
- **Channel cohort:** Users acquired through the same marketing channel

### Step 2: Choose Your Metric

Select the metric that best reflects the hypothesis you are testing.

| Goal | Metric | Measurement |
|------|--------|-------------|
| Product stickiness | Retention rate | % of users active in period N who return in period N+1 |
| Monetization | Revenue per user | Total cohort revenue divided by cohort size |
| Engagement | Core actions per user | Average number of key actions per active user per period |
| Growth | Referral rate | Number of invites sent that convert, per cohort member |

### Step 3: Build the Cohort Table

**Retention cohort table example:**

| Signup Week | Size | Week 1 | Week 2 | Week 3 | Week 4 | Week 8 | Week 12 |
|------------|------|--------|--------|--------|--------|--------|---------|
| Jan 1-7 | 200 | 42% | 28% | 22% | 18% | 12% | 9% |
| Jan 8-14 | 180 | 45% | 31% | 25% | 20% | 14% | 11% |
| Jan 15-21 | 220 | 48% | 35% | 28% | 23% | 16% | - |
| Jan 22-28 | 250 | 50% | 37% | 30% | 25% | - | - |
| Feb 1-7 | 230 | 53% | 39% | 32% | - | - | - |

### Step 4: Read the Table

**Read across rows:** How does a single cohort degrade over time? This is the retention curve. Steeper = worse retention.

**Read down columns:** How do newer cohorts compare to older ones at the same age? Improving = product is getting better. Declining = product is getting worse.

**The key insight:** If newer cohorts retain better at the same age, your product improvements are working. If they retain worse, something is going wrong despite growth.

### Step 5: Act on Findings

| Pattern | What It Means | Action |
|---------|--------------|--------|
| Newer cohorts retain better | Product improvements are working | Continue current strategy; double down on winning changes |
| Newer cohorts retain worse | Product or acquisition quality is declining | Investigate recent changes; audit acquisition channels |
| Retention flattens at a certain week | Product has a natural engagement ceiling | Focus on deepening value for retained users |
| Retention drops sharply in Week 1 | Onboarding or first-use experience is broken | Redesign activation flow |
| Later cohorts are larger but retain worse | Growth is outpacing product quality | Slow growth; fix retention before scaling |

## Pirate Metrics (AARRR) Aligned With Lean Startup

Dave McClure's Pirate Metrics framework maps cleanly to lean startup stages:

### Acquisition

**Question:** How do users find you?

| Metric | Formula | Good Benchmark |
|--------|---------|----------------|
| Visitor-to-signup rate | Signups / Unique visitors | 2-5% for B2C, 5-15% for B2B |
| Cost per acquisition (CPA) | Marketing spend / New signups | Varies by industry; must be below LTV |
| Channel mix | % of signups by source | No single channel > 50% (diversification) |

### Activation

**Question:** Do users have a great first experience?

| Metric | Formula | Good Benchmark |
|--------|---------|----------------|
| Onboarding completion rate | Users completing setup / Signups | 60-80% |
| Time to first value | Time from signup to core action | Under 5 minutes for consumer; under 1 day for B2B |
| Aha moment conversion | Users reaching key milestone / Signups | 40-70% |

### Retention

**Question:** Do users come back?

| Metric | Formula | Good Benchmark |
|--------|---------|----------------|
| Day 1 / Day 7 / Day 30 retention | Active on Day N / Cohort size | Varies by category (see below) |
| Weekly active / Monthly active ratio | WAU / MAU | 25%+ is healthy |
| Churn rate | Users lost / Total users per period | Under 5% monthly for SaaS |

**Retention benchmarks by category:**

| Category | Day 1 | Day 7 | Day 30 |
|----------|-------|-------|--------|
| Social/messaging | 50-70% | 30-50% | 20-35% |
| E-commerce | 25-40% | 10-20% | 5-15% |
| SaaS (B2B) | 80-95% | 70-85% | 60-80% |
| Mobile gaming | 35-50% | 15-25% | 5-15% |
| Productivity tools | 40-60% | 25-40% | 15-30% |

### Revenue

**Question:** How do you make money?

| Metric | Formula | Good Benchmark |
|--------|---------|----------------|
| Average revenue per user (ARPU) | Total revenue / Active users | Depends on pricing model |
| Lifetime value (LTV) | ARPU multiplied by average lifespan | 3x+ CAC |
| Conversion to paid | Paid users / Total active users | 2-5% freemium; 15-30% free trial |
| Net revenue retention | (Starting MRR + expansion - contraction - churn) / Starting MRR | 100%+ for B2B SaaS |

### Referral

**Question:** Do users tell others?

| Metric | Formula | Good Benchmark |
|--------|---------|----------------|
| Viral coefficient (K) | Invites per user multiplied by conversion rate of invites | Above 0.5 is strong; above 1.0 is viral |
| Net Promoter Score (NPS) | % Promoters minus % Detractors | 40+ is excellent |
| Referral rate | Users who refer / Total active users | 10%+ indicates strong word of mouth |
| Organic traffic share | Organic visits / Total visits | 40%+ suggests brand strength |

## Metric Selection by Stage

### Pre-Product-Market Fit

Focus on engagement and retention. Revenue metrics are premature.

**Primary metrics:**
- Retention (Week 1, Week 4 by cohort)
- Core action completion rate
- Qualitative: Sean Ellis test ("How would you feel if you could no longer use this product?")
- NPS from active users
- Session frequency

**Do not optimize:** CAC, LTV, revenue, viral coefficient. These are meaningless without product-market fit.

### Post-Product-Market Fit (Pre-Scale)

Focus on unit economics and channel efficiency.

**Primary metrics:**
- LTV and LTV/CAC ratio
- CAC by channel
- Monthly retention and churn by cohort
- Revenue per user trends
- Activation rate

**Do not optimize:** Brand awareness, market share, total revenue. Scale metrics come after unit economics are healthy.

### Growth Stage

Focus on efficiency at scale and sustainable growth.

**Primary metrics:**
- Net revenue retention
- Payback period (months to recover CAC)
- Gross margin
- Growth rate (month over month)
- Channel saturation indicators

## Dashboard Design Principles

### Principle 1: One Page, One Story

Each dashboard should answer one question. Do not combine acquisition, engagement, and revenue on a single screen. Create separate views for separate questions.

### Principle 2: Show Trends, Not Snapshots

A single number is meaningless without context. Always show the metric over time (at least 8 weeks) and compare to the previous period.

### Principle 3: Cohort by Default

Default views should show cohort data. Aggregate views should require a deliberate click or toggle. This prevents the team from accidentally reading vanity numbers.

### Principle 4: Include Absolute Numbers

Percentages without absolute numbers mislead. "50% conversion rate" sounds great until you learn the sample was 4 users. Always show both the percentage and the underlying count.

### Principle 5: Highlight Decisions, Not Data

Add annotations to the dashboard showing when experiments launched. This creates a visual connection between actions and results.

## Common Metric Mistakes and Corrections

| Mistake | Why It Is Wrong | Correction |
|---------|----------------|------------|
| Tracking 30+ metrics simultaneously | Attention is diluted; team cannot focus | Pick 3-5 primary metrics per stage |
| Celebrating total user growth while retention declines | Growth masks product problems | Always lead with cohort retention |
| Measuring weekly without cohort segmentation | Cannot distinguish product improvement from marketing spend | Segment every metric by cohort |
| Setting metric targets after seeing results | Confirmation bias; any result looks like success | Set targets before running experiments |
| Ignoring qualitative data because "we have the numbers" | Numbers tell you what; interviews tell you why | Pair every quantitative metric with 5-10 customer conversations per month |
| Optimizing a metric that does not connect to business outcomes | Local optimization without global impact | Map every metric to a business outcome (retention to LTV, activation to retention, etc.) |
| Changing metric definitions mid-experiment | Results become incomparable | Lock definitions before experiments start; create new metrics if needed |

Good metrics create honest conversations. Bad metrics create comfortable delusions. The discipline of innovation accounting is choosing honesty over comfort.
