---
name: adobe-prod-checklist
description: |
  Execute Adobe production deployment checklist covering credential management,
  API health checks, rate limit configuration, and rollback procedures
  for Firefly Services, PDF Services, and I/O Events integrations.
  Trigger with phrases like "adobe production", "deploy adobe",
  "adobe go-live", "adobe launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Production Checklist

## Overview

Complete checklist for deploying Adobe API integrations to production, covering credential security, health monitoring, graceful degradation, and rollback procedures.

## Prerequisites

- Staging environment tested and verified
- Production OAuth credentials created in Developer Console
- Deployment pipeline with secret injection
- Monitoring and alerting infrastructure ready

## Instructions

### Pre-Deployment: Credentials & Configuration

- [ ] Production OAuth Server-to-Server credentials created (separate from staging)
- [ ] `ADOBE_CLIENT_ID` and `ADOBE_CLIENT_SECRET` stored in secret manager (not env files)
- [ ] Scopes are minimal: only APIs actually used in production
- [ ] Token caching implemented (avoid re-generating per request)
- [ ] I/O Events webhook endpoints use HTTPS with valid TLS cert
- [ ] Webhook challenge response handler implemented (for registration)

### Pre-Deployment: Code Quality

- [ ] All tests passing (`npm test`)
- [ ] No hardcoded credentials (grep for `p8_` prefix patterns)
- [ ] Error handling covers: `401`, `403`, `429`, `500`, `503`
- [ ] Rate limiting/backoff with `Retry-After` header support
- [ ] Webhook signature verification using RSA-SHA256
- [ ] Logging redacts credentials and PII
- [ ] API response validation (Zod or equivalent)

### Pre-Deployment: Infrastructure

- [ ] Health check endpoint verifies Adobe IMS token generation:

```typescript
// api/health.ts
export async function adobeHealthCheck() {
  const start = Date.now();
  try {
    // Test token generation (validates credentials are still valid)
    const token = await getAccessToken();
    return {
      status: 'healthy',
      latencyMs: Date.now() - start,
      tokenValid: !!token,
    };
  } catch (error: any) {
    return {
      status: 'unhealthy',
      latencyMs: Date.now() - start,
      error: error.message,
    };
  }
}
```

- [ ] Circuit breaker configured for Adobe API calls
- [ ] Graceful degradation: app works (degraded) if Adobe is down
- [ ] PDF Services monthly quota tracking (if on free tier)

### Deploy: Gradual Rollout

```bash
# 1. Pre-flight checks
curl -sf https://staging.example.com/health | jq '.services.adobe'
curl -s https://status.adobe.com | head -5

# 2. Verify production credentials work
curl -s -o /dev/null -w "%{http_code}" -X POST \
  'https://ims-na1.adobelogin.com/ims/token/v3' \
  -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}"
# Expected: 200

# 3. Deploy canary (10%)
kubectl set image deployment/app app=image:new-version
kubectl rollout pause deployment/app

# 4. Monitor for 10 minutes — check error rates
# Watch for 401 (credential issues), 429 (rate limits), 500 (server errors)

# 5. If healthy, complete rollout
kubectl rollout resume deployment/app
kubectl rollout status deployment/app
```

### Post-Deployment Verification

- [ ] Health check endpoint returns `healthy` for Adobe
- [ ] Test a real API call (e.g., Firefly image generation, PDF extraction)
- [ ] Webhook delivery confirmed (check I/O Events dashboard)
- [ ] Error rate baseline established in monitoring
- [ ] On-call team has `adobe-incident-runbook` accessible

### Rollback Procedure

```bash
# Immediate rollback
kubectl rollout undo deployment/app
kubectl rollout status deployment/app

# Verify old version is healthy
curl -sf https://production.example.com/health | jq '.services.adobe'
```

## Alert Configuration

| Alert | Condition | Severity |
|-------|-----------|----------|
| Adobe Auth Failure | Any `401` errors | P1 — credential issue |
| Adobe Rate Limited | `429` errors > 5/min | P2 — reduce throughput |
| Adobe API Down | `503` errors > 10/min | P2 — enable fallback |
| Adobe High Latency | p99 > 10s | P3 — investigate |
| PDF Quota Low | < 50 transactions remaining | P3 — upgrade or throttle |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 401 after deploy | Wrong credentials for environment | Verify secret manager path |
| 429 spike | Traffic increase from new feature | Add rate limiting queue |
| Health check flapping | Token caching not working | Check cache TTL logic |
| Webhook delivery stopped | Challenge response broken | Test webhook registration |

## Resources

- [Adobe Status Page](https://status.adobe.com)
- [Adobe Developer Console](https://developer.adobe.com/console)
- [Adobe Developer Support](https://developer.adobe.com/support)

## Next Steps

For version upgrades, see `adobe-upgrade-migration`.
