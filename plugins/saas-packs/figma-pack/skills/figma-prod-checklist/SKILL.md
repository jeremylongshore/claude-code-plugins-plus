---
name: figma-prod-checklist
description: |
  Production readiness checklist for Figma REST API integrations.
  Use when deploying Figma integrations to production, preparing for launch,
  or auditing an existing integration for production fitness.
  Trigger with phrases like "figma production", "deploy figma",
  "figma go-live", "figma launch checklist".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Production Checklist

## Overview
Complete checklist for deploying Figma API integrations to production, covering authentication, error handling, rate limits, monitoring, and rollback.

## Prerequisites
- Staging environment tested and verified
- Production PAT or OAuth credentials ready
- Monitoring infrastructure available

## Instructions

### Step 1: Authentication & Secrets
- [ ] Production PAT stored in secret manager (not env files)
- [ ] PAT uses minimum required scopes (`file_content:read`, not `files:read`)
- [ ] PAT expiry tracked (max 90 days) with rotation reminder
- [ ] OAuth refresh token flow tested (if using OAuth)
- [ ] Separate tokens for dev/staging/prod
- [ ] No tokens in client-side code or git history

### Step 2: Error Handling
- [ ] All HTTP status codes handled (400, 403, 404, 429, 500)
- [ ] `Retry-After` header honored on 429 responses
- [ ] Exponential backoff with jitter for transient errors
- [ ] Max retry limit to prevent infinite loops
- [ ] Graceful degradation when Figma is unavailable
- [ ] Error responses do not leak token values in logs

### Step 3: Rate Limiting
- [ ] Request queue with concurrency control (max 3-5 concurrent)
- [ ] Batch node IDs in single requests (up to 50 per call)
- [ ] Response caching for frequently accessed files (TTL: 60-300s)
- [ ] Rate limit monitor with proactive throttling
- [ ] No tight loops calling Figma API without delays

### Step 4: Monitoring & Health
```typescript
// Health check endpoint
async function figmaHealthCheck() {
  const start = Date.now();
  try {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': process.env.FIGMA_PAT! },
      signal: AbortSignal.timeout(5000),
    });
    return {
      status: res.ok ? 'healthy' : 'degraded',
      latencyMs: Date.now() - start,
      httpStatus: res.status,
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      latencyMs: Date.now() - start,
      error: error instanceof Error ? error.message : 'Unknown',
    };
  }
}
```

- [ ] Health endpoint includes Figma connectivity check
- [ ] Alerts on sustained 429 errors (>5/min)
- [ ] Alerts on 403 errors (token expiry)
- [ ] Alerts on response latency >5s (P95)
- [ ] Dashboard tracks requests/min, error rate, latency

### Step 5: Data Handling
- [ ] Image export URLs treated as temporary (expire after 30 days)
- [ ] No PII from Figma stored without user consent
- [ ] File data cached with appropriate TTL
- [ ] Large file responses streamed, not buffered entirely in memory

### Step 6: Webhook Production Setup
- [ ] HTTPS endpoint (Figma requires TLS)
- [ ] Passcode verification on every incoming webhook
- [ ] Idempotency handling for duplicate deliveries
- [ ] Quick response (200 within 5s) with async processing
- [ ] Dead letter queue for failed webhook processing

### Step 7: Pre-Flight Verification
```bash
#!/bin/bash
echo "=== Figma Production Pre-Flight ==="

# 1. Token valid?
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me)
echo "Auth: $STATUS (expect 200)"

# 2. File accessible?
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}?depth=1")
echo "File: $STATUS (expect 200)"

# 3. Figma status page
echo -n "Figma Status: "
curl -s https://www.figmastatus.com/api/v2/status.json 2>/dev/null \
  | jq -r '.status.description // "Unable to check"'

echo "=== Pre-flight complete ==="
```

## Output
- All checklist items verified
- Health check endpoint deployed
- Monitoring and alerting configured
- Pre-flight script passing

## Error Handling
| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Auth Failure | 403 errors > 0 | P1 | Rotate PAT immediately |
| Rate Limited | 429 errors > 5/min | P2 | Reduce request rate; check plan tier |
| High Latency | P95 > 5000ms | P2 | Check Figma status; add caching |
| API Down | 5xx errors > 10/min | P1 | Enable fallback; check status.figma.com |

## Resources
- [Figma Status Page](https://status.figma.com)
- [Figma Rate Limits](https://developers.figma.com/docs/rest-api/rate-limits/)
- [Figma API Scopes](https://developers.figma.com/docs/rest-api/scopes/)

## Next Steps
For version upgrades, see `figma-upgrade-migration`.
