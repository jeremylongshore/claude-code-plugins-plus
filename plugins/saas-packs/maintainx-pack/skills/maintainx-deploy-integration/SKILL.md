---
name: maintainx-deploy-integration
description: |
  Deploy MaintainX integrations to production platforms.
  Use when deploying MaintainX-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy maintainx", "maintainx production",
  "maintainx production deploy", "maintainx CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, maintainx]
---

# MaintainX Deploy Integration

## Overview

Deploy MaintainX-powered applications to popular platforms with proper secrets management.


## Prerequisites
- MaintainX API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Vercel Deployment

### Environment Setup
```bash
vercel secrets add maintainx_api_key sk_live_***
vercel secrets add maintainx_webhook_secret whsec_***
vercel link
vercel --prod
```

### vercel.json Configuration
```json
{
  "env": {
    "MAINTAINX_API_KEY": "@maintainx_api_key"
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
app = "my-maintainx-app"
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
fly secrets set MAINTAINX_API_KEY=sk_live_***
fly deploy
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const maintainxStatus = await checkMaintainXConnection();

  return Response.json({
    status: maintainxStatus ? 'healthy' : 'degraded',
    services: {
      maintainx: maintainxStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store MaintainX API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with MaintainX integration.

### Step 4: Verify Health
Test the health check endpoint to confirm MaintainX connectivity.

## Output
- Application deployed to production
- MaintainX secrets securely configured
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
- [MaintainX Deploy Guide](https://docs.maintainx.com/deploy)

## Next Steps
For webhook handling, see `maintainx-webhooks-events`.