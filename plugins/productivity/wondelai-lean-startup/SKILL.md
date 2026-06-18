---
name: lean-startup
description: 'Design MVPs, validated learning experiments, and pivot-or-persevere decisions using Build-Measure-Learn. Use when the user mentions "MVP scope", "validated learning", "pivot or persevere", "vanity metrics", "test assumptions", "innovation accounting", "build-measure-learn", or "minimum viable experiment". Also trigger when deciding what to include in a first version, measuring startup progress, or evaluating whether to change direction on a product bet. Covers innovation accounting and actionable metrics. For 5-day prototype testing, see design-sprint. For customer motivation analysis, see jobs-to-be-done.'
license: MIT
metadata:
  author: wondelai
  version: "1.2.0"
---

# Lean Startup Methodology

A systematic approach to building startups and launching new products that shortens development cycles and rapidly discovers whether a business model is viable.

## Core Principle

**Entrepreneurship is a form of management.** Success doesn't require a perfect plan or brilliant insight—it requires a systematic process for testing assumptions, learning from customers, and iterating rapidly.

**The foundation:** Most startups fail not because they couldn't build what they planned, but because they built the wrong thing. Lean Startup applies scientific experimentation to eliminate waste and accelerate validated learning.

## Scoring

**Goal: 10/10.** Rate product development plans, experiments, or metrics 0-10 against Lean Startup principles: full Build-Measure-Learn application and evidence-based decisions score 10; waterfall thinking or waste lowers the score. Always state the current score and the specific improvements needed to reach 10/10.

## The Build-Measure-Learn Loop

The fundamental cycle: **IDEAS → BUILD (product) → MEASURE (data) → LEARN (knowledge) → back to IDEAS.**

**Critical insight:** Plan the loop backward:
1. **What do we want to learn?** (hypothesis to test)
2. **How will we know if we learned it?** (metrics)
3. **What's the minimum we can build?** (MVP)

**Goal:** Minimize total time through the loop.

See: [references/build-measure-learn.md](references/build-measure-learn.md) for detailed loop execution and reverse planning.

## Validated Learning

Learning what customers really want through experiments on real behavior—not feature requests, surveys, or focus groups (people mispredict their own behavior). Measure what customers *do*, not what they *say*, and run experiments that could falsify your assumptions. Vanity wins (downloads, signups without engagement) are not learning.

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

The version of a new product that allows maximum validated learning with the least effort. Not a prototype (technical feasibility), not a beta (quality), not a minimum marketable product—a learning vehicle, often embarrassingly small and low quality, and usually much smaller than you think.

**MVP Types:**

| Type | What It Is | When to Use | Example |
|------|------------|-------------|---------|
| **Concierge** | Manual service pretending to be automated | Test if solution is valuable | Food on the Table (manual meal planning) |
| **Wizard of Oz** | Fake automation, manual backend | Test if automation is needed | Zappos (no inventory, bought shoes retail) |
| **Smoke test** | Landing page + signup, no product | Test demand before building | Dropbox video (explained concept, measured signups) |
| **Single feature** | One core feature only | Test which feature is most valuable | Twitter (just status updates) |
| **Piecemeal** | Combine existing tools | Test workflow before custom build | Groupon (WordPress + email) |

**Design questions:** What's the riskiest assumption? What's the minimum that tests it? How do we measure whether it was validated?

See: [references/mvp-design.md](references/mvp-design.md) for MVP types, design patterns, and sizing.

## Leap-of-Faith Assumptions

The assumptions that, if wrong, will cause your business to fail. Identify them, prioritize by risk (which failure would be fatal?), and test the riskiest first—never in order of ease.

| Assumption Type | Question | Test Method |
|----------------|----------|-------------|
| **Value hypothesis** | Do customers care about this problem? | Smoke test, concierge MVP |
| **Growth hypothesis** | How will customers discover us? | Channel tests, referral experiments |
| **Retention hypothesis** | Will customers come back? | Cohort analysis, engagement metrics |
| **Monetization hypothesis** | Will customers pay? | Pre-orders, pricing tests |

**Example—Dropbox:** Leap of faith: "people will download and use a file sync tool." Test: explainer video before building scale infrastructure. Result: beta list grew from 5,000 to 75,000 overnight—demand validated.

See: [references/assumptions.md](references/assumptions.md) for assumption mapping frameworks.

## Innovation Accounting

Measuring progress when traditional metrics fail: revenue and customers start at zero, and vanity metrics look good without driving decisions.

### 1. Establish the Baseline

Measure current reality precisely, even if it's zero or embarrassing: conversion funnel (signup → active → retained → paying), engagement (DAU/MAU, session length, features used), economics (CAC, LTV, churn).

### 2. Tune the Engine

Run experiments to improve baseline metrics: A/B test pricing ($9 vs. $19/mo), onboarding completion rates, acquisition channels (SEO vs. paid vs. referral). Each experiment targets a measurable improvement through validated learning.

### 3. Pivot or Persevere

Decide from evidence: Are metrics moving the right way? Is the rate of improvement acceptable given the runway? Are we learning what we expected?

See: [references/innovation-accounting.md](references/innovation-accounting.md) for metric frameworks and dashboards.

## Actionable vs. Vanity Metrics

Vanity metrics make you feel good but don't change behavior; actionable metrics drive decisions and clarify cause and effect.

| Vanity | Why It's Bad | Actionable Alternative |
|--------|-------------|------------------------|
| **Total signups** | Always goes up, no context | **% signup → active** (conversion rate) |
| **Page views** | Doesn't indicate value | **Time on page**, **bounce rate** |
| **Total users** | Includes inactive/churned | **Active users** (DAU, WAU, MAU) |
| **Downloads** | Doesn't mean usage | **DAU/downloads** (activation rate) |
| **Revenue** | Without context | **Revenue per cohort**, **LTV/CAC** |

**Three characteristics of actionable metrics:** actionable (clear cause-and-effect, reproducible), accessible (simple, understood by everyone), auditable (underlying data can be checked).

**Example:** Vanity: "We have 100,000 users!" Actionable: "Channel X users retain 2x better than channel Y—double down on X."

**Cohort analysis:** Group users by signup date and track behavior over time—the only way to see whether the product is actually improving.

See: [references/metrics.md](references/metrics.md) for metric selection and tracking.

## Pivot or Persevere

A pivot is a structured course correction designed to test a new hypothesis about the product, strategy, or engine of growth.

**Pivot when:** experiments repeatedly fail to validate hypotheses, metrics stay flat despite iterations, customer feedback contradicts the vision, or progress is too slow for the runway. **Persevere when:** metrics are improving (even slowly), clear learning is happening, and adjustments move the right direction.

**Pivot Types:**

| Pivot Type | What Changes | Example |
|------------|-------------|---------|
| **Zoom-in** | Single feature becomes the whole product | Instagram (photo filters from Burbn) |
| **Zoom-out** | Product becomes a single feature | Flickr (photo-sharing from Game Neverending) |
| **Customer segment** | Same problem, different customer | Groupon (activism platform → local deals) |
| **Customer need** | Same customer, different problem | Potbelly (antique store → sandwiches) |
| **Platform** | App ↔ Platform | YouTube (dating site → video platform) |
| **Business architecture** | High margin/low volume ↔ low margin/high volume | Salesforce (software → SaaS) |
| **Value capture** | Monetization model change | Android (paid → free + app revenue) |
| **Engine of growth** | Viral, sticky, or paid model | Facebook (viral in colleges → paid advertising) |
| **Channel** | How you reach customers | Salesforce (direct sales → self-service) |
| **Technology** | Different technology, same solution | Apple (Intel → ARM chips) |

**Cadence:** Successful startups commonly pivot 1-5 times before product-market fit. **Anti-pattern:** "pivoting" without validating that the new direction solves the core problem.

See: [references/pivots.md](references/pivots.md) for pivot decision frameworks and case studies.

## The Three Engines of Growth

How a startup acquires and retains customers sustainably. **Pick one engine, optimize it, then consider adding others**—running multiple engines simultaneously dilutes focus and learning.

### 1. Sticky Engine of Growth

Retention-driven: `growth rate = new customer acquisition rate − churn rate`. Track churn rate, retention cohorts (30/60/90 days), and DAU/MAU. Fits SaaS, subscriptions, social networks. Strategy: improve the product until natural growth exceeds churn.

### 2. Viral Engine of Growth

Customers bring customers: `viral coefficient = (% who invite) × (invites sent) × (% who join)`; above 1.0 means exponential, self-sustaining growth. Track the coefficient, viral cycle time, and referral attribution. Fits Dropbox, Hotmail, WhatsApp. Strategy: build virality into the product itself.

### 3. Paid Engine of Growth

Spend to acquire: requires `LTV > CAC` (target LTV/CAC > 3x). Track CAC, LTV, and payback period. Fits e-commerce and traditional businesses. Strategy: optimize until each customer's profit funds acquiring more.

See: [references/growth-engines.md](references/growth-engines.md) for engine selection and optimization.

## The Five Whys

Root cause analysis: when a problem occurs, ask "why?" five times, then invest proportionally at every level—not just the symptom.

**Example—website went down:**
1. **Why?** Server ran out of memory
2. **Why?** Memory leak in a new feature
3. **Why?** Code wasn't reviewed for memory management
4. **Why?** No code review process for infrastructure changes
5. **Why?** Team is moving too fast to create processes

**Proportional investments:** fix the bug (1), add memory monitoring (2), implement code review (3-4), slow down to build quality processes (5). **Anti-pattern:** stopping at level 1.

See: [references/five-whys.md](references/five-whys.md) for facilitation guides.

## Small Batches

Work in small batches for faster feedback loops, easier pivots, less waste when you're wrong, and faster time to market.

| Large Batch | Small Batch |
|-------------|-------------|
| Build entire product, then launch | Launch landing page, then build |
| Release quarterly | Release weekly or daily |
| Plan 12-month roadmap | Plan 6-week cycles |
| Big bang rewrite | Incremental refactoring |

**Continuous deployment** is the ultimate small batch: deploy every commit, catch bugs immediately, learn continuously, reduce risk per release.

See: [references/small-batches.md](references/small-batches.md) for implementation patterns.

## Lean Startup Applied: From Idea to Scale

**Phase 1—Problem/Solution Fit:** validate that the problem exists and customers care, via customer discovery, smoke tests, and concierge MVPs. Metric: customers willing to pay or commit.

**Phase 2—Product/Market Fit:** build the MVP and iterate on usage data. Metric: high retention, organic growth, strong engagement.

**Phase 3—Scale:** optimize the growth engine and unit economics. Metric: sustainable, profitable growth. **Anti-pattern:** skipping Phases 1-2 and jumping straight to scale.

**By context:**
- **SaaS startup:** smoke test (landing page + email list) → concierge MVP with 10 customers → single-feature MVP → measure retention, NPS, feature usage → pivot or scale on cohort data
- **Corporate innovation:** separate innovation accounting from core-business metrics, shield teams from quarterly revenue pressure, unlock metered funding on validated-learning milestones
- **Product features:** deploy behind a feature flag → A/B test against core metrics → kill, iterate, or scale based on data

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
| **Premature scale optimization** | Polishing before product-market fit | Validate learning first; quality follows evidence |

## Quick Diagnostic

Audit any product development plan:

| Question | If No | Action |
|----------|-------|--------|
| What's the riskiest assumption? | Building on shaky ground | Map leap-of-faith assumptions |
| How will you test it? | You're guessing | Design MVP to test the assumption |
| What metric will validate/invalidate? | You won't learn | Define actionable metrics |
| Can you test with less than this? | Over-building | Shrink the MVP further |
| What will you do if the experiment fails? | No pivot criteria | Define pivot triggers upfront |

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

For the complete framework, research, and case studies:

- [*"The Lean Startup"*](https://www.amazon.com/Lean-Startup-Entrepreneurs-Continuous-Innovation/dp/0307887898?tag=wondelai00-20) by Eric Ries
- [*"The Startup Way"*](https://www.amazon.com/Startup-Way-Companies-Entrepreneurial-Management/dp/1101903201?tag=wondelai00-20) by Eric Ries (applying Lean Startup to established companies)

## About the Author

**Eric Ries** is an entrepreneur and author who developed the Lean Startup methodology as co-founder and CTO of IMVU, where he pioneered the continuous deployment and customer development practices behind it. *The Lean Startup* has been translated into over 30 languages and shaped startup culture worldwide. He later created the Long-Term Stock Exchange (LTSE).
