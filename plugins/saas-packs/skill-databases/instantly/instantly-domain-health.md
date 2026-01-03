# instantly-domain-health

> Monitor and maintain sending domain health metrics for optimal deliverability

## Directory Structure

```
instantly-domain-health/
├── SKILL.md
└── examples/
    ├── check_dns_records.py
    ├── monitor_bounces.py
    ├── health_dashboard.py
    └── alert_config.json
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Domain health monitoring and maintenance procedures |
| check_dns_records.py | Python | Validate SPF, DKIM, DMARC configuration |
| monitor_bounces.py | Python | Track bounce rates and identify problematic patterns |
| health_dashboard.py | Python | Aggregate domain health metrics for monitoring |
| alert_config.json | JSON | Alert thresholds for domain health degradation |

## Summary

**Category:** Operations
**Target Audience:** Email deliverability specialists maintaining sender reputation
**Trigger Phrases:** "check instantly domain health", "email deliverability monitoring", "spf dkim dmarc instantly", "bounce rate monitoring", "sender reputation check"
**Definition of Success (Technical):** SPF DKIM DMARC records valid and bounce rate under 3%
**Definition of Success (Business):** Consistent inbox placement rates above industry benchmarks
**Production:** true
**Version:** 1.0.0
**License:** MIT
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
