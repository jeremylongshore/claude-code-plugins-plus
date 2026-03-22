---
name: intercom-prod-checklist
description: |
  Execute Intercom production readiness checklist and rollback procedures.
  Use when deploying Intercom integrations to production, preparing for launch,
  or implementing go-live validation.
  Trigger with phrases like "intercom production", "deploy intercom",
  "intercom go-live", "intercom launch checklist", "intercom production readiness".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Production Checklist

## Overview

Complete checklist for deploying Intercom integrations to production, covering authentication, error handling, rate limits, webhooks, and monitoring.

## Pre-Deployment Checklist

### Authentication and Secrets

- [ ] Production access token stored in secret manager (not env files)
- [ ] Token has minimal required OAuth scopes
- [ ] Token rotation procedure documented and tested
- [ ] Separate tokens for dev/staging/production workspaces
- [ ] No hardcoded tokens in source code (verified with `grep -r "dG9r" .`)

### API Integration Quality

- [ ] All API calls wrapped in error handling (`try/catch` with `IntercomError`)
- [ ] 429 rate limit retry with exponential backoff implemented
- [ ] 5xx server error retry implemented
- [ ] Request timeouts configured (recommended: 30s)
- [ ] Pagination handles cursor-based iteration correctly
- [ ] Contact search uses compound queries efficiently

### Webhook Endpoints

- [ ] Webhook URL uses HTTPS (Intercom requires it)
- [ ] `X-Hub-Signature` verification implemented (HMAC-SHA1)
- [ ] Webhook handler responds within 5 seconds (Intercom timeout)
- [ ] Idempotency: duplicate webhooks handled gracefully
- [ ] Failed webhook retry handled (Intercom retries once after 1 min)

### Data Handling

- [ ] PII redacted from logs (emails, names, phone numbers)
- [ ] Contact data cached with appropriate TTL
- [ ] GDPR deletion handler implemented for contact data
- [ ] Custom attributes validated before sending to API

### Monitoring and Alerting

- [ ] Health check endpoint includes Intercom connectivity test
- [ ] Error rate alerting configured (threshold: 5% over 5 min)
- [ ] Rate limit usage tracked (alert at 80% of limit)
- [ ] Latency monitoring (alert if P95 > 2 seconds)
- [ ] Intercom status page monitored (https://status.intercom.com)

## Production Health Check

```typescript
import { IntercomClient, IntercomError } from "intercom-client";

interface IntercomHealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  latencyMs: number;
  authenticated: boolean;
  rateLimitRemaining?: number;
  error?: string;
}

async function checkIntercomHealth(
  client: IntercomClient
): Promise<IntercomHealthStatus> {
  const start = Date.now();
  try {
    const admins = await client.admins.list();
    return {
      status: "healthy",
      latencyMs: Date.now() - start,
      authenticated: true,
      rateLimitRemaining: undefined, // Parsed from response headers
    };
  } catch (err) {
    const latencyMs = Date.now() - start;
    if (err instanceof IntercomError) {
      return {
        status: err.statusCode === 429 ? "degraded" : "unhealthy",
        latencyMs,
        authenticated: err.statusCode !== 401,
        error: `${err.statusCode}: ${err.message}`,
      };
    }
    return {
      status: "unhealthy",
      latencyMs,
      authenticated: false,
      error: (err as Error).message,
    };
  }
}

// Express health endpoint
app.get("/health", async (req, res) => {
  const intercom = await checkIntercomHealth(client);
  const overall = intercom.status === "healthy" ? 200 : 503;
  res.status(overall).json({
    status: intercom.status,
    services: { intercom },
    timestamp: new Date().toISOString(),
  });
});
```

## Pre-Flight Verification Script

```bash
#!/bin/bash
set -euo pipefail

echo "=== Intercom Production Pre-Flight ==="

# 1. Auth check
echo -n "Auth: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me)
[ "$STATUS" = "200" ] && echo "PASS" || { echo "FAIL ($STATUS)"; exit 1; }

# 2. Rate limit headroom
echo -n "Rate limit remaining: "
REMAINING=$(curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me 2>/dev/null | grep -i x-ratelimit-remaining | awk '{print $2}')
echo "$REMAINING"

# 3. Intercom platform status
echo -n "Intercom status: "
curl -s https://status.intercom.com/api/v2/status.json | jq -r '.status.indicator'

# 4. Webhook endpoint reachable (if configured)
if [ -n "${WEBHOOK_URL:-}" ]; then
  echo -n "Webhook endpoint: "
  WH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$WEBHOOK_URL")
  echo "$WH_STATUS"
fi

echo "=== Pre-flight complete ==="
```

## Rollback Procedure

```bash
# 1. Disable Intercom integration via feature flag
curl -X PATCH https://your-config-service/flags/intercom_enabled \
  -d '{"value": false}'

# 2. If using k8s, rollback deployment
kubectl rollout undo deployment/intercom-service
kubectl rollout status deployment/intercom-service

# 3. Verify rollback
curl -s https://your-app.com/health | jq '.services.intercom'

# 4. Disable webhooks in Intercom Developer Hub
# (prevents queued webhook deliveries to unhealthy endpoint)
```

## Error Handling

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| API unreachable | 5xx > 10/min | P1 | Enable fallback, check status page |
| Auth failure | Any 401 | P1 | Rotate token, verify in Developer Hub |
| Rate limited | 429 > 5/min | P2 | Reduce request volume, add queuing |
| High latency | P95 > 3s | P2 | Check Intercom status, enable caching |
| Webhook failures | Delivery errors | P3 | Check endpoint health, verify signature |

## Resources

- [Intercom Status](https://status.intercom.com)
- [Rate Limiting](https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting)
- [Webhook Setup](https://developers.intercom.com/docs/webhooks/setting-up-webhooks)

## Next Steps

For version upgrades, see `intercom-upgrade-migration`.
