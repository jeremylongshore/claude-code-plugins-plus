# klingai-cost-controls

> Implement cost controls and budget management

## Directory Structure

```
klingai-cost-controls/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 budget_enforcer.py      # Budget enforcement logic
    ├── 🐍 cost_alerting.py        # Cost threshold alerts
    └── 🐍 spend_dashboard.py      # Spending dashboard
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with cost control strategies |
| `budget_enforcer.py` | 🐍 Python | Enforce spending limits |
| `cost_alerting.py` | 🐍 Python | Alert on cost thresholds |
| `spend_dashboard.py` | 🐍 Python | Visualize spending patterns |

## Summary

**Category:** enterprise
**Target Audience:** Finance or operations lead
**Trigger Phrases:** `klingai budget`, `kling ai cost control`, `limit klingai spending`, `klingai cost management`

### What This Skill Does

This skill implements cost controls and budget management for Kling AI. It covers:

- Budget limit configuration
- Real-time spend tracking
- Alert thresholds (50%, 75%, 90%, 100%)
- Automatic generation blocking on budget exceeded
- Cost allocation by team/project
- Forecasting and trend analysis

### Technical Success Criteria

- Budget enforcement preventing overruns
- Alerting on threshold breaches
- Cost allocation tracking

### Business Success Criteria

- Controlled spending within approved limits
- Predictable monthly costs
- Clear cost visibility for stakeholders

## Related Skills

- `klingai-pricing-basics` - Understanding costs
- `klingai-team-setup` - Per-team budgets
- `klingai-usage-analytics` - Cost analytics
