---
name: clickup-incident-runbook
description: |
  Execute ClickUp API incident response: triage, diagnosis, mitigation,
  and postmortem for API failures and integration outages.
  Trigger: "clickup incident", "clickup outage", "clickup down",
  "clickup on-call", "clickup emergency", "clickup API broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Incident Runbook

## Overview

Rapid incident response for ClickUp API v2 integration failures. Covers triage, diagnosis by error type, mitigation, and postmortem.

## Severity Classification

| Level | Definition | Response Time | Example |
|-------|-----------|---------------|---------|
| P1 | All ClickUp API calls failing | < 15 min | 401 on all requests, API unreachable |
| P2 | Degraded service | < 1 hour | High latency, rate limited, partial 500s |
| P3 | Minor impact | < 4 hours | Webhook delays, non-critical endpoint errors |
| P4 | No user impact | Next business day | Monitoring gaps, documentation issues |

## Step 1: Quick Triage (< 2 minutes)

```bash
#!/bin/bash
echo "=== ClickUp Incident Triage ==="

# 1. Is ClickUp itself down?
echo -n "ClickUp platform: "
curl -sf https://status.clickup.com/api/v2/summary.json 2>/dev/null | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['status']['description'])" 2>/dev/null \
  || echo "UNREACHABLE"

# 2. Can we authenticate?
echo -n "Auth: "
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" 2>/dev/null)
echo "HTTP $STATUS"

# 3. Rate limit status
echo -n "Rate limit: "
curl -sD - -o /dev/null https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" 2>&1 | \
  grep -i "X-RateLimit-Remaining" | awk '{print $2}' | tr -d '\r'

# 4. API latency
echo -n "Latency: "
curl -sf -o /dev/null -w "%{time_total}s\n" \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN"

# 5. Our service health (adjust URL)
echo -n "Our health endpoint: "
curl -sf http://localhost:3000/health 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>/dev/null \
  || echo "UNREACHABLE"
```

## Decision Tree

```
ClickUp API errors?
├── YES: Check status.clickup.com
│   ├── ClickUp incident → Enable fallback mode. Wait. Monitor.
│   └── No ClickUp incident → Our issue
│       ├── 401 errors → Token rotated/revoked → Regenerate token
│       ├── 429 errors → Rate limited → Enable queuing, check for loops
│       ├── 403 errors → Permission changed → Check workspace access
│       └── 500 errors → Intermittent ClickUp issue → Retry with backoff
└── NO: Our service down?
    ├── YES → Infrastructure issue (pods, memory, network)
    └── NO → Resolved or intermittent. Monitor.
```

## Remediation by Error Type

### 401 Unauthorized (Token Issue)

```bash
# Verify token is set and valid
echo "Token length: ${#CLICKUP_API_TOKEN}"

# Test with explicit token
curl -v https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" 2>&1 | grep "< HTTP"

# If invalid: regenerate in ClickUp Settings > Apps > API Token
# Then update in your secrets manager:
gh secret set CLICKUP_API_TOKEN --body "pk_NEW_TOKEN"
# OR: vault kv put secret/clickup/api-token value="pk_NEW_TOKEN"
```

### 429 Rate Limited

```bash
# Check current rate limit state
curl -sD - -o /dev/null https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" 2>&1 | grep -i ratelimit

# Check for runaway loops in your application
# Look for rapid repeated calls to same endpoint
```

Mitigation: Enable request queuing, check for infinite loops, consider plan upgrade.

### 500/503 ClickUp Server Error

```bash
# Check ClickUp status page
curl -sf https://status.clickup.com/api/v2/summary.json | \
  python3 -c "import sys,json; [print(f'  {c[\"name\"]}: {c[\"status\"]}') for c in json.load(sys.stdin)['components']]"
```

Mitigation: Enable graceful degradation (circuit breaker), queue writes for retry.

## Graceful Degradation

```typescript
// Circuit breaker for ClickUp API
class ClickUpCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private readonly threshold = 5;
  private readonly resetMs = 60000;

  isOpen(): boolean {
    if (this.failures >= this.threshold) {
      if (Date.now() - this.lastFailure > this.resetMs) {
        this.failures = 0; // Reset after cooldown
        return false;
      }
      return true;
    }
    return false;
  }

  recordFailure(): void {
    this.failures++;
    this.lastFailure = Date.now();
  }

  recordSuccess(): void {
    this.failures = 0;
  }
}

const breaker = new ClickUpCircuitBreaker();

async function resilientClickUpCall<T>(path: string, fallback: T): Promise<T> {
  if (breaker.isOpen()) {
    console.warn('[clickup] Circuit breaker OPEN, using fallback');
    return fallback;
  }

  try {
    const result = await clickupRequest(path);
    breaker.recordSuccess();
    return result;
  } catch (error) {
    breaker.recordFailure();
    console.error('[clickup] API error, circuit breaker count:', breaker['failures']);
    return fallback;
  }
}
```

## Communication Templates

### Internal (Slack)

```
P[1-4] INCIDENT: ClickUp Integration
Status: INVESTIGATING | IDENTIFIED | MONITORING | RESOLVED
Impact: [user-facing impact description]
Cause: [root cause if known]
Action: [current mitigation steps]
Next update: [time]
```

### Postmortem Template

```markdown
## Incident: ClickUp API [Error Type]
**Date:** YYYY-MM-DD | **Duration:** Xh Ym | **Severity:** P[1-4]

### Timeline
- HH:MM - Alert fired / issue reported
- HH:MM - Triage started
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Resolved

### Root Cause
[Technical explanation]

### Action Items
- [ ] [Preventive measure] - Owner - Due date
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status page | DNS/network issue | Use mobile or VPN |
| Token rotation fails | Insufficient permissions | Need workspace admin |
| Circuit breaker stuck open | resetMs too long | Reduce reset threshold |
| Webhook backlog | ClickUp retrying failed deliveries | Fix endpoint, events replay |

## Resources

- [ClickUp Status Page](https://status.clickup.com)
- [ClickUp Common Errors](https://developer.clickup.com/docs/common_errors)
- [ClickUp Rate Limits](https://developer.clickup.com/docs/rate-limits)

## Next Steps

For data handling during incidents, see `clickup-data-handling`.
