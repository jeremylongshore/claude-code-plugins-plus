---
name: fireflies-prod-checklist
description: |
  Execute Fireflies.ai production deployment checklist with health checks and rollback.
  Use when deploying Fireflies.ai integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "fireflies production", "deploy fireflies",
  "fireflies go-live", "fireflies launch checklist".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, deployment]

---
# Fireflies.ai Production Checklist

## Overview
Complete checklist for deploying Fireflies.ai integrations to production. Covers API key management, webhook setup, health checks, and monitoring.

## Prerequisites
- Staging environment tested
- Production API key from Fireflies dashboard
- Webhook endpoint with HTTPS and signature verification
- Monitoring infrastructure ready

## Pre-Deployment Checklist

### API & Auth
- [ ] Production `FIREFLIES_API_KEY` in secret manager (not env file)
- [ ] API key has minimum required access
- [ ] `FIREFLIES_WEBHOOK_SECRET` configured (16-32 chars)
- [ ] Separate keys for dev/staging/prod environments
- [ ] Key rotation procedure documented

### Code Quality
- [ ] All GraphQL queries tested against real API in staging
- [ ] Error handling for all Fireflies error codes (`auth_failed`, `too_many_requests`, `require_ai_credits`)
- [ ] Rate limiting with exponential backoff implemented
- [ ] No hardcoded API keys or transcript IDs
- [ ] Webhook signature verification (HMAC-SHA256) enabled

### Webhook Configuration
- [ ] Webhook URL registered in Fireflies dashboard (Settings > Developer settings)
- [ ] HTTPS endpoint with valid TLS certificate
- [ ] `x-hub-signature` header verified on every request
- [ ] Webhook handler responds with 200 immediately (process async)
- [ ] Dead-letter queue for failed webhook processing

### Health Check Endpoint
```typescript
// /api/health
export async function GET() {
  const checks: Record<string, any> = {};

  // Fireflies API connectivity
  try {
    const start = Date.now();
    const res = await fetch("https://api.fireflies.ai/graphql", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
      },
      body: JSON.stringify({ query: "{ user { email } }" }),
      signal: AbortSignal.timeout(5000),
    });
    const json = await res.json();
    checks.fireflies = {
      status: json.errors ? "error" : "healthy",
      latencyMs: Date.now() - start,
      error: json.errors?.[0]?.code,
    };
  } catch (err) {
    checks.fireflies = { status: "unreachable", error: (err as Error).message };
  }

  const allHealthy = Object.values(checks).every((c: any) => c.status === "healthy");
  return Response.json(
    { status: allHealthy ? "healthy" : "degraded", checks },
    { status: allHealthy ? 200 : 503 }
  );
}
```

### Monitoring & Alerting
- [ ] Alert on Fireflies API errors (5xx, 401, 429)
- [ ] Track webhook delivery latency
- [ ] Monitor transcript processing queue depth
- [ ] Dashboard showing: meetings/day, avg processing time, error rate
- [ ] PagerDuty/Slack alert for auth failures (P1)

### Alerting Thresholds
| Alert | Condition | Severity |
|-------|-----------|----------|
| Auth failure | Any `auth_failed` error | P1 -- API key may be revoked |
| Rate limited | 429 errors > 5/min | P2 -- backoff or upgrade plan |
| API unreachable | Health check fails 3x | P1 -- check Fireflies status |
| Webhook backlog | Queue > 100 events | P3 -- scale webhook processor |

## Deployment Steps

### Step 1: Pre-flight
```bash
set -euo pipefail
# Verify staging passes
curl -f https://staging.example.com/api/health | jq '.checks.fireflies'

# Verify production API key works
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY_PROD" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { email is_admin } }"}' | jq .
```

### Step 2: Deploy
```bash
set -euo pipefail
# Deploy with your platform
# Vercel: vercel --prod
# Docker: docker push && kubectl apply
# Fly.io: fly deploy --app production

# Verify health immediately
curl -f https://production.example.com/api/health | jq .
```

### Step 3: Post-Deploy Verification
```bash
set -euo pipefail
# Verify webhook is registered
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY_PROD" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { email } }"}' | jq .

# Test webhook delivery (upload a short audio file)
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY_PROD" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation($input: AudioUploadInput) { uploadAudio(input: $input) { success message } }",
    "variables": { "input": { "url": "https://example.com/test.mp3", "title": "Deploy Test" } }
  }' | jq .
```

## Rollback
```bash
set -euo pipefail
# Immediate rollback
# Platform-specific: revert deployment to previous version

# Verify rollback
curl -f https://production.example.com/api/health | jq '.checks.fireflies'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Auth fails post-deploy | Wrong API key in production secrets | Update secret, redeploy |
| Webhook not firing | URL not saved in Fireflies dashboard | Re-register at app.fireflies.ai/settings |
| Rate limiting in prod | Burst traffic on deploy | Enable request queuing |
| Missing transcripts | Bot not joining meetings | Verify calendar integration is connected |

## Output
- Production deployment with verified health checks
- Webhook endpoint receiving and verifying events
- Monitoring and alerting configured
- Rollback procedure tested

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [Fireflies Webhooks](https://docs.fireflies.ai/graphql-api/webhooks)

## Next Steps
For version upgrades, see `fireflies-upgrade-migration`.
