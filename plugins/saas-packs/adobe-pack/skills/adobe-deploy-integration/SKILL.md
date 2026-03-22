---
name: adobe-deploy-integration
description: |
  Deploy Adobe-powered applications to Vercel, Cloud Run, and Adobe App Builder
  with proper credential injection and health monitoring.
  Use when deploying Adobe API integrations to production platforms.
  Trigger with phrases like "deploy adobe", "adobe Vercel",
  "adobe Cloud Run", "adobe App Builder deploy", "adobe production deploy".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(gcloud:*), Bash(aio:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Deploy Integration

## Overview

Deploy Adobe-powered applications to three platforms: Vercel (serverless), Google Cloud Run (containers), and Adobe App Builder (native Adobe Runtime). Each with proper OAuth credential management.

## Prerequisites

- Adobe OAuth Server-to-Server credentials for production
- Platform CLI installed (`vercel`, `gcloud`, or `aio`)
- Application tested in staging environment

## Instructions

### Option A: Adobe App Builder (Native Adobe Hosting)

App Builder deploys serverless Runtime actions directly to Adobe infrastructure:

```bash
# Login to Adobe I/O CLI (requires IMS auth since AIO CLI v11)
aio login

# Select your project and workspace
aio console project select
aio console workspace select Production

# Deploy all actions, static assets, and event registrations
aio app deploy

# Check deployed actions
aio runtime action list

# View action logs
aio runtime activation list --limit 10
aio runtime activation logs <activationId>
```

```javascript
// app.config.yaml — App Builder configuration
application:
  actions: actions
  web: web-src
  runtimeManifest:
    packages:
      my-adobe-app:
        actions:
          process-image:
            function: actions/process-image/index.js
            runtime: nodejs:20
            inputs:
              ADOBE_CLIENT_ID: $ADOBE_CLIENT_ID
              ADOBE_CLIENT_SECRET: $ADOBE_CLIENT_SECRET
            annotations:
              require-adobe-auth: true
              final: true
```

### Option B: Vercel Deployment

```bash
# Set Adobe credentials as Vercel environment variables
vercel env add ADOBE_CLIENT_ID production
vercel env add ADOBE_CLIENT_SECRET production
vercel env add ADOBE_SCOPES production

# Deploy
vercel --prod
```

```json
// vercel.json
{
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 60
    }
  },
  "env": {
    "ADOBE_CLIENT_ID": "@adobe_client_id",
    "ADOBE_CLIENT_SECRET": "@adobe_client_secret",
    "ADOBE_SCOPES": "@adobe_scopes"
  }
}
```

```typescript
// api/firefly/generate.ts — Vercel serverless function
import type { VercelRequest, VercelResponse } from '@vercel/node';
import { getAccessToken } from '../../src/adobe/client';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') return res.status(405).end();

  try {
    const token = await getAccessToken();
    const fireflyResponse = await fetch(
      'https://firefly-api.adobe.io/v3/images/generate',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'x-api-key': process.env.ADOBE_CLIENT_ID!,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(req.body),
      }
    );

    const result = await fireflyResponse.json();
    return res.status(fireflyResponse.status).json(result);
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
}
```

### Option C: Google Cloud Run

```bash
# Store credentials in Secret Manager
echo -n "${ADOBE_CLIENT_ID}" | gcloud secrets create adobe-client-id --data-file=-
echo -n "${ADOBE_CLIENT_SECRET}" | gcloud secrets create adobe-client-secret --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/${PROJECT_ID}/adobe-service

gcloud run deploy adobe-service \
  --image gcr.io/${PROJECT_ID}/adobe-service \
  --region us-central1 \
  --platform managed \
  --set-secrets="ADOBE_CLIENT_ID=adobe-client-id:latest,ADOBE_CLIENT_SECRET=adobe-client-secret:latest" \
  --set-env-vars="ADOBE_SCOPES=openid,AdobeID,firefly_api" \
  --min-instances=1 \
  --timeout=60s
```

### Health Check Endpoint (All Platforms)

```typescript
// api/health.ts
export async function GET() {
  const checks: Record<string, any> = {};

  // Test Adobe IMS token generation
  try {
    const start = Date.now();
    const token = await getAccessToken();
    checks.adobe = {
      status: 'healthy',
      latencyMs: Date.now() - start,
      tokenLength: token.length,
    };
  } catch (error: any) {
    checks.adobe = {
      status: 'unhealthy',
      error: error.message,
    };
  }

  const overall = Object.values(checks).every(
    (c: any) => c.status === 'healthy'
  ) ? 'healthy' : 'degraded';

  return Response.json({
    status: overall,
    services: checks,
    timestamp: new Date().toISOString(),
  });
}
```

## Output

- Application deployed to chosen platform
- Adobe credentials injected via platform secret management
- Health check endpoint validates IMS connectivity
- Serverless function timeout configured for Adobe API latency

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `aio app deploy` auth error | Not logged in to AIO CLI | Run `aio login` |
| Vercel function timeout | Adobe API takes > 10s | Increase `maxDuration` in vercel.json |
| Cloud Run cold start timeout | Token generation on cold start | Set `min-instances=1` |
| Secret not found | Wrong secret name | Verify with `gcloud secrets list` or `vercel env ls` |

## Resources

- [Adobe App Builder Deployment](https://developer.adobe.com/app-builder/docs/guides/app_builder_guides/deployment/deployment)
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/services/secrets)

## Next Steps

For webhook handling, see `adobe-webhooks-events`.
