# retellai-observability

> Set up comprehensive observability with call metrics, latency tracking, and alerting rules

## Directory Structure

```
retellai-observability/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for observability implementation |
| examples/example.py | Python | Example metrics collection and alerting configuration |

## Summary

**Category:** enterprise
**Target Audience:** SREs, DevOps engineers, Platform engineers
**Trigger Phrases:** `retell monitoring`, `retell metrics`, `retell observability`, `monitor retell`, `retell alerts`

### What This Skill Does

This skill sets up comprehensive observability for Retell AI voice agents. It covers collecting call metrics (duration, completion rate, latency), implementing distributed tracing for call flows, structured logging for debugging, alerting rules for anomaly detection, and dashboard creation for operational visibility.

### Technical Success Criteria

- Call metrics collection enabled
- Latency tracking for voice response times
- Structured logging implemented
- Alert rules deployed to PagerDuty/Slack
- Dashboards created in Grafana/DataDog

### Business Success Criteria

- Faster incident detection
- Improved MTTR for voice issues
- <5 minute detection time for Retell AI-related incidents

## Related Skills

- retellai-incident-runbook - Incident response
- retellai-call-analytics - Business metrics
- retellai-advanced-troubleshooting - Deep debugging
