---
name: juicebox-deploy-integration
description: |
  Deploy Juicebox integrations to production platforms.
  Use when deploying Juicebox-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy juicebox", "juicebox production",
  "juicebox production deploy", "juicebox CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, juicebox]
---

# Juicebox Deploy Integration

## Overview

Deploy Juicebox integrations as webhook workers — always-on endpoints that
receive events (contact created, message sent) and trigger downstream actions.


## Prerequisites
- Juicebox API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Webhook Worker (Recommended for Sales/crm)

### Why Webhooks?
Juicebox sends events (contact created, deal stage changed)
to your endpoint. Your worker processes these events and triggers downstream actions.

### Webhook Endpoint
```typescript
// api/webhooks/juicebox.ts
export default async function handler(req: Request) {

  const event = await req.json();


  switch (event.type) {

    case 'contact.created':
      await enrichAndAssign(event.data.contact);
      break;
    case 'deal.stage_changed':
      await notifySlack(event.data.deal);
      break;

  }

  return new Response('OK', { status: 200 });
}
```

### Deploy
```bash
# Fly.io — always-on, auto-TLS, persistent
fly secrets set JUICEBOX_API_KEY="$JUICEBOX_API_KEY"
fly secrets set JUICEBOX_WEBHOOK_SECRET="$JUICEBOX_WEBHOOK_SECRET"
fly deploy
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const juiceboxStatus = await checkJuiceboxConnection();

  return Response.json({
    status: juiceboxStatus ? 'healthy' : 'degraded',
    services: {
      juicebox: juiceboxStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Juicebox API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Juicebox integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Juicebox connectivity.

## Output
- Application deployed to production
- Juicebox secrets securely configured
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
- [Juicebox Deploy Guide](https://docs.juicebox.com/deploy)

## Next Steps
For webhook handling, see `juicebox-webhooks-events`.