---
name: klaviyo-incident-runbook
description: |
  Execute Klaviyo incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Klaviyo-related outages, investigating API errors,
  or running post-incident reviews for Klaviyo integration failures.
  Trigger with phrases like "klaviyo incident", "klaviyo outage",
  "klaviyo down", "klaviyo on-call", "klaviyo emergency", "klaviyo broken".
allowed-tools: Read, Grep, Bash(curl:*), Bash(kubectl:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Incident Runbook

## Overview

Rapid incident response for Klaviyo API outages and integration failures: quick triage, decision trees, mitigation steps, and postmortem templates.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | Complete outage | <15 min | All Klaviyo API calls returning 5xx |
| P2 | Degraded service | <1 hour | 429 rate limiting, high latency |
| P3 | Minor impact | <4 hours | Webhook delays, single endpoint errors |
| P4 | No user impact | Next business day | Monitoring gaps, deprecation warnings |

## Quick Triage (Run Immediately)

```bash
#!/bin/bash
# klaviyo-triage.sh -- run this first during any incident

echo "=== Klaviyo Quick Triage ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Is Klaviyo itself down?
echo ""
echo "--- Klaviyo Status Page ---"
curl -s "https://status.klaviyo.com/api/v2/status.json" 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"][\"description\"]}')" \
  || echo "Could not reach status page"

# 2. Can we authenticate?
echo ""
echo "--- API Auth Check ---"
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/klaviyo-triage.json \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/" 2>/dev/null)
echo "Auth response: HTTP $HTTP_CODE"

# 3. Rate limit status
echo ""
echo "--- Rate Limit Headers ---"
curl -s -I \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/profiles/?page[size]=1" 2>/dev/null \
  | grep -iE "ratelimit|retry-after" || echo "No rate limit headers returned"

# 4. Our app health
echo ""
echo "--- Application Health ---"
curl -s "http://localhost:3000/health" 2>/dev/null \
  | python3 -m json.tool 2>/dev/null || echo "App health check unavailable"
```

## Decision Tree

```
Is Klaviyo API returning errors?
├── YES
│   ├── status.klaviyo.com shows incident?
│   │   ├── YES → Klaviyo-side outage
│   │   │   → Enable fallback mode
│   │   │   → Monitor status page for resolution
│   │   │   → Communicate to stakeholders
│   │   └── NO → Our integration issue
│   │       ├── 401/403? → API key problem (see below)
│   │       ├── 429? → Rate limit hit (see below)
│   │       ├── 400? → Payload validation error
│   │       └── 5xx? → Likely intermittent, retry with backoff
│   └── What status code?
│       ├── 401 → Key revoked/rotated → Verify & rotate
│       ├── 403 → Missing scope → Check API key scopes
│       ├── 429 → Rate limited → Reduce concurrency
│       └── 5xx → Server error → Retry, check status page
└── NO
    ├── Is our app healthy?
    │   ├── YES → Resolved or intermittent → Monitor
    │   └── NO → Our infrastructure → Check pods, memory, network
    └── Are webhooks arriving?
        ├── YES → Partial issue → Check specific endpoint
        └── NO → Webhook endpoint down → Check route, certificate
```

## Immediate Actions by Error Type

### 401 -- Authentication Failure

```bash
# 1. Verify API key is set
echo "Key length: ${#KLAVIYO_PRIVATE_KEY} chars"
echo "Key prefix: ${KLAVIYO_PRIVATE_KEY:0:3}"

# 2. Test the key directly
curl -s -w "\nHTTP %{http_code}\n" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/"

# 3. If key is invalid: generate new key in Klaviyo dashboard
# Settings > API Keys > Create Private API Key

# 4. Update in deployment platform
# GCP: echo -n "pk_new_***" | gcloud secrets versions add klaviyo-key --data-file=-
# AWS: aws secretsmanager update-secret --secret-id klaviyo-key --secret-string "pk_new_***"

# 5. Restart application to pick up new key
```

### 429 -- Rate Limited

```bash
# 1. Check current rate limit
curl -s -I \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/profiles/?page[size]=1" 2>/dev/null \
  | grep -i "ratelimit\|retry-after"

# 2. Reduce request volume immediately
# - Lower queue concurrency
# - Enable request sampling
# - Pause non-critical background jobs

# 3. Check for runaway processes
# Look for loops making excessive API calls
```

### 5xx -- Klaviyo Server Error

```bash
# 1. Check Klaviyo status page
curl -s "https://status.klaviyo.com/api/v2/status.json" | python3 -m json.tool

# 2. Enable graceful degradation
# Your app should continue working without Klaviyo
# Queue failed requests for retry when Klaviyo recovers

# 3. Monitor for recovery
watch -n 30 'curl -s -w "%{http_code}" -o /dev/null \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/"'
```

## Communication Templates

### Internal (Slack)

```
P[1/2] INCIDENT: Klaviyo Integration
Status: INVESTIGATING / MITIGATING / RESOLVED
Impact: [What users are experiencing]
Root cause: [Klaviyo outage / Our key expired / Rate limit exceeded]
Current action: [What we're doing right now]
ETA: [When we expect resolution]
Incident lead: @[name]
```

### External (Status Page)

```
Klaviyo Integration -- Degraded Performance

Some features powered by Klaviyo (email subscriptions, event tracking)
are experiencing delays. Customer data is being queued and will be
processed once the issue is resolved.

No data loss is expected. We are monitoring the situation.

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection

```bash
# Generate debug bundle
bash klaviyo-debug-bundle.sh

# Export application logs
# (adjust for your logging setup)
journalctl -u my-app --since "2 hours ago" | grep -i klaviyo > incident-logs.txt

# Capture metrics snapshot
curl -s "localhost:9090/api/v1/query?query=klaviyo_api_errors_total" > metrics-snapshot.json
```

### Postmortem Template

```markdown
## Incident: Klaviyo [Error Type]
**Date:** YYYY-MM-DD HH:MM - HH:MM UTC
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Incident Lead:** [Name]

### Summary
[1-2 sentence description of what happened]

### Timeline (UTC)
- HH:MM - Alert fired: [description]
- HH:MM - Incident acknowledged by [name]
- HH:MM - Root cause identified: [description]
- HH:MM - Mitigation applied: [what was done]
- HH:MM - Service restored
- HH:MM - Monitoring confirmed stable

### Root Cause
[Technical explanation]

### Impact
- Affected users: [number/percentage]
- Failed API calls: [count]
- Data queued for retry: [count]

### Action Items
- [ ] [Action] - Owner: [name] - Due: [date]
- [ ] [Action] - Owner: [name] - Due: [date]

### Lessons Learned
- What went well: [...]
- What could improve: [...]
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status page | Network issue | Use mobile or check Twitter @klaviyo |
| Metrics unavailable | Prometheus down | Check direct API with cURL |
| Key rotation panic | No backup key | Always have a rotation procedure documented |
| Alert fatigue | Too many false alarms | Tune thresholds based on baseline |

## Resources

- [Klaviyo Status Page](https://status.klaviyo.com)
- [Klaviyo Support](https://support.klaviyo.com)
- [API Error Alerts](https://developers.klaviyo.com/en/docs/review_api_error_alerts)

## Next Steps

For data handling, see `klaviyo-data-handling`.
