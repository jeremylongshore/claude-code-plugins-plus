---
name: hubspot-prod-checklist
description: |
  Execute HubSpot production deployment checklist and go-live procedures.
  Use when deploying HubSpot integrations to production, preparing for launch,
  or implementing health checks for HubSpot connectivity.
  Trigger with phrases like "hubspot production", "deploy hubspot",
  "hubspot go-live", "hubspot launch checklist", "hubspot health check".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Production Checklist

## Overview

Complete checklist for deploying HubSpot CRM integrations to production with health checks, monitoring, and rollback procedures.

## Prerequisites

- Staging environment tested and verified
- Production private app token with minimal scopes
- Deployment pipeline configured
- Monitoring/alerting ready

## Instructions

### Step 1: Pre-Deployment Verification

- [ ] Production private app created with minimal scopes
- [ ] Access token stored in secret manager (not env file)
- [ ] `.env` files in `.gitignore`
- [ ] No hardcoded tokens in source (`grep -r "pat-na1" src/`)
- [ ] Webhook endpoints use HTTPS only
- [ ] Webhook signature verification implemented (v3)
- [ ] Error handling covers 401, 403, 404, 409, 429, 5xx
- [ ] Rate limiting/backoff implemented (`numberOfApiCallRetries: 3`)
- [ ] Batch operations used where possible (max 100/batch)
- [ ] All tests passing against developer test account

### Step 2: Health Check Endpoint

```typescript
import * as hubspot from '@hubspot/api-client';

interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  hubspot: {
    connected: boolean;
    latencyMs: number;
    rateLimitRemaining?: number;
  };
  timestamp: string;
}

async function hubspotHealthCheck(): Promise<HealthCheckResult> {
  const client = new hubspot.Client({
    accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  });

  const start = Date.now();
  try {
    // Cheapest possible API call: fetch 1 contact
    await client.crm.contacts.basicApi.getPage(1);
    return {
      status: 'healthy',
      hubspot: {
        connected: true,
        latencyMs: Date.now() - start,
      },
      timestamp: new Date().toISOString(),
    };
  } catch (error: any) {
    const status = error?.code || error?.statusCode || 500;
    return {
      status: status === 429 ? 'degraded' : 'unhealthy',
      hubspot: {
        connected: false,
        latencyMs: Date.now() - start,
      },
      timestamp: new Date().toISOString(),
    };
  }
}

// Express endpoint
app.get('/health', async (req, res) => {
  const result = await hubspotHealthCheck();
  const httpStatus = result.status === 'healthy' ? 200 :
                     result.status === 'degraded' ? 200 : 503;
  res.status(httpStatus).json(result);
});
```

### Step 3: Monitoring Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| HubSpot unreachable | Health check fails 3x | P1 |
| High error rate | 5xx errors > 10/min | P1 |
| Auth failure | Any 401/403 response | P1 (token revoked?) |
| Rate limited | 429 errors > 5/min | P2 |
| High latency | p95 > 3000ms | P2 |
| Daily quota low | < 10% remaining | P3 |

### Step 4: Graceful Degradation

```typescript
async function withHubSpotFallback<T>(
  operation: () => Promise<T>,
  fallback: T
): Promise<{ data: T; degraded: boolean }> {
  try {
    const data = await operation();
    return { data, degraded: false };
  } catch (error: any) {
    console.error('HubSpot call failed, using fallback:', {
      status: error?.code,
      message: error?.body?.message,
      correlationId: error?.body?.correlationId,
    });
    return { data: fallback, degraded: true };
  }
}
```

### Step 5: Deploy Verification

```bash
#!/bin/bash
# post-deploy-verify.sh

echo "=== HubSpot Post-Deploy Verification ==="

# 1. Health check
HEALTH=$(curl -sf https://your-app.com/health | jq -r '.hubspot.connected')
echo "HubSpot connected: $HEALTH"
[ "$HEALTH" = "true" ] || { echo "FAIL: HubSpot not connected"; exit 1; }

# 2. Verify CRM access
STATUS=$(curl -so /dev/null -w "%{http_code}" \
  https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN")
echo "CRM API status: $STATUS"
[ "$STATUS" = "200" ] || { echo "FAIL: CRM access denied"; exit 1; }

# 3. Check rate limit headroom
REMAINING=$(curl -sI https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i 'x-hubspot-ratelimit-daily-remaining' | awk '{print $2}' | tr -d '\r')
echo "Daily rate limit remaining: $REMAINING"

# 4. Check HubSpot status page
HS_STATUS=$(curl -s https://status.hubspot.com/api/v2/summary.json | jq -r '.status.description')
echo "HubSpot platform status: $HS_STATUS"

echo "=== Verification complete ==="
```

## Output

- All checklist items verified
- Health check endpoint deployed and accessible
- Monitoring alerts configured
- Graceful degradation implemented
- Post-deploy verification script passing

## Error Handling

| Issue | Response |
|-------|----------|
| Health check fails after deploy | Rollback immediately |
| 401 in production | Token was regenerated -- update secret and redeploy |
| 429 spike after deploy | New code making too many calls -- add batching/caching |
| 5xx from HubSpot | Check status.hubspot.com -- enable fallback mode |

## Resources

- [HubSpot Status Page](https://status.hubspot.com)
- [HubSpot API Usage Guidelines](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [Private Apps Overview](https://developers.hubspot.com/docs/guides/apps/private-apps/overview)

## Next Steps

For version upgrades, see `hubspot-upgrade-migration`.
