# openrouter-usage-analytics

> Build usage analytics and reporting for OpenRouter

## Directory Structure

```
openrouter-usage-analytics/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 analytics_collector.py  # Collect usage data
    ├── 🐍 report_generator.py     # Generate analytics reports
    └── 🐍 dashboard_api.py        # Dashboard data API
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with analytics implementation guide |
| `analytics_collector.py` | 🐍 Python | Collect and store usage metrics |
| `report_generator.py` | 🐍 Python | Generate scheduled reports |
| `dashboard_api.py` | 🐍 Python | API for dashboard visualizations |

## Summary

**Category:** enterprise
**Target Audience:** Data analyst or operations
**Trigger Phrases:** `openrouter analytics`, `openrouter usage`, `openrouter reports`, `openrouter metrics`

### What This Skill Does

This skill builds usage analytics and reporting for OpenRouter operations. It covers:

- Usage data collection and storage
- Key metrics (requests, tokens, models, costs)
- Model usage distribution
- Trend analysis and visualization
- Scheduled report generation
- Export and integration with BI tools

### Technical Success Criteria

- Comprehensive usage metrics and dashboards
- Automated report generation
- Historical trend analysis

### Business Success Criteria

- Data-driven optimization of AI operations
- Clear visibility for stakeholders
- Usage patterns informing decisions

## Related Skills

- `openrouter-cost-controls` - Cost analytics
- `openrouter-debug-bundle` - Usage from logs
- `openrouter-audit-logging` - Detailed usage logs
