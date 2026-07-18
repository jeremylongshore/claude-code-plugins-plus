---
name: clickhouse-deploy-integration
description: |
  Deploy ClickHouse-backed applications to Vercel, Fly.io, and Cloud Run with
  connection pooling, secrets, and health checks.
  Use when deploying applications that connect to ClickHouse Cloud, configuring
  platform secrets, or setting up deployment pipelines to serverless or
  container hosts.
  Trigger with "deploy clickhouse app", "clickhouse Vercel", "clickhouse Cloud
  Run", "clickhouse production deploy", "clickhouse Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Deploy Integration

## Overview

Deploy applications that connect to ClickHouse Cloud from serverless and
container platforms with proper connection management and secrets handling. The
same platform-agnostic connection module drives all three targets — Vercel,
Fly.io, and Cloud Run — so only the secrets mechanism and runtime model change
per platform.

## Prerequisites

- ClickHouse Cloud instance (or self-hosted with public endpoint)
- Platform CLI installed (vercel, fly, or gcloud)
- Application tested locally against ClickHouse

## Instructions

### Step 1: ClickHouse Connection Module (Platform-Agnostic)

Write a singleton client so a serverless cold start reuses one connection
instead of opening a new pool per invocation. Keep `max_open_connections` low
for serverless and enable compression to cut egress.

```typescript
// src/db.ts — singleton for serverless-safe connections
import { createClient, ClickHouseClient } from '@clickhouse/client';

let client: ClickHouseClient | null = null;

export function getClickHouse(): ClickHouseClient {
  if (!client) {
    client = createClient({
      url: process.env.CLICKHOUSE_HOST!,         // https://<host>:8443
      username: process.env.CLICKHOUSE_USER!,
      password: process.env.CLICKHOUSE_PASSWORD!,
      database: process.env.CLICKHOUSE_DATABASE ?? 'default',
      request_timeout: 30_000,
      max_open_connections: 5,    // Low for serverless (many cold starts)
      compression: {
        request: true,            // Saves egress bandwidth
        response: true,
      },
    });
  }
  return client;
}
```

### Step 2: Pick a platform and deploy

Choose the target that matches your runtime model, then set secrets and deploy.
All three import the `getClickHouse()` module above unchanged.

- **Vercel (serverless functions)** — `vercel env add` per secret; best for API
  endpoints. Keep `max_open_connections` at 1-3.
- **Fly.io (containers)** — `fly secrets set` + a `fly.toml` health check; best
  for long-running apps with persistent connections.
- **Cloud Run (containers)** — secrets via Secret Manager (`--set-secrets`);
  best for event-driven workloads. Set `--min-instances=1` to avoid cold-start
  connection churn.

Full per-platform commands, the Next.js App Router query example, `fly.toml`,
the Cloud Run deploy script, and a platform comparison table:
[Platform deployment walkthrough](references/platform-deployment.md).

### Step 3: Add health check and graceful shutdown

Expose a `/health` endpoint that pings ClickHouse (drives Fly.io / Cloud Run
readiness probes) and close the client on `SIGTERM`/`SIGINT` so pending inserts
flush before the container is recycled. Full code:
[Production patterns](references/production-patterns.md).

## Output

Running this skill produces a deployable ClickHouse-connected application:

- `src/db.ts` — a singleton ClickHouse client, serverless-safe and compressed.
- Platform config with secrets set: Vercel env vars, `fly.toml` + `fly secrets`,
  or a Cloud Run service wired to Secret Manager.
- A `/health` endpoint reporting `{ status, clickhouse: { connected, latencyMs } }`.
- Graceful-shutdown handlers that flush pending inserts on `SIGTERM`/`SIGINT`.
- A live deployment reachable over HTTPS on the chosen platform.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `ECONNRESET` on Vercel | Function timeout | Reduce query scope, increase timeout |
| `TLS handshake` failed | Wrong port | Use port 8443 for Cloud |
| Secret not found | Env var not set | Check platform secret config |
| Cold start latency | New connection per invocation | Use `min-instances=1` on Cloud Run |

## Examples

**Deploy an analytics API to Vercel:** set the four `CLICKHOUSE_*` secrets with
`vercel env add`, drop the `getClickHouse()` module in `src/db.ts`, and add a
route that runs a parameterized `SELECT ... GROUP BY event_type`. See the full
Next.js App Router handler under the Vercel section of the
[Platform deployment walkthrough](references/platform-deployment.md).

**Deploy a long-running container to Fly.io:** add a `[[http_service.checks]]`
block pointing at `/health`, `fly secrets set` the ClickHouse credentials, then
`fly deploy` — see the complete `fly.toml` in the
[Platform deployment walkthrough](references/platform-deployment.md).

**Deploy an event-driven service to Cloud Run:** store host + password in Secret
Manager, wire them with `--set-secrets`, and set `--min-instances=1`. Full
deploy script in the
[Platform deployment walkthrough](references/platform-deployment.md).

## Resources

- [ClickHouse Cloud Connection](https://clickhouse.com/docs/cloud/get-started)
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)

## Next Steps

For data ingestion patterns, see `clickhouse-webhooks-events`.
