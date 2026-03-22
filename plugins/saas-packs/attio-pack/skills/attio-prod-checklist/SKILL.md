---
name: attio-prod-checklist
description: |
  Production readiness checklist for Attio API integrations -- auth,
  error handling, rate limits, health checks, monitoring, and rollback.
  Trigger: "attio production", "deploy attio", "attio go-live",
  "attio launch checklist", "attio production ready".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Production Checklist

## Overview

Systematic checklist for launching Attio API integrations in production. Covers the real failure modes observed in Attio integrations.

## Prerequisites

- Staging environment tested
- Production API token created with minimal scopes
- Monitoring infrastructure available

## Instructions

### Phase 1: Authentication & Secrets

```
[ ] Production token created with minimal scopes (see attio-security-basics)
[ ] Token stored in platform secrets manager (not env file on disk)
[ ] Separate tokens for dev/staging/prod environments
[ ] .env files in .gitignore
[ ] No tokens in logs, error messages, or client-side bundles
[ ] Token rotation procedure documented
```

**Verify:**
```bash
# Confirm production token works
curl -s -o /dev/null -w "%{http_code}" \
  https://api.attio.com/v2/objects \
  -H "Authorization: Bearer ${ATTIO_API_KEY_PROD}"
# Must return 200
```

### Phase 2: Error Handling

```
[ ] All API calls wrapped in try/catch
[ ] AttioApiError class distinguishes retryable (429, 5xx) from fatal errors
[ ] Exponential backoff with jitter on 429 responses
[ ] Retry-After header honored (Attio sends a date, not seconds)
[ ] 5xx errors retried (Attio may have transient issues)
[ ] 400/422 validation errors logged with request body for debugging
[ ] 403 scope errors produce actionable log messages
[ ] 404 errors handled gracefully (records can be deleted/merged)
```

### Phase 3: Rate Limiting

```
[ ] Queue-based throttling implemented (p-queue or similar)
[ ] Concurrency limited to 5-10 parallel requests
[ ] Bulk operations use query endpoint (1 POST) instead of N GETs
[ ] Batch imports use offset-based pagination, not individual fetches
[ ] Rate limit monitor logs approaching-limit warnings
```

**Key fact:** Attio uses a 10-second sliding window. Rate limit scores are summed across all tokens in the workspace.

### Phase 4: Data Integrity

```
[ ] Record creation uses PUT (assert) for idempotent upserts where possible
[ ] Email/domain values validated before sending to API
[ ] Phone numbers formatted in E.164 ("+14155551234")
[ ] Record-reference attributes use verified target_record_ids
[ ] Pagination handles all pages (check data.length === limit to know if more)
[ ] Webhook events processed idempotently (deduplicate by event ID)
```

### Phase 5: Health Check Endpoint

```typescript
// api/health.ts -- include Attio in your health check
export async function GET() {
  const start = Date.now();
  let attioStatus: "healthy" | "degraded" | "down" = "down";
  let attioLatency = 0;

  try {
    const res = await fetch("https://api.attio.com/v2/objects", {
      headers: { Authorization: `Bearer ${process.env.ATTIO_API_KEY}` },
      signal: AbortSignal.timeout(5000),
    });
    attioLatency = Date.now() - start;
    attioStatus = res.ok ? "healthy" : "degraded";
  } catch {
    attioLatency = Date.now() - start;
  }

  return Response.json({
    status: attioStatus === "healthy" ? "healthy" : "degraded",
    services: {
      attio: { status: attioStatus, latencyMs: attioLatency },
    },
    timestamp: new Date().toISOString(),
  });
}
```

### Phase 6: Monitoring & Alerting

```
[ ] Health check endpoint hits Attio every 60s
[ ] Alert on: 5xx errors > 3/min (P1)
[ ] Alert on: 429 errors > 5/min (P2)
[ ] Alert on: 401/403 errors > 0 (P1 -- token may be revoked)
[ ] Alert on: Health check latency > 3000ms (P2)
[ ] Alert on: Health check failure 3 consecutive times (P1)
[ ] Log all Attio API calls with: method, path, status, duration_ms
```

**Structured logging example:**
```typescript
function logAttioCall(
  method: string,
  path: string,
  status: number,
  durationMs: number,
  error?: string
): void {
  console.log(JSON.stringify({
    service: "attio",
    method,
    path,
    status,
    durationMs,
    error,
    timestamp: new Date().toISOString(),
  }));
}
```

### Phase 7: Graceful Degradation

```typescript
// Circuit breaker: stop calling Attio if consistently failing
class AttioCircuitBreaker {
  private consecutiveFailures = 0;
  private openUntil = 0;

  async call<T>(operation: () => Promise<T>, fallback: T): Promise<T> {
    if (Date.now() < this.openUntil) {
      console.warn("Attio circuit open, using fallback");
      return fallback;
    }

    try {
      const result = await operation();
      this.consecutiveFailures = 0;
      return result;
    } catch (err) {
      this.consecutiveFailures++;
      if (this.consecutiveFailures >= 5) {
        this.openUntil = Date.now() + 30_000; // 30s cooldown
        console.error("Attio circuit opened after 5 failures");
      }
      return fallback;
    }
  }
}
```

### Phase 8: Webhook Production Config

```
[ ] Webhook endpoint uses HTTPS (required)
[ ] Signature verification implemented (see attio-security-basics)
[ ] Replay attack protection: reject timestamps > 5 minutes old
[ ] Idempotency: deduplicate events by event ID
[ ] Webhook handler returns 200 quickly, processes async
[ ] Failed processing triggers retry (return 5xx to Attio)
[ ] Webhook secret stored in secrets manager
```

### Phase 9: Rollback Plan

```
[ ] Previous deployment artifact available
[ ] Database migrations are backwards-compatible
[ ] Feature flag to disable Attio integration without deploy
[ ] Documented: how to roll back, who to notify, what to monitor
```

```typescript
// Feature flag example
const ATTIO_ENABLED = process.env.ATTIO_ENABLED !== "false";

async function syncToAttio(data: any): Promise<void> {
  if (!ATTIO_ENABLED) {
    console.log("Attio sync disabled via feature flag");
    return;
  }
  await client.post("/objects/people/records", { data });
}
```

## Error Handling

| Pre-launch check | Risk if skipped |
|-----------------|----------------|
| Token scoping | Data breach via over-permissioned token |
| Rate limit handling | Cascading failures during bulk operations |
| Retry-After parsing | Infinite retry loops or dropped requests |
| Health check | Silent failures go undetected |
| Webhook verification | Attacker can inject fake events |
| Circuit breaker | Attio outage takes down your entire app |

## Resources

- [Attio REST API Overview](https://docs.attio.com/rest-api/overview)
- [Attio Rate Limiting](https://docs.attio.com/rest-api/guides/rate-limiting)
- [Attio Status Page](https://status.attio.com)
- [Attio Webhooks Guide](https://docs.attio.com/rest-api/guides/webhooks)

## Next Steps

For version upgrades, see `attio-upgrade-migration`.
