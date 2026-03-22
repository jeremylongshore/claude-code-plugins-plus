---
name: webflow-prod-checklist
description: |
  Execute Webflow production deployment checklist — token security, rate limit hardening,
  health checks, circuit breakers, gradual rollout, and rollback procedures.
  Use when deploying Webflow integrations to production or preparing for launch.
  Trigger with phrases like "webflow production", "deploy webflow",
  "webflow go-live", "webflow launch checklist", "webflow production ready".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Production Checklist

## Overview

Complete pre-deployment checklist for Webflow Data API v2 integrations, covering
authentication, error handling, rate limits, monitoring, and rollback.

## Prerequisites

- Staging environment tested and verified
- Production API token with minimal scopes
- Deployment pipeline configured
- Monitoring/alerting infrastructure ready

## Instructions

### Pre-Deployment Configuration

- [ ] **Production API token** in secure vault (not .env file on server)
- [ ] **Minimal scopes** — only scopes the integration actually uses
- [ ] **Site token** used where workspace token is not needed
- [ ] **Environment variables** set in deployment platform (Vercel/Fly/Cloud Run)
- [ ] **Webhook secrets** stored securely, not hardcoded
- [ ] **No tokens in client-side code** — all API calls server-side only

### Code Quality Verification

- [ ] **All tests passing** — unit tests with mocked SDK, integration tests with test token
- [ ] **No hardcoded credentials** — `grep -r "Bearer " src/` returns nothing
- [ ] **Error handling** covers 400, 401, 403, 404, 409, 429, 500
- [ ] **Rate limit handling** — SDK `maxRetries` configured, bulk endpoints used
- [ ] **Pagination** — all list operations handle `offset`/`limit` correctly
- [ ] **Logging** is production-appropriate (no PII, structured JSON)
- [ ] **Webhook signatures verified** — `verifyWebhookSignature()` on every webhook

### Rate Limit Readiness

- [ ] **Bulk endpoints** used for multi-item operations (100 items/request max)
- [ ] **Request queue** with concurrency control (p-queue or similar)
- [ ] **Site publish** rate limited to max 1 per minute
- [ ] **Retry-After** header honored in custom retry logic
- [ ] **SDK maxRetries** set (default: 2, increase for critical paths)

### Health Check Endpoint

```typescript
// api/health.ts
import { WebflowClient } from "webflow-api";

export async function GET() {
  const webflow = new WebflowClient({
    accessToken: process.env.WEBFLOW_API_TOKEN!,
  });

  const checks: Record<string, any> = {};
  const start = Date.now();

  try {
    const { sites } = await webflow.sites.list();
    checks.webflow = {
      status: "connected",
      sites: sites?.length || 0,
      latencyMs: Date.now() - start,
    };
  } catch (error: any) {
    checks.webflow = {
      status: "disconnected",
      error: error.statusCode || error.message,
      latencyMs: Date.now() - start,
    };
  }

  const healthy = checks.webflow.status === "connected";

  return Response.json(
    {
      status: healthy ? "healthy" : "degraded",
      services: checks,
      timestamp: new Date().toISOString(),
    },
    { status: healthy ? 200 : 503 }
  );
}
```

### Circuit Breaker Pattern

```typescript
class WebflowCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: "closed" | "open" | "half-open" = "closed";

  constructor(
    private threshold = 5,      // failures before opening
    private resetTimeMs = 60000  // time before trying again
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === "open") {
      if (Date.now() - this.lastFailure > this.resetTimeMs) {
        this.state = "half-open";
      } else {
        throw new Error("Circuit breaker is open — Webflow API unavailable");
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error: any) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess() {
    this.failures = 0;
    this.state = "closed";
  }

  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = "open";
      console.error(`Circuit breaker OPEN after ${this.failures} failures`);
    }
  }
}

const breaker = new WebflowCircuitBreaker();

// Usage
const sites = await breaker.execute(() => webflow.sites.list());
```

### Monitoring Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| API unreachable | Health check fails 3x consecutive | P1 |
| Auth failure | Any 401 or 403 response | P1 |
| High error rate | Error rate > 5% over 5 min | P2 |
| Rate limited | 429 responses > 5/min | P2 |
| High latency | P95 > 3000ms | P3 |
| Token expiring | Token age > 90 days (rotation schedule) | P3 |

### Graceful Degradation

```typescript
async function getContentWithFallback(
  collectionId: string,
  cachedData: any[]
): Promise<any[]> {
  try {
    const { items } = await breaker.execute(() =>
      webflow.collections.items.listItemsLive(collectionId)
    );
    // Update cache on success
    await updateCache(collectionId, items);
    return items || [];
  } catch (error) {
    console.warn("Webflow unavailable, serving cached content");
    return cachedData;
  }
}
```

### Pre-Flight Verification Script

```bash
#!/bin/bash
echo "=== Webflow Production Pre-Flight ==="

# 1. Token works
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  https://api.webflow.com/v2/sites)
echo "Token valid: $([ "$HTTP" = "200" ] && echo "YES" || echo "NO (HTTP $HTTP)")"

# 2. Webflow platform status
STATUS=$(curl -s https://status.webflow.com/api/v2/status.json | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['status']['description'])" 2>/dev/null)
echo "Webflow status: ${STATUS:-unknown}"

# 3. Rate limit headroom
curl -s -I -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  https://api.webflow.com/v2/sites 2>/dev/null | \
  grep -i "x-ratelimit-remaining" || echo "Rate limit headers not available"

# 4. Health endpoint
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://your-app.com/api/health)
echo "Health endpoint: HTTP $HEALTH"
```

### Rollback Procedure

```bash
# Immediate rollback steps:
# 1. Revert to previous deployment
vercel rollback     # Vercel
fly releases        # Fly.io — find previous release
fly deploy --image registry/app:previous-tag  # Fly.io

# 2. If using feature flags, disable Webflow integration
# 3. Monitor error rates for resolution
```

## Output

- Production-hardened Webflow integration
- Health check endpoint with latency tracking
- Circuit breaker preventing cascade failures
- Monitoring alerts configured
- Rollback procedure documented and tested

## Error Handling

| Issue | Response | Severity |
|-------|----------|----------|
| Token revoked in production | Rotate immediately, restart pods | P1 |
| Webflow outage | Circuit breaker opens, serve cache | P2 |
| Rate limit exhaustion | Queue backs up, requests delayed | P2 |
| Webhook delivery failures | Check ngrok/tunnel, verify URL | P3 |

## Resources

- [Webflow Status Page](https://status.webflow.com)
- [Rate Limits](https://developers.webflow.com/data/reference/rate-limits)
- [API Reference](https://developers.webflow.com/data/reference/rest-introduction)

## Next Steps

For version upgrades, see `webflow-upgrade-migration`.
