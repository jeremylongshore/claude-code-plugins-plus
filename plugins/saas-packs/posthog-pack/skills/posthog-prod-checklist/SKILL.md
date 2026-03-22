---
name: posthog-prod-checklist
description: |
  Production readiness checklist for PostHog integrations: SDK configuration,
  graceful degradation, health checks, shutdown hooks, and rollback procedures.
  Trigger: "posthog production", "deploy posthog", "posthog go-live",
  "posthog launch checklist", "posthog production ready".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, deployment]
---

# PostHog Production Checklist

## Overview

Production readiness verification for PostHog integrations. Covers SDK configuration hardening, graceful degradation when PostHog is unavailable, health check endpoints, proper shutdown hooks for serverless, and rollback procedures.

## Prerequisites

- PostHog integration tested in staging
- Production PostHog project with `phc_` key
- Personal API key (`phx_`) for server-side features
- Deployment pipeline configured

## Instructions

### Pre-Deployment Checklist

**SDK Configuration:**
- [ ] `api_host` set to correct region (`us.i.posthog.com` or `eu.i.posthog.com`)
- [ ] `capture_pageview: false` if using SPA with manual pageview tracking
- [ ] `capture_pageleave: true` for session duration accuracy
- [ ] Reverse proxy configured to bypass ad blockers (see `posthog-sdk-patterns`)
- [ ] `posthog.debug()` disabled in production (guarded by `NODE_ENV`)
- [ ] `autocapture` configured to exclude noisy elements

**Server-Side:**
- [ ] `posthog.shutdown()` called in SIGTERM handler and serverless function cleanup
- [ ] `personalApiKey` set for local flag evaluation (not just project key)
- [ ] `flushAt` and `flushInterval` tuned (default 20/10s is fine for most apps)

**Security:**
- [ ] Personal API key (`phx_`) never in client bundles or NEXT_PUBLIC_ vars
- [ ] `.env` files in `.gitignore`
- [ ] Separate PostHog project per environment

### Step 1: Production SDK Configuration

```typescript
// lib/posthog-production.ts
import { PostHog } from 'posthog-node';

const posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  host: process.env.POSTHOG_HOST || 'https://us.i.posthog.com',
  personalApiKey: process.env.POSTHOG_PERSONAL_API_KEY,
  flushAt: 20,
  flushInterval: 10000,
  requestTimeout: 10000,
  maxRetries: 3,
});

// Graceful shutdown
async function shutdown() {
  await posthog.shutdown();
  process.exit(0);
}
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
```

### Step 2: Graceful Degradation

```typescript
// PostHog should never break your app — wrap all calls
function safeCapture(distinctId: string, event: string, properties?: Record<string, any>) {
  try {
    posthog.capture({ distinctId, event, properties });
  } catch (error) {
    // Log but never throw — analytics should not crash your app
    console.error('[PostHog] Capture failed:', (error as Error).message);
  }
}

async function safeGetFlag(flagKey: string, userId: string, defaultValue: boolean = false): Promise<boolean> {
  try {
    const result = await posthog.isFeatureEnabled(flagKey, userId);
    return result ?? defaultValue;
  } catch (error) {
    console.error('[PostHog] Flag evaluation failed:', (error as Error).message);
    return defaultValue; // Always return safe default
  }
}
```

### Step 3: Health Check Endpoint

```typescript
// api/health.ts (Next.js API route or Express handler)
export async function GET() {
  const checks: Record<string, { status: string; latencyMs?: number }> = {};

  // PostHog capture test
  const captureStart = performance.now();
  try {
    posthog.capture({
      distinctId: 'healthcheck',
      event: '$healthcheck',
      properties: { test: true },
    });
    await posthog.flush();
    checks.posthog_capture = {
      status: 'ok',
      latencyMs: Math.round(performance.now() - captureStart),
    };
  } catch {
    checks.posthog_capture = { status: 'degraded' };
  }

  // PostHog flag evaluation test
  const flagStart = performance.now();
  try {
    await posthog.getAllFlags('healthcheck');
    checks.posthog_flags = {
      status: 'ok',
      latencyMs: Math.round(performance.now() - flagStart),
    };
  } catch {
    checks.posthog_flags = { status: 'degraded' };
  }

  const overall = Object.values(checks).every(c => c.status === 'ok') ? 'healthy' : 'degraded';
  return Response.json({ status: overall, checks }, { status: overall === 'healthy' ? 200 : 503 });
}
```

### Step 4: Serverless Function Pattern

```typescript
// For Vercel Edge Functions, AWS Lambda, etc.
import { PostHog } from 'posthog-node';

export async function handler(request: Request) {
  // Create client per invocation in serverless (or use module-level singleton)
  const posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    host: 'https://us.i.posthog.com',
    flushAt: 1,       // Flush immediately in serverless
    flushInterval: 0,  // Don't wait
  });

  try {
    posthog.capture({
      distinctId: getUserId(request),
      event: 'api_called',
      properties: { endpoint: new URL(request.url).pathname },
    });

    const result = await doWork(request);
    return Response.json(result);
  } finally {
    // CRITICAL: Always flush before function exits
    await posthog.shutdown();
  }
}
```

### Step 5: Pre-Flight Verification

```bash
set -euo pipefail
# 1. Verify PostHog is reachable from production
curl -sf "https://us.i.posthog.com/healthz" && echo "PostHog: OK" || echo "PostHog: UNREACHABLE"

# 2. Verify capture works
curl -s -X POST 'https://us.i.posthog.com/capture/' \
  -H 'Content-Type: application/json' \
  -d "{\"api_key\":\"$NEXT_PUBLIC_POSTHOG_KEY\",\"event\":\"deploy_preflight\",\"distinct_id\":\"deploy\"}" | jq .

# 3. Verify feature flags load
curl -s -X POST 'https://us.i.posthog.com/decide/?v=3' \
  -H 'Content-Type: application/json' \
  -d "{\"api_key\":\"$NEXT_PUBLIC_POSTHOG_KEY\",\"distinct_id\":\"deploy-check\"}" | \
  jq '{flags_count: (.featureFlags | length), session_recording: (.sessionRecording != false)}'

# 4. Verify admin API (if using server-side features)
curl -sf "https://app.posthog.com/api/projects/$POSTHOG_PROJECT_ID/" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" | jq '.name' && echo "Admin API: OK"
```

## Error Handling

| Alert | Trigger | Severity | Action |
|-------|---------|----------|--------|
| PostHog capture failing | Error rate > 1% | P3 | Check API host, verify key |
| Flag evaluation slow | p95 > 500ms | P2 | Enable local evaluation with `personalApiKey` |
| Events not appearing | Zero events for 30min | P2 | Check `shutdown()` is called, verify flush |
| Admin API 401 | Personal key rejected | P1 | Rotate key in PostHog settings |

## Rollback Procedure

```bash
set -euo pipefail
# Quick rollback if PostHog causes issues
# Option 1: Disable PostHog via env var
kubectl set env deployment/app POSTHOG_ENABLED=false
kubectl rollout restart deployment/app

# Option 2: Roll back deployment
kubectl rollout undo deployment/app
kubectl rollout status deployment/app
```

## Output

- Production-hardened PostHog SDK configuration
- Graceful degradation wrappers (never crash on analytics failure)
- Health check endpoint verifying capture and flag evaluation
- Serverless shutdown pattern
- Pre-flight verification commands

## Resources

- [PostHog Node.js SDK](https://posthog.com/docs/libraries/node)
- [PostHog Status Page](https://status.posthog.com)
- [PostHog Support](https://posthog.com/docs/support)

## Next Steps

For version upgrades, see `posthog-upgrade-migration`.
