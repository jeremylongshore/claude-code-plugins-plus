---
name: groq-prod-checklist
description: |
  Execute Groq production deployment checklist and go-live procedures.
  Use when deploying Groq integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "groq production", "deploy groq",
  "groq go-live", "groq launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, deployment]

---
# Groq Production Checklist

## Overview
Complete pre-launch checklist for deploying Groq-powered applications to production. Covers API key security, model selection, rate limit planning, fallback strategies, and monitoring setup.

## Prerequisites
- Staging environment tested with Groq API
- Groq Developer or Enterprise plan (free tier is not suitable for production)
- Production API key created in console.groq.com
- Monitoring and alerting infrastructure ready

## Pre-Deployment Checklist

### API Key & Auth
- [ ] Production API key stored in secret manager (not `.env` files)
- [ ] Key is NOT shared with development or staging environments
- [ ] Key rotation procedure documented and tested
- [ ] Pre-commit hook blocks `gsk_` pattern in code

### Model Selection
- [ ] Production model chosen and tested (recommend `llama-3.3-70b-versatile`)
- [ ] Fallback model configured (`llama-3.1-8b-instant`)
- [ ] Deprecated model IDs removed (check [deprecations](https://console.groq.com/docs/deprecations))
- [ ] `max_tokens` set to actual expected output size (not context max)

### Rate Limit Planning
- [ ] Production rate limits known (check console.groq.com/settings/limits)
- [ ] Estimated peak RPM < 80% of limit
- [ ] Estimated peak TPM < 80% of limit
- [ ] Exponential backoff with `retry-after` header implemented
- [ ] Request queue for burst protection (`p-queue` or similar)

### Error Handling
- [ ] All Groq error types caught (`Groq.APIError`, `Groq.APIConnectionError`)
- [ ] 429 errors retried with backoff
- [ ] 5xx errors retried with backoff
- [ ] 401 errors trigger alert (key may be revoked)
- [ ] Network timeouts configured (default 60s may be too long)
- [ ] Circuit breaker pattern for sustained failures

### Fallback & Degradation
```typescript
async function completionWithFallback(messages: any[]) {
  try {
    return await groq.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages,
      timeout: 15_000,
    });
  } catch (err: any) {
    if (err.status === 429 || err.status >= 500) {
      console.warn("Groq primary failed, trying fallback model");
      try {
        return await groq.chat.completions.create({
          model: "llama-3.1-8b-instant",
          messages,
          timeout: 10_000,
        });
      } catch {
        console.error("Groq fully unavailable, degrading gracefully");
        return { choices: [{ message: { content: "Service temporarily unavailable. Please try again." } }] };
      }
    }
    throw err;
  }
}
```

### Health Check Endpoint
```typescript
// /api/health or /healthz
export async function GET() {
  const checks: Record<string, any> = { status: "healthy" };
  const start = performance.now();

  try {
    await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "OK" }],
      max_tokens: 1,
      temperature: 0,
    });
    checks.groq = { status: "connected", latencyMs: Math.round(performance.now() - start) };
  } catch (err: any) {
    checks.status = "degraded";
    checks.groq = { status: "error", error: err.status || err.message };
  }

  return Response.json(checks, { status: checks.status === "healthy" ? 200 : 503 });
}
```

### Monitoring Setup
- [ ] Latency histogram (p50, p95, p99)
- [ ] Token throughput counter (tokens/sec by model)
- [ ] Error rate by status code (429, 5xx)
- [ ] Rate limit remaining gauge (from response headers)
- [ ] Cost tracking (tokens * price per million)
- [ ] Alert: latency p95 > 1s (Groq normally < 200ms)
- [ ] Alert: error rate > 5%
- [ ] Alert: rate limit remaining < 10%

### Spending Controls
- [ ] Monthly spending cap set in Groq Console
- [ ] Budget alerts at 50%, 80%, 95%
- [ ] Auto-pause enabled when cap is reached

### Documentation
- [ ] Incident runbook created (see `groq-incident-runbook`)
- [ ] Key rotation SOP documented
- [ ] On-call knows how to check [status.groq.com](https://status.groq.com)
- [ ] Rollback procedure tested

## Go-Live Verification
```bash
set -euo pipefail
# Pre-flight checks
echo "1. Groq API status..."
curl -sf https://status.groq.com > /dev/null && echo "OK" || echo "ISSUE"

echo "2. Production key valid..."
curl -sf https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY_PROD" | jq '.data | length'

echo "3. Health endpoint..."
curl -sf https://your-app.com/api/health | jq .

echo "4. Rate limit headroom..."
curl -si https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY_PROD" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  2>/dev/null | grep -i "x-ratelimit-remaining"
```

## Error Handling
| Alert | Condition | Severity |
|-------|-----------|----------|
| API errors spike | 5xx rate > 5/min | P1 |
| Latency degraded | p95 > 1000ms | P2 |
| Rate limited | 429 count > 5/min | P2 |
| Auth failure | Any 401 error | P1 |
| Spending near cap | >90% of monthly budget | P3 |

## Resources
- [Groq Status Page](https://status.groq.com)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Spend Limits](https://console.groq.com/docs/spend-limits)
- [Groq Models (check deprecations)](https://console.groq.com/docs/deprecations)

## Next Steps
For version upgrades, see `groq-upgrade-migration`.
