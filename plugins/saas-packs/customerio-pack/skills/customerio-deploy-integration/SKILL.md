---
name: customerio-deploy-integration
description: |
  Deploy Customer.io integrations to production platforms.
  Use when deploying Customer.io-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy customerio", "customerio production",
  "customerio production deploy", "customerio CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, customerio]
---

# Customer.io Deploy Integration

## Overview

Deploy Customer.io integrations as webhook workers — always-on endpoints that
receive events (contact created, message sent) and trigger downstream actions.


## Prerequisites
- Customer.io API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Webhook Worker (Recommended for Communication)

### Why Webhooks?
Customer.io sends events (message delivered, user replied)
to your endpoint. Your worker processes these events and triggers downstream actions.

### Webhook Endpoint
```typescript
// api/webhooks/customerio.ts
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
fly secrets set CUSTOMERIO_API_KEY="$CUSTOMERIO_API_KEY"
fly secrets set CUSTOMERIO_WEBHOOK_SECRET="$CUSTOMERIO_WEBHOOK_SECRET"
fly deploy
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const customerioStatus = await checkCustomer.ioConnection();

  return Response.json({
    status: customerioStatus ? 'healthy' : 'degraded',
    services: {
      customerio: customerioStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Customer.io API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Customer.io integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Customer.io connectivity.

## Output
- Application deployed to production
- Customer.io secrets securely configured
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
- [Customer.io Deploy Guide](https://docs.customerio.com/deploy)

## Next Steps
For webhook handling, see `customerio-webhooks-events`.