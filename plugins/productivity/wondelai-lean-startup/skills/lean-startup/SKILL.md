---
name: lean-startup
description: |
  Design MVPs, validated learning experiments, and pivot-or-persevere decisions using Build-Measure-Learn. Use when the user mentions "MVP scope", "validated learning", "pivot or persevere", "vanity metrics", or "test assumptions". Covers innovation accounting and actionable metrics. For 5-day prototype testing, see design-sprint. For customer motivation analysis, see jobs-to-be-done. Trigger with 'lean', 'startup'.
allowed-tools: Read, Glob, Grep
license: MIT
author: Wondelai <hello@wondelai.com>
version: 1.0.1
compatible-with: claude-code, codex, openclaw
tags: [productivity, testing, lean-startup]
---
# Lean Startup Methodology

A systematic approach to building startups and launching new products that shortens development cycles and rapidly discovers if a business model is viable.

## Core Principle

**Entrepreneurship is a form of management.** Success doesn't require a perfect plan or brilliant insight—it requires a systematic process for testing assumptions, learning from customers, and iterating rapidly.

**The foundation:** Most startups fail not because they couldn't build what they planned, but because they built the wrong thing. The Lean Startup methodology applies scientific experimentation to eliminate waste and accelerate validated learning.

## Scoring

**Goal: 10/10.** When reviewing or creating product development plans, experiments, or metrics, rate them 0-10 based on adherence to Lean Startup principles. A 10/10 means full application of Build-Measure-Learn, validated learning, and evidence-based decisions; lower scores indicate waterfall thinking or waste. Always provide the current score and specific improvements needed to reach 10/10.

## The Build-Measure-Learn Loop

The fundamental cycle of Lean Startup:

```
     IDEAS
       ↓
    BUILD → Product
       ↓
    MEASURE → Data
       ↓
    LEARN → Knowledge
       ↓
    (back to IDEAS)
```

**Critical insight:** The loop is actually backward. Start with what you want to learn, determine metrics that will inform that learning, then build the minimum product to collect those metrics.

**Reverse planning:**
1. **What do we want to learn?** (hypothesis to test)
2. **How will we know if we learned it?** (metrics)
3. **What's the minimum we can build?** (MVP)

**Goal:** Minimize total time through the loop.

See: [references/build-measure-learn.md](references/build-measure-learn.md) for detailed loop execution.

## Validated Learning

**Definition:** Learning what customers really want through validated experiments, not opinion or anecdotes.

**Validated learning is not:**
- Building features customers request (they don't know what they want)
- Achieving vanity metrics (downloads, signups without engagement)
- Doing surveys or focus groups (people lie/mispredict behavior)

**Validated learning is:**
- Testing hypotheses with real behavior
- Measuring what customers *do*, not what they *say*
- Running experiments that could falsify your assumptions
- Learning = when your predictions were wrong

**The Validation Ladder:**

| Level | Evidence | Strength |
|-------|----------|----------|
| 1 | "I think customers want this" | Weakest (opinion) |
| 2 | "Customers said they want this" | Weak (stated preference) |
| 3 | "Customers signed up for early access" | Medium (low commitment) |
| 4 | "Customers paid a deposit" | Strong (real commitment) |
| 5 | "Customers are actively using it" | Strongest (revealed preference) |

**Target:** Level 4-5 before building at scale.

## Minimum Viable Product (MVP)

**Definition:** The version of a new product that allows a team to collect the maximum amount of validated learning with the least effort.

**MVP is not:**
- A prototype (not about proving technical feasibility)
- A beta version (not about quality or features)
- A minimum marketable product (it might be embarrassing)

**MVP is:**
- A learning vehicle
- The smallest experiment to test a hypothesis
- Often much smaller than you think

**MVP Types:**

| Type | What It Is | When to Use | Example |
|------|------------|-------------|---------|
| **Concierge** | Manual service pretending to be automated | Test if solution is valuable | Food on the Table (manual meal planning) |
| **Wizard of Oz** | Fake automation, manual backend | Test if automation is needed | Zappos (no inventory, bought shoes retail) |
| **Smoke test** | Landing page + signup, no product | Test demand before building | Dropbox video (explained concept, measured signups) |
| **Single feature** | One core feature only | Test which feature is most valuable | Twitter (just status updates) |
| **Piecemeal** | Combine existing tools | Test workflow before custom build | Groupon (WordPress + email) |

**MVP Design Questions:**
- What's the riskiest assumption to test first?
- What's the minimum to test that assumption?
- How do we measure if the assumption was validated?

**Common mistakes:**
- Building too much (overestimate MVP size)
- Optimizing for scale prematurely
- Confusing quality with learning (MVP can be low quality)
- Skipping the experiment (building without hypothesis)

See: [references/mvp-design.md](references/mvp-design.md) for MVP types and design patterns.

## Leap-of-Faith Assumptions

**Definition:** The assumptions that, if wrong, will cause your business to fail.

**Process:**
1. **Identify your business model's critical assumptions**
2. **Prioritize by risk** (which failure would be fatal?)
3. **Test the riskiest assumption first**

**Common leap-of-faith assumptions:**

| Assumption Type | Question | Test Method |
|----------------|----------|-------------|
| **Value hypothesis** | Do customers care about this problem? | Smoke test, concierge MVP |
| **Growth hypothesis** | How will customers discover us? | Channel tests, referral experiments |
| **Retention hypothesis** | Will customers come back? | Cohort analysis, engagement metrics |
| **Monetization hypothesis** | Will customers pay? | Pre-orders, pricing tests |

**Example: Dropbox**
- **Leap-of-faith:** "People will download and use a file sync tool"
- **Test:** Explainer video showing product (before building full version)
- **Metric:** Beta signup list grew from 5,000 to 75,000 overnight
- **Learning:** Validated demand before building scale infrastructure

**Anti-pattern:** Testing assumptions in order of ease rather than risk.

See: [references/assumptions.md](references/assumptions.md) for assumption mapping frameworks.

## Innovation Accounting

**Definition:** Measuring progress when traditional accounting doesn't apply.

**The problem with traditional metrics:**
- Revenue (startups start at $0)
- Customers (startups start at 0)
- Vanity metrics (look good but don't drive decisions)

**Innovation accounting framework:**

### 1. Establish the Baseline
**Question:** Where are we today?

Measure current reality, even if it's zero or embarrassing.

**Metrics to establish:**
- Conversion funnel (signup → active → retained → paying)
- Engagement (DAU/MAU, session length, features used)
- Economics (CAC, LTV, churn rate)

**Goal:** Know your starting point precisely.

### 2. Tune the Engine
**Question:** What can we improve to move toward our goal?

Run experiments to improve baseline metrics.

**Examples:**
- A/B test pricing ($9/mo vs. $19/mo)
- Test onboarding flows (% who complete setup)
- Experiment with channels (SEO vs. paid vs. referral)

**Goal:** Systematically improve metrics through validated learning.

### 3. Pivot or Persevere
**Question:** Are we making sufficient progress, or do we need to change strategy?

Based on data, decide whether to continue or pivot.

**Criteria:**
- Are metrics moving in the right direction?
- Is the rate of improvement acceptable?
- Are we learning what we expected?

**Goal:** Make evidence-based strategic decisions.

See: [references/innovation-accounting.md](references/innovation-accounting.md) for metric frameworks and dashboards.

## Actionable vs. Vanity Metrics

**Vanity metrics:** Make you feel good but don't change behavior.

**Actionable metrics:** Drive decisions and clarify cause and effect.

| Vanity | Why It's Bad | Actionable Alternative |
|--------|-------------|------------------------|
| **Total signups** | Always goes up, no context | **% signup → active** (conversion rate) |
| **Page views** | Doesn't indicate value | **Time on page**, **bounce rate** |
| **Total users** | Includes inactive/churned | **Active users** (DAU, WAU, MAU) |
| **Downloads** | Doesn't mean usage | **DAU/downloads** (activation rate) |
| **Revenue** | Without context | **Revenue per cohort**, **LTV/CAC** |

**Three characteristics of actionable metrics:**

1. **Actionable:** Clear cause-and-effect (can reproduce)
2. **Accessible:** Simple, understandable by everyone
3. **Auditable:** Can check the underlying data (not a black box)

**Example:**
- **Vanity:** "We have 100,000 users!"
- **Actionable:** "Users from channel X have 2x retention vs. channel Y. Let's double down on X."

**Cohort analysis:** Group users by signup date and track behavior over time. Reveals if product is actually improving.

See: [references/metrics.md](references/metrics.md) for metric selection and tracking.

## Pivot or Persevere

**Pivot:** A structured course correction designed to test a new hypothesis about the product, strategy, or engine of growth.

**When to pivot:**
- Experiments consistently fail to validate hypotheses
- Metrics are flat despite multiple iterations
- Customer feedback contradicts your vision
- Progress is too slow given runway

**When to persevere:**
- Metrics are improving (even if slowly)
- Clear learning is happening
- Adjustments are moving in right direction

**Pivot Types:**

| Pivot Type | What Changes | Example |
|------------|-------------|---------|
| **Zoom-in pivot** | Single feature becomes the whole product | Instagram (photo filters from Burbn check-in app) |
| **Zoom-out pivot** | Product becomes a single feature | Flickr (photo-sharing from Game Neverending) |
| **Customer segment** | Same problem, different customer | Groupon (activism platform → local deals) |
| **Customer need** | Same customer, different problem | Potbelly Sandwich (antique store → sandwiches) |
| **Platform** | App → Platform or Platform → App | YouTube (dating site → video platform) |
| **Business architecture** | High margin, low volume ↔ Low margin, high volume | Salesforce (software → SaaS) |
| **Value capture** | Monetization model change | Android (paid → free + app revenue) |
| **Engine of growth** | Viral, sticky, or paid growth model | Facebook (viral within colleges → paid advertising) |
| **Channel** | How you reach customers | Salesforce (direct sales → self-service) |
| **Technology** | Different technology, same solution | Apple (Intel → ARM chips) |

**Pivot cadence:** Many successful startups pivot 1-5 times before finding product-market fit.

**Anti-pattern:** "Pivot" without validating that the new direction solves the core problem.

See: [references/pivots.md](references/pivots.md) for pivot decision frameworks and case studies.

## The Three Engines of Growth

**Growth engine:** How your startup acquires and retains customers sustainably.

**Choose one engine to focus on:**

### 1. Sticky Engine of Growth

**Mechanism:** High retention, low churn

**Formula:** `Growth rate = New customer acquisition rate - Churn rate`

**Focus:** Keep customers coming back

**Metrics:**
- Churn rate (% who stop using per month)
- Retention cohorts (% still active after 30/60/90 days)
- Engagement (DAU/MAU ratio)

**Examples:** SaaS, subscription services, social networks

**Strategy:** Improve product until churn rate is low enough that natural growth exceeds churn.

### 2. Viral Engine of Growth

**Mechanism:** Customers bring other customers

**Formula:** `Viral coefficient = (% who invite) × (invites sent) × (% who join)`

**Focus:** Viral coefficient > 1.0 = exponential growth

**Metrics:**
- Viral coefficient (invites → signups)
- Viral cycle time (how long until referred user invites others)
- Referral source attribution

**Examples:** Dropbox, Hotmail, WhatsApp

**Strategy:** Build virality into the product. Must be > 1.0 to be self-sustaining.

### 3. Paid Engine of Growth

**Mechanism:** Spend money to acquire customers

**Formula:** `LTV (Lifetime Value) > CAC (Customer Acquisition Cost)`

**Focus:** Unit economics that allow reinvestment

**Metrics:**
- CAC (cost per acquisition)
- LTV (average revenue per customer)
- LTV/CAC ratio (target: > 3x)
- Payback period (how long to recoup CAC)

**Examples:** E-commerce, traditional businesses

**Strategy:** Optimize until each customer generates enough profit to acquire more customers.

**Warning:** Don't use multiple engines simultaneously. Pick one, optimize it, then consider adding others.

See: [references/growth-engines.md](references/growth-engines.md) for engine selection and optimization.

## The Five Whys

**Purpose:** Root cause analysis to prevent problems from recurring.

**Process:**
1. A problem occurs (bug, outage, customer complaint)
2. Ask "Why did this happen?" → Answer
3. Ask "Why?" about that answer → Second answer
4. Repeat 5 times until you reach the root cause
5. Make proportional investments at each level

**Example:**

**Problem:** Website went down

1. **Why?** Server ran out of memory
2. **Why?** Memory leak in new feature
3. **Why?** Code wasn't reviewed for memory management
4. **Why?** No code review process for infrastructure changes
5. **Why?** Team is moving too fast to create processes

**Proportional investments:**
- Fix the immediate bug (level 1)
- Add memory monitoring (level 2)
- Implement code review (level 3-4)
- Slow down to build quality processes (level 5)

**Anti-pattern:** Stop at level 1 (just fix the symptom).

See: [references/five-whys.md](references/five-whys.md) for facilitation guides.

## Small Batches

**Principle:** Work in small batches to accelerate learning and reduce waste.

**Why small batches win:**
- Faster feedback loops
- Easier to pivot
- Less waste when you're wrong
- Faster time to market

**Examples:**

| Large Batch | Small Batch |
|-------------|-------------|
| Build entire product, then launch | Launch landing page, then build |
| Release quarterly | Release weekly or daily |
| Plan 12-month roadmap | Plan 6-week cycles |
| Big bang rewrite | Incremental refactoring |

**Continuous deployment:** The ultimate small batch = deploy every code commit.

**Benefits:**
- Bugs are caught immediately
- Learning happens continuously
- Reduced risk per deployment

See: [references/small-batches.md](references/small-batches.md) for implementation patterns.

## Lean Startup Applied

**For different contexts:**

### SaaS Startup
1. **Smoke test:** Landing page + email list (validate demand)
2. **Concierge MVP:** Manually deliver service to 10 customers (validate value)
3. **Single-feature MVP:** Build one core workflow (validate engagement)
4. **Measure:** Retention, NPS, feature usage
5. **Pivot or scale:** Based on cohort data

### Corporate Innovation
1. **Innovation accounting:** Separate metrics from core business
2. **Protected teams:** Shield from quarterly revenue pressure
3. **Metered funding:** Unlock funding based on validated learning milestones
4. **Internal entrepreneurship:** Treat team as startup within company

### Product Features
1. **Feature flags:** Deploy behind flag, test with small cohort
2. **A/B test:** Measure impact on core metrics
3. **Kill, iterate, or scale:** Based on data

See: [references/applications.md](references/applications.md) for context-specific guides.

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|------|
| **Building too much** | Waste before validation | Test with smoke test or concierge first |
| **Asking customers** | People don't know/mispredict | Observe behavior, not opinions |
| **Vanity metrics** | Feel-good numbers, no decisions | Track cohorts, conversion, retention |
| **No hypothesis** | Can't learn if you don't predict | Write hypothesis before each experiment |
| **Pivot too slow** | Waste runway | Set clear pivot criteria upfront |
| **Skip innovation accounting** | Can't tell if you're improving | Establish baseline, measure tuning efforts |

## Quick Diagnostic

Audit any product development plan:

| Question | If No | Action |
|----------|-------|--------|
| What's the riskiest assumption? | You're building on shaky ground | Map leap-of-faith assumptions |
| How will you test it? | You're guessing | Design MVP to test assumption |
| What metric will validate/invalidate? | You won't learn | Define actionable metrics |
| Can you test with less than this? | You're over-building | Shrink MVP further |
| What will you do if the experiment fails? | No pivot criteria | Define pivot triggers upfront |

## The Lean Startup Applied: From Idea to Scale

**Phase 1: Problem/Solution Fit**
- **Goal:** Validate the problem exists and customers care
- **Method:** Customer discovery, smoke tests, concierge MVP
- **Metric:** Customers willing to pay or commit

**Phase 2: Product/Market Fit**
- **Goal:** Build something people want
- **Method:** Build MVP, iterate based on usage data
- **Metric:** High retention, organic growth, strong engagement

**Phase 3: Scale**
- **Goal:** Grow efficiently
- **Method:** Optimize growth engine, improve unit economics
- **Metric:** Sustainable, profitable growth

**Anti-pattern:** Skipping Phase 1-2 and jumping straight to scale.

## Reference Files

- [build-measure-learn.md](references/build-measure-learn.md): Detailed loop execution, reverse planning
- [mvp-design.md](references/mvp-design.md): MVP types, design patterns, sizing
- [assumptions.md](references/assumptions.md): Leap-of-faith assumption mapping
- [innovation-accounting.md](references/innovation-accounting.md): Metric frameworks, dashboards
- [metrics.md](references/metrics.md): Actionable vs. vanity, cohort analysis, metric selection
- [pivots.md](references/pivots.md): Pivot types, decision frameworks, case studies
- [growth-engines.md](references/growth-engines.md): Sticky, viral, paid engines in depth
- [five-whys.md](references/five-whys.md): Root cause analysis, facilitation guides
- [small-batches.md](references/small-batches.md): Batch size reduction, continuous deployment
- [applications.md](references/applications.md): SaaS, corporate innovation, features
- [case-studies.md](references/case-studies.md): Dropbox, IMVU, Zappos, Groupon, and failures

## Further Reading

This skill is based on Eric Ries' Lean Startup methodology. For the complete framework, research, and case studies:

- [*"The Lean Startup"*](https://www.amazon.com/Lean-Startup-Entrepreneurs-Continuous-Innovation/dp/0307887898?tag=wondelai00-20) by Eric Ries
- [*"The Startup Way"*](https://www.amazon.com/Startup-Way-Companies-Entrepreneurial-Management/dp/1101903201?tag=wondelai00-20) by Eric Ries (applying Lean Startup to established companies)

## Overview

A systematic approach to building startups and products that shortens development cycles by applying the Build-Measure-Learn loop, validated learning, and innovation accounting to eliminate waste.

## Prerequisites

- A product idea or business hypothesis to validate
- Access to target customers for experiments (even a small initial group)
- Ability to define and measure actionable metrics (conversion, retention, engagement)

## Instructions

1. Identify leap-of-faith assumptions — use the Quick Diagnostic table to audit your plan
2. Design the smallest MVP to test the riskiest assumption first
3. Define actionable metrics and run the Build-Measure-Learn loop
4. Use innovation accounting to evaluate progress and decide pivot-or-persevere

## Output

- **Hypothesis card**: Assumption, test method, success metric, and pivot criteria
- **MVP specification**: Type (concierge, smoke test, single-feature, etc.) and scope
- **Experiment results**: Baseline metrics, tuning outcomes, and pivot-or-persevere recommendation

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| No clear hypothesis | Building without a testable assumption | Map leap-of-faith assumptions before designing MVP |
| Vanity metrics only | Tracking totals instead of cohorts | Switch to actionable metrics (conversion, retention, LTV/CAC) |
| MVP too large | Over-engineering before validation | Apply the "can you test with less?" filter from Quick Diagnostic |

## Examples

- **Smoke test**: Landing page with signup form to validate demand before building any product (Dropbox pattern).
- **Concierge MVP**: Manually deliver the service to 10 customers to validate the value hypothesis before automating.

## Resources

- [references/build-measure-learn.md](references/build-measure-learn.md) — detailed loop execution and reverse planning
- [references/mvp-design.md](references/mvp-design.md) — MVP types, design patterns, and sizing
- [references/metrics.md](references/metrics.md) — actionable vs vanity metrics and cohort analysis
- [*"The Lean Startup"*](https://www.amazon.com/Lean-Startup-Entrepreneurs-Continuous-Innovation/dp/0307887898?tag=wondelai00-20) by Eric Ries — the complete methodology

