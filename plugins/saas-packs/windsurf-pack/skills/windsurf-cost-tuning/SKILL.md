---
name: windsurf-cost-tuning
description: |
  Optimize Windsurf costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Windsurf billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "windsurf cost", "windsurf billing",
  "reduce windsurf costs", "windsurf pricing", "windsurf expensive", "windsurf budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Windsurf Cost Tuning

## Overview
Optimize Windsurf AI IDE licensing costs by right-sizing seat allocation and matching plan tiers to actual AI feature usage. Windsurf charges per seat with different tiers offering different AI capabilities (Free: basic completions, Pro: Cascade + Supercomplete + Command). The primary cost lever is ensuring every Pro seat is actively used -- a developer averaging <5 AI interactions per day may not justify the Pro tier cost.

## Prerequisites
- Windsurf Admin dashboard access
- Team usage analytics data
- Understanding of which AI features each team member uses

## Instructions

### Step 1: Audit Seat Utilization
```yaml
# Seat utilization analysis from Admin Dashboard > Analytics
seat_audit:
  total_pro_seats: 20
  high_usage:  8    # >20 AI interactions/day (power users)
  medium_usage: 5   # 5-20 interactions/day (regular users)
  low_usage: 4      # 1-5 interactions/day (occasional)
  inactive: 3       # <1 interaction/day (wasting money)

# Action: Downgrade 3 inactive seats to Free = immediate savings
# Action: Review 4 low-usage seats -- offer training or downgrade
```

### Step 2: Match Features to Needs
```yaml
# Not everyone needs the same tier
seat_allocation:
  full_time_developers:
    tier: Pro
    features_used: [cascade, supercomplete, command, inline_chat]
    justification: "Core workflow, high ROI"

  code_reviewers:
    tier: Free (or basic)
    features_needed: [supercomplete]  # Occasional completions only
    justification: "Reading code more than writing"

  designers_with_code:
    tier: Free
    features_needed: []  # Rarely use AI features
    justification: "Mainly CSS/HTML, AI less useful"

  contractors_short_term:
    tier: Free
    justification: "Temporary, not worth Pro investment"
```

### Step 3: Track ROI per Seat
```typescript
// Measure productivity impact to justify costs
function calculateSeatROI(member: { completionsAccepted: number; cascadeFlows: number; hoursSaved: number }) {
  const seatCostPerMonth = 25; // Pro tier
  const hourlyRate = 75; // Developer hourly rate
  const moneySaved = member.hoursSaved * hourlyRate;
  const roi = (moneySaved - seatCostPerMonth) / seatCostPerMonth * 100;
  return { moneySaved, roi: `${roi.toFixed(0)}% ROI` };
}
// If ROI < 0%, seat is costing more than it saves
```

### Step 4: Negotiate Enterprise Pricing
```yaml
# Volume discounts for larger teams
negotiation_tips:
  - threshold: 20+ seats
    action: "Request volume discount (typically 15-20% off list)"
  - threshold: 50+ seats
    action: "Request enterprise tier with custom pricing"
  - annual_vs_monthly: "Annual commitment typically saves 15-20%"
  - bundling: "Bundle with other Codeium products for better rates"
```

### Step 5: Quarterly Review Cycle
```yaml
# Implement quarterly seat optimization review
quarterly_review:
  step_1: "Export usage analytics from Admin Dashboard"
  step_2: "Identify seats with <5 interactions/day for 60+ days"
  step_3: "Survey low-usage members: need training or not useful?"
  step_4: "Downgrade or remove underperforming seats"
  step_5: "Reallocate freed seats to new team members or save costs"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Paying for unused Pro seats | No utilization monitoring | Implement quarterly seat reviews |
| Developer resistance to downgrade | Perceived loss of tool | Show usage data, offer training first |
| Cannot track usage | Admin analytics not enabled | Contact Windsurf support for enterprise analytics |
| Cost growing with team | No seat approval process | Require manager approval for new Pro seats |

## Examples
```yaml
# Cost optimization example
before:
  pro_seats: 20
  monthly_cost: "$500" # 20 * $25
after_optimization:
  pro_seats: 13  # Removed 3 inactive, downgraded 4 low-usage
  monthly_cost: "$325"
  annual_savings: "$2,100"
```
