---
name: notion-deploy-integration
description: |
  Deploy Node.js applications that use the Notion API to production on Vercel,
  Railway, or Fly.io. Use when deploying Notion-powered backends, setting up
  NOTION_TOKEN in production secrets, configuring serverless singleton patterns,
  or adding health checks that verify Notion connectivity. Trigger with "deploy
  notion app", "notion production", "notion vercel deploy", "notion railway",
  "notion fly.io".
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(vercel:*), Bash(railway:*), Bash(fly:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
- deployment
- serverless
compatibility: Designed for Claude Code
---
# Deploy Notion-Integrated Applications

## Overview

Ship Node.js apps that talk to the Notion API to Vercel, Railway, or Fly.io. This skill covers environment variable management, the Notion client singleton pattern for serverless, rate limit handling at 3 req/sec, health check endpoints that verify Notion connectivity, and caching strategies to reduce API calls.

Deep code lives in `references/` so this file stays a lean walkthrough. Read a reference when a step needs the full module, then Write or Edit the code into your project's `src/`.

## Prerequisites

- Node.js >= 18 project with `@notionhq/client` installed (`npm i @notionhq/client`)
- Working Notion integration tested locally with a valid `NOTION_TOKEN` (starts with `ntn_`)
- Platform CLI installed for your target: `vercel`, `railway`, or `fly`
- Database or page IDs your integration needs access to

## Authentication

Every request authenticates with an internal integration token (`NOTION_TOKEN`, prefix `ntn_`), created at `notion.so/my-integrations` and passed as `auth` to the client. In production the token is stored as an encrypted platform secret and injected at runtime — never committed to source. Store it with `vercel env add NOTION_TOKEN production`, `railway variables set NOTION_TOKEN=...`, or `fly secrets set NOTION_TOKEN=...`. Each database or page must also be explicitly shared with the integration in the Notion UI, or queries return `ObjectNotFound`.

## Instructions

### Step 1 — Prepare the application for production

Build a production entry point with four modules: a Notion client singleton, a rate limiter, a response cache, and a health check. The singleton is the essential piece — serverless containers recycle unpredictably, so a module-level client reuses connections across warm invocations instead of paying cold-start and rate-limit cost per request:

```typescript
// src/notion-client.ts — singleton for serverless environments
import { Client, LogLevel } from '@notionhq/client';

let client: Client | null = null;

export function getNotionClient(): Client {
  if (!client) {
    if (!process.env.NOTION_TOKEN) {
      throw new Error('NOTION_TOKEN environment variable is not set');
    }
    client = new Client({
      auth: process.env.NOTION_TOKEN,
      logLevel: process.env.NODE_ENV === 'production' ? LogLevel.WARN : LogLevel.DEBUG,
      timeoutMs: 30_000,
    });
  }
  return client;
}
```

The rate limiter (token bucket for the 3 req/sec cap), the TTL response cache, and the `healthCheck()` function are provided in full — read [production-ready application modules](references/implementation.md) and copy each into `src/`.

### Step 2 — Deploy to your target platform

Pick one platform. All three inject `NOTION_TOKEN` at runtime from an encrypted secret:

- **Vercel** — serverless functions; best for Next.js apps, API routes, low-traffic webhooks (~200ms cold start).
- **Railway** — always-on containers; best for long-running sync services and apps needing persistent state.
- **Fly.io** — edge containers; best for global distribution and multi-region low-latency proxies.

Each path (secret setup, deploy command, and the framework-specific API-route wiring for the singleton, rate limiter, and cache) is in [platform deployment paths](references/platform-deployment.md).

### Step 3 — Monitor Notion API errors in production

Add structured error logging so Notion-specific failures surface in your monitoring tool (Sentry, Datadog, or platform logs). The full `classifyNotionError` / `logNotionError` module — which maps every `@notionhq/client` error code to a retryability flag and an operator action, plus the API-route wiring — lives in [production error monitoring](references/production-error-monitoring.md). Copy it to `src/notion-error-handler.ts` and call `logNotionError(error, context)` from every catch block that touches the Notion API.

Key metrics to watch:

- Rate limit hits (429 responses) per minute — alert if sustained above 5/min
- Health check latency — alert if Notion `latencyMs` exceeds 2000ms
- Auth failures (401/403) — alert immediately; means token rotation is needed
- Cache hit ratio — target > 70% in steady state; a low ratio means wasted API calls

## Output

This workflow produces:

- Node.js application deployed to Vercel, Railway, or Fly.io
- `NOTION_TOKEN` stored as an encrypted platform secret (never in source code)
- Notion client singleton that reuses connections across serverless invocations
- Rate limiter enforcing the 3 req/sec Notion API limit
- In-memory response cache reducing redundant API calls
- `/health` endpoint that verifies live Notion API connectivity
- Structured error logging classifying Notion API failures by severity

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| `NOTION_TOKEN is not set` at runtime | Secret not configured for environment | Re-add secret: `vercel env add` / `railway variables set` / `fly secrets set` |
| Cold start timeout (> 10s) | Large dependency tree or slow Notion handshake | Set `min_machines_running: 1` (Fly.io) or use Railway always-on |
| 429 Rate Limited in logs | Exceeding 3 req/sec sustained | Increase cache TTL, batch queries, add request queuing |
| Health check returns `degraded` | Token expired or Notion outage | Check `status.notion.com`; rotate token if 401 |
| `ObjectNotFound` on database query | Database not shared with integration | Open Notion, click Share, add the integration |
| Serverless function creates multiple clients | Not using singleton pattern | Import `getNotionClient()` from the shared module, not `new Client()` |

## Examples

Two complete, copy-ready examples live in [full deployment examples](references/examples.md):

- **Minimal Express server** — a platform-agnostic server wiring the singleton, rate limiter, health check, and error handler into `/health` and `/api/query` routes.
- **Deploy script** — a `deploy.sh [vercel|railway|fly]` that builds, sets the secret, deploys, and verifies the health endpoint.

## Resources

- [Notion API Reference](https://developers.notion.com/reference/intro) — official REST API docs
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client) — official SDK with built-in retry
- [Notion API Rate Limits](https://developers.notion.com/reference/request-limits) — 3 req/sec per integration
- [Notion API Status](https://status.notion.com) — check during outages
- [Vercel Environment Variables](https://vercel.com/docs/projects/environment-variables) — secret management
- [Railway Variables](https://docs.railway.app/reference/variables) — encrypted secrets
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/) — runtime secret injection

## Next Steps

- Add webhook receivers with the `notion-webhooks-events` skill
- Set up database sync pipelines with the `notion-sync-databases` skill
- Implement page content extraction with the `notion-extract-content` skill
