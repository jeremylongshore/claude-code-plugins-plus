# Lean Startup Methodology - Implementation Guide

Step-by-step methodology for designing MVPs, running validated learning experiments, and making evidence-based pivot-or-persevere decisions.

## The Build-Measure-Learn Loop

The fundamental cycle of Lean Startup:

```
     IDEAS
       ↓
     BUILD (minimum viable product)
       ↓
     PRODUCT
       ↓
     MEASURE (actionable metrics)
       ↓
     DATA
       ↓
     LEARN (validated learning)
       ↓
     IDEAS (refined or pivoted)
```

Each loop should answer one specific question about your business model. The faster you loop, the faster you learn.

## Step 1: Define Your Leap-of-Faith Assumptions

Before building anything, identify the critical assumptions your business model depends on.

**1a. Two categories of assumptions**
- **Value hypothesis**: does the product deliver value to customers? (Do customers actually want this?)
- **Growth hypothesis**: will customers tell others about it? (Will this grow?)

**1b. Finding your riskiest assumption**
- List every assumption your business requires to be true
- Rank by: (1) how critical is this to success? and (2) how uncertain is it?
- The intersection of high-criticality + high-uncertainty = your riskiest assumption
- This is what you test FIRST, not what's easy to build

**Example assumptions to question:**
- "Customers will pay $X/month for this"
- "Customers experience this problem frequently enough to care"
- "Our target customer segment is reachable through [channel]"
- "Users will change their existing behavior to use our product"
- "The unit economics work at our target scale"

## Step 2: Design Your Minimum Viable Product (MVP)

An MVP is not a simple version of the product. It is the minimum experiment needed to test your riskiest assumption.

**2a. The MVP decision framework**
- What is the minimum we need to build to test the assumption?
- What is NOT in the MVP? (Equally important question)
- How will we measure whether the assumption is true or false?
- What decision will we make based on the result?

**2b. MVP types by assumption type**

| Assumption | MVP Type | How It Works |
|------------|---------|-------------|
| "People want this" | Landing page | Build the marketing page, measure sign-ups |
| "People will pay for this" | Concierge MVP | Deliver manually what the software would do |
| "People will use this regularly" | Wizard of Oz | Human runs the "automation" behind the scenes |
| "People can figure out how to use this" | Prototype test | Clickable prototype + 5 user interviews |
| "This channel converts customers" | Paid acquisition test | Run ads to a landing page, measure conversion |

**2c. The concierge MVP in detail**
- Provide the service manually to your first 10-50 customers
- You learn: what they actually want, what causes friction, what drives value
- Only automate after you understand the manual version deeply
- Example: Airbnb's founders photographed apartments themselves before building the photo product

## Step 3: Measure with Actionable Metrics

Vanity metrics look good but don't help you make decisions. Actionable metrics connect to real business behavior.

**3a. The three A's of good metrics**
- **Actionable**: if the number changes, you know what you changed that caused it
- **Accessible**: the metric is easy to understand and available to everyone on the team
- **Auditable**: you can verify the data is correct by checking it against real customer behavior

**3b. Vanity vs. actionable metrics**

| Vanity Metric | Why It's Misleading | Actionable Alternative |
|---------------|--------------------|-----------------------|
| Total registered users | Includes inactive, churned users | Monthly active users (MAU) |
| Page views | Could be bots or single curious visitors | Session time + return visit rate |
| Gross revenue | Hides COGS and unit economics | Gross margin, CAC, LTV |
| Downloads | Doesn't measure engagement | DAU, D1 retention |
| "Engagement" | Undefined, unfalsifiable | Actions per session that correlate with retention |

**3c. Cohort analysis**
- Do not analyze customers as a single group — analyze by cohort (when they signed up)
- A growing user base can mask declining retention if older cohorts churn faster than new ones arrive
- If cohort analysis shows flat or worsening retention over time, you have a fundamental problem

## Step 4: Innovation Accounting

Innovation accounting replaces traditional business metrics for early-stage work, where the numbers are too small to be meaningful in isolation.

**4a. Three milestones**
1. **Establish baseline**: run your MVP and measure where you actually are
2. **Tune the engine**: systematically improve one metric at a time
3. **Pivot or persevere**: is the rate of improvement fast enough to reach the business hypothesis?

**4b. The dashboard**
Define 3-5 metrics that, together, tell the story of whether your business model is working:
- Acquisition: how many people are finding you?
- Activation: how many have a positive first experience?
- Retention: how many come back?
- Revenue: how many pay you?
- Referral: how many refer others?

This is the AARRR (Pirate Metrics) framework — pick the 1-2 that matter most for your current stage.

**4c. Setting a threshold**
- Before an experiment, define: "If we see X result, we'll persevere. If we see Y result, we'll pivot."
- This prevents post-hoc rationalization of ambiguous results
- Example: "If 15%+ of landing page visitors sign up for beta access, we'll proceed to build the MVP"

## Step 5: The Pivot-or-Persevere Decision

**5a. When to pivot**
- You've run 3+ experiments on the same assumption and haven't moved the metric
- The rate of improvement is too slow to reach your business hypothesis in a reasonable timeframe
- Customer interviews reveal that your assumption was fundamentally wrong

**5b. Types of pivots**

| Pivot Type | What Changes | Example |
|------------|-------------|---------|
| Zoom-in | One feature becomes the whole product | Twitter was a feature of Odeo (podcasting) |
| Zoom-out | The product becomes a feature of a larger product | Instagram was a checkin app; photos were a feature |
| Customer segment | Same product, different target customer | Your power users are not who you originally targeted |
| Customer need | Same customer, different problem to solve | The customer exists but this isn't their real pain |
| Platform | Application → platform; platform → application | |
| Business architecture | High-margin/low-volume ↔ Low-margin/high-volume | |
| Channel | Change how you reach customers | Direct sales → channel partners |

**5c. Persevere criteria**
- The engine of growth is working, but slowly
- Each experiment moves the metric in the right direction
- You understand why it's slow and have a plan to accelerate

## Step 6: Validated Learning Documentation

Document each experiment formally to prevent learning loss.

**Experiment template:**
```
EXPERIMENT: [Name]
DATE: [Date range]
HYPOTHESIS: We believe [assumption] is true because [reasoning].
TEST: We will [action] and measure [metric].
CRITERIA: If we see [threshold result], the hypothesis is validated.
RESULTS: We observed [actual result].
LEARNING: [What we now know, including what was surprising]
DECISION: Persevere / Pivot (type) / Explore further
```

Maintain a library of past experiments. They are the institutional knowledge of what you've learned.

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Building too much before testing | Months wasted on wrong direction | Define MVP as minimum to test the assumption, not minimum viable product |
| Measuring vanity metrics | False confidence, wrong decisions | Define actionable metrics with clear decision thresholds before experiments |
| Too short experiment duration | Insufficient data, misleading results | Most experiments need 2-4 weeks minimum |
| Not defining pivot criteria in advance | Post-hoc rationalization of failure | Write "if X then pivot, if Y then persevere" before you see results |
| Pivoting too often | Never learn anything deeply | A pivot should follow a failed validated learning attempt, not just impatience |

## Quick-Start Checklist

- [ ] Riskiest assumption identified (high-criticality × high-uncertainty)
- [ ] MVP type chosen to test the assumption (landing page, concierge, wizard-of-oz)
- [ ] 3-5 actionable metrics defined (not vanity metrics)
- [ ] Pivot/persevere threshold defined in advance (specific numbers)
- [ ] Experiment template completed before starting
- [ ] Experiment duration defined (minimum 2 weeks)
- [ ] Cohort analysis set up (not just aggregate metrics)
- [ ] Customer interview schedule set (5+ interviews per experiment round)
- [ ] Experiment results documented in the learning library
