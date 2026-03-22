---
name: obsidian-deploy-integration
description: |
  Deploy Obsidian integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Obsidian-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy obsidian", "obsidian Vercel",
  "obsidian production deploy", "obsidian Cloud Run", "obsidian Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, obsidian]
---

# Obsidian Deploy Integration

## Overview
Deploy Obsidian-powered applications to popular platforms with proper secrets management.

## Prerequisites
- Obsidian API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented

## Vercel Deployment

### Environment Setup
```bash
# Add Obsidian secrets to Vercel
vercel secrets add obsidian_api_key sk_live_***
vercel secrets add obsidian_webhook_secret whsec_***

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
    "OBSIDIAN_API_KEY": "@obsidian_api_key"
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
app = "my-obsidian-app"
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
# Set Obsidian secrets
fly secrets set OBSIDIAN_API_KEY=sk_live_***
fly secrets set OBSIDIAN_WEBHOOK_SECRET=whsec_***

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
SERVICE_NAME="obsidian-service"
REGION="us-central1"

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets=OBSIDIAN_API_KEY=obsidian-api-key:latest
```

## Environment Configuration Pattern

```typescript
// config/obsidian.ts
interface ObsidianConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  webhookSecret?: string;
}

export function getObsidianConfig(): ObsidianConfig {
  const env = process.env.NODE_ENV || 'development';

  return {
    apiKey: process.env.OBSIDIAN_API_KEY!,
    environment: env as ObsidianConfig['environment'],
    webhookSecret: process.env.OBSIDIAN_WEBHOOK_SECRET,
  };
}
```

## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const obsidianStatus = await checkObsidianConnection();

  return Response.json({
    status: obsidianStatus ? 'healthy' : 'degraded',
    services: {
      obsidian: obsidianStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide below.

### Step 2: Configure Secrets
Store Obsidian API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Obsidian integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Obsidian connectivity.

## Output
- Application deployed to production
- Obsidian secrets securely configured
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
    vercel secrets add obsidian_api_key "$OBSIDIAN_API_KEY"
    vercel --prod
    ;;
  fly)
    fly secrets set OBSIDIAN_API_KEY="$OBSIDIAN_API_KEY"
    fly deploy
    ;;
esac
```

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Obsidian Deploy Guide](https://docs.obsidian.com/deploy)

## Next Steps
For webhook handling, see `obsidian-webhooks-events`.