# perplexity-cost-controls

> Implement cost controls and budget management

## Directory Structure

```
perplexity-cost-controls/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── budget_manager.py       # Budget enforcement logic
    ├── cost_alerts.py          # Cost alert notifications
    ├── spending_limits.yaml    # Spending limit configuration
    └── cost_report.py          # Generate cost reports
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with cost control patterns |
| `budget_manager.py` | Python | Enforce spending limits |
| `cost_alerts.py` | Python | Alert on spending thresholds |
| `spending_limits.yaml` | YAML | Define spending limits and budgets |
| `cost_report.py` | Python | Generate cost analysis reports |

## Summary

**Category:** enterprise
**Target Audience:** Finance or operations lead
**Trigger Phrases:** `perplexity budget`, `perplexity spending`, `control perplexity cost`, `perplexity limits`

### What This Skill Does

This skill teaches cost control for Perplexity:

- Setting budget limits and alerts
- Implementing spending caps
- Per-team or per-project budgets
- Cost allocation and chargeback
- Spending forecasting

### Technical Success Criteria

- Budget enforcement preventing overruns
- Alerts triggered at thresholds
- Usage properly allocated

### Business Success Criteria

- Controlled spending within approved limits
- Clear cost visibility and accountability
- Predictable monthly costs

## Related Skills

- `perplexity-pricing-usage` - Understanding pricing
- `perplexity-usage-analytics` - Usage data for budgeting
- `perplexity-caching-strategy` - Reduce costs through caching
