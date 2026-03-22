---
name: quicknode-deploy-integration
description: |
  Deploy QuickNode integrations to production platforms.
  Use when deploying QuickNode-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy quicknode", "quicknode production",
  "quicknode production deploy", "quicknode CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, quicknode]
---

# QuickNode Deploy Integration

## Overview

Deploy QuickNode integrations as secure webhook workers with HMAC signature
verification, idempotent processing, and dead-letter queues for reliability.


## Prerequisites
- QuickNode API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Webhook Worker (Recommended for Fintech)

### Why Webhooks?
QuickNode sends events (transaction completed, card authorized)
to your endpoint. Your worker processes these events and triggers downstream actions.

### Webhook Endpoint
```typescript
// api/webhooks/quicknode.ts
export default async function handler(req: Request) {

  // CRITICAL: Verify HMAC signature before processing
  const signature = req.headers.get('x-quicknode-signature');
  const body = await req.text();
  const expected = crypto.createHmac('sha256', process.env.QUICKNODE_WEBHOOK_SECRET!)
    .update(body).digest('hex');
  if (!crypto.timingSafeEqual(Buffer.from(signature!), Buffer.from(expected))) {
    return new Response('Invalid signature', { status: 401 });
  }
  const event = JSON.parse(body);


  switch (event.type) {

    case 'transaction.completed':
      await syncToAccounting(event.data.transaction);
      break;
    case 'card.declined':
      await alertTeam(event.data);
      break;

  }

  return new Response('OK', { status: 200 });
}
```

### Deploy
```bash
# Fly.io — always-on, auto-TLS, persistent
fly secrets set QUICKNODE_API_KEY="$QUICKNODE_API_KEY"
fly secrets set QUICKNODE_WEBHOOK_SECRET="$QUICKNODE_WEBHOOK_SECRET"
fly deploy
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const quicknodeStatus = await checkQuickNodeConnection();

  return Response.json({
    status: quicknodeStatus ? 'healthy' : 'degraded',
    services: {
      quicknode: quicknodeStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store QuickNode API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with QuickNode integration.

### Step 4: Verify Health
Test the health check endpoint to confirm QuickNode connectivity.

## Output
- Application deployed to production
- QuickNode secrets securely configured
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
- [QuickNode Deploy Guide](https://docs.quicknode.com/deploy)

## Next Steps
For webhook handling, see `quicknode-webhooks-events`.