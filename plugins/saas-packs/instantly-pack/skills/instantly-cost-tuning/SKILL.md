---
name: instantly-cost-tuning
description: |
  Optimize Instantly costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Instantly billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "instantly cost", "instantly billing",
  "reduce instantly costs", "instantly pricing", "instantly expensive", "instantly budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Instantly Cost Tuning

## Overview
Optimize Instantly email outreach costs by managing sending account count, right-sizing your plan tier, and maximizing deliverability (which is the core ROI metric). Instantly pricing combines per-seat costs with sending volume tiers (Growth: 5K leads/month, Hypergrowth: 25K leads/month, Light Speed: 100K leads/month). The biggest cost lever is improving deliverability -- a well-warmed account sending 50 emails/day with 40% open rate outperforms 3 accounts sending 200 emails/day with 10% open rate, at 1/3 the cost.

## Prerequisites
- Instantly workspace admin access
- Sending account reputation data
- Campaign performance analytics

## Instructions

### Step 1: Audit Account Efficiency
```bash
# Check per-account performance
curl "https://api.instantly.ai/api/v1/account/status" \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq '.accounts[] | {
    email, daily_limit, sent_today,
    reputation_score, warmup_status,
    effective_sends: (.sent_today * .reputation_score / 100)
  }' | jq -s 'sort_by(-.effective_sends)'
# Accounts with low reputation are wasting sends (emails go to spam)
```

### Step 2: Consolidate Sending Accounts
```yaml
# Before: 10 accounts, each sending 30 emails/day = 300 sends/day
# Problem: 4 accounts have <50 reputation score (emails going to spam)
current:
  accounts: 10
  effective_sends_per_day: 180  # Only 6 accounts delivering well
  monthly_cost: "$97/month per account subscription"

optimized:
  accounts: 6               # Remove low-reputation accounts
  effective_sends_per_day: 180  # Same effective volume
  monthly_cost: "58% of original"
```

### Step 3: Optimize Warmup Strategy
```yaml
# Proper warmup maximizes deliverability, which maximizes ROI
warmup_best_practices:
  new_account:
    week_1: 5 emails/day      # Start very low
    week_2: 15 emails/day
    week_3: 30 emails/day
    week_4: 50 emails/day     # Full sending capacity
    total_warmup: 28 days

  # Don't rush warmup to save time -- a burnt account costs more to replace
  # than 4 weeks of gradual warmup

  monitoring:
    check_daily: reputation_score
    pause_if: reputation_score < 60
    reduce_volume_if: bounce_rate > 3%
```

### Step 4: Right-Size Your Plan
```yaml
# Plan selection based on actual sending needs
growth_plan:
  leads: 5000/month
  best_for: "Small team, 1-2 SDRs, testing campaigns"
  cost: "$37/month"

hypergrowth_plan:
  leads: 25000/month
  best_for: "Active outbound team, 3-5 SDRs"
  cost: "$97/month"
  tip: "Only upgrade when Growth plan consistently hits >80% lead capacity"

# Calculate: if you're on Hypergrowth but only importing 3K leads/month,
# switch to Growth and save $60/month
```

### Step 5: Improve Reply Rate (Best ROI Optimization)
```yaml
# The highest ROI optimization is improving reply rate, not sending more emails
optimization_priority:
  1_clean_lead_lists:
    action: "Verify emails before importing"
    impact: "Reduces bounces, protects reputation, fewer wasted sends"
  2_personalize_sequences:
    action: "Use merge tags and custom variables"
    impact: "2-3x reply rate improvement"
  3_optimize_sending_schedule:
    action: "Send Tuesday-Thursday 9-11am recipient timezone"
    impact: "20-30% better open rates"
  4_a_b_test_subject_lines:
    action: "Test 2-3 variants per campaign"
    impact: "10-20% open rate improvement"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Paying for unused sending capacity | Plan oversized for actual volume | Downgrade plan tier |
| Low ROI per dollar spent | Poor deliverability | Fix warmup, clean lists, improve personalization |
| Account costs without results | Account reputation too low | Pause account, rewarm or replace domain |
| High bounce rate | Unverified lead lists | Use email verification before import |

## Examples
```bash
# Quick ROI calculator
echo "Monthly cost: \$97 (Hypergrowth)"
echo "Leads contacted: 5000"
echo "Reply rate: 3%"
echo "Replies: 150"
echo "Cost per reply: \$0.65"
echo "If you improve reply rate to 5%: replies=250, cost/reply=\$0.39 (40% better ROI)"
```
