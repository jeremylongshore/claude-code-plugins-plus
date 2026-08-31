---
name: hex-deploy-integration
description: 'Deploy Hex integrations to Vercel, Fly.io, and Cloud Run platforms.

  Use when deploying Hex-powered applications to production,

  configuring platform-specific secrets, or setting up deployment pipelines.

  Trigger with phrases like "deploy hex", "hex Vercel",

  "hex production deploy", "hex Cloud Run", "hex Fly.io".

  '
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hex
- data
- analytics
compatibility: Designed for Claude Code
---
# Hex Deploy Integration

## Overview

Deploy Hex orchestration services that trigger project runs from web endpoints or cron jobs.

## Instructions

### Vercel — On-Demand Data Refresh

```typescript
// api/refresh.ts
export default async function handler(req, res) {
  const response = await fetch(`https://app.hex.tech/api/v1/project/${process.env.HEX_PROJECT_ID}/run`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${process.env.HEX_API_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ inputParams: req.body || {}, updateCacheResult: true }),
  });
  res.json(await response.json());
}
```

```bash
vercel env add HEX_API_TOKEN production
vercel env add HEX_PROJECT_ID production
```

### Cloud Run — Scheduled Orchestrator

```bash
gcloud run deploy hex-orchestrator \
  --image gcr.io/$PROJECT_ID/hex-orchestrator \
  --set-secrets=HEX_API_TOKEN=hex-api-token:latest \
  --timeout=600
```

## Prerequisites

- An approved deployment change, secret references, project/destination allowlist, and immutable client/configuration revision.
- Safe canary project, baselines for health/latency/quota/output assertions, and a tested rollback/cancel artifact.

## Output

Produce a deployment receipt with artifact digest, environment, canary project, health/latency/quota/aggregate assertion outcomes, owner approval, rollout state, and rollback reference. Exclude SQL, output, and secrets.

## Error Handling

Halt for unknown project/destination, unauthorized scope, failed canary assertion, unbounded retry, or leaked output in telemetry. Cancel affected execution and restore the previous revision rather than bypassing a gate.

## Examples

`artifact=sha256:opaque; env=staging; canary=proj-sandbox-12; health=pass; assertions=pass; quota=pass; rollback=release-r31` supports controlled promotion.

## Resources

- [Hex API](https://learn.hex.tech/docs/api/api-overview)
