---
name: notion-prod-checklist
description: |
  Execute Notion production deployment checklist and readiness verification.
  Use when deploying Notion integrations to production, preparing for launch,
  or verifying go-live readiness.
  Trigger with phrases like "notion production", "deploy notion",
  "notion go-live", "notion launch checklist", "notion production ready".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Production Checklist

## Overview
Complete checklist for deploying Notion integrations to production, covering auth, error handling, rate limits, monitoring, and rollback.

## Prerequisites
- Working integration tested in staging
- Production Notion token ready
- Deployment platform configured

## Instructions

### Authentication & Secrets
- [ ] Production `NOTION_TOKEN` stored in secret manager (not env files)
- [ ] Token has minimum required capabilities (least privilege)
- [ ] All target pages/databases shared with production integration
- [ ] Token rotation procedure documented
- [ ] No tokens in source code or git history (`grep -r "ntn_\|secret_" .`)

### Error Handling
- [ ] All API calls wrapped in try/catch with `isNotionClientError`
- [ ] 429 rate limits handled (SDK built-in retry enabled)
- [ ] 404 errors handled gracefully (page not shared vs not exists)
- [ ] 401/403 errors trigger alerts (token expired or revoked)
- [ ] Validation errors (400) logged with full error message

### Rate Limit Compliance
- [ ] Bulk operations use queuing (p-queue at 3 req/s max)
- [ ] Pagination uses `start_cursor`, not repeated full queries
- [ ] No unbounded parallel requests (`Promise.all` over large arrays)
- [ ] Batch size respects API limits (100 items per query, 100 blocks per append)

### Monitoring & Alerting
```typescript
// Health check endpoint
async function notionHealthCheck() {
  const start = Date.now();
  try {
    const me = await notion.users.me({});
    return {
      status: 'healthy',
      latencyMs: Date.now() - start,
      bot: me.name,
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      latencyMs: Date.now() - start,
      error: isNotionClientError(error) ? error.code : 'unknown',
    };
  }
}
```

- [ ] Health check endpoint includes Notion connectivity test
- [ ] Alerts configured for: auth failures, high error rate, elevated latency
- [ ] Structured logging for all Notion API calls (request ID, latency, status)

### Data Integrity
- [ ] Page property names match production database schema exactly
- [ ] Required title property always included in `pages.create`
- [ ] Select/multi-select option names match existing options
- [ ] Date properties use ISO 8601 format (`2026-04-01`)
- [ ] Rich text arrays are never empty (Notion rejects `[]`)

### API Version
```typescript
// Pin the API version explicitly
const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  notionVersion: '2022-06-28', // Pin to tested version
});
```
- [ ] `notionVersion` pinned in client configuration
- [ ] Tested against the specific API version in production

### Graceful Degradation
```typescript
async function getDataWithFallback(dbId: string) {
  try {
    return await notion.databases.query({ database_id: dbId });
  } catch (error) {
    console.error('Notion unavailable, using cached data');
    return getCachedResults(dbId);
  }
}
```
- [ ] Application works (degraded) when Notion is unavailable
- [ ] Cached data available for read-heavy endpoints
- [ ] Users notified of degraded state (not silent failures)

### Rollback Plan
```bash
# Verify pre-deployment
curl -sf https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq .name

# Quick rollback: revert to previous deployment
# (platform-specific: kubectl rollout undo, vercel rollback, etc.)
```
- [ ] Previous working version tagged and deployable
- [ ] Rollback procedure documented and tested
- [ ] Data migration (if any) is reversible

## Output
- All checklist items verified
- Health check passing against production Notion API
- Monitoring and alerting active
- Rollback procedure tested

## Error Handling
| Alert | Condition | Severity |
|-------|-----------|----------|
| Auth Failure | 401/403 errors > 0 | P1 — token may be revoked |
| High Error Rate | >5% of requests failing | P2 |
| Rate Limited | 429 errors sustained | P2 — review request patterns |
| High Latency | P95 > 3000ms | P3 |
| Notion Down | status.notion.com incident | P2 — activate fallback |

## Examples

### Pre-Deploy Smoke Test
```bash
#!/bin/bash
echo "Notion Production Smoke Test"
RESULT=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28")

if [ "$RESULT" = "200" ]; then
  echo "PASS: Auth OK"
else
  echo "FAIL: HTTP $RESULT"
  exit 1
fi
```

## Resources
- [Notion API Best Practices](https://developers.notion.com/docs/best-practices-for-handling-api-keys)
- [Notion Status Page](https://status.notion.com)
- [API Request Limits](https://developers.notion.com/reference/request-limits)

## Next Steps
For version upgrades, see `notion-upgrade-migration`.
