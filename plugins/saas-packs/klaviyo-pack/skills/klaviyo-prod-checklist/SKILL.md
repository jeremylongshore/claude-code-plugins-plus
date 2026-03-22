---
name: klaviyo-prod-checklist
description: |
  Execute Klaviyo production deployment checklist and validation procedures.
  Use when deploying Klaviyo integrations to production, preparing for launch,
  or implementing go-live procedures for email/SMS marketing.
  Trigger with phrases like "klaviyo production", "deploy klaviyo",
  "klaviyo go-live", "klaviyo launch checklist", "klaviyo prod ready".
allowed-tools: Read, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Production Checklist

## Overview

Complete checklist for deploying Klaviyo integrations to production, with health checks, rollback procedures, and validation against real Klaviyo API endpoints.

## Prerequisites

- Staging environment tested and verified
- Production API key with correct scopes (`pk_*`)
- Webhook signing secret configured
- Monitoring and alerting ready

## Instructions

### Pre-Deployment Checklist

#### Authentication & Secrets
- [ ] Production `KLAVIYO_PRIVATE_KEY` stored in secret manager (not env file)
- [ ] Key has minimal scopes (only what the app needs)
- [ ] Webhook signing secret (`KLAVIYO_WEBHOOK_SIGNING_SECRET`) configured
- [ ] Public key (`KLAVIYO_PUBLIC_KEY`) set for client-side tracking (if used)
- [ ] No hardcoded keys in codebase (`grep -r "pk_" src/`)

#### API Integration
- [ ] All API calls use `klaviyo-api` SDK (not raw HTTP)
- [ ] SDK version pinned in `package.json` (not `^` or `*`)
- [ ] `revision` header set to `2024-10-15` (or current supported revision)
- [ ] All profile creates use `createOrUpdateProfile` (upsert, not create)
- [ ] Events include `uniqueId` for deduplication where applicable
- [ ] Phone numbers validated as E.164 format (`+15551234567`)

#### Error Handling & Resilience
- [ ] 429 retry logic honors `Retry-After` header
- [ ] 5xx errors retried with exponential backoff
- [ ] 401/403 errors logged with alert (key rotation needed)
- [ ] Circuit breaker or graceful degradation when Klaviyo is down
- [ ] Request queue prevents exceeding 75 req/s burst limit

#### Webhook Security
- [ ] Webhook endpoint uses HTTPS only
- [ ] HMAC-SHA256 signature verification enabled
- [ ] Idempotency handling (dedup by event ID)
- [ ] Webhook endpoint returns 200 within 30 seconds

#### Monitoring
- [ ] Health check endpoint includes Klaviyo connectivity test
- [ ] Alert on 429 rate (>5/min = P2)
- [ ] Alert on 401/403 errors (any = P1)
- [ ] Alert on 5xx errors (>10/min = P1)
- [ ] API latency tracked (P95 > 5s = P2)
- [ ] Klaviyo status page monitored ([status.klaviyo.com](https://status.klaviyo.com))

### Health Check Implementation

```typescript
// src/health/klaviyo.ts
import { ApiKeySession, AccountsApi } from 'klaviyo-api';

export async function checkKlaviyoHealth(): Promise<{
  status: 'healthy' | 'degraded' | 'down';
  latencyMs: number;
  accountId?: string;
  error?: string;
}> {
  const start = Date.now();
  try {
    const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
    const accountsApi = new AccountsApi(session);
    const result = await accountsApi.getAccounts();

    return {
      status: 'healthy',
      latencyMs: Date.now() - start,
      accountId: result.body.data[0].id,
    };
  } catch (error: any) {
    return {
      status: error.status === 429 ? 'degraded' : 'down',
      latencyMs: Date.now() - start,
      error: `${error.status}: ${error.body?.errors?.[0]?.detail || error.message}`,
    };
  }
}

// Express health endpoint
app.get('/health', async (req, res) => {
  const klaviyo = await checkKlaviyoHealth();
  const overallStatus = klaviyo.status === 'healthy' ? 200 : 503;
  res.status(overallStatus).json({
    status: klaviyo.status,
    services: { klaviyo },
    timestamp: new Date().toISOString(),
  });
});
```

### Pre-Flight Validation Script

```bash
#!/bin/bash
# scripts/preflight-klaviyo.sh
set -euo pipefail

echo "=== Klaviyo Production Pre-Flight ==="

# 1. Check Klaviyo status
echo -n "Klaviyo Status Page: "
STATUS=$(curl -s "https://status.klaviyo.com/api/v2/status.json" | python3 -c "import sys,json; print(json.load(sys.stdin)['status']['description'])" 2>/dev/null)
echo "$STATUS"
[ "$STATUS" = "All Systems Operational" ] || echo "WARNING: Klaviyo has active incidents"

# 2. Verify API key
echo -n "API Auth: "
HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/")
echo "HTTP $HTTP_CODE"
[ "$HTTP_CODE" = "200" ] || { echo "FAIL: API auth returned $HTTP_CODE"; exit 1; }

# 3. Check rate limit headroom
echo -n "Rate Limit: "
curl -s -I \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/profiles/?page[size]=1" 2>/dev/null \
  | grep -i "ratelimit-remaining" || echo "Headers not available"

# 4. Verify SDK version
echo -n "SDK Version: "
node -e "console.log(require('klaviyo-api/package.json').version)" 2>/dev/null || echo "Not installed"

echo ""
echo "=== Pre-flight complete ==="
```

### Rollback Procedure

```bash
# Immediate rollback: disable Klaviyo integration
# Option 1: Feature flag (preferred)
# Set KLAVIYO_ENABLED=false in your deployment platform

# Option 2: Deploy previous version
git log --oneline -5  # Find last known-good commit
git revert HEAD        # Revert the deployment commit
# Push and deploy

# Option 3: If using Kubernetes
kubectl rollout undo deployment/your-app
kubectl rollout status deployment/your-app
```

## Alert Thresholds

| Alert | Condition | Severity |
|-------|-----------|----------|
| API Auth Failure | Any 401/403 | P1 -- key may be revoked |
| API Unreachable | 5xx > 10/min | P1 -- check status page |
| Rate Limited | 429 > 5/min | P2 -- reduce request volume |
| High Latency | P95 > 5s | P2 -- check network/Klaviyo load |
| Webhook Signature Invalid | Any rejection | P2 -- verify signing secret |

## Resources

- [Klaviyo Status Page](https://status.klaviyo.com)
- [API Versioning Policy](https://developers.klaviyo.com/en/docs/api_versioning_and_deprecation_policy)
- [Rate Limits](https://developers.klaviyo.com/en/docs/rate_limits_and_error_handling)

## Next Steps

For version upgrades, see `klaviyo-upgrade-migration`.
