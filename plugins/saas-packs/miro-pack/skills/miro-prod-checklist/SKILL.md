---
name: miro-prod-checklist
description: |
  Execute Miro REST API v2 production deployment checklist and rollback procedures.
  Use when deploying Miro integrations to production, preparing for launch,
  or implementing go-live procedures for Miro apps.
  Trigger with phrases like "miro production", "deploy miro",
  "miro go-live", "miro launch checklist", "miro production ready".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, production, deployment]
compatible-with: claude-code
---

# Miro Production Checklist

## Overview

Complete checklist for deploying Miro REST API v2 integrations to production, covering OAuth configuration, rate limit readiness, monitoring, and rollback.

## Pre-Deployment: OAuth & Scopes

- [ ] **Production Miro app created** at https://developers.miro.com (separate from dev app)
- [ ] **OAuth scopes minimized** — only scopes actively used (see `miro-security-basics`)
- [ ] **Redirect URI** points to production HTTPS endpoint
- [ ] **Client secret** stored in secret manager (not env vars on disk)
- [ ] **Token refresh** logic tested — handles expired tokens gracefully
- [ ] **Token storage** uses encrypted database or vault (not filesystem)

## Pre-Deployment: Code Quality

- [ ] **No hardcoded tokens** — scan with `grep -r "eyJ\|Bearer " src/`
- [ ] **Error handling** covers all Miro HTTP status codes (400, 401, 403, 404, 429, 5xx)
- [ ] **Rate limiting** — backoff with `Retry-After` header support (see `miro-rate-limits`)
- [ ] **Webhook signatures** validated with timing-safe comparison
- [ ] **Pagination** handled for all list endpoints (`cursor` parameter)
- [ ] **Content-Type** header set to `application/json` on all POST/PATCH requests
- [ ] **All tests passing** including integration tests against test board

## Pre-Deployment: Infrastructure

- [ ] **Health check** endpoint verifies Miro API connectivity

```typescript
// GET /health
async function healthCheck() {
  const start = Date.now();
  try {
    const response = await fetch('https://api.miro.com/v2/boards?limit=1', {
      headers: { 'Authorization': `Bearer ${token}` },
      signal: AbortSignal.timeout(5000),
    });

    return {
      miro: {
        status: response.ok ? 'healthy' : 'degraded',
        latencyMs: Date.now() - start,
        rateLimitRemaining: response.headers.get('X-RateLimit-Remaining'),
      },
    };
  } catch (error) {
    return {
      miro: { status: 'unhealthy', latencyMs: Date.now() - start, error: error.message },
    };
  }
}
```

- [ ] **Circuit breaker** configured for Miro API calls

```typescript
class MiroCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private readonly threshold = 5;
  private readonly resetMs = 60000;

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.isOpen()) {
      throw new Error('Miro circuit breaker is open — API calls suspended');
    }

    try {
      const result = await operation();
      this.failures = 0;
      return result;
    } catch (error) {
      this.failures++;
      this.lastFailure = Date.now();
      throw error;
    }
  }

  private isOpen(): boolean {
    if (this.failures < this.threshold) return false;
    if (Date.now() - this.lastFailure > this.resetMs) {
      this.failures = 0; // Half-open: allow one retry
      return false;
    }
    return true;
  }
}
```

- [ ] **Graceful degradation** — app continues working if Miro API is unavailable
- [ ] **Monitoring** — Prometheus/Datadog metrics for Miro API latency and error rates
- [ ] **Alerting** configured for error rate >5%, P95 latency >3s, and 429 responses

## Pre-Deployment: Miro App Settings

- [ ] **App name and description** are professional (visible to users during OAuth consent)
- [ ] **App icon** uploaded (displayed in Miro marketplace and OAuth screen)
- [ ] **Support email** configured in app settings
- [ ] **App manifest** reviewed if using Miro app manifest format

## Deployment Verification

```bash
# 1. Verify production token works
curl -s -w "\nHTTP %{http_code} in %{time_total}s\n" \
  -H "Authorization: Bearer $MIRO_ACCESS_TOKEN_PROD" \
  "https://api.miro.com/v2/boards?limit=1"

# 2. Check rate limit headroom
curl -sI -H "Authorization: Bearer $MIRO_ACCESS_TOKEN_PROD" \
  "https://api.miro.com/v2/boards?limit=1" | grep -i ratelimit

# 3. Verify webhook endpoint is reachable (if using webhooks)
curl -s -o /dev/null -w "%{http_code}" https://your-app.com/webhooks/miro

# 4. Verify health check
curl -s https://your-app.com/health | jq '.miro'
```

## Post-Deployment Monitoring

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Miro API Down | 5xx errors > 10/min | P1 | Enable fallback, check status.miro.com |
| Auth Failures | 401/403 > 0/min | P1 | Check token, verify scopes |
| Rate Limited | 429 errors > 5/min | P2 | Reduce request rate, check queue config |
| High Latency | P95 > 3000ms | P2 | Check board size, enable caching |
| Health Degraded | Health check fails 3x | P2 | Investigate connectivity |

## Rollback Procedure

```bash
# Immediate rollback — disable Miro integration
# Option 1: Feature flag
curl -X PATCH https://config.your-app.com/flags \
  -d '{"miro_enabled": false}'

# Option 2: Environment variable
# Set MIRO_ENABLED=false and restart

# Option 3: Container rollback
kubectl rollout undo deployment/miro-integration
kubectl rollout status deployment/miro-integration
```

## Documentation Requirements

- [ ] Incident runbook created (see `miro-incident-runbook`)
- [ ] Token rotation procedure documented
- [ ] On-call escalation path includes Miro-specific steps
- [ ] Board cleanup procedure for orphaned test data

## Resources

- [Miro App Settings](https://developers.miro.com)
- [Miro Status Page](https://status.miro.com)
- [App Manifest](https://developers.miro.com/docs/app-manifest)

## Next Steps

For version upgrades, see `miro-upgrade-migration`.
