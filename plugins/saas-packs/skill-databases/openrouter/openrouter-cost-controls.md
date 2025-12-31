# openrouter-cost-controls

> Implement cost controls and budget management for OpenRouter

## Directory Structure

```
openrouter-cost-controls/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 budget_manager.py       # Budget enforcement and tracking
    ├── 🐍 alert_service.py        # Cost threshold alerting
    └── ⚙️ budget_config.yaml      # Budget policies and limits
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with cost control patterns |
| `budget_manager.py` | 🐍 Python | Per-key and per-user budget enforcement |
| `alert_service.py` | 🐍 Python | Threshold alerts via email/Slack/webhook |
| `budget_config.yaml` | ⚙️ YAML | Budget limits, alert thresholds, policies |

## Summary

**Category:** enterprise
**Target Audience:** Finance or operations lead
**Trigger Phrases:** `openrouter budget`, `openrouter cost control`, `openrouter spending limit`, `openrouter alerts`

### What This Skill Does

This skill implements comprehensive cost controls for OpenRouter:

- Per-key credit limits and enforcement
- Per-user and per-team budget tracking
- Alert thresholds at configurable levels
- Hard limits preventing overruns
- Cost attribution and chargeback reports

### Technical Success Criteria

- Hard spending limits enforced automatically
- Alerts triggered at configured thresholds
- Usage tracked and attributed per key/user

### Business Success Criteria

- No unexpected budget overruns
- Predictable monthly costs
- Cost attribution to teams/projects

## Related Skills

- `openrouter-usage-analytics` - Usage tracking and reporting
- `openrouter-pricing-basics` - Cost estimation
- `openrouter-team-setup` - Multi-user configuration
