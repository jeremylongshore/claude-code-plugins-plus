# perplexity-monitoring-alerts

> Set up monitoring and alerting for Perplexity operations

## Directory Structure

```
perplexity-monitoring-alerts/
├── SKILL.md                    # Main skill definition with YAML frontmatter
└── examples/                   # Optional examples directory
    ├── metrics_collector.py    # Collect operational metrics
    ├── alert_rules.yaml        # Alert rule definitions
    ├── grafana_dashboard.json  # Grafana dashboard template
    └── pagerduty_config.yaml   # PagerDuty integration
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | Markdown | Skill definition with monitoring patterns |
| `metrics_collector.py` | Python | Collect and export metrics |
| `alert_rules.yaml` | YAML | Alert rule definitions and thresholds |
| `grafana_dashboard.json` | JSON | Pre-built Grafana dashboard |
| `pagerduty_config.yaml` | YAML | PagerDuty alert routing |

## Summary

**Category:** cicd
**Target Audience:** DevOps engineer
**Trigger Phrases:** `perplexity monitoring`, `perplexity alerts`, `monitor perplexity`, `perplexity dashboard`

### What This Skill Does

This skill teaches monitoring for Perplexity operations:

- Collecting API metrics (latency, errors, usage)
- Setting up alert thresholds
- Building operational dashboards
- Integrating with alerting systems
- SLA monitoring

### Technical Success Criteria

- Proactive monitoring with actionable alerts
- Key metrics captured and visualized
- Alert routing configured correctly

### Business Success Criteria

- Early detection of issues
- Reduced mean time to detection (MTTD)
- SLA compliance monitoring

## Related Skills

- `perplexity-debug-logging` - Logging for investigation
- `perplexity-usage-analytics` - Usage analysis
- `perplexity-prod-checklist` - Monitoring as readiness item
