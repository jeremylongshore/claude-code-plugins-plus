---
name: supabase-deploy-integration
description: |
  Supabase deployment patterns for Vercel, Fly.io, and Cloud Run.
  Trigger phrases: "deploy supabase", "supabase Vercel",
  "supabase production deploy", "supabase Cloud Run".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Deploy Integration

## Overview
Deploy Supabase-powered applications to popular platforms.

## Vercel Deployment

### Environment Setup
```bash
# Add Supabase secrets to Vercel
vercel secrets add supabase_api_key sk_live_***
vercel secrets add supabase_webhook_secret whsec_***

# Link to project
vercel link

# Deploy preview
vercel

# Deploy production
vercel --prod
```

### vercel.json Configuration
```json
{
  "env": {
    "SUPABASE_API_KEY": "@supabase_api_key"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

## Fly.io Deployment

### fly.toml
```toml
app = "my-supabase-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
```

### Secrets
```bash
# Set Supabase secrets
fly secrets set SUPABASE_API_KEY=sk_live_***
fly secrets set SUPABASE_WEBHOOK_SECRET=whsec_***

# Deploy
fly deploy
```

## Google Cloud Run

### Dockerfile
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["npm", "start"]
```

### Deploy Script
```bash
#!/bin/bash
# deploy-cloud-run.sh

PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE_NAME="supabase-service"
REGION="us-central1"

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets=SUPABASE_API_KEY=supabase-api-key:latest
```

## Environment Configuration Pattern

```typescript
// config/supabase.ts
interface SupabaseConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  webhookSecret?: string;
}

export function getSupabaseConfig(): SupabaseConfig {
  const env = process.env.NODE_ENV || 'development';

  return {
    apiKey: process.env.SUPABASE_API_KEY!,
    environment: env as SupabaseConfig['environment'],
    webhookSecret: process.env.SUPABASE_WEBHOOK_SECRET,
  };
}
```

## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const supabaseStatus = await checkSupabaseConnection();

  return Response.json({
    status: supabaseStatus ? 'healthy' : 'degraded',
    services: {
      supabase: supabaseStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Next Steps
For webhook handling, see `supabase-webhooks-events`.