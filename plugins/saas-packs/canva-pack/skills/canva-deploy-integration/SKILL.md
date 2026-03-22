---
name: canva-deploy-integration
description: |
  Deploy Canva integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Canva-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy canva", "canva Vercel",
  "canva production deploy", "canva Cloud Run", "canva Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, canva]
---

# Canva Deploy Integration

## Overview
Deploy Canva-powered applications to popular platforms with proper secrets management.

## Prerequisites
- Canva API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented

## Vercel Deployment

### Environment Setup
```bash
# Add Canva secrets to Vercel
vercel secrets add canva_api_key sk_live_***
vercel secrets add canva_webhook_secret whsec_***

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
    "CANVA_API_KEY": "@canva_api_key"
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
app = "my-canva-app"
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
# Set Canva secrets
fly secrets set CANVA_API_KEY=sk_live_***
fly secrets set CANVA_WEBHOOK_SECRET=whsec_***

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
SERVICE_NAME="canva-service"
REGION="us-central1"

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets=CANVA_API_KEY=canva-api-key:latest
```

## Environment Configuration Pattern

```typescript
// config/canva.ts
interface CanvaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  webhookSecret?: string;
}

export function getCanvaConfig(): CanvaConfig {
  const env = process.env.NODE_ENV || 'development';

  return {
    apiKey: process.env.CANVA_API_KEY!,
    environment: env as CanvaConfig['environment'],
    webhookSecret: process.env.CANVA_WEBHOOK_SECRET,
  };
}
```

## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const canvaStatus = await checkCanvaConnection();

  return Response.json({
    status: canvaStatus ? 'healthy' : 'degraded',
    services: {
      canva: canvaStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide below.

### Step 2: Configure Secrets
Store Canva API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Canva integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Canva connectivity.

## Output
- Application deployed to production
- Canva secrets securely configured
- Health check endpoint functional
- Environment-specific configuration in place

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing configuration | Add secret via platform CLI |
| Deploy timeout | Large build | Increase build timeout |
| Health check fails | Wrong API key | Verify environment variable |
| Cold start issues | No warm-up | Configure minimum instances |

## Examples

### Quick Deploy Script
```bash
#!/bin/bash
# Platform-agnostic deploy helper
case "$1" in
  vercel)
    vercel secrets add canva_api_key "$CANVA_API_KEY"
    vercel --prod
    ;;
  fly)
    fly secrets set CANVA_API_KEY="$CANVA_API_KEY"
    fly deploy
    ;;
esac
```

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Canva Deploy Guide](https://docs.canva.com/deploy)

## Next Steps
For webhook handling, see `canva-webhooks-events`.