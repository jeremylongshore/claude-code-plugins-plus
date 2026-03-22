---
name: linear-prod-checklist
description: |
  Production readiness checklist for Linear integrations.
  Use when preparing to deploy, reviewing production requirements,
  or auditing existing Linear deployments.
  Trigger: "linear production checklist", "deploy linear",
  "linear production ready", "linear go live", "linear launch".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, deployment, audit]

---
# Linear Production Checklist

## Overview
Comprehensive checklist and implementation patterns for deploying Linear integrations to production. Covers authentication, error handling, rate limiting, monitoring, data handling, and deployment verification.

## Prerequisites
- Working development integration passing all tests
- Production Linear workspace (or production API key)
- Deployment infrastructure (Vercel, Cloud Run, etc.)
- Secret management solution (not `.env` files in production)

## Pre-Production Checklist

### 1. Authentication & Security
```
[ ] Production API key generated (separate from dev)
[ ] API key stored in secret manager (Vault, AWS SM, GCP SM)
[ ] OAuth redirect URIs updated for production domain
[ ] Webhook secrets are unique per environment
[ ] All dev secrets rotated before launch
[ ] HTTPS enforced on all endpoints
[ ] Webhook HMAC-SHA256 verification implemented
[ ] Webhook timestamp validation (< 60s age)
[ ] Token refresh flow implemented (mandatory since Oct 2025)
```

### 2. Error Handling & Resilience
```
[ ] All Linear API calls wrapped in try/catch
[ ] Rate limit retry with exponential backoff (max 5 retries)
[ ] 30s timeout on all API calls
[ ] Graceful degradation when Linear API is down
[ ] Error logging includes context (no secrets in logs)
[ ] InvalidInputLinearError caught separately from network errors
[ ] Alerts configured for auth failures and error rate spikes
```

### 3. Performance & Rate Limits
```
[ ] Pagination with first:50 for all list queries
[ ] Caching for static data (teams, states, labels) — 10-30 min TTL
[ ] Request batching for bulk operations (20 mutations per batch)
[ ] Query complexity stays under 5,000 pts per request
[ ] No polling — webhooks for real-time updates
[ ] N+1 query patterns eliminated (use rawRequest for joins)
[ ] Response times monitored with p95 alerting
```

### 4. Monitoring & Observability
```
[ ] Health check endpoint hitting Linear API
[ ] API latency metrics collected per operation
[ ] Error rate monitoring with alerting (>1% = alert)
[ ] Rate limit remaining tracked (alert if < 100 requests)
[ ] Structured JSON logging for API calls and webhooks
[ ] Webhook delivery tracking via Linear-Delivery header
```

### 5. Data Handling
```
[ ] No PII logged or stored unnecessarily
[ ] Webhook event idempotency (deduplicate by Linear-Delivery)
[ ] Data retention policy defined for synced data
[ ] Stale data detection with periodic consistency checks
```

## Production Configuration

```typescript
import { LinearClient } from "@linear/sdk";

interface ProdConfig {
  linear: { apiKey: string; webhookSecret: string };
  rateLimit: { maxRetries: number; baseDelayMs: number; maxDelayMs: number };
  cache: { teamsTtl: number; statesTtl: number; labelsTtl: number };
  timeouts: { requestMs: number; webhookProcessMs: number };
}

const config: ProdConfig = {
  linear: {
    apiKey: await getSecret("linear-api-key-prod"),
    webhookSecret: await getSecret("linear-webhook-secret-prod"),
  },
  rateLimit: { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 30000 },
  cache: { teamsTtl: 600, statesTtl: 1800, labelsTtl: 600 },
  timeouts: { requestMs: 30000, webhookProcessMs: 5000 },
};

function createProductionClient(): LinearClient {
  return new LinearClient({ apiKey: config.linear.apiKey });
}
```

## Health Check Implementation

```typescript
interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  latencyMs: number;
  details: {
    authentication: boolean;
    apiReachable: boolean;
    rateLimitOk: boolean;
  };
  timestamp: string;
}

async function checkHealth(client: LinearClient): Promise<HealthStatus> {
  const start = Date.now();
  const details = { authentication: false, apiReachable: false, rateLimitOk: true };

  try {
    const viewer = await client.viewer;
    details.authentication = true;
    details.apiReachable = true;

    const latencyMs = Date.now() - start;
    return {
      status: latencyMs > 3000 ? "degraded" : "healthy",
      latencyMs,
      details,
      timestamp: new Date().toISOString(),
    };
  } catch (error: any) {
    details.apiReachable = !error.message?.includes("ENOTFOUND");
    return {
      status: "unhealthy",
      latencyMs: Date.now() - start,
      details,
      timestamp: new Date().toISOString(),
    };
  }
}

// Express endpoint
app.get("/health/linear", async (req, res) => {
  const health = await checkHealth(client);
  res.status(health.status === "unhealthy" ? 503 : 200).json(health);
});
```

## Deployment Verification Script

```typescript
// scripts/verify-deployment.ts
import { LinearClient } from "@linear/sdk";

async function verify(): Promise<void> {
  console.log("Verifying Linear integration...\n");

  const checks = [
    {
      name: "Environment variables",
      check: async () => !!(process.env.LINEAR_API_KEY && process.env.LINEAR_WEBHOOK_SECRET),
    },
    {
      name: "API authentication",
      check: async () => { await new LinearClient({ apiKey: process.env.LINEAR_API_KEY! }).viewer; return true; },
    },
    {
      name: "Team access",
      check: async () => {
        const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
        const teams = await client.teams();
        return teams.nodes.length > 0;
      },
    },
    {
      name: "Write capability",
      check: async () => {
        const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
        const teams = await client.teams();
        const r = await client.createIssue({
          teamId: teams.nodes[0].id,
          title: "[DEPLOY-CHECK] Safe to delete",
        });
        if (r.success) {
          const issue = await r.issue;
          await issue?.delete();
        }
        return r.success;
      },
    },
  ];

  let passed = 0;
  let failed = 0;

  for (const { name, check } of checks) {
    try {
      const ok = await check();
      console.log(ok ? `  PASS: ${name}` : `  FAIL: ${name}`);
      ok ? passed++ : failed++;
    } catch (error: any) {
      console.log(`  FAIL: ${name} — ${error.message}`);
      failed++;
    }
  }

  console.log(`\nResults: ${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

verify();
```

## Post-Deployment Monitoring

```typescript
// Key metrics to track after deploy
const ALERT_THRESHOLDS = {
  errorRate: 0.01,        // Alert if >1% of requests fail
  p99LatencyMs: 3000,     // Alert if p99 > 3 seconds
  rateLimitRemaining: 100, // Alert if remaining requests < 100
};

// First 30 minutes after deploy: watch for
// - Auth failures (key mismatch between environments)
// - Rate limit spikes (init burst fetching too much data)
// - Webhook signature failures (secret not updated in new env)
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Health check `unhealthy` | API key invalid/expired | Regenerate key, update secret manager |
| Webhook sig fails in prod | Secret mismatch | Verify `LINEAR_WEBHOOK_SECRET` matches Linear webhook config |
| Rate limit burst on deploy | Startup fetches too much | Add request queue, cache static data |
| Deploy verification fails | Missing env vars | Run verification locally first |

## Resources
- [Linear API Status](https://status.linear.app)
- [Linear Security](https://linear.app/security)
- [API Changelog](https://linear.app/changelog)
