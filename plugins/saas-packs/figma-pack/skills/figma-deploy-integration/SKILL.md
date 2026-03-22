---
name: figma-deploy-integration
description: |
  Deploy Figma-powered applications to Vercel, Cloud Run, and Fly.io.
  Use when deploying webhook receivers, design token APIs,
  or Figma-connected web apps to production platforms.
  Trigger with phrases like "deploy figma", "figma Vercel",
  "figma production deploy", "figma Cloud Run".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Deploy Integration

## Overview
Deploy Figma webhook receivers and design API services to production platforms with proper secret management and health checks.

## Prerequisites
- Figma PAT for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application tested locally with Figma API

## Instructions

### Step 1: Vercel Deployment (Webhook Receiver)
```bash
# Store Figma secrets
vercel env add FIGMA_PAT production
vercel env add FIGMA_WEBHOOK_PASSCODE production

# Deploy
vercel --prod
```

```typescript
// api/webhooks/figma.ts (Vercel serverless function)
import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

export async function POST(req: NextRequest) {
  const payload = await req.json();

  // Verify passcode
  const expected = process.env.FIGMA_WEBHOOK_PASSCODE!;
  const received = payload.passcode || '';
  if (!crypto.timingSafeEqual(Buffer.from(received), Buffer.from(expected))) {
    return NextResponse.json({ error: 'Invalid passcode' }, { status: 401 });
  }

  // Process webhook event
  switch (payload.event_type) {
    case 'FILE_UPDATE':
      console.log(`File updated: ${payload.file_name} (${payload.file_key})`);
      // Trigger token re-sync, invalidate cache, etc.
      break;
    case 'FILE_COMMENT':
      console.log(`New comment on ${payload.file_name}`);
      break;
    case 'LIBRARY_PUBLISH':
      console.log(`Library published: ${payload.file_name}`);
      break;
  }

  return NextResponse.json({ received: true });
}

export const config = { maxDuration: 10 };
```

### Step 2: Google Cloud Run (Design Token API)
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY dist/ ./dist/
ENV PORT=8080
CMD ["node", "dist/server.js"]
```

```bash
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE="figma-token-api"
REGION="us-central1"

# Store PAT in Secret Manager
echo -n "${FIGMA_PAT}" | gcloud secrets create figma-pat --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE
gcloud run deploy $SERVICE \
  --image gcr.io/$PROJECT_ID/$SERVICE \
  --region $REGION \
  --platform managed \
  --set-secrets="FIGMA_PAT=figma-pat:latest" \
  --allow-unauthenticated \
  --max-instances=5 \
  --timeout=30s
```

### Step 3: Fly.io (Persistent Webhook Service)
```toml
# fly.toml
app = "figma-webhook-service"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true
  min_machines_running = 1

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"
```

```bash
fly secrets set FIGMA_PAT=figd_your-token
fly secrets set FIGMA_WEBHOOK_PASSCODE=your-passcode
fly deploy
```

### Step 4: Health Check Endpoint
```typescript
// src/health.ts -- works on any platform
import { figmaFetch } from './figma-client';

export async function healthHandler(req: Request): Promise<Response> {
  const start = Date.now();

  try {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': process.env.FIGMA_PAT! },
      signal: AbortSignal.timeout(5000),
    });

    return Response.json({
      status: res.ok ? 'healthy' : 'degraded',
      figma: {
        authenticated: res.ok,
        latencyMs: Date.now() - start,
      },
      timestamp: new Date().toISOString(),
    });
  } catch {
    return Response.json({
      status: 'unhealthy',
      figma: { authenticated: false, latencyMs: Date.now() - start },
    }, { status: 503 });
  }
}
```

## Output
- Application deployed with Figma secrets configured
- Webhook endpoint receiving Figma events
- Health check validating Figma connectivity
- Platform-specific optimizations applied

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found in runtime | Wrong env name | Verify with platform CLI (`vercel env ls`) |
| Webhook timeout | Processing too slow | Return 200 immediately, process async |
| Cold start latency | Serverless cold boot | Use Fly.io `min_machines_running: 1` or Cloud Run min instances |
| Health check fails | PAT expired | Rotate token via platform secret management |

## Resources
- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Fly.io Documentation](https://fly.io/docs)

## Next Steps
For webhook handling, see `figma-webhooks-events`.
