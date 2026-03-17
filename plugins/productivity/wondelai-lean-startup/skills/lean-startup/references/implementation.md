# Lean Startup -- Build-Measure-Learn Implementation Guide

## Overview

Apply Eric Ries's Lean Startup methodology (Build-Measure-Learn, validated learning, innovation accounting) to systematically test assumptions and avoid building products nobody wants.

## The Build-Measure-Learn Loop

```
                  BUILD
                 /     \
           IDEAS         PRODUCT
                          |
    LEARN                MEASURE
     \                   /
      DATA  <----------
```

## Step 1: Identify Leap-of-Faith Assumptions

Before building, identify what must be true for the business to work.

```markdown
## Assumption Mapping

Business model assumption:
"Customers will pay $___ per month for ___"

Value hypothesis (do customers want this?):
"[Persona] will prefer [our solution] over [current alternative] because ___"

Growth hypothesis (how will it spread?):
"New customers will come through [viral / paid / sticky] because ___"

Riskiest assumption: ___ (test this first)
```

## Step 2: Design the Minimum Viable Experiment

```markdown
## Experiment Card

Assumption being tested: ___
Type of experiment: [Landing page / Wizard of Oz / Concierge / Survey / A/B test]

Hypothesis statement:
"We believe [assumption].
We will know this is true when [metric] reaches [threshold]
within [time period]."

Success metric: ___  Target: ___
Failure condition: ___
```

## MVP Types

| Type | Description | When to Use |
|------|-------------|-------------|
| Landing page | Measure demand before building | Pre-product |
| Concierge | Manually deliver the service | Validate value |
| Wizard of Oz | Fake automated backend | Validate UX |
| Piecemeal | Combine existing tools (Zapier) | Fast validation |
| Single-feature | Build one core feature only | Post-launch |

## Step 3: Innovation Accounting

Track leading indicators, not vanity metrics.

```markdown
## Metric Audit

Vanity metrics (avoid as success criteria):
- Total signups, total pageviews, total downloads

Actionable metrics (use these):
- Activation rate: % who complete key action after signup
- Retention rate: % returning after 1/7/30 days
- Referral rate: new users from existing users per month
- Revenue per user

Baseline -> Target for this sprint:
Metric: ___  Baseline: ___  Target: ___  Deadline: ___
```

## Step 4: Pivot or Persevere Decision

```markdown
## Pivot Criteria

Persevere if:
- Core metric is improving week-over-week
- Users say problem is painful AND solution is good
- Learning confirmed the hypothesis

Consider pivoting if (after 3+ iterations):
- Core metric is flat or declining
- Users find workarounds rather than using your solution
- Same retention/activation issues despite multiple changes

Pivot options:
- Zoom-in: One feature becomes the product
- Zoom-out: Feature becomes one part of larger product
- Customer segment: Same product, different target
- Platform: Switch from app to API (or vice versa)
- Business architecture: High margin <-> High volume switch
```

## Validated Learning Log

```markdown
| Sprint | Assumption Tested | Metric | Result | Learning | Decision |
|--------|------------------|--------|--------|----------|----------|
| 1 | ___ | ___ | ___ | ___ | Persevere/Pivot |
| 2 | ___ | ___ | ___ | ___ | ___ |
```

## References

- Ries, E. (2011). *The Lean Startup.* Crown Business.
- Ries, E. (2017). *The Startup Way.*
