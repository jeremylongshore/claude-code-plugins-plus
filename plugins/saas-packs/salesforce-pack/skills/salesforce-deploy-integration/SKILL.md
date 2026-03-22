---
name: salesforce-deploy-integration
description: |
  Deploy Salesforce integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Salesforce-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy salesforce", "salesforce Vercel",
  "salesforce production deploy", "salesforce Cloud Run", "salesforce Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesforce]
---

# Salesforce Deploy Integration

## Overview
Deploy Salesforce-powered applications to popular platforms with proper secrets management.

## Prerequisites
- Salesforce API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented

## Vercel Deployment

### Environment Setup
```bash
# Add Salesforce secrets to Vercel
vercel secrets add salesforce_api_key sk_live_***
vercel secrets add salesforce_webhook_secret whsec_***

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
    "SALESFORCE_API_KEY": "@salesforce_api_key"
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
app = "my-salesforce-app"
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
# Set Salesforce secrets
fly secrets set SALESFORCE_API_KEY=sk_live_***
fly secrets set SALESFORCE_WEBHOOK_SECRET=whsec_***

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
SERVICE_NAME="salesforce-service"
REGION="us-central1"

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets=SALESFORCE_API_KEY=salesforce-api-key:latest
```

## Environment Configuration Pattern

```typescript
// config/salesforce.ts
interface SalesforceConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  webhookSecret?: string;
}

export function getSalesforceConfig(): SalesforceConfig {
  const env = process.env.NODE_ENV || 'development';

  return {
    apiKey: process.env.SALESFORCE_API_KEY!,
    environment: env as SalesforceConfig['environment'],
    webhookSecret: process.env.SALESFORCE_WEBHOOK_SECRET,
  };
}
```

## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const salesforceStatus = await checkSalesforceConnection();

  return Response.json({
    status: salesforceStatus ? 'healthy' : 'degraded',
    services: {
      salesforce: salesforceStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide below.

### Step 2: Configure Secrets
Store Salesforce API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Salesforce integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Salesforce connectivity.

## Output
- Application deployed to production
- Salesforce secrets securely configured
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
    vercel secrets add salesforce_api_key "$SALESFORCE_API_KEY"
    vercel --prod
    ;;
  fly)
    fly secrets set SALESFORCE_API_KEY="$SALESFORCE_API_KEY"
    fly deploy
    ;;
esac
```

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Salesforce Deploy Guide](https://docs.salesforce.com/deploy)

## Next Steps
For webhook handling, see `salesforce-webhooks-events`.