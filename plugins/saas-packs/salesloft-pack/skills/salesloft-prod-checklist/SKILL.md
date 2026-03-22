---
name: salesloft-prod-checklist
description: |
  Production readiness checklist for SalesLoft API integrations.
  Use when deploying SalesLoft integrations to production, preparing for launch,
  or validating go-live requirements.
  Trigger: "salesloft production", "deploy salesloft", "salesloft go-live checklist".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Production Checklist

## Overview

Go-live checklist for SalesLoft API integrations covering auth, error handling, monitoring, rate limits, and rollback procedures.

## Pre-Launch Checklist

### Authentication & Secrets
- [ ] Production OAuth app created (separate from dev/staging)
- [ ] Tokens stored in secret manager (AWS Secrets Manager, GCP Secret Manager, Vault)
- [ ] Token refresh logic tested (simulated expired token)
- [ ] Webhook signing secret rotated from dev value

### Error Handling
- [ ] 401 triggers automatic token refresh (not crash)
- [ ] 429 handled with backoff using `Retry-After` header
- [ ] 5xx retried with exponential backoff (max 3 attempts)
- [ ] 422 validation errors logged with request payload
- [ ] Circuit breaker prevents cascade during SalesLoft outages

### Rate Limiting
- [ ] Cost-based budget calculated for expected volume
- [ ] Deep pagination avoided (page > 100 costs 3-30x)
- [ ] Bulk operations use `p-queue` or similar throttle
- [ ] Rate limit headers logged for capacity planning

### Monitoring & Alerting
```typescript
// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const start = Date.now();
    await api.get('/me.json');
    res.json({
      status: 'healthy',
      salesloft: { connected: true, latencyMs: Date.now() - start },
    });
  } catch {
    res.status(503).json({ status: 'degraded', salesloft: { connected: false } });
  }
});
```

- [ ] Health check includes SalesLoft connectivity
- [ ] Alert on 5xx error rate > 5/min (P1)
- [ ] Alert on 429 rate > 10/min (P2)
- [ ] Alert on auth failure (P1 -- token may be revoked)
- [ ] Latency p99 tracked (baseline: 300ms reads, 500ms writes)

### Data Integrity
- [ ] Idempotency keys on all create/update operations
- [ ] Duplicate detection by email before person creation
- [ ] Webhook events deduplicated by event ID
- [ ] Audit log captures all API mutations

### Rollback Procedure

```bash
# 1. Revert deployment
kubectl rollout undo deployment/salesloft-integration
# or: git revert HEAD && git push

# 2. Verify old version healthy
curl -f https://app.example.com/health

# 3. Pause any running cadence syncs
# 4. Notify sales team of rollback
```

## Post-Launch Verification

```bash
# Smoke test production endpoints
curl -s -H "Authorization: Bearer $PROD_TOKEN" \
  https://api.salesloft.com/v2/me.json | jq '.data.email'

curl -s -H "Authorization: Bearer $PROD_TOKEN" \
  'https://api.salesloft.com/v2/people.json?per_page=1' | jq '.metadata.paging.total_count'
```

## Error Handling

| Alert | Condition | Severity | Runbook |
|-------|-----------|----------|---------|
| Auth Down | 401 errors > 0 | P1 | Rotate token, check OAuth app |
| Rate Limited | 429 errors > 10/min | P2 | Reduce request volume |
| API Errors | 5xx > 5/min | P1 | Check status.salesloft.com |
| High Latency | p99 > 2000ms | P3 | Check SalesLoft status |

## Resources

- [SalesLoft Status](https://status.salesloft.com)
- [API Logs](https://developers.salesloft.com/docs/platform/guides/api-logs/)

## Next Steps

For version upgrades, see `salesloft-upgrade-migration`.
