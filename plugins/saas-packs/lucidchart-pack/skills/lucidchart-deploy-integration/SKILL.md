---
name: lucidchart-deploy-integration
description: |
  Deploy Lucidchart integrations to production platforms.
  Use when deploying Lucidchart-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy lucidchart", "lucidchart production",
  "lucidchart production deploy", "lucidchart CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lucidchart]
---

# Lucidchart Deploy Integration

## Overview

Deploy Lucidchart integration as a CI/CD pipeline step that exports assets,
syncs design tokens, or generates code from design files during the build.


## Prerequisites
- Lucidchart API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Vercel Deployment

### Environment Setup
```bash
vercel secrets add lucidchart_api_key sk_live_***
vercel secrets add lucidchart_webhook_secret whsec_***
vercel link
vercel --prod
```

### vercel.json Configuration
```json
{
  "env": {
    "LUCIDCHART_API_KEY": "@lucidchart_api_key"
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
app = "my-lucidchart-app"
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
fly secrets set LUCIDCHART_API_KEY=sk_live_***
fly deploy
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const lucidchartStatus = await checkLucidchartConnection();

  return Response.json({
    status: lucidchartStatus ? 'healthy' : 'degraded',
    services: {
      lucidchart: lucidchartStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Lucidchart API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Lucidchart integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Lucidchart connectivity.

## Output
- Application deployed to production
- Lucidchart secrets securely configured
- Health check endpoint functional
- Environment-specific configuration in place

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing configuration | Add secret via platform CLI |
| Deploy timeout | Large build | Increase build timeout |
| Health check fails | Wrong API key | Verify environment variable |
| Cold start issues | No warm-up | Configure minimum instances |

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Lucidchart Deploy Guide](https://docs.lucidchart.com/deploy)

## Next Steps
For webhook handling, see `lucidchart-webhooks-events`.