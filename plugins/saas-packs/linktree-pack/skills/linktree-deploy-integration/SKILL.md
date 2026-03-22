---
name: linktree-deploy-integration
description: |
  Deploy Linktree integrations to production platforms.
  Use when deploying Linktree-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy linktree", "linktree production",
  "linktree production deploy", "linktree CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linktree]
---

# Linktree Deploy Integration

## Overview

Deploy Linktree integrations as webhook workers — always-on endpoints that
receive events (contact created, message sent) and trigger downstream actions.


## Prerequisites
- Linktree API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Webhook Worker (Recommended for Communication)

### Why Webhooks?
Linktree sends events (message delivered, user replied)
to your endpoint. Your worker processes these events and triggers downstream actions.

### Webhook Endpoint
```typescript
// api/webhooks/linktree.ts
export default async function handler(req: Request) {

  const event = await req.json();


  switch (event.type) {

    case 'message.delivered':
      await updateDeliveryStats(event.data);
      break;
    case 'message.bounced':
      await handleBounce(event.data.recipient);
      break;

  }

  return new Response('OK', { status: 200 });
}
```

### Deploy
```bash
# Fly.io — always-on, auto-TLS, persistent
fly secrets set LINKTREE_API_KEY="$LINKTREE_API_KEY"
fly secrets set LINKTREE_WEBHOOK_SECRET="$LINKTREE_WEBHOOK_SECRET"
fly deploy
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const linktreeStatus = await checkLinktreeConnection();

  return Response.json({
    status: linktreeStatus ? 'healthy' : 'degraded',
    services: {
      linktree: linktreeStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Linktree API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Linktree integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Linktree connectivity.

## Output
- Application deployed to production
- Linktree secrets securely configured
- Health check endpoint functional
- Environment-specific configuration in place

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing configuration | Add secret via platform CLI |
| Deploy timeout | Large build | Increase build timeout |
| Health check fails | Wrong API key | Verify environment variable |
| Cold start issues | No warm-up | Configure minimum instances |

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Linktree Deploy Guide](https://docs.linktree.com/deploy)

## Next Steps
For webhook handling, see `linktree-webhooks-events`.