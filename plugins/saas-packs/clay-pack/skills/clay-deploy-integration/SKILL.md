---
name: clay-deploy-integration
description: |
  Deploy Clay-powered applications to Vercel, Cloud Run, or Docker with proper secrets management.
  Use when deploying Clay webhook receivers, enrichment pipelines,
  or CRM sync services to production infrastructure.
  Trigger with phrases like "deploy clay", "clay Vercel", "clay production deploy",
  "clay Cloud Run", "clay Docker", "host clay integration".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(gcloud:*), Bash(docker:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, deployment]

---
# Clay Deploy Integration

## Overview

Deploy applications that integrate with Clay (webhook receivers, enrichment processors, CRM sync services) to production platforms. Clay itself is a hosted SaaS -- you deploy the code that *interacts* with Clay, not Clay itself. The critical requirement is a publicly accessible HTTPS endpoint for Clay's HTTP API columns to call back to.

## Prerequisites

- Application code that handles Clay webhooks or HTTP API callbacks
- Platform CLI installed (vercel, gcloud, or docker)
- Clay webhook URL and/or API key stored securely
- HTTPS endpoint accessible from the public internet

## Instructions

### Step 1: Vercel Deployment (Serverless)

Best for: Webhook receivers, small-scale enrichment handlers.

```bash
# Set Clay secrets in Vercel
vercel env add CLAY_WEBHOOK_URL production
vercel env add CLAY_API_KEY production
vercel env add CLAY_WEBHOOK_SECRET production

# Deploy
vercel --prod
```

```typescript
// api/clay/callback.ts — Vercel serverless function
import type { VercelRequest, VercelResponse } from '@vercel/node';
import crypto from 'crypto';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') return res.status(405).end();

  // Validate webhook signature
  const signature = req.headers['x-clay-signature'] as string;
  const secret = process.env.CLAY_WEBHOOK_SECRET!;
  const expected = crypto.createHmac('sha256', secret)
    .update(JSON.stringify(req.body))
    .digest('hex');

  if (!crypto.timingSafeEqual(Buffer.from(signature || ''), Buffer.from(expected))) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Process enriched data from Clay HTTP API column
  const enrichedLead = req.body;
  console.log('Received enriched lead:', {
    email: enrichedLead.email,
    company: enrichedLead.company_name,
    score: enrichedLead.icp_score,
  });

  // Push to CRM, database, or outreach tool
  await processLead(enrichedLead);

  return res.status(200).json({ status: 'processed' });
}
```

### Step 2: Cloud Run Deployment (Container)

Best for: High-volume enrichment pipelines, CRM sync services.

```dockerfile
# Dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist/ ./dist/
EXPOSE 8080
ENV PORT=8080
CMD ["node", "dist/index.js"]
```

```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/$PROJECT_ID/clay-handler

gcloud run deploy clay-handler \
  --image gcr.io/$PROJECT_ID/clay-handler \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets "CLAY_API_KEY=clay-api-key:latest,CLAY_WEBHOOK_SECRET=clay-webhook-secret:latest" \
  --min-instances 1 \
  --max-instances 10
```

### Step 3: Docker Compose (Self-Hosted)

Best for: On-premise deployments, development staging.

```yaml
# docker-compose.yml
version: '3.8'
services:
  clay-handler:
    build: .
    ports:
      - "3000:3000"
    environment:
      - CLAY_WEBHOOK_URL=${CLAY_WEBHOOK_URL}
      - CLAY_API_KEY=${CLAY_API_KEY}
      - CLAY_WEBHOOK_SECRET=${CLAY_WEBHOOK_SECRET}
      - DATABASE_URL=${DATABASE_URL}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Step 4: Configure Clay to Call Your Deployed Endpoint

Once deployed, update your Clay table's HTTP API column:

1. Get your deployment URL (e.g., `https://clay-handler.vercel.app` or Cloud Run URL)
2. In Clay table, edit the HTTP API column
3. Set URL to: `https://your-deployment.com/api/clay/callback`
4. Test on a single row before enabling auto-run

### Step 5: Health Check Endpoint

```typescript
// src/health.ts — health check that verifies Clay connectivity
app.get('/health', async (req, res) => {
  const checks: Record<string, string> = {
    server: 'ok',
    clay_webhook: 'unknown',
    database: 'unknown',
  };

  // Check Clay webhook reachability
  try {
    const webhookTest = await fetch(process.env.CLAY_WEBHOOK_URL!, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ _health_check: true }),
    });
    checks.clay_webhook = webhookTest.ok ? 'ok' : `error: ${webhookTest.status}`;
  } catch {
    checks.clay_webhook = 'unreachable';
  }

  const allHealthy = Object.values(checks).every(v => v === 'ok');
  res.status(allHealthy ? 200 : 503).json({ status: allHealthy ? 'healthy' : 'degraded', checks });
});
```

### Step 6: Production Environment Variables

```bash
# Required for all deployments
CLAY_WEBHOOK_URL=https://app.clay.com/api/v1/webhooks/your-id
CLAY_WEBHOOK_SECRET=your-shared-secret

# Optional (Enterprise only)
CLAY_API_KEY=clay_ent_your_key

# Application-specific
DATABASE_URL=postgresql://...
CRM_API_KEY=your-crm-key
PORT=3000
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Clay can't reach callback | Endpoint not public HTTPS | Verify URL is accessible, check firewall |
| Cold start timeout | Serverless function too slow | Set min-instances=1 on Cloud Run |
| Missing secrets in deploy | Env vars not configured | Add via platform CLI before deploying |
| Health check fails | Clay webhook URL invalid | Re-copy webhook URL from Clay table |

## Resources

- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Clay University -- HTTP API Integration](https://university.clay.com/docs/http-api-integration-overview)

## Next Steps

For webhook handling patterns, see `clay-webhooks-events`.
