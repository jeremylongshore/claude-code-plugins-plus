---
name: notion-deploy-integration
description: |
  Deploy Notion integrations to Vercel, Fly.io, and Cloud Run.
  Use when deploying Notion-powered applications to production,
  configuring platform-specific secrets, or setting up webhook receivers.
  Trigger with phrases like "deploy notion", "notion Vercel",
  "notion production deploy", "notion Cloud Run", "notion Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Deploy Integration

## Overview
Deploy Notion-powered applications (API backends, webhook receivers, sync services) to Vercel, Fly.io, or Google Cloud Run with proper secrets management.

## Prerequisites
- Working Notion integration tested locally
- Production `NOTION_TOKEN`
- Platform CLI installed (`vercel`, `fly`, or `gcloud`)

## Instructions

### Step 1: Vercel (Serverless Functions)
Best for: Next.js apps, API routes, webhook endpoints.

```bash
# Set secrets
vercel env add NOTION_TOKEN production
# Paste your ntn_xxx token when prompted

# Deploy
vercel --prod
```

**API Route Example (Next.js):**
```typescript
// app/api/notion/query/route.ts
import { Client } from '@notionhq/client';
import { NextResponse } from 'next/server';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

export async function POST(request: Request) {
  const { databaseId, filter } = await request.json();

  try {
    const response = await notion.databases.query({
      database_id: databaseId,
      filter,
      page_size: 50,
    });

    const pages = response.results
      .filter((p): p is any => 'properties' in p)
      .map(page => ({
        id: page.id,
        title: page.properties.Name?.title?.[0]?.plain_text ?? '',
        lastEdited: page.last_edited_time,
      }));

    return NextResponse.json({ pages, hasMore: response.has_more });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.code ?? 'unknown', message: error.message },
      { status: error.status ?? 500 }
    );
  }
}
```

### Step 2: Fly.io (Long-Running Services)
Best for: Webhook receivers, sync daemons, services needing persistent connections.

```toml
# fly.toml
app = "my-notion-service"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
```

```bash
# Set secrets
fly secrets set NOTION_TOKEN=ntn_xxx

# Deploy
fly deploy

# Verify
fly status
curl https://my-notion-service.fly.dev/health
```

### Step 3: Google Cloud Run (Container-Based)
Best for: GCP-native deployments, VPC access, Cloud Scheduler jobs.

```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist/ ./dist/
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```bash
# Create secret in Secret Manager
echo -n "ntn_xxx" | gcloud secrets create notion-token --data-file=-

# Build and deploy
gcloud run deploy notion-service \
  --source . \
  --region us-central1 \
  --platform managed \
  --set-secrets=NOTION_TOKEN=notion-token:latest \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=10

# Verify
gcloud run services describe notion-service --region us-central1 --format='value(status.url)'
```

### Step 4: Health Check Endpoint
Include in every deployment:

```typescript
import { Client, isNotionClientError } from '@notionhq/client';
import express from 'express';

const app = express();
const notion = new Client({ auth: process.env.NOTION_TOKEN });

app.get('/health', async (req, res) => {
  const checks: Record<string, any> = {
    service: 'healthy',
    timestamp: new Date().toISOString(),
  };

  try {
    const start = Date.now();
    await notion.users.me({});
    checks.notion = { connected: true, latencyMs: Date.now() - start };
  } catch (error) {
    checks.notion = {
      connected: false,
      error: isNotionClientError(error) ? error.code : 'unknown',
    };
    checks.service = 'degraded';
  }

  const status = checks.service === 'healthy' ? 200 : 503;
  res.status(status).json(checks);
});

app.listen(process.env.PORT || 3000);
```

### Step 5: Webhook Receiver Deployment
```typescript
// Notion webhook handler — works on any platform
app.post('/webhooks/notion', express.json(), async (req, res) => {
  // Verification handshake (sent during webhook setup)
  if (req.body.type === 'url_verification') {
    return res.json({ challenge: req.body.challenge });
  }

  // Process event asynchronously (respond immediately)
  res.status(200).json({ received: true });

  // Handle event after response
  try {
    const { type, data } = req.body;
    console.log(`Webhook event: ${type}`, data?.id);

    switch (type) {
      case 'page.created':
      case 'page.content_updated':
      case 'page.properties_updated':
        await handlePageEvent(data);
        break;
      case 'page.deleted':
        await handlePageDeleted(data);
        break;
      default:
        console.log(`Unhandled event type: ${type}`);
    }
  } catch (error) {
    console.error('Webhook processing failed:', error);
  }
});
```

## Output
- Application deployed to production platform
- `NOTION_TOKEN` securely stored in platform secrets
- Health check endpoint verifying Notion connectivity
- Webhook receiver (if applicable) responding to events

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found at runtime | Wrong secret name | Check platform secret configuration |
| Cold start timeout | First request too slow | Set min instances > 0 |
| Health check failing | Token expired | Rotate token in secret manager |
| Webhook verification failing | Wrong URL | Ensure HTTPS and correct path |

## Examples

### Quick Deploy (Platform-Agnostic)
```bash
#!/bin/bash
case "$1" in
  vercel) vercel env add NOTION_TOKEN production && vercel --prod ;;
  fly)    fly secrets set NOTION_TOKEN="$NOTION_TOKEN" && fly deploy ;;
  gcloud) gcloud run deploy notion-svc --source . --set-secrets=NOTION_TOKEN=notion-token:latest ;;
  *)      echo "Usage: deploy.sh [vercel|fly|gcloud]" ;;
esac
```

## Resources
- [Vercel Environment Variables](https://vercel.com/docs/projects/environment-variables)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Notion Webhooks](https://developers.notion.com/reference/webhooks)

## Next Steps
For webhook handling details, see `notion-webhooks-events`.
