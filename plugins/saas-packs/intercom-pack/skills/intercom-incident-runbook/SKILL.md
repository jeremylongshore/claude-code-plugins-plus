---
name: intercom-incident-runbook
description: |
  Execute Intercom incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Intercom API outages, investigating integration errors,
  or running post-incident reviews for Intercom failures.
  Trigger with phrases like "intercom incident", "intercom outage",
  "intercom down", "intercom on-call", "intercom emergency", "intercom broken".
allowed-tools: Read, Grep, Bash(curl:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Incident Runbook

## Overview

Rapid incident response procedures for Intercom integration failures, including triage by HTTP status code, mitigation steps, and postmortem template.

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| P1 | All Intercom API calls failing | < 15 min | 401 auth failures, API unreachable |
| P2 | Degraded service | < 1 hour | High latency, rate limited (429) |
| P3 | Partial impact | < 4 hours | Webhook delays, search timeouts |
| P4 | No user impact | Next business day | Monitoring gaps, stale cache |

## Quick Triage (Copy-Paste)

```bash
#!/bin/bash
echo "=== Intercom Incident Triage ==="

# 1. Is Intercom's API responding?
echo -n "1. API reachable: "
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me
echo ""

# 2. Is there a platform-wide incident?
echo -n "2. Intercom status: "
curl -s https://status.intercom.com/api/v2/status.json | jq -r '.status.description'

# 3. Active incidents on Intercom's side?
echo -n "3. Active incidents: "
curl -s https://status.intercom.com/api/v2/incidents/unresolved.json | jq '.incidents | length'

# 4. Rate limit status
echo -n "4. Rate limit remaining: "
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me 2>/dev/null | grep -i x-ratelimit-remaining | awk '{print $2}'

# 5. Our health check
echo -n "5. Our integration health: "
curl -s https://your-app.com/health | jq '.services.intercom.status' 2>/dev/null || echo "UNKNOWN"
```

## Decision Tree

```
API returning errors?
├── YES ──▶ Check status.intercom.com
│           ├── Incident reported ──▶ Intercom's problem
│           │   → Enable graceful degradation
│           │   → Monitor for resolution
│           │   → No action needed on our side
│           └── No incident ──▶ Our integration issue
│               ├── 401 → Token expired/revoked → Rotate token
│               ├── 403 → Scope missing → Add OAuth scope
│               ├── 429 → Rate limited → Enable queue/backoff
│               └── 5xx → Server error → Retry with backoff
└── NO ──▶ Is our service healthy?
           ├── YES → Resolved or intermittent → Monitor
           └── NO → Our infrastructure issue
               → Check pods, memory, network, DNS
```

## Mitigation by Error Type

### 401 - Authentication Failed

```bash
# Verify token is valid
curl -s -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me | jq '.type'
# Expected: "admin"
# If error: Token is invalid or revoked

# IMMEDIATE: Regenerate token
# Developer Hub > Your App > Authentication > Generate new token
# Update in secret manager:
aws secretsmanager update-secret \
  --secret-id intercom/production/token \
  --secret-string "new_token_here"

# Restart application to pick up new token
kubectl rollout restart deployment/intercom-service
```

### 429 - Rate Limited

```bash
# Check rate limit headers
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me 2>/dev/null | grep -i "x-ratelimit"

# Immediate: Reduce request volume
# - Pause any batch/sync jobs
# - Enable request queuing if available

# Check if multiple apps are consuming workspace quota
# Limit: 25,000 req/min per workspace across all apps
```

### 5xx - Intercom Server Errors

```bash
# 1. Check Intercom status
curl -s https://status.intercom.com/api/v2/status.json | jq

# 2. Enable graceful degradation
# Your app should serve cached data or fallback UI

# 3. Track request_id from error responses for Intercom support
# Error response includes: { "request_id": "req_abc123" }
```

## Graceful Degradation Pattern

```typescript
import { IntercomClient, IntercomError } from "intercom-client";
import { LRUCache } from "lru-cache";

const cache = new LRUCache<string, any>({ max: 10000, ttl: 3600000 }); // 1hr fallback

async function getContactWithFallback(contactId: string): Promise<any> {
  try {
    const contact = await client.contacts.find({ contactId });
    cache.set(contactId, contact); // Update cache on success
    return contact;
  } catch (err) {
    if (err instanceof IntercomError && (err.statusCode === 429 || (err.statusCode ?? 0) >= 500)) {
      // Return stale cached data during outages
      const cached = cache.get(contactId);
      if (cached) {
        console.warn(`[Intercom] Serving cached data for ${contactId} due to ${err.statusCode}`);
        return { ...cached, _stale: true };
      }
    }
    throw err;
  }
}
```

## Communication Templates

### Internal Slack

```
[P1] INCIDENT: Intercom Integration
Status: INVESTIGATING
Impact: [Customer conversations not loading / messages not sending]
Cause: [Intercom API returning 5xx / our token expired / rate limited]
Action: [Enabling fallback / rotating token / pausing sync jobs]
Next update: [Time]
Commander: @[name]
```

### Postmortem Template

```markdown
## Incident: Intercom [Type]
**Date:** YYYY-MM-DD HH:MM - HH:MM UTC
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Intercom request_ids:** [req_abc123, req_def456]

### Summary
[1-2 sentences describing what happened and user impact]

### Timeline
- HH:MM - First alert: [what triggered]
- HH:MM - Triage started: [findings]
- HH:MM - Mitigation: [action taken]
- HH:MM - Resolution: [what fixed it]

### Root Cause
[Technical explanation of why it happened]

### Impact
- Conversations affected: N
- Users unable to reach support: N
- Duration of degraded service: Xm

### Action Items
- [ ] [Preventive measure] - Owner - Due
- [ ] [Monitoring gap to fill] - Owner - Due
- [ ] [Documentation to update] - Owner - Due
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Triage script fails | Token not set | Export INTERCOM_ACCESS_TOKEN |
| Status page unreachable | DNS/network | Try mobile network or VPN |
| Can't rotate token | No Developer Hub access | Escalate to workspace admin |
| Cache empty during outage | No pre-warming | Implement cache warming job |

## Resources

- [Intercom Status Page](https://status.intercom.com)
- [Intercom Status API](https://status.intercom.com/api)
- [Error Codes](https://developers.intercom.com/docs/references/rest-api/errors/error-codes)
- [Rate Limiting](https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting)

## Next Steps

For data handling compliance, see `intercom-data-handling`.
