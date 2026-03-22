---
name: canva-incident-runbook
description: |
  Execute Canva Connect API incident response with triage, mitigation, and postmortem.
  Use when responding to Canva-related outages, investigating API errors,
  or running post-incident reviews for Canva integration failures.
  Trigger with phrases like "canva incident", "canva outage",
  "canva down", "canva on-call", "canva emergency", "canva broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Incident Runbook

## Overview

Rapid incident response for Canva Connect API integration failures. Covers triage, mitigation, escalation, and postmortem.

## Quick Triage (First 5 Minutes)

```bash
#!/bin/bash
# canva-triage.sh — Run immediately when incident detected

echo "=== Canva Triage ==="

# 1. Is it Canva or us?
echo -n "Canva API: "
curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)\n" \
  -H "Authorization: Bearer $CANVA_ACCESS_TOKEN" \
  "https://api.canva.com/rest/v1/users/me"

# 2. Check our health endpoint
echo -n "Our health: "
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "https://api.ourapp.com/health"

# 3. Error rate (if Prometheus available)
echo "Error rate (5min):"
curl -s "localhost:9090/api/v1/query?query=rate(canva_api_errors_total[5m])" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['result'])" 2>/dev/null \
  || echo "Prometheus not available"

# 4. Rate limit status
echo -n "Rate limit remaining: "
curl -sD - -o /dev/null -H "Authorization: Bearer $CANVA_ACCESS_TOKEN" \
  "https://api.canva.com/rest/v1/designs?limit=1" 2>&1 \
  | grep -i "x-ratelimit-remaining" || echo "unknown"
```

## Decision Tree

```
API returning errors?
├── YES → What HTTP status?
│   ├── 401 → Token expired → Refresh token, check rotation
│   ├── 403 → Scope issue → Verify integration permissions
│   ├── 429 → Rate limited → Enable backoff, check Retry-After
│   ├── 5xx → Canva outage → Enable fallback, monitor status page
│   └── Other → Check request format against API docs
└── NO → Is our integration healthy?
    ├── YES → Likely resolved or intermittent → Monitor
    └── NO → Check our infra (pods, memory, DNS, TLS)
```

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | All design operations broken | < 15 min | All API calls returning 5xx |
| P2 | Degraded — some operations fail | < 1 hour | Exports failing, designs work |
| P3 | Minor — non-critical feature down | < 4 hours | Webhooks delayed |
| P4 | No user impact | Next business day | Monitoring gap |

## Immediate Mitigation by Error Type

### 401 — Token Expired / Revoked

```bash
# Check if token is valid
curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.canva.com/rest/v1/users/me | python3 -m json.tool

# If expired: refresh all affected users' tokens
# If revoked: users must re-authorize via OAuth flow
```

### 429 — Rate Limited

```bash
# Check how long to wait
curl -sD - -o /dev/null -H "Authorization: Bearer $TOKEN" \
  "https://api.canva.com/rest/v1/designs" 2>&1 \
  | grep -i "retry-after"

# Immediate: reduce request rate
# Enable queue-based rate limiting
```

### 5xx — Canva Service Error

```bash
# Check Canva status page (no official status.canva.com for API)
# Check Canva developer community for reported outages

# Enable graceful degradation
# Return cached data where possible
# Show "Design features temporarily unavailable" to users
```

## Communication Templates

### Internal (Slack)

```
P[1-4] INCIDENT: Canva Integration
Status: INVESTIGATING | MITIGATING | RESOLVED
Impact: [Describe user impact]
API Response: HTTP [status code]
Current action: [What you're doing]
Next update: [Time]
IC: @[name]
```

### External (Status Page)

```
Canva Design Features — Degraded Performance

We are experiencing issues with our design integration.
Users may see delays or errors when creating/exporting designs.

We are actively working with our design platform provider to resolve this.

Last updated: [ISO 8601 timestamp]
```

## Post-Incident

### Evidence Collection

```bash
# Collect logs for the incident window
kubectl logs -l app=canva-integration --since=2h > incident-canva-logs.txt

# Export metrics
curl "localhost:9090/api/v1/query_range?query=canva_api_errors_total&start=$(date -d '2 hours ago' +%s)&end=$(date +%s)&step=60" > metrics.json
```

### Postmortem Template

```markdown
## Incident: Canva API [Error Type]
**Date:** YYYY-MM-DD HH:MM UTC
**Duration:** X hours Y minutes
**Severity:** P[1-4]

### Summary
[1-2 sentence description]

### Timeline (UTC)
- HH:MM — [First alert / error detected]
- HH:MM — [Investigation started]
- HH:MM — [Root cause identified]
- HH:MM — [Mitigation applied]
- HH:MM — [Confirmed resolved]

### Root Cause
[Was it Canva-side or our integration? Token issue? Rate limit? Code bug?]

### Impact
- Users affected: N
- Failed operations: N designs / N exports

### Action Items
- [ ] [Preventive measure] — Owner — Due date
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't determine if Canva is down | No status page API | Test with known-good token |
| Token refresh fails | Revoked integration | Re-authorize user |
| All users affected | Integration-level issue | Check client credentials |
| Single user affected | User-level token issue | Refresh that user's token |

## Resources

- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)
- [Canva Changelog](https://www.canva.dev/docs/connect/changelog/)

## Next Steps

For data handling, see `canva-data-handling`.
