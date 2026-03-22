---
name: webflow-incident-runbook
description: |
  Execute Webflow incident response — triage by HTTP status (401/403/429/500),
  circuit breaker activation, cached fallback, Webflow status page checks,
  communication templates, and postmortem process.
  Trigger with phrases like "webflow incident", "webflow outage",
  "webflow down", "webflow on-call", "webflow emergency", "webflow broken".
allowed-tools: Read, Grep, Bash(curl:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Incident Runbook

## Overview

Rapid incident response procedures for Webflow Data API v2 integration failures.
Covers triage, immediate remediation by error type, graceful degradation,
stakeholder communication, and postmortem.

## Prerequisites

- Access to Webflow dashboard and status page
- Application logs and metrics access
- Communication channels (Slack, PagerDuty)
- Cached fallback data available

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | Integration fully down | < 15 min | All API calls returning 401/500 |
| P2 | Degraded service | < 1 hour | High 429 rate, elevated latency |
| P3 | Minor impact | < 4 hours | Webhook delays, form sync lag |
| P4 | No user impact | Next business day | Monitoring gap, stale cache |

## Quick Triage (Run First)

```bash
#!/bin/bash
echo "=== Webflow Incident Triage ==="
echo "Time: $(date -u)"

# 1. Webflow platform status
echo ""
echo "--- Platform Status ---"
curl -s https://status.webflow.com/api/v2/status.json 2>/dev/null | \
  python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Status: {d[\"status\"][\"description\"]}')
for c in d.get('components',[]):
  if c['status'] != 'operational':
    print(f'  DEGRADED: {c[\"name\"]} ({c[\"status\"]})')
" 2>/dev/null || echo "Cannot reach status page"

# 2. API connectivity
echo ""
echo "--- API Connectivity ---"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  https://api.webflow.com/v2/sites 2>/dev/null)
echo "Sites endpoint: HTTP $HTTP"

# 3. Rate limit status
echo ""
echo "--- Rate Limits ---"
curl -sI -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  https://api.webflow.com/v2/sites 2>/dev/null | \
  grep -i "x-ratelimit\|retry-after" || echo "No rate limit headers"

# 4. Our health endpoint
echo ""
echo "--- App Health ---"
HEALTH=$(curl -s https://your-app.com/api/health 2>/dev/null)
echo "$HEALTH" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Status: {d[\"status\"]}')
for k,v in d.get('services',{}).items():
  print(f'  {k}: {v.get(\"status\",\"unknown\")} ({v.get(\"latencyMs\",\"?\")}ms)')
" 2>/dev/null || echo "Health endpoint unreachable"
```

## Decision Tree

```
Is Webflow API returning errors?
├── YES
│   ├── status.webflow.com shows incident?
│   │   ├── YES → Activate fallback. Wait for Webflow resolution.
│   │   └── NO → Our issue. Check token, config, network.
│   ├── HTTP 401/403?
│   │   └── Token issue. See "Auth Failure" below.
│   ├── HTTP 429?
│   │   └── Rate limited. See "Rate Limit" below.
│   └── HTTP 500/502/503?
│       └── Webflow server issue. Activate circuit breaker.
└── NO
    ├── Our service healthy?
    │   ├── YES → Likely resolved or intermittent. Monitor closely.
    │   └── NO → Our infrastructure issue (pods, memory, network).
    └── Webhooks not firing?
        └── Check webhook registrations and endpoint accessibility.
```

## Immediate Actions by Error Type

### 401/403 — Authentication Failure (P1)

```bash
# Verify token is set
echo "Token present: ${WEBFLOW_API_TOKEN:+YES}${WEBFLOW_API_TOKEN:-NO}"

# Test token
curl -s -o /dev/null -w "HTTP %{http_code}" \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  https://api.webflow.com/v2/sites

# If 401: Token was revoked or expired
# Action: Generate new token at developers.webflow.com
# Then update in deployment platform:
# vercel env rm WEBFLOW_API_TOKEN production && vercel env add WEBFLOW_API_TOKEN production
# fly secrets set WEBFLOW_API_TOKEN=new-token
# kubectl create secret generic webflow-secrets --from-literal=api-token=NEW_TOKEN --dry-run=client -o yaml | kubectl apply -f -

# Restart application to pick up new token
```

### 429 — Rate Limited (P2)

```bash
# Check Retry-After header
curl -sI -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  https://api.webflow.com/v2/sites 2>&1 | grep -i "retry-after"

# Immediate: Enable request queuing
# If feature flag available:
# curl -X POST https://your-app.com/admin/feature-flags \
#   -d '{"webflow_queue_mode": true}'

# Long-term fixes:
# 1. Switch reads to CDN-cached live endpoints (no rate limit)
# 2. Use bulk endpoints (100 items = 1 API call)
# 3. Reduce polling frequency
# 4. Contact Webflow for limit increase (enterprise)
```

### 500/502/503 — Webflow Server Error (P2)

```bash
# Confirm Webflow is the source
curl -s https://status.webflow.com/api/v2/status.json | jq '.status.description'

# Activate cached fallback
# Your circuit breaker should handle this automatically.
# If not, manually enable:
# curl -X POST https://your-app.com/admin/feature-flags \
#   -d '{"webflow_fallback_mode": true}'

# Monitor for recovery
watch -n 30 'curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  https://api.webflow.com/v2/sites'
```

### Webhook Delivery Failure (P3)

```bash
# Check webhook registrations
curl -s "https://api.webflow.com/v2/sites/$WEBFLOW_SITE_ID/webhooks" \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" | \
  jq '.webhooks[] | {id, triggerType, url, createdOn}'

# Verify endpoint is accessible
curl -s -o /dev/null -w "%{http_code}" https://your-app.com/webhooks/webflow

# Re-register if webhook was deleted
curl -X POST "https://api.webflow.com/v2/sites/$WEBFLOW_SITE_ID/webhooks" \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"triggerType": "form_submission", "url": "https://your-app.com/webhooks/webflow"}'
```

## Communication Templates

### Internal (Slack)

```
P[1-4] INCIDENT: Webflow Integration
Status: INVESTIGATING | IDENTIFIED | MONITORING | RESOLVED
Impact: [What users experience]
Root cause: [Webflow outage / Token expired / Rate limited / Our bug]
Current action: [What we're doing]
Next update in: [15 min / 1 hour]
Incident commander: @[name]
```

### External (Status Page)

```
Webflow Integration — Degraded Performance

We're experiencing issues with content updates powered by our Webflow integration.
[Specific impact: delayed content / forms not processing / orders not syncing].

Our team is actively working on resolution. Existing content remains accessible.

Last updated: [timestamp UTC]
```

## Post-Incident

### Evidence Collection

```bash
# Export recent logs
grep -i "webflow\|429\|401\|500" /var/log/app/*.log | tail -200 > incident-logs.txt

# Export metrics snapshot
curl "http://prometheus:9090/api/v1/query_range?\
query=rate(webflow_api_errors_total[5m])&\
start=$(date -d '2 hours ago' +%s)&\
end=$(date +%s)&step=60" > incident-metrics.json

# Generate debug bundle
./webflow-debug-bundle.sh
```

### Postmortem Template

```markdown
## Incident: Webflow [Error Description]
**Date:** YYYY-MM-DD HH:MM — HH:MM UTC
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Impact:** [Users affected, revenue impact]

### Timeline
- HH:MM — Alert fired: [description]
- HH:MM — Triage started
- HH:MM — Root cause identified: [cause]
- HH:MM — Mitigation applied: [action]
- HH:MM — Service restored

### Root Cause
[Technical explanation]

### What Went Well
- [What worked]

### What Went Wrong
- [What failed]

### Action Items
- [ ] [Preventive measure] — Owner — Due date
- [ ] [Monitoring improvement] — Owner — Due date
```

## Output

- Triage script identifying the error source
- Decision tree for rapid root cause identification
- Remediation steps for every HTTP error type
- Communication templates for internal and external stakeholders
- Evidence collection for postmortem

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Status page unreachable | Network issue or DNS | Use mobile data or VPN |
| Can't rotate token | Lost dashboard access | Contact Webflow support |
| Circuit breaker stuck open | Reset time too long | Manually reset or adjust threshold |
| Stale cache served | Fallback active too long | Set TTL on cached content |

## Resources

- [Webflow Status Page](https://status.webflow.com)
- [Webflow Support](https://support.webflow.com)
- [API Reference](https://developers.webflow.com/data/reference/rest-introduction)

## Next Steps

For data handling and compliance, see `webflow-data-handling`.
