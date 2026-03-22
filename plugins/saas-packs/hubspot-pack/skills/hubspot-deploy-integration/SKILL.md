---
name: hubspot-deploy-integration
description: |
  Deploy HubSpot integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying HubSpot-powered applications, configuring platform secrets,
  or setting up deployment pipelines with HubSpot access tokens.
  Trigger with phrases like "deploy hubspot", "hubspot Vercel",
  "hubspot Cloud Run", "hubspot Fly.io", "hubspot production deploy".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Deploy Integration

## Overview

Deploy HubSpot-powered applications to Vercel, Fly.io, or Google Cloud Run with proper secret management and health checks.

## Prerequisites

- HubSpot private app token for production
- Platform CLI installed (vercel, fly, or gcloud)
- Application code with health check endpoint

## Instructions

### Step 1: Vercel Deployment

```bash
# Add HubSpot secrets to Vercel
vercel env add HUBSPOT_ACCESS_TOKEN production
# Paste: pat-na1-xxxxx

# Optional webhook secret
vercel env add HUBSPOT_WEBHOOK_SECRET production
```

```json
// vercel.json
{
  "env": {
    "HUBSPOT_ACCESS_TOKEN": "@hubspot-access-token"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

```typescript
// api/hubspot/contacts.ts (Vercel serverless function)
import * as hubspot from '@hubspot/api-client';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3,
});

export default async function handler(req: Request) {
  if (req.method === 'GET') {
    const contacts = await client.crm.contacts.basicApi.getPage(
      10, undefined, ['firstname', 'lastname', 'email']
    );
    return Response.json(contacts.results);
  }

  if (req.method === 'POST') {
    const body = await req.json();
    const contact = await client.crm.contacts.basicApi.create({
      properties: body,
      associations: [],
    });
    return Response.json(contact, { status: 201 });
  }
}
```

```bash
# Deploy
vercel --prod
```

### Step 2: Fly.io Deployment

```toml
# fly.toml
app = "my-hubspot-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"
```

```bash
# Set HubSpot secrets
fly secrets set HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxx
fly secrets set HUBSPOT_WEBHOOK_SECRET=your-secret

# Deploy
fly deploy

# Verify health
fly status
curl https://my-hubspot-app.fly.dev/health
```

### Step 3: Google Cloud Run Deployment

```bash
#!/bin/bash
# deploy-cloud-run.sh
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE_NAME="hubspot-service"
REGION="us-central1"

# Store token in Secret Manager
echo -n "pat-na1-xxxxx" | gcloud secrets create hubspot-access-token \
  --data-file=- --replication-policy="automatic"

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding hubspot-access-token \
  --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --set-secrets=HUBSPOT_ACCESS_TOKEN=hubspot-access-token:latest \
  --min-instances=1 \
  --max-instances=10 \
  --memory=512Mi \
  --timeout=30s
```

### Step 4: Health Check for All Platforms

```typescript
// src/health.ts
import * as hubspot from '@hubspot/api-client';

export async function healthCheck(): Promise<{
  status: string;
  services: Record<string, any>;
  timestamp: string;
}> {
  const client = new hubspot.Client({
    accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  });

  let hubspotStatus = { connected: false, latencyMs: 0 };
  const start = Date.now();

  try {
    await client.crm.contacts.basicApi.getPage(1);
    hubspotStatus = { connected: true, latencyMs: Date.now() - start };
  } catch {
    hubspotStatus = { connected: false, latencyMs: Date.now() - start };
  }

  return {
    status: hubspotStatus.connected ? 'healthy' : 'degraded',
    services: { hubspot: hubspotStatus },
    timestamp: new Date().toISOString(),
  };
}
```

## Output

- Application deployed to chosen platform
- HubSpot access token stored in platform's secret manager
- Health check endpoint verifying HubSpot connectivity
- HTTPS enforced on all endpoints

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found at runtime | Wrong env var name | Check platform secret config |
| Deploy timeout | Large build | Increase build timeout |
| Health check fails | Wrong token for environment | Verify production token |
| Cold start latency | Serverless function | Set `min-instances=1` or use warm-up |

## Resources

- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)
- [Cloud Run with Secret Manager](https://cloud.google.com/run/docs/configuring/secrets)
- [HubSpot Private Apps](https://developers.hubspot.com/docs/guides/apps/private-apps/overview)

## Next Steps

For webhook handling, see `hubspot-webhooks-events`.
