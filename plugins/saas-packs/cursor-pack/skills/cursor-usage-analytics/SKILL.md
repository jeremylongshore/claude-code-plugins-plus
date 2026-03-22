---
name: "cursor-usage-analytics"
description: |
  Track and analyze Cursor usage metrics via admin dashboard: requests, model usage, team productivity,
  and cost optimization. Triggers on "cursor analytics", "cursor usage", "cursor metrics",
  "cursor reporting", "cursor dashboard", "cursor ROI".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
tags: [saas, cursor, analytics, dashboard]

---
# Cursor Usage Analytics

Track and analyze Cursor usage metrics for Business and Enterprise plans. Covers dashboard metrics, cost optimization, adoption tracking, and ROI measurement.

## Admin Dashboard Overview

Access: [cursor.com/settings](https://cursor.com/settings) > Team > Usage (Business/Enterprise only)

```
┌─ Dashboard ────────────────────────────────────────────┐
│                                                        │
│  Total Requests This Month:  12,847                    │
│  Fast Requests Remaining:    2,153 / 15,000            │
│  Active Users:               28 / 30 seats             │
│  Most Used Model:            Claude Sonnet (62%)       │
│                                                        │
│  ┌─ Usage Trend ─────────────────────────────────┐     │
│  │  ▆▆▇▇██▇▆▇█▇▇▆▅                              │     │
│  │  Mon Tue Wed Thu Fri Sat Sun                   │     │
│  └───────────────────────────────────────────────┘     │
│                                                        │
│  ┌─ Top Users ───────────────────────────────────┐     │
│  │  alice@co.com     847 requests  (Sonnet)      │     │
│  │  bob@co.com       623 requests  (GPT-4o)      │     │
│  │  carol@co.com     591 requests  (Auto)        │     │
│  └───────────────────────────────────────────────┘     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Key Metrics

### Request Metrics

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Total requests | All AI interactions (Chat, Composer, Inline Edit) | Growing month-over-month |
| Fast requests | Premium model uses (count against quota) | Stay under monthly limit |
| Slow requests | Queued requests after quota exceeded | Minimize (upgrade if high) |
| Tab acceptances | How often Tab suggestions are accepted | 30-50% acceptance rate is healthy |

### User Adoption Metrics

| Metric | Healthy | Needs Attention |
|--------|---------|-----------------|
| Weekly active users | 80%+ of seats | Below 50% of seats |
| Requests per user/day | 5-20 | Below 3 (underutilization) |
| Users with 0 requests (30d) | 0-10% of seats | Above 20% (wasted seats) |
| Model diversity | 2-3 models used | Single model only |

### Cost Metrics

| Metric | Calculation |
|--------|-------------|
| Cost per seat | Plan price / active users |
| Cost per request | Total spend / total requests |
| BYOK costs | Sum of API provider invoices |
| Total AI spend | Cursor subscription + BYOK costs |

## Quota Management

### Fast Request Quota

Each team member gets ~500 fast requests per month (varies by plan). Fast requests are consumed when using premium models (Claude Sonnet/Opus, GPT-4o, o1, etc.).

When quota is exceeded:
- Requests are queued as "slow" (may take 30-60 seconds instead of 5-10)
- Tab completion is unaffected
- cursor-small model remains fast

### Strategies to Stay Under Quota

```
1. Default to Auto mode
   - Cursor routes simple queries to cheaper models
   - Only uses premium models when complexity warrants it

2. Educate team on model selection
   - Simple questions → cursor-small or GPT-4o-mini
   - Standard coding → GPT-4o or Claude Sonnet
   - Hard problems only → Claude Opus, o1 (these burn quota fast)

3. Reduce round-trips
   - Write detailed prompts (fewer back-and-forth turns)
   - Use @Files instead of @Codebase (less context = faster)
   - Start new chats instead of continuing stale ones

4. BYOK for power users
   - Heavy users can use their own API keys
   - Their requests don't count against team quota
```

## Reporting for Stakeholders

### Monthly Report Template

```markdown
# Cursor Usage Report - [Month Year]

## Summary
- Active users: X / Y seats (X% utilization)
- Total AI requests: X,XXX
- Fast request quota usage: XX%
- Monthly cost: $X,XXX

## Adoption Trends
- New users onboarded: X
- Users showing increased usage: X
- Inactive users (0 requests): X

## Model Usage Distribution
- Claude Sonnet: XX%
- GPT-4o: XX%
- Auto: XX%
- Other: XX%

## Recommendations
- [Scale / optimize / train based on data]
```

### ROI Calculation

```
Time saved per developer per day:         ~1 hour (conservative estimate)
Working days per month:                   22
Developer hourly cost (fully loaded):     $75
Monthly time savings per developer:       22 hours × $75 = $1,650

Cursor cost per developer:                $40/month (Business)
ROI per developer:                        $1,650 - $40 = $1,610/month
ROI multiple:                             41x

Break-even: developer saves >32 minutes/month
```

**Note:** Actual time savings vary. Track team velocity (story points, PRs merged, cycle time) before and after Cursor adoption for data-driven ROI.

## Usage Optimization Playbook

### For Underutilized Teams (< 5 requests/user/day)

```
1. Run team training session (30 min demo of Chat + Composer)
2. Share the cursor-hello-world skill for hands-on practice
3. Create project rules (.cursor/rules/) so AI gives better results
4. Assign "AI Champion" per team to share tips and answer questions
5. Set a 30-day adoption goal and review progress
```

### For Overutilized Teams (quota consistently exceeded)

```
1. Review model usage -- are users defaulting to expensive models?
2. Enable Auto mode as team default
3. Train on efficient prompting (fewer turns = fewer requests)
4. Consider BYOK for top 5 users (offloads their usage from team quota)
5. Evaluate upgrading to more seats or Enterprise plan
```

### For Inconsistent Usage

```
1. Check if project rules are configured (AI is less useful without them)
2. Verify indexing works (poor @Codebase = poor experience)
3. Look for extension conflicts (GitHub Copilot still enabled?)
4. Survey team for friction points and address them
```

## Enterprise Considerations

- **Advanced analytics**: Enterprise plans include detailed per-user, per-model, per-project breakdowns
- **API access**: Programmatic access to usage data for integration with internal dashboards (Enterprise)
- **Compliance reporting**: Usage logs can support audit requirements (who used AI, when, which model)
- **Cost allocation**: Tag usage by team/project for internal chargeback accounting

## Resources

- [Cursor Admin Dashboard](https://cursor.com/settings)
- [Cursor Pricing](https://cursor.com/pricing)
- [Cursor Enterprise](https://cursor.com/enterprise)
