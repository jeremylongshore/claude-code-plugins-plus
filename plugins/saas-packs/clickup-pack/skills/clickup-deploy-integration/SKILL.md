---
name: clickup-deploy-integration
description: |
  Deploy ClickUp API integrations to Vercel, Fly.io, and Cloud Run with
  secure secrets management and health checks.
  Trigger: "deploy clickup", "clickup Vercel", "clickup production deploy",
  "clickup Cloud Run", "clickup Fly.io", "clickup hosting".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Deploy Integration

## Overview

Deploy ClickUp-powered applications with secure token management. ClickUp API v2 is a standard REST API -- your app just needs `CLICKUP_API_TOKEN` available at runtime and outbound HTTPS to `api.clickup.com`.

## Required Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `CLICKUP_API_TOKEN` | Personal API token or OAuth access token | Yes |
| `CLICKUP_TEAM_ID` | Workspace ID for scoped operations | Recommended |
| `CLICKUP_WEBHOOK_SECRET` | For webhook signature validation | If using webhooks |

## Vercel Deployment

```bash
# Add secrets
vercel env add CLICKUP_API_TOKEN production
vercel env add CLICKUP_TEAM_ID production

# Deploy
vercel --prod
```

```typescript
// api/clickup/tasks.ts (Vercel serverless function)
export async function GET(request: Request) {
  const listId = new URL(request.url).searchParams.get('list_id');
  if (!listId) return Response.json({ error: 'list_id required' }, { status: 400 });

  const response = await fetch(
    `https://api.clickup.com/api/v2/list/${listId}/task?archived=false`,
    { headers: { 'Authorization': process.env.CLICKUP_API_TOKEN! } }
  );

  if (!response.ok) {
    return Response.json({ error: 'ClickUp API error' }, { status: response.status });
  }

  const data = await response.json();
  return Response.json(data.tasks);
}
```

## Fly.io Deployment

```bash
# Set secrets (encrypted at rest)
fly secrets set CLICKUP_API_TOKEN=pk_12345678_YOUR_TOKEN
fly secrets set CLICKUP_TEAM_ID=1234567

# Deploy
fly deploy
```

```toml
# fly.toml
app = "my-clickup-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[[http_service.checks]]
  grace_period = "5s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"
```

## Google Cloud Run

```bash
# Store token in Secret Manager
echo -n "pk_12345678_YOUR_TOKEN" | gcloud secrets create clickup-api-token --data-file=-

# Deploy with secret mounted as env var
gcloud run deploy clickup-service \
  --image gcr.io/$PROJECT_ID/clickup-service \
  --region us-central1 \
  --set-secrets=CLICKUP_API_TOKEN=clickup-api-token:latest \
  --set-env-vars=CLICKUP_TEAM_ID=1234567 \
  --allow-unauthenticated
```

## Health Check Endpoint

```typescript
// src/health.ts — verify ClickUp connectivity
export async function healthCheck() {
  const start = Date.now();

  try {
    const response = await fetch('https://api.clickup.com/api/v2/user', {
      headers: { 'Authorization': process.env.CLICKUP_API_TOKEN! },
      signal: AbortSignal.timeout(5000),
    });

    const remaining = response.headers.get('X-RateLimit-Remaining');

    return {
      status: response.ok ? 'healthy' : 'degraded',
      clickup: {
        connected: response.ok,
        httpStatus: response.status,
        latencyMs: Date.now() - start,
        rateLimitRemaining: remaining ? parseInt(remaining) : null,
      },
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      clickup: {
        connected: false,
        error: error instanceof Error ? error.message : 'Unknown',
        latencyMs: Date.now() - start,
      },
    };
  }
}
```

## Webhook Endpoint for Deployments

```typescript
// api/webhooks/clickup.ts — receive ClickUp webhook events
export async function POST(request: Request) {
  const body = await request.json();

  // ClickUp webhook payloads include event type and history_items
  const { event, task_id, history_items } = body;

  // Process async (respond within 30s or ClickUp marks as failed)
  // Queue for processing if needed
  console.log(`ClickUp event: ${event} for task ${task_id}`);

  return Response.json({ received: true });
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found in runtime | Missing env config | Verify with platform CLI |
| Cold start timeout | ClickUp API slow on first call | Set min instances = 1 |
| Health check fails | Token rotated | Update secret, redeploy |
| Webhook endpoint 5xx | Slow processing | Respond 200 immediately, process async |

## Resources

- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)
- [Cloud Run Secret Manager](https://cloud.google.com/run/docs/configuring/secrets)

## Next Steps

For webhook event handling, see `clickup-webhooks-events`.
