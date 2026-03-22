---
name: canva-deploy-integration
description: |
  Deploy Canva Connect API integrations to Vercel, Fly.io, and Cloud Run.
  Use when deploying Canva-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy canva", "canva Vercel",
  "canva production deploy", "canva Cloud Run", "canva Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Deploy Integration

## Overview

Deploy Canva Connect API integrations to popular platforms with secure OAuth credential management. The Canva API requires server-side token exchange — client secrets and refresh tokens must never reach the browser.

## Prerequisites

- Canva OAuth credentials (client ID + secret)
- Platform CLI installed (vercel, fly, or gcloud)
- HTTPS domain for OAuth redirect URIs
- Application code ready for deployment

## Vercel

### Secrets

```bash
# Add Canva OAuth credentials
vercel env add CANVA_CLIENT_ID production
vercel env add CANVA_CLIENT_SECRET production
vercel env add CANVA_REDIRECT_URI production  # e.g. https://your-app.vercel.app/auth/canva/callback
```

### vercel.json

```json
{
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "no-store" }
      ]
    }
  ]
}
```

### API Route (Next.js / Vercel Functions)

```typescript
// api/canva/callback.ts — OAuth callback
export async function GET(req: Request) {
  const url = new URL(req.url);
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');

  // Exchange code for tokens (server-side only)
  const tokens = await exchangeCodeForToken({
    code: code!,
    codeVerifier: await getVerifierFromSession(state!),
    clientId: process.env.CANVA_CLIENT_ID!,
    clientSecret: process.env.CANVA_CLIENT_SECRET!,
    redirectUri: process.env.CANVA_REDIRECT_URI!,
  });

  // Store tokens in your database
  await saveTokens(userId, tokens);
  return Response.redirect('/dashboard');
}
```

## Fly.io

### fly.toml

```toml
app = "my-canva-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"
  CANVA_REDIRECT_URI = "https://my-canva-app.fly.dev/auth/canva/callback"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
```

### Secrets

```bash
fly secrets set CANVA_CLIENT_ID=OCAxxxxxxxxxxxxxxxx
fly secrets set CANVA_CLIENT_SECRET=xxxxxxxxxxxxxxxx
fly deploy
```

## Google Cloud Run

### Deploy Script

```bash
#!/bin/bash
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE_NAME="canva-integration"
REGION="us-central1"

# Store secrets in Secret Manager
echo -n "OCAxxxxxxxxxxxxxxxx" | gcloud secrets create canva-client-id --data-file=-
echo -n "xxxxxxxxxxxxxxxx" | gcloud secrets create canva-client-secret --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="CANVA_CLIENT_ID=canva-client-id:latest,CANVA_CLIENT_SECRET=canva-client-secret:latest" \
  --set-env-vars="CANVA_REDIRECT_URI=https://$SERVICE_NAME-xxxxx.run.app/auth/canva/callback"
```

## Health Check

```typescript
// api/health.ts — confirms Canva API connectivity
export async function GET() {
  const start = Date.now();
  let canvaStatus: string;

  try {
    const res = await fetch('https://api.canva.com/rest/v1/users/me', {
      headers: { 'Authorization': `Bearer ${await getServiceToken()}` },
      signal: AbortSignal.timeout(5000),
    });
    canvaStatus = res.ok ? 'healthy' : `error:${res.status}`;
  } catch {
    canvaStatus = 'unreachable';
  }

  return Response.json({
    status: canvaStatus === 'healthy' ? 'healthy' : 'degraded',
    services: { canva: { status: canvaStatus, latencyMs: Date.now() - start } },
    timestamp: new Date().toISOString(),
  });
}
```

## Redirect URI Configuration

After deploying, update your Canva integration settings with the production redirect URI:

| Platform | Redirect URI Pattern |
|----------|---------------------|
| Vercel | `https://your-app.vercel.app/auth/canva/callback` |
| Fly.io | `https://your-app.fly.dev/auth/canva/callback` |
| Cloud Run | `https://your-service-xxxxx.run.app/auth/canva/callback` |
| Custom Domain | `https://app.yourdomain.com/auth/canva/callback` |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| OAuth callback fails | Redirect URI mismatch | Update URI in Canva dashboard |
| Secret not found | Missing env var | Add via platform CLI |
| Cold start timeout | OAuth exchange slow | Set min instances to 1 |
| HTTPS required | HTTP redirect URI | All platforms default to HTTPS |

## Resources

- [Canva Creating Integrations](https://www.canva.dev/docs/connect/creating-integrations/)
- [Vercel Docs](https://vercel.com/docs)
- [Fly.io Docs](https://fly.io/docs)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

## Next Steps

For webhook handling, see `canva-webhooks-events`.
