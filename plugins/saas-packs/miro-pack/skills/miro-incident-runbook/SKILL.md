---
name: miro-incident-runbook
description: |
  Execute Miro REST API v2 incident response with triage, mitigation, and postmortem.
  Use when responding to Miro-related outages, investigating API errors,
  or running post-incident reviews for Miro integration failures.
  Trigger with phrases like "miro incident", "miro outage",
  "miro down", "miro on-call", "miro emergency", "miro broken".
allowed-tools: Read, Grep, Bash(curl:*), Bash(jq:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, incident-response, runbook]
compatible-with: claude-code
---

# Miro Incident Runbook

## Overview

Rapid incident response for Miro REST API v2 integration failures: triage, mitigation, recovery, and postmortem.

## Severity Levels

| Level | Definition | Response | Example |
|-------|------------|----------|---------|
| P1 | Complete integration outage | < 15 min | Miro API returns 5xx on all calls |
| P2 | Degraded service | < 1 hour | High latency, partial 429s |
| P3 | Minor impact | < 4 hours | Webhook delays, single-board errors |
| P4 | No user impact | Next business day | Monitoring gaps, non-critical warnings |

## Quick Triage (First 5 Minutes)

```bash
#!/bin/bash
# miro-triage.sh — Run this first during any Miro incident

echo "=== MIRO TRIAGE $(date -u +%H:%M:%SZ) ==="

# 1. Is Miro itself down?
echo -n "Miro Status: "
curl -sf "https://status.miro.com/api/v2/status.json" | jq -r '.status.description' 2>/dev/null || echo "STATUS PAGE UNREACHABLE"

# 2. Can we reach the API?
echo -n "API Connectivity: "
curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)" \
  -H "Authorization: Bearer ${MIRO_ACCESS_TOKEN}" \
  "https://api.miro.com/v2/boards?limit=1" 2>/dev/null
echo ""

# 3. What's our rate limit status?
echo "Rate Limit:"
curl -sI -H "Authorization: Bearer ${MIRO_ACCESS_TOKEN}" \
  "https://api.miro.com/v2/boards?limit=1" 2>/dev/null | \
  grep -i "x-ratelimit\|retry-after" || echo "  No rate limit headers"

# 4. Token validity
echo -n "Token: "
TOKEN_RESP=$(curl -s -H "Authorization: Bearer ${MIRO_ACCESS_TOKEN}" \
  "https://api.miro.com/v1/oauth-token" 2>/dev/null)
echo "$TOKEN_RESP" | jq -r '"scopes: \(.scopes // "INVALID"), team: \(.team.id // "N/A")"' 2>/dev/null || echo "INVALID OR EXPIRED"

# 5. Our health check
echo -n "App Health: "
curl -sf "${APP_URL:-http://localhost:3000}/health" | jq -r '.miro.status // "UNAVAILABLE"' 2>/dev/null || echo "HEALTH CHECK FAILED"
```

## Decision Tree

```
Miro API returning errors?
├── YES → What status code?
│   ├── 401/403 → Token issue
│   │   ├── Token expired? → Refresh token (see below)
│   │   └── Scopes changed? → Re-authorize via OAuth flow
│   ├── 429 → Rate limited
│   │   ├── Check X-RateLimit-Remaining header
│   │   ├── Honor Retry-After header
│   │   └── Reduce request rate or enable queue
│   ├── 404 → Board/item not found
│   │   └── Verify IDs haven't changed
│   └── 500/502/503 → Miro platform issue
│       ├── Check status.miro.com
│       ├── Enable graceful degradation
│       └── Wait for Miro to resolve
└── NO → Is our integration healthy?
    ├── YES → Intermittent. Monitor for recurrence.
    └── NO → Our infrastructure issue
        ├── Check pods/containers
        ├── Check memory/CPU
        └── Check network/DNS
```

## Immediate Actions by Error Type

### 401 — Token Expired

```bash
# Refresh access token
curl -s -X POST https://api.miro.com/v1/oauth/token \
  -d "grant_type=refresh_token" \
  -d "client_id=${MIRO_CLIENT_ID}" \
  -d "client_secret=${MIRO_CLIENT_SECRET}" \
  -d "refresh_token=${MIRO_REFRESH_TOKEN}" | jq

# If refresh token is also expired, user must re-authorize:
# Redirect to: https://miro.com/oauth/authorize?response_type=code&client_id=${MIRO_CLIENT_ID}&redirect_uri=${REDIRECT_URI}
```

### 403 — Insufficient Permissions

```bash
# Check what scopes the token has
curl -s -H "Authorization: Bearer ${MIRO_ACCESS_TOKEN}" \
  "https://api.miro.com/v1/oauth-token" | jq '.scopes'

# Compare with what the failed endpoint requires
# boards:read for GET endpoints
# boards:write for POST/PATCH/DELETE endpoints
# team:read / organizations:read for team/org endpoints
```

### 429 — Rate Limited

```bash
# Check current rate limit status
curl -sI -H "Authorization: Bearer ${MIRO_ACCESS_TOKEN}" \
  "https://api.miro.com/v2/boards?limit=1" | grep -i ratelimit

# Response headers:
# X-RateLimit-Limit: 100000 (credits per minute)
# X-RateLimit-Remaining: 0
# Retry-After: 30 (seconds)

# Immediate mitigation: pause all non-critical API calls
# Long-term: implement caching + webhooks (see miro-performance-tuning)
```

### 5xx — Miro Platform Issue

```bash
# 1. Confirm it's Miro-side
curl -s "https://status.miro.com/api/v2/status.json" | jq '.status'

# 2. Check for ongoing incidents
curl -s "https://status.miro.com/api/v2/incidents/unresolved.json" | \
  jq '.incidents[] | {name, status, updated_at}'

# 3. Enable graceful degradation in your app
# Feature flag: MIRO_FALLBACK_ENABLED=true
# Serve cached data, queue writes for retry when Miro recovers
```

## Communication Templates

### Internal (Slack/PagerDuty)

```
P[1-4] INCIDENT: Miro Integration
Status: INVESTIGATING | IDENTIFIED | MONITORING | RESOLVED
Impact: [What users experience]
Root cause: [Miro-side outage | Token expired | Rate limited | Our bug]
Action: [What we're doing now]
ETA: [Expected resolution time]
Next update: [When]
```

### External (Status Page)

```
Miro Integration — Degraded Performance

We are experiencing issues with our Miro integration.
[Board sync / item creation / webhook processing] may be delayed.

Root cause: [Brief technical explanation]
Workaround: [If any — e.g., "Changes will sync when service recovers"]

Last updated: [timestamp UTC]
```

## Post-Incident Evidence Collection

```bash
# Collect evidence for postmortem
INCIDENT_DIR="miro-incident-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$INCIDENT_DIR"

# API response during incident
curl -s -H "Authorization: Bearer ${MIRO_ACCESS_TOKEN}" \
  "https://api.miro.com/v2/boards?limit=1" > "$INCIDENT_DIR/api-response.json"

# Miro status page snapshot
curl -s "https://status.miro.com/api/v2/incidents/unresolved.json" > "$INCIDENT_DIR/miro-status.json"

# Application metrics (adjust query for your Prometheus)
curl -s "http://prometheus:9090/api/v1/query_range?query=rate(miro_errors_total[5m])&start=$(date -d '2 hours ago' +%s)&end=$(date +%s)&step=60" > "$INCIDENT_DIR/error-metrics.json"

# Package (exclude tokens)
tar -czf "$INCIDENT_DIR.tar.gz" "$INCIDENT_DIR"
echo "Evidence collected: $INCIDENT_DIR.tar.gz"
```

## Postmortem Template

```markdown
## Incident: Miro [Error Type]
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Impact:** [Users affected, features impacted]

### Timeline (UTC)
- HH:MM — [First error detected by monitoring]
- HH:MM — [On-call alerted]
- HH:MM — [Root cause identified]
- HH:MM — [Mitigation applied]
- HH:MM — [Service restored]

### Root Cause
[Technical explanation — e.g., "Access token expired and refresh logic
had a bug where it used the old refresh token instead of the new one
returned in the last refresh response."]

### What Went Well
- [Monitoring detected the issue within 2 minutes]
- [Runbook was accurate and followed]

### What Went Wrong
- [Token refresh logic untested in integration tests]
- [No alerting on 401 error rate]

### Action Items
- [ ] Add integration test for token refresh flow — @owner — Due date
- [ ] Add P1 alert for miro_errors_total{error_type="auth"} > 0 — @owner — Due date
- [ ] Document token rotation procedure — @owner — Due date
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Status page unreachable | DNS/network | Use mobile or VPN |
| Token refresh fails | Refresh token revoked | User must re-authorize |
| Rate limit persists after reset | Clock skew | Use `Retry-After` header, not local clock |
| Metrics unavailable | Prometheus down | Check application logs directly |

## Resources

- [Miro Status Page](https://status.miro.com)
- [Miro Developer Support](https://developers.miro.com/docs/getting-help)
- [Rate Limiting Reference](https://developers.miro.com/reference/rate-limiting)

## Next Steps

For data handling and compliance, see `miro-data-handling`.
