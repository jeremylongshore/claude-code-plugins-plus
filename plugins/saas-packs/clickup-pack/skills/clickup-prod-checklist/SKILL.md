---
name: clickup-prod-checklist
description: |
  Production readiness checklist for ClickUp API v2 integrations covering
  auth, rate limits, error handling, monitoring, and rollback.
  Trigger: "clickup production", "clickup go-live", "clickup launch checklist",
  "clickup prod ready", "deploy clickup to production".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Production Checklist

## Overview

Complete checklist for deploying ClickUp API v2 integrations to production.

## Pre-Launch Checklist

### Authentication & Secrets
- [ ] Production API token stored in secrets manager (not env files)
- [ ] Token uses a service account, not a personal user account
- [ ] `.env` files in `.gitignore`; pre-commit hook catches `pk_*` patterns
- [ ] Token rotation procedure documented and tested
- [ ] OAuth client secret server-side only (never in client bundle)

### Error Handling
- [ ] All API calls handle 401 (re-auth), 429 (backoff), 500 (retry)
- [ ] Exponential backoff with jitter on rate limits
- [ ] ClickUp-specific error codes parsed (`ECODE` field in responses)
- [ ] Circuit breaker pattern prevents cascade failures
- [ ] Graceful degradation when ClickUp API is down

### Rate Limits
- [ ] Know your plan's limit (100/1K/10K req/min)
- [ ] Rate limit headers monitored (`X-RateLimit-Remaining`)
- [ ] Request queuing prevents burst overruns
- [ ] Caching reduces unnecessary API calls
- [ ] Webhooks replace polling where possible

### Monitoring
- [ ] Health check endpoint verifies ClickUp connectivity
- [ ] API latency tracked per endpoint
- [ ] Error rate alerting (>5% triggers P2)
- [ ] Rate limit remaining alerting (<10% triggers warning)
- [ ] Structured logging with request/response metadata

### Webhooks (if applicable)
- [ ] Endpoint uses HTTPS
- [ ] Responds with 200 within 30 seconds
- [ ] Idempotent processing (tracks `history_items[].id`)
- [ ] Async processing after immediate 200 response
- [ ] Handles ClickUp auto-disable (re-register if needed)

## Production Health Verification

```bash
#!/bin/bash
# run-prod-checks.sh

echo "=== ClickUp Production Checks ==="

# 1. Auth works
echo -n "Auth: "
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN")
[ "$STATUS" = "200" ] && echo "PASS" || echo "FAIL ($STATUS)"

# 2. Rate limit headroom
echo -n "Rate limit: "
REMAINING=$(curl -sD - -o /dev/null \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" 2>&1 | \
  grep -i "X-RateLimit-Remaining" | awk '{print $2}' | tr -d '\r')
echo "${REMAINING} remaining"

# 3. API latency
echo -n "Latency: "
LATENCY=$(curl -sf -o /dev/null -w "%{time_total}" \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN")
echo "${LATENCY}s"
[ "$(echo "$LATENCY > 2" | bc -l)" = "1" ] && echo "  WARNING: latency > 2s"

# 4. Workspace accessible
echo -n "Workspaces: "
TEAMS=$(curl -sf https://api.clickup.com/api/v2/team \
  -H "Authorization: $CLICKUP_API_TOKEN" | \
  python3 -c "import sys,json; print(len(json.load(sys.stdin)['teams']))" 2>/dev/null)
echo "${TEAMS} accessible"

# 5. ClickUp platform status
echo -n "Platform: "
curl -sf https://status.clickup.com/api/v2/summary.json | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['status']['description'])" 2>/dev/null || echo "Unknown"

echo "=== Checks Complete ==="
```

## Rollback Procedure

```bash
# 1. If ClickUp token is compromised
# - Regenerate token in ClickUp Settings > Apps
# - Update secret in deployment platform
# - Redeploy

# 2. If integration is causing issues
# - Feature flag: disable ClickUp integration
# - Or: set CLICKUP_ENABLED=false and redeploy

# 3. If version upgrade broke things
# - Revert deployment to previous version
# - Pin API calls to specific behavior (no v3 endpoints)
```

## Error Handling

| Alert | Condition | Severity |
|-------|-----------|----------|
| API unreachable | 0 successful requests in 5min | P1 |
| Auth failures | Any 401 response | P1 |
| Rate limited | X-RateLimit-Remaining = 0 | P2 |
| High latency | P95 > 3 seconds | P2 |
| Webhook failures | 3+ consecutive 5xx | P3 |

## Resources

- [ClickUp Status Page](https://status.clickup.com)
- [ClickUp Rate Limits](https://developer.clickup.com/docs/rate-limits)

## Next Steps

For version upgrades, see `clickup-upgrade-migration`.
