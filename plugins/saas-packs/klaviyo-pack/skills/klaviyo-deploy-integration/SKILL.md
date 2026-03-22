---
name: klaviyo-deploy-integration
description: |
  Deploy Klaviyo integrations to production platforms.
  Use when deploying Klaviyo-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy klaviyo", "klaviyo production",
  "klaviyo production deploy", "klaviyo CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klaviyo]
---

# Klaviyo Deploy Integration

## Overview

Deploy Klaviyo integrations as webhook workers — always-on endpoints that
receive events (contact created, message sent) and trigger downstream actions.


## Prerequisites
- Klaviyo API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Webhook Worker (Recommended for Communication)

### Why Webhooks?
Klaviyo sends events (message delivered, user replied)
to your endpoint. Your worker processes these events and triggers downstream actions.

### Webhook Endpoint
```typescript
// api/webhooks/klaviyo.ts
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
fly secrets set KLAVIYO_API_KEY="$KLAVIYO_API_KEY"
fly secrets set KLAVIYO_WEBHOOK_SECRET="$KLAVIYO_WEBHOOK_SECRET"
fly deploy
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const klaviyoStatus = await checkKlaviyoConnection();

  return Response.json({
    status: klaviyoStatus ? 'healthy' : 'degraded',
    services: {
      klaviyo: klaviyoStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Klaviyo API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Klaviyo integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Klaviyo connectivity.

## Output
- Application deployed to production
- Klaviyo secrets securely configured
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
- [Klaviyo Deploy Guide](https://docs.klaviyo.com/deploy)

## Next Steps
For webhook handling, see `klaviyo-webhooks-events`.