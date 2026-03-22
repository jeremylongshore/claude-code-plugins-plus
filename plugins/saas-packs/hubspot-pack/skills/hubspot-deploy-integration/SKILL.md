---
name: hubspot-deploy-integration
description: |
  Deploy HubSpot integrations to production platforms.
  Use when deploying HubSpot-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy hubspot", "hubspot production",
  "hubspot production deploy", "hubspot CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hubspot]
---

# HubSpot Deploy Integration

## Overview

Deploy HubSpot integrations as webhook workers — always-on endpoints that
receive events (contact created, message sent) and trigger downstream actions.


## Prerequisites
- HubSpot API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Webhook Worker (Recommended for Sales/crm)

### Why Webhooks?
HubSpot sends events (contact created, deal stage changed)
to your endpoint. Your worker processes these events and triggers downstream actions.

### Webhook Endpoint
```typescript
// api/webhooks/hubspot.ts
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
fly secrets set HUBSPOT_API_KEY="$HUBSPOT_API_KEY"
fly secrets set HUBSPOT_WEBHOOK_SECRET="$HUBSPOT_WEBHOOK_SECRET"
fly deploy
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const hubspotStatus = await checkHubSpotConnection();

  return Response.json({
    status: hubspotStatus ? 'healthy' : 'degraded',
    services: {
      hubspot: hubspotStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store HubSpot API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with HubSpot integration.

### Step 4: Verify Health
Test the health check endpoint to confirm HubSpot connectivity.

## Output
- Application deployed to production
- HubSpot secrets securely configured
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
- [HubSpot Deploy Guide](https://docs.hubspot.com/deploy)

## Next Steps
For webhook handling, see `hubspot-webhooks-events`.