---
name: fathom-deploy-integration
description: |
  Deploy Fathom integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Fathom-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy fathom", "fathom Vercel",
  "fathom production deploy", "fathom Cloud Run", "fathom Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fathom]
---

# Fathom Deploy Integration

## Overview
Deploy Fathom-powered applications to popular platforms with proper secrets management.

## Prerequisites
- Fathom API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented

## Vercel Deployment

### Environment Setup
```bash
# Add Fathom secrets to Vercel
vercel secrets add fathom_api_key sk_live_***
vercel secrets add fathom_webhook_secret whsec_***

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
    "FATHOM_API_KEY": "@fathom_api_key"
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
app = "my-fathom-app"
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
# Set Fathom secrets
fly secrets set FATHOM_API_KEY=sk_live_***
fly secrets set FATHOM_WEBHOOK_SECRET=whsec_***

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
SERVICE_NAME="fathom-service"
REGION="us-central1"

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets=FATHOM_API_KEY=fathom-api-key:latest
```

## Environment Configuration Pattern

```typescript
// config/fathom.ts
interface FathomConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  webhookSecret?: string;
}

export function getFathomConfig(): FathomConfig {
  const env = process.env.NODE_ENV || 'development';

  return {
    apiKey: process.env.FATHOM_API_KEY!,
    environment: env as FathomConfig['environment'],
    webhookSecret: process.env.FATHOM_WEBHOOK_SECRET,
  };
}
```

## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const fathomStatus = await checkFathomConnection();

  return Response.json({
    status: fathomStatus ? 'healthy' : 'degraded',
    services: {
      fathom: fathomStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide below.

### Step 2: Configure Secrets
Store Fathom API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Fathom integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Fathom connectivity.

## Output
- Application deployed to production
- Fathom secrets securely configured
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
    vercel secrets add fathom_api_key "$FATHOM_API_KEY"
    vercel --prod
    ;;
  fly)
    fly secrets set FATHOM_API_KEY="$FATHOM_API_KEY"
    fly deploy
    ;;
esac
```

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Fathom Deploy Guide](https://docs.fathom.com/deploy)

## Next Steps
For webhook handling, see `fathom-webhooks-events`.