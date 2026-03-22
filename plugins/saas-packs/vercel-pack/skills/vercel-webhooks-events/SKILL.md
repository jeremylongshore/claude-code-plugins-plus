---
name: vercel-webhooks-events
description: |
  Implement Vercel webhook handling with signature verification and event processing.
  Use when setting up webhook endpoints, processing deployment events,
  or building integrations that react to Vercel deployment lifecycle.
  Trigger with phrases like "vercel webhook", "vercel events",
  "vercel deployment.ready", "handle vercel events", "vercel webhook signature".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, webhooks, events, integration]

---
# Vercel Webhooks & Events

## Overview
Handle Vercel webhook events (deployment.created, deployment.ready, deployment.error) with HMAC signature verification. Covers both integration webhooks (Vercel Marketplace) and project-level deploy hooks.

## Prerequisites
- HTTPS endpoint accessible from the internet
- Webhook secret from Vercel dashboard or integration settings
- `crypto` module for HMAC signature verification

## Instructions

### Step 1: Register a Webhook
In the Vercel dashboard:
1. Go to **Settings > Webhooks**
2. Add your endpoint URL (must be HTTPS)
3. Select events to subscribe to
4. Copy the webhook secret for signature verification

Or for Integration webhooks, configure in the Integration Console at `vercel.com/dashboard/integrations`.

### Step 2: Verify Webhook Signature
```typescript
// api/webhooks/vercel.ts
import type { VercelRequest, VercelResponse } from '@vercel/node';
import crypto from 'crypto';

const WEBHOOK_SECRET = process.env.VERCEL_WEBHOOK_SECRET!;

function verifySignature(body: string, signature: string): boolean {
  const expectedSignature = crypto
    .createHmac('sha1', WEBHOOK_SECRET)
    .update(body)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Get raw body for signature verification
  const rawBody = JSON.stringify(req.body);
  const signature = req.headers['x-vercel-signature'] as string;

  if (!signature || !verifySignature(rawBody, signature)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Process the event
  const event = req.body;
  await handleEvent(event);

  res.status(200).json({ received: true });
}
```

### Step 3: Handle Deployment Events
```typescript
// lib/webhook-handlers.ts
interface VercelWebhookEvent {
  id: string;
  type: string;
  createdAt: number;
  payload: {
    deployment: {
      id: string;
      name: string;
      url: string;
      meta: Record<string, string>;
    };
    project: {
      id: string;
      name: string;
    };
    target: 'production' | 'preview' | null;
    user: { id: string; email: string; username: string };
  };
}

async function handleEvent(event: VercelWebhookEvent): Promise<void> {
  switch (event.type) {
    case 'deployment.created':
      console.log(`Deployment started: ${event.payload.deployment.url}`);
      // Notify Slack, update status board, etc.
      break;

    case 'deployment.ready':
      console.log(`Deployment ready: ${event.payload.deployment.url}`);
      // Run smoke tests against the deployment URL
      // Notify team of successful deploy
      if (event.payload.target === 'production') {
        await notifyProductionDeploy(event);
      }
      break;

    case 'deployment.error':
      console.error(`Deployment failed: ${event.payload.deployment.id}`);
      // Alert on-call engineer
      // Create incident ticket
      await notifyDeploymentError(event);
      break;

    case 'deployment.canceled':
      console.log(`Deployment canceled: ${event.payload.deployment.id}`);
      break;

    case 'project.created':
      console.log(`New project: ${event.payload.project.name}`);
      break;

    case 'project.removed':
      console.log(`Project removed: ${event.payload.project.name}`);
      break;

    default:
      console.log(`Unhandled event type: ${event.type}`);
  }
}
```

### Step 4: Idempotency — Prevent Duplicate Processing
```typescript
// lib/idempotency.ts
// Vercel may retry webhook delivery — track processed event IDs
const processedEvents = new Set<string>(); // Use Redis in production

async function processWebhookIdempotent(
  event: VercelWebhookEvent,
  handler: (e: VercelWebhookEvent) => Promise<void>
): Promise<boolean> {
  if (processedEvents.has(event.id)) {
    console.log(`Skipping duplicate event: ${event.id}`);
    return false;
  }

  await handler(event);
  processedEvents.add(event.id);
  return true;
}
```

### Step 5: Slack Notification Example
```typescript
// lib/notifications.ts
async function notifyProductionDeploy(event: VercelWebhookEvent): Promise<void> {
  const { deployment, project, user } = event.payload;

  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `Production deploy complete`,
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: [
              `*${project.name}* deployed to production`,
              `By: ${user.username}`,
              `URL: https://${deployment.url}`,
              `Commit: ${deployment.meta?.githubCommitMessage ?? 'N/A'}`,
            ].join('\n'),
          },
        },
      ],
    }),
  });
}

async function notifyDeploymentError(event: VercelWebhookEvent): Promise<void> {
  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `Deployment FAILED for ${event.payload.project.name} — ${event.payload.deployment.id}`,
    }),
  });
}
```

### Step 6: Test Webhooks Locally
```bash
# Use the Vercel CLI to test webhook signatures
# Or use a tunnel service for local testing
npx localtunnel --port 3000
# Gives you a public URL like https://xxx.loca.lt

# Send a test webhook payload
curl -X POST http://localhost:3000/api/webhooks/vercel \
  -H "Content-Type: application/json" \
  -H "x-vercel-signature: $(echo -n '{"type":"deployment.ready","id":"test"}' | openssl dgst -sha1 -hmac 'your-secret' | awk '{print $2}')" \
  -d '{"type":"deployment.ready","id":"test"}'
```

## Webhook Event Types

| Event | Trigger |
|-------|---------|
| `deployment.created` | New deployment started building |
| `deployment.ready` | Deployment build completed successfully |
| `deployment.error` | Deployment build failed |
| `deployment.canceled` | Deployment was canceled |
| `project.created` | New project created |
| `project.removed` | Project deleted |
| `domain.created` | Domain added to project |
| `integration.configuration.removed` | Integration uninstalled |

## Output
- Webhook endpoint with HMAC signature verification
- Event handlers for deployment lifecycle events
- Idempotent processing preventing duplicates
- Slack notifications for production deploys and failures

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Invalid signature` | Wrong webhook secret or body mismatch | Verify secret matches dashboard, use raw body for HMAC |
| Webhook not received | Endpoint not publicly accessible | Ensure HTTPS, check firewall rules |
| Duplicate processing | Webhook retried by Vercel | Implement idempotency with event ID tracking |
| `504 timeout` on webhook endpoint | Handler takes too long | Return 200 immediately, process async in background |
| Missing `x-vercel-signature` | Not a real Vercel webhook | Reject requests without the signature header |

## Resources
- [Vercel Webhooks API](https://vercel.com/docs/webhooks/webhooks-api)
- [Setting Up Webhooks](https://vercel.com/docs/webhooks)
- [Deploy Hooks](https://vercel.com/docs/deploy-hooks)
- [Integration Webhooks](https://vercel.com/docs/integrations/create-integration)

## Next Steps
For performance optimization, see `vercel-performance-tuning`.
