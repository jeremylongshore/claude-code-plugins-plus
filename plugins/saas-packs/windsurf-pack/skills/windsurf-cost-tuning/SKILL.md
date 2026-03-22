---
name: windsurf-cost-tuning
description: |
  Optimize Windsurf licensing costs through seat management, tier selection, and credit monitoring.
  Use when analyzing Windsurf billing, reducing per-seat costs,
  or implementing usage monitoring and budget controls.
  Trigger with phrases like "windsurf cost", "windsurf billing",
  "reduce windsurf costs", "windsurf pricing", "windsurf budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, cost-optimization, licensing, teams]

---
# Windsurf Cost Tuning

## Overview
Optimize Windsurf AI IDE licensing costs by right-sizing seat allocation, matching plan tiers to actual usage, and monitoring credit consumption. Windsurf charges per seat with different tiers offering different AI capabilities.

## Prerequisites
- Windsurf Admin dashboard access (Teams or Enterprise)
- Team usage data (at least 30 days)
- Understanding of team roles and AI usage patterns

## Instructions

### Step 1: Understand the Pricing Model

| Plan | Price | Credits/mo | Key Features |
|------|-------|-----------|-------------|
| Free | $0 | 25 | SWE-1 Lite unlimited, basic Supercomplete |
| Pro | $15/mo | 500 | All models, Cascade Write, Previews, 5 deploys/day |
| Teams | $30/user/mo | 500/user | Admin controls, shared billing, analytics |
| Enterprise | Custom ($60+/user) | Custom | SSO, RBAC, audit, self-hosted option |

Annual commitment typically saves 15-20% over monthly billing.

### Step 2: Audit Seat Utilization

```yaml
# Export from Admin Dashboard > Analytics > Member Usage
seat_audit:
  total_pro_seats: 20

  high_usage: 8         # >20 Cascade interactions/day — power users
  medium_usage: 5       # 5-20 interactions/day — regular users
  low_usage: 4          # 1-5 interactions/day — occasional users
  inactive: 3           # <1 interaction/day — wasting money

  monthly_cost: 600     # 20 x $30/seat
  wasted_on_inactive: 90  # 3 x $30/seat

  actions:
    - Downgrade 3 inactive seats to Free (save $90/mo)
    - Offer training to 4 low-usage users
    - Review low users after 30 days — downgrade if still low
```

### Step 3: Match Tier to Role

```yaml
# Not every team member needs the same tier
seat_allocation:
  full_time_developers:
    tier: Pro or Teams
    features_used: [cascade_write, supercomplete, command, previews]
    justification: "Core workflow, high ROI"

  code_reviewers:
    tier: Free
    features_needed: [supercomplete]
    justification: "Reading more than writing, occasional completions"

  designers:
    tier: Free
    features_needed: []
    justification: "Mainly CSS/HTML, AI less impactful"

  contractors_short_term:
    tier: Free
    justification: "Temporary, not worth Pro investment"

  tech_leads:
    tier: Pro
    features_used: [cascade_chat, code_review]
    justification: "Architecture questions, PR review assistance"
```

### Step 4: Calculate ROI per Seat

```typescript
function calculateSeatROI(member: {
  monthlyCreditsUsed: number;
  cascadeTasksCompleted: number;
  estimatedHoursSaved: number;
}) {
  const seatCostPerMonth = 30; // Teams tier
  const hourlyRate = 75; // Average developer hourly rate
  const moneySaved = member.estimatedHoursSaved * hourlyRate;
  const roi = ((moneySaved - seatCostPerMonth) / seatCostPerMonth) * 100;

  return {
    moneySaved: `$${moneySaved}`,
    roi: `${roi.toFixed(0)}%`,
    verdict: roi > 0 ? "KEEP" : "REVIEW",
  };
}

// Example: Developer saves 2 hours/month with Cascade
// ROI = ((2 * $75) - $30) / $30 * 100 = 400% ROI
// Clearly worth it.

// Example: Designer uses Supercomplete once/week
// ROI = ((0.25 * $75) - $30) / $30 * 100 = -37% ROI
// Switch to Free tier.
```

### Step 5: Credit Conservation Strategies

```markdown
## Reduce Credit Burn Without Reducing Productivity

1. Use SWE-1 Lite for simple tasks (0 credits)
   - Quick syntax questions
   - Simple explanations
   - Basic code navigation help

2. Write better prompts (fewer retries = fewer credits)
   - Include file paths, constraints, expected output
   - Use @ mentions for context
   - One comprehensive prompt > five vague ones

3. Use Workflows for repetitive tasks
   - Build once, run many times
   - More efficient than ad-hoc Cascade conversations

4. Leverage free features
   - Supercomplete (Tab): unlimited on all plans
   - Command mode (Cmd+I): unlimited on Pro
   - Workspace rules: improve output without extra prompts

5. Team training
   - Developers who know Windsurf well use fewer credits
   - Share effective prompt examples
   - Demonstrate workflow creation
```

### Step 6: Implement Quarterly Review Cycle

```yaml
quarterly_review:
  week_1: "Export usage analytics from Admin Dashboard"
  week_2: "Identify seats with <5 interactions/day for 60+ days"
  week_3: "Survey low-usage members: need training or not useful?"
  week_4: "Execute changes: downgrade, reallocate, or train"

negotiation_tips:
  20_plus_seats: "Request 15-20% volume discount"
  50_plus_seats: "Negotiate enterprise tier with custom pricing"
  annual_commitment: "15-20% savings over monthly"
  competing_tools: "Mention Cursor/Copilot pricing for leverage"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Paying for unused seats | No utilization monitoring | Quarterly seat audit |
| Dev resistance to downgrade | Perceived loss of tools | Show usage data, offer training |
| Can't track usage | Analytics not enabled | Contact Windsurf for admin API access |
| Costs growing with team | No seat approval process | Require manager approval for new Pro seats |
| Credits exhausted mid-sprint | No monitoring | Set credit usage alerts in admin dashboard |

## Examples

### Quick Cost Analysis
```bash
echo "Monthly cost estimate:"
echo "Pro seats: $PRO_COUNT x \$15 = \$(($PRO_COUNT * 15))"
echo "Team seats: $TEAM_COUNT x \$30 = \$(($TEAM_COUNT * 30))"
echo "Free seats: $FREE_COUNT x \$0 = \$0"
```

### Free Features Checklist
```
These features are FREE (no credits) on all plans:
- Supercomplete (Tab completions)
- .windsurfrules (AI context)
- .codeiumignore (indexing control)
- .windsurf/rules/ (workspace rules)
- Cascade Memories (persistent context)
- Extension support (VS Code compatible)
```

## Resources
- [Windsurf Pricing](https://windsurf.com/pricing)
- [Windsurf Admin Guide](https://docs.windsurf.com/windsurf/guide-for-admins)

## Next Steps
For architecture planning, see `windsurf-reference-architecture`.
