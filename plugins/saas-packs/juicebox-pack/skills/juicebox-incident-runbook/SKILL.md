---
name: juicebox-incident-runbook
description: |
  Juicebox incident response.
  Trigger: "juicebox incident", "juicebox outage".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Incident Runbook

## Triage
```bash
curl -s -H "Authorization: Bearer $JUICEBOX_API_KEY" https://api.juicebox.ai/v1/health
curl -s -H "Authorization: Bearer $JUICEBOX_API_KEY" https://api.juicebox.ai/v1/account/quota
```

## Severity
| Level | Condition | Response |
|-------|-----------|----------|
| P1 | API down | Immediate |
| P2 | Rate limited | 15 min |
| P3 | Partial data | 1 hour |

## Mitigation
- API down: serve cached results
- Rate limited: reduce frequency
- Quota exhausted: pause automation

## Resources
- [Status](https://status.juicebox.ai)

## Next Steps
See `juicebox-data-handling`.
