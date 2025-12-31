# instantly-email-warmup

> Configure and monitor email warmup for new sending domains to establish sender reputation

## Directory Structure

```
instantly-email-warmup/
├── SKILL.md
└── examples/
    ├── start_warmup.py
    ├── monitor_warmup.py
    ├── warmup_schedule.json
    └── warmup_metrics.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Email warmup configuration and monitoring best practices |
| start_warmup.py | Python | Initialize warmup pool for new email accounts |
| monitor_warmup.py | Python | Track warmup progress and health metrics |
| warmup_schedule.json | JSON | Warmup schedule configuration template |
| warmup_metrics.py | Python | Calculate and report warmup effectiveness |

## Summary

**Category:** Operations
**Target Audience:** Email operations engineers managing sending infrastructure
**Trigger Phrases:** "email warmup instantly", "warm up sending domain", "instantly warmup pool", "new email account warmup", "sender reputation instantly"
**Definition of Success (Technical):** Warmup pool active with daily volume increasing per schedule
**Definition of Success (Business):** New sending domains achieve inbox placement above 90%
**Production:** true
**Version:** 1.0.0
**License:** MIT
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
